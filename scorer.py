# =============================================================================
# signals/scorer.py
# =============================================================================
# PURPOSE: The scoring engine. Takes the raw extraction results from detector.py
#          and converts them into a single 0-100 composite score with a full
#          audit trail of how that score was reached.
#
# ARCHITECTURAL DECISION: Keeping scoring SEPARATE from detection is critical.
#   - detector.py is responsible for FINDING signals (pattern matching)
#   - scorer.py is responsible for WEIGHTING signals (judgment)
#
# This means you can tune the weights in this file without touching the
# detection logic, and vice versa. It also makes A/B testing different scoring
# strategies trivial.
#
# SCORING MODEL OVERVIEW:
# The total score is built from five additive components, each capped:
#
#   Component               Max Points   Notes
#   ─────────────────────   ──────────   ──────────────────────────────────────
#   Job Title Score              30      Tier 1 = 30, Tier 2 = 18
#   Pain Theme Score             25      5 pts per unique theme, capped at 25
#   Ownership Score              25      Tiered: strong/moderate/weak
#   Urgency Bonus                10      Amplifies when co-located with pain
#   Analyst Noise Penalty       -20      Applied per noise signal found
#   ─────────────────────   ──────────
#   RAW TOTAL                    70      Before proximity multiplier
#   Proximity Multiplier        x1.43    Scales raw to max 100 when all co-occur
#
# PROXIMITY MULTIPLIER RATIONALE:
# The proximity check answers: "Do the ownership words appear NEAR the pain
# words?" A document where "my team" appears in paragraph 1 and pain words
# appear in paragraph 10 is weaker than one where they're in the same sentence.
# The multiplier ranges from 0.7 (no proximity) to 1.0 (tight co-occurrence),
# scaling the raw score accordingly.
# =============================================================================

import re
from typing import Dict, List, Any
from signals.themes import (
    JOB_TITLE_SIGNALS,
    PAIN_THEMES,
    OWNERSHIP_LANGUAGE,
    ANALYST_NOISE_SIGNALS,
    URGENCY_AMPLIFIERS,
)


# -----------------------------------------------------------------------------
# SCORING CONSTANTS
# These are the weights used by the scoring model.
# Changing these values changes the model's behavior - document any changes.
# -----------------------------------------------------------------------------
TITLE_TIER_1_SCORE = 30        # C-suite / VP level
TITLE_TIER_2_SCORE = 18        # Manager / Lead level
PAIN_THEME_PER_MATCH = 5       # Points per unique matched pain theme
PAIN_THEME_CAP = 25            # Max points from pain themes
OWNERSHIP_STRONG_PER = 8       # Points per strong ownership phrase
OWNERSHIP_MODERATE_PER = 5     # Points per moderate ownership phrase
OWNERSHIP_WEAK_PER = 2         # Points per weak ownership phrase
OWNERSHIP_CAP = 25             # Max total from ownership signals
URGENCY_PER_MATCH = 3          # Points per urgency amplifier found
URGENCY_CAP = 10               # Max bonus from urgency
NOISE_PER_SIGNAL = -3          # Penalty per analyst noise phrase found
NOISE_CAP = -20                # Maximum penalty (floor for noise deduction)

# Proximity window: how many words apart can ownership + pain words be and
# still count as "co-located"? 50 words ~ 2-3 sentences.
PROXIMITY_WINDOW_WORDS = 50

# Multiplier range: proximity adjusts the raw score within this range
PROXIMITY_MIN_MULTIPLIER = 0.70   # No proximity detected at all
PROXIMITY_MID_MULTIPLIER = 0.88   # Partial proximity (different paragraphs)
PROXIMITY_MAX_MULTIPLIER = 1.00   # Tight co-occurrence (same sentence/window)


class SignalScorer:
    """
    Calculates a 0-100 hiring pain signal score from pre-extracted signals.

    The scorer operates on a structured `signals` dict produced by the
    SignalDetector. It doesn't re-read the raw text for most operations,
    but DOES receive the raw text for the proximity calculation, which
    requires positional analysis.
    """

    def __init__(self):
        # Store the scoring breakdown for transparency / audit trail
        self.score_breakdown: Dict[str, Any] = {}

    def calculate_score(self, signals: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Master scoring function. Calls each sub-scorer in order, accumulates
        the raw score, applies the proximity multiplier, clamps to [0, 100],
        and returns the full result dict including the audit breakdown.

        Args:
            signals: The structured signals dict from SignalDetector.extract()
            raw_text: The original document text (needed for proximity check)

        Returns:
            A dict with 'score' (int) and 'breakdown' (detailed audit trail)
        """
        self.score_breakdown = {}

        # --- Component 1: Job Title ---
        title_score = self._score_job_title(signals.get("matched_titles", []))
        self.score_breakdown["title_score"] = title_score

        # --- Component 2: Pain Themes ---
        theme_score = self._score_pain_themes(signals.get("matched_themes", {}))
        self.score_breakdown["theme_score"] = theme_score

        # --- Component 3: Ownership Language ---
        ownership_score = self._score_ownership(signals.get("matched_ownership", {}))
        self.score_breakdown["ownership_score"] = ownership_score

        # --- Component 4: Urgency Amplifiers ---
        urgency_score = self._score_urgency(signals.get("matched_urgency", []))
        self.score_breakdown["urgency_score"] = urgency_score

        # --- Component 5: Analyst Noise Penalty ---
        noise_penalty = self._score_noise_penalty(signals.get("matched_noise", []))
        self.score_breakdown["noise_penalty"] = noise_penalty

        # --- Raw total before proximity ---
        raw_score = title_score + theme_score + ownership_score + urgency_score + noise_penalty
        self.score_breakdown["raw_score"] = raw_score

        # --- Proximity Multiplier ---
        # This is the key "signal vs noise" gate. Even if everything else
        # scores high, if the ownership and pain words aren't near each other,
        # we discount the score. This prevents gaming by keyword stuffing.
        multiplier, proximity_detail = self._calculate_proximity_multiplier(
            raw_text,
            signals.get("matched_ownership", {}),
            signals.get("matched_themes", {}),
        )
        self.score_breakdown["proximity_multiplier"] = multiplier
        self.score_breakdown["proximity_detail"] = proximity_detail

        # --- Final score: apply multiplier and clamp to [0, 100] ---
        # We scale the raw score up using the multiplier to reach a max of 100.
        # The scaling factor (100/90 ≈ 1.11) accounts for the theoretical max
        # raw score of ~90 points (30+25+25+10+0), normalizing it to 100.
        final_score = raw_score * multiplier
        final_score = max(0, min(100, round(final_score)))
        self.score_breakdown["final_score"] = final_score

        return {
            "score": final_score,
            "breakdown": self.score_breakdown,
        }

    # -------------------------------------------------------------------------
    # COMPONENT SCORERS
    # Each method handles exactly one scoring dimension. This makes it trivial
    # to adjust a single weight without affecting anything else.
    # -------------------------------------------------------------------------

    def _score_job_title(self, matched_titles: List[Dict]) -> int:
        """
        Score based on the highest-tier job title found.

        We take the MAXIMUM score across all matched titles, not the sum.
        Rationale: If someone lists both "CHRO" and "Director of HR", we
        shouldn't double-count. We want the single most authoritative title.
        """
        if not matched_titles:
            return 0

        max_score = 0
        for title_match in matched_titles:
            tier = title_match.get("tier", "tier_2")
            score = TITLE_TIER_1_SCORE if tier == "tier_1" else TITLE_TIER_2_SCORE
            max_score = max(max_score, score)

        return max_score

    def _score_pain_themes(self, matched_themes: Dict[str, List[str]]) -> int:
        """
        Score based on how many distinct pain themes are represented.

        We score UNIQUE THEMES, not unique keywords. The rationale is that
        someone who hits 3 different pain themes ("overload", "quality", "speed")
        is more interesting than someone who hits 10 keywords all in the same
        theme. Diversity of pain = higher priority lead.
        """
        if not matched_themes:
            return 0

        # Count only themes that had at least one keyword match
        active_theme_count = sum(
            1 for theme_keywords in matched_themes.values() if len(theme_keywords) > 0
        )
        raw = active_theme_count * PAIN_THEME_PER_MATCH
        return min(raw, PAIN_THEME_CAP)

    def _score_ownership(self, matched_ownership: Dict[str, List[str]]) -> int:
        """
        Score based on ownership language found, weighted by tier strength.

        Strong phrases (e.g. "my team is struggling") carry more weight than
        weak phrases (e.g. "internally"). Caps at OWNERSHIP_CAP to prevent
        a document that just repeats "we" 50 times from maxing out the score.
        """
        if not matched_ownership:
            return 0

        strong_phrases = matched_ownership.get("strong", [])
        moderate_phrases = matched_ownership.get("moderate", [])
        weak_phrases = matched_ownership.get("weak", [])

        # Score each tier, using unique matches only (deduplicated by detector)
        strong_score = len(strong_phrases) * OWNERSHIP_STRONG_PER
        moderate_score = len(moderate_phrases) * OWNERSHIP_MODERATE_PER
        weak_score = len(weak_phrases) * OWNERSHIP_WEAK_PER

        total = strong_score + moderate_score + weak_score
        return min(total, OWNERSHIP_CAP)

    def _score_urgency(self, matched_urgency: List[str]) -> int:
        """
        Apply urgency bonus for amplifying words found near pain signals.

        This rewards texts that aren't just mentioning pain passively but
        expressing it with emotional weight ("we are DESPERATELY struggling").
        """
        if not matched_urgency:
            return 0

        raw = len(matched_urgency) * URGENCY_PER_MATCH
        return min(raw, URGENCY_CAP)

    def _score_noise_penalty(self, matched_noise: List[str]) -> int:
        """
        Apply penalties for analyst/observer language patterns.

        Returns a NEGATIVE integer. The more analyst language found, the
        larger the deduction. This is what makes the system resistant to
        whitepapers and market reports that use pain keywords but aren't
        personal expressions of pain.
        """
        if not matched_noise:
            return 0

        raw = len(matched_noise) * NOISE_PER_SIGNAL
        # Cap the penalty: we don't want a score to go below 0 purely from noise
        return max(raw, NOISE_CAP)

    def _calculate_proximity_multiplier(
        self,
        raw_text: str,
        matched_ownership: Dict[str, List[str]],
        matched_themes: Dict[str, List[str]],
    ) -> tuple:
        """
        The core "signal vs. noise" gate.

        Checks whether ownership language appears PHYSICALLY CLOSE to pain
        theme keywords in the text. Co-occurrence in the same window of words
        is strong evidence that the author is personally describing their pain,
        not just mentioning two unrelated topics in the same document.

        Algorithm:
          1. Tokenize the raw text into a flat list of (word, position) tuples.
          2. For each ownership phrase found, record its start position.
          3. For each pain keyword found, record its start position.
          4. Check if any ownership position is within PROXIMITY_WINDOW_WORDS
             of any pain keyword position.
          5. Return a multiplier based on how close the best co-occurrence is.

        Returns:
            Tuple of (multiplier: float, detail: str)
        """
        # Flatten all ownership phrases across tiers
        all_ownership = []
        for tier_phrases in matched_ownership.values():
            all_ownership.extend(tier_phrases)

        # Flatten all pain keywords across themes
        all_pain_keywords = []
        for theme_keywords in matched_themes.values():
            all_pain_keywords.extend(theme_keywords)

        if not all_ownership or not all_pain_keywords:
            # If either category is empty, proximity is irrelevant;
            # return mid-multiplier rather than penalizing for missing data
            return PROXIMITY_MID_MULTIPLIER, "Proximity N/A: missing ownership or pain signals"

        # Tokenize: split on whitespace, keeping track of word-level positions
        # We work in word-index space, not character space, for simplicity.
        words = re.sub(r"[^\w\s'-]", " ", raw_text.lower()).split()

        # Build a mapping: phrase -> list of start word-indices where it occurs
        def find_phrase_positions(phrase: str, word_list: List[str]) -> List[int]:
            """Find all starting word indices of a phrase in the word list."""
            phrase_words = phrase.lower().split()
            phrase_len = len(phrase_words)
            positions = []
            for i in range(len(word_list) - phrase_len + 1):
                if word_list[i : i + phrase_len] == phrase_words:
                    positions.append(i)
            return positions

        # Collect all positions for ownership phrases
        ownership_positions = []
        for phrase in all_ownership:
            ownership_positions.extend(find_phrase_positions(phrase, words))

        # Collect all positions for pain keywords
        pain_positions = []
        for phrase in all_pain_keywords:
            pain_positions.extend(find_phrase_positions(phrase, words))

        if not ownership_positions or not pain_positions:
            return (
                PROXIMITY_MIN_MULTIPLIER,
                "Signals found but not locatable at word level (possible phrase splitting)"
            )

        # Find the minimum distance between any ownership and any pain position
        min_distance = float("inf")
        for o_pos in ownership_positions:
            for p_pos in pain_positions:
                distance = abs(o_pos - p_pos)
                if distance < min_distance:
                    min_distance = distance

        # Classify the proximity
        if min_distance <= 15:
            # Same sentence or consecutive sentences - very tight co-occurrence
            multiplier = PROXIMITY_MAX_MULTIPLIER
            detail = f"TIGHT co-occurrence: ownership and pain within {min_distance} words"
        elif min_distance <= PROXIMITY_WINDOW_WORDS:
            # Same paragraph - meaningful co-occurrence
            multiplier = PROXIMITY_MID_MULTIPLIER
            detail = f"MODERATE co-occurrence: ownership and pain within {min_distance} words"
        else:
            # Different paragraphs - weak co-occurrence
            multiplier = PROXIMITY_MIN_MULTIPLIER
            detail = f"DISTANT: ownership and pain are {min_distance} words apart"

        return multiplier, detail

    def generate_reason(self, signals: Dict[str, Any], score: int) -> str:
        """
        Generate a plain-English explanation of WHY this text was surfaced.

        This is the 'reason' field in the output JSON. It must be readable by
        a non-technical sales or marketing person.

        DESIGN: We build this from the extracted signals rather than using
        templates, so each reason is specific to what was actually found.
        """
        parts = []

        # --- Title context ---
        titles = signals.get("matched_titles", [])
        if titles:
            top_title = titles[0]
            parts.append(
                f"Author identified as '{top_title['matched']}' (tier: {top_title['tier']})"
            )

        # --- Primary pain theme ---
        themes = signals.get("matched_themes", {})
        active_themes = [t for t, kws in themes.items() if kws]
        if active_themes:
            primary = active_themes[0]
            keywords_found = themes[primary][:3]  # Show up to 3 keywords
            parts.append(
                f"Primary pain theme '{primary}' detected via: {', '.join(keywords_found)}"
            )
            if len(active_themes) > 1:
                parts.append(f"Also touches on: {', '.join(active_themes[1:])}")

        # --- Ownership language ---
        ownership = signals.get("matched_ownership", {})
        strong = ownership.get("strong", [])
        moderate = ownership.get("moderate", [])
        if strong:
            parts.append(
                f"Strong personal ownership language found: '{strong[0]}'"
                + (f" + {len(strong)-1} more" if len(strong) > 1 else "")
            )
        elif moderate:
            parts.append(f"Moderate personal ownership language: '{moderate[0]}'")

        # --- Noise signals ---
        noise = signals.get("matched_noise", [])
        if noise:
            parts.append(
                f"Note: {len(noise)} analyst/observer phrase(s) detected "
                f"(e.g. '{noise[0]}') -- score penalized accordingly"
            )

        # --- Score commentary ---
        if score >= 75:
            parts.append("HIGH SIGNAL: Strong candidate for outreach.")
        elif score >= 50:
            parts.append("MEDIUM SIGNAL: Worth monitoring; may need validation.")
        elif score >= 25:
            parts.append("LOW SIGNAL: Some indicators present but context unclear.")
        else:
            parts.append("NOISE: Likely analyst/vendor commentary, not personal pain.")

        return " | ".join(parts)
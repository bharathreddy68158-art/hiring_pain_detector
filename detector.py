# =============================================================================
# signals/detector.py
# =============================================================================
# PURPOSE: The core signal extraction class. Reads raw text and produces a
#          structured dict of everything it found — titles, pain themes,
#          ownership phrases, noise signals, urgency amplifiers.
#
# ARCHITECTURAL DECISION: The detector is PURELY a pattern matcher. It does not
# assign scores or make judgments. It simply finds things and reports them.
# All scoring judgment is deferred to scorer.py. This single-responsibility
# design makes the detector unit-testable in complete isolation.
#
# HOW MATCHING WORKS:
#   All matching is case-insensitive and uses two strategies:
#   1. PHRASE matching: Check if the full phrase exists as a substring.
#      (e.g., "my team" anywhere in the text)
#   2. REGEX matching: For title detection, we use word-boundary regex to
#      avoid matching "chr" inside "chromosome" matching "chro".
#
# INPUT: Raw string of text (LinkedIn post, blog excerpt, transcript chunk)
# OUTPUT: A structured dict of all signals found, ready for scorer.py
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


class SignalDetector:
    """
    Extracts structured hiring-pain signals from unstructured text.

    Usage:
        detector = SignalDetector()
        signals = detector.extract(text="...", company="Acme Corp")
    """

    def extract(self, text: str, company: str = "Unknown", source_url: str = "") -> Dict[str, Any]:
        """
        Main extraction method. Runs all sub-extractors and assembles the
        unified signals dict.

        Args:
            text:       The raw input text to analyze
            company:    The company name (passed through to output)
            source_url: The origin URL (passed through to output)

        Returns:
            A structured dict with all extracted signals and metadata.
        """
        # Normalize: lowercase copy of text for all matching operations.
        # We keep the original for display purposes.
        normalized = text.lower()

        # Run each extractor
        matched_titles = self._extract_titles(normalized)
        matched_themes = self._extract_pain_themes(normalized)
        matched_ownership = self._extract_ownership(normalized)
        matched_noise = self._extract_noise(normalized)
        matched_urgency = self._extract_urgency(normalized)

        # Determine the PRIMARY signal type:
        # The theme with the most matched keywords wins. This becomes the
        # `signal_type` field in the output JSON.
        primary_theme = self._determine_primary_theme(matched_themes)

        # Collect all matched keywords for the output JSON:
        # Flatten themes + ownership (strong only) into one list for display.
        all_matched_keywords = self._collect_display_keywords(
            matched_themes, matched_ownership
        )

        return {
            # -- Metadata (passed through) --
            "company": company,
            "source_url": source_url,

            # -- Derived classification --
            "primary_theme": primary_theme,

            # -- Raw extraction results (consumed by scorer.py) --
            "matched_titles": matched_titles,
            "matched_themes": matched_themes,
            "matched_ownership": matched_ownership,
            "matched_noise": matched_noise,
            "matched_urgency": matched_urgency,

            # -- Display-ready field for JSON output --
            "matched_keywords": all_matched_keywords,
        }

    # -------------------------------------------------------------------------
    # PRIVATE EXTRACTOR METHODS
    # Each handles exactly one category of signal.
    # -------------------------------------------------------------------------

    def _extract_titles(self, normalized_text: str) -> List[Dict[str, str]]:
        """
        Scan for job title signals.

        Returns a list of dicts, one per match, e.g.:
            [{"matched": "chro", "tier": "tier_1"}, ...]

        WHY DICTS NOT STRINGS: We need to carry the tier metadata forward to
        the scorer so it can apply the correct point weight.

        REGEX APPROACH: We use word-boundary matching (\b) to avoid partial
        matches. "CHRO" in "CHROnicle" would otherwise match incorrectly.
        However, for multi-word phrases like "head of recruiting", simple
        substring matching is fine because the phrase is specific enough.
        """
        found = []
        seen = set()  # Deduplicate: don't report the same title twice

        for tier, titles in JOB_TITLE_SIGNALS.items():
            for title in titles:
                # For single-word titles (like "chro", "cpo"), use word boundary
                # For multi-word phrases, substring match is sufficient
                if " " not in title:
                    pattern = r"\b" + re.escape(title) + r"\b"
                    match = re.search(pattern, normalized_text)
                    found_it = match is not None
                else:
                    found_it = title in normalized_text

                if found_it and title not in seen:
                    seen.add(title)
                    found.append({"matched": title, "tier": tier})

        return found

    def _extract_pain_themes(self, normalized_text: str) -> Dict[str, List[str]]:
        """
        Scan for pain theme keywords, grouped by theme.

        Returns a dict mapping each theme name to a list of keywords found.
        Empty list means that theme wasn't detected.

        Example return:
        {
            "recruiter_overload": ["overwhelmed", "drowning in resumes"],
            "interview_speed": [],
            ...
        }

        WHY GROUP BY THEME: The scorer needs theme diversity (# of distinct themes)
        not just total keyword count. This structure makes that calculation trivial.
        """
        theme_matches = {}

        for theme_name, keywords in PAIN_THEMES.items():
            matched_in_theme = []
            for keyword in keywords:
                if keyword in normalized_text and keyword not in matched_in_theme:
                    matched_in_theme.append(keyword)
            theme_matches[theme_name] = matched_in_theme

        return theme_matches

    def _extract_ownership(self, normalized_text: str) -> Dict[str, List[str]]:
        """
        Scan for first-person / ownership language, grouped by tier strength.

        Returns a dict of {tier: [matched_phrases]}.

        WHY TIER STRUCTURE: The scorer applies different point values per tier
        (strong=8pts, moderate=5pts, weak=2pts). The tiered structure in the
        return value makes it easy to apply tier-specific weights without
        re-examining the text.
        """
        ownership_matches = {"strong": [], "moderate": [], "weak": []}

        for tier, phrases in OWNERSHIP_LANGUAGE.items():
            for phrase in phrases:
                if phrase in normalized_text and phrase not in ownership_matches[tier]:
                    ownership_matches[tier].append(phrase)

        return ownership_matches

    def _extract_noise(self, normalized_text: str) -> List[str]:
        """
        Scan for analyst / observer language patterns.

        Returns a flat list of matched noise phrases. The scorer will apply
        a penalty per phrase found. No tiering here — all noise is equally bad.
        """
        matched_noise = []
        for phrase in ANALYST_NOISE_SIGNALS:
            if phrase in normalized_text and phrase not in matched_noise:
                matched_noise.append(phrase)
        return matched_noise

    def _extract_urgency(self, normalized_text: str) -> List[str]:
        """
        Scan for urgency amplifiers.

        Returns a flat list of matched amplifier words. The scorer uses the
        COUNT of unique matches to calculate a bonus (with a cap).
        """
        matched_urgency = []
        for word in URGENCY_AMPLIFIERS:
            if word in normalized_text and word not in matched_urgency:
                matched_urgency.append(word)
        return matched_urgency

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------

    def _determine_primary_theme(self, matched_themes: Dict[str, List[str]]) -> str:
        """
        Determine the single most dominant pain theme.

        Strategy: the theme with the most matched keywords is the primary theme.
        Ties are broken by the order themes appear in PAIN_THEMES (arbitrary
        but consistent).

        Returns "unknown" if no themes were matched at all.
        """
        if not matched_themes:
            return "unknown"

        # Sort by number of matches descending, take the first
        sorted_themes = sorted(
            matched_themes.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        best_theme, best_keywords = sorted_themes[0]
        if not best_keywords:
            return "unknown"

        return best_theme

    def _collect_display_keywords(
        self,
        matched_themes: Dict[str, List[str]],
        matched_ownership: Dict[str, List[str]],
    ) -> List[str]:
        """
        Assemble the flat list of keywords shown in the output JSON.

        We include:
          - All matched pain keywords (from all themes)
          - Strong ownership phrases (these are the most readable/meaningful)

        Capped at 10 items total to keep the output concise.
        """
        display = []

        # Add pain keywords from all themes
        for kws in matched_themes.values():
            display.extend(kws)

        # Add strong ownership signals
        display.extend(matched_ownership.get("strong", []))

        # Deduplicate and cap
        seen = set()
        unique = []
        for item in display:
            if item not in seen:
                seen.add(item)
                unique.append(item)

        return unique[:10]
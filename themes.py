# =============================================================================
# signals/themes.py
# =============================================================================
# PURPOSE: Central repository for all heuristic word-banks and dictionaries.
#
# ARCHITECTURAL DECISION: Keeping all vocabulary in a single, flat module means
# that a non-technical stakeholder (e.g., a recruiter or HR analyst) can open
# this file and update the word-banks without touching any logic code.
# This separation of "data" from "behavior" is the most defensible design choice
# in the entire system - it makes the system auditable and maintainable.
#
# HOW SCORING USES THIS MODULE:
#   scorer.py imports these dictionaries and checks the input text against each
#   category. Each category contributes a weighted sub-score. The weights are
#   documented below alongside each group.
# =============================================================================


# -----------------------------------------------------------------------------
# 1. JOB TITLE SIGNALS
# Scoring weight: 30 points (the highest single weight)
#
# RATIONALE: The speaker's role is the #1 differentiator between "high signal"
# (someone who owns a hiring process) and "noise" (an analyst or vendor).
# A CHRO saying "we're struggling" is an actionable lead. An analyst saying
# "CHROs are struggling" is market commentary. This dictionary is the first
# filter applied.
#
# TIER DESIGN: We use two tiers because a CHRO/VP-level title carries more
# weight than a coordinator-level title. The scorer will grant:
#   - TIER_1 match: 30 points (C-suite, VP-level, direct ownership of hiring)
#   - TIER_2 match: 18 points (Manager-level, influential but not strategic)
# -----------------------------------------------------------------------------
JOB_TITLE_SIGNALS = {
    "tier_1": [
        "chro",
        "chief human resources officer",
        "chief people officer",
        "cpo",
        "vp of talent",
        "vp of people",
        "vp of hr",
        "vice president of talent",
        "vice president of people",
        "vice president of human resources",
        "head of talent acquisition",
        "head of recruiting",
        "head of people",
        "head of hr",
        "director of talent acquisition",
        "director of recruiting",
        "director of people operations",
        "director of hr",
        "talent acquisition director",
        "people operations director",
        "global head of recruiting",
        "global head of talent",
    ],
    "tier_2": [
        "recruiting manager",
        "talent acquisition manager",
        "hr manager",
        "people manager",
        "senior recruiter",
        "lead recruiter",
        "recruiting lead",
        "talent acquisition lead",
        "hr business partner",
        "hrbp",
        "recruiting coordinator",
        "people operations manager",
    ],
}


# -----------------------------------------------------------------------------
# 2. PAIN THEME SIGNALS
# Scoring weight: Up to 25 points (5 per matched theme, capped)
#
# RATIONALE: These are the core "problem categories" we are trying to detect.
# Each key is a named theme (used in the output JSON as `signal_type`).
# The values are lists of phrases/words associated with that pain point.
#
# DESIGN NOTE: Phrases are preferred over single words where possible because
# "slow" alone is too ambiguous, but "slow to hire" is unambiguous.
# The detector will check for both full phrases and individual keywords.
#
# THEME DEFINITIONS:
#   - interview_speed: Pain around time-to-hire, scheduling lag
#   - recruiter_overload: Too many reqs, burnout, capacity issues
#   - inconsistent_evaluation: Bias, lack of rubrics, interviewers off-script
#   - quality_of_hire: Bad hires, misalignment, attrition after hire
#   - candidate_experience: Drop-off, ghosting, brand damage
#   - sourcing_pipeline: Top-of-funnel is dry or polluted with poor fits
# -----------------------------------------------------------------------------
PAIN_THEMES = {
    "interview_speed": [
        "time to hire",
        "time-to-hire",
        "slow to hire",
        "hiring too slow",
        "takes too long",
        "slow interview",
        "scheduling delays",
        "interview scheduling",
        "hiring velocity",
        "speed of hiring",
        "days to offer",
        "offer turnaround",
        "lengthy process",
        "extended process",
        "candidates dropping off",
        "losing candidates",
        "losing talent",
        "losing top talent",
        "candidates going elsewhere",
        "competing offers",
    ],
    "recruiter_overload": [
        "drowning in resumes",
        "buried in applications",
        "too many reqs",
        "req load",
        "recruiter burnout",
        "overwhelmed",
        "understaffed",
        "under-resourced",
        "capacity issues",
        "bandwidth",
        "not enough recruiters",
        "recruiter to req ratio",
        "requisition overload",
        "high volume",
        "volume of applications",
        "screening fatigue",
        "too many applicants",
        "flooded with resumes",
        "resume pile",
        "recruiter ratio",
        "team is stretched",
        "stretched thin",
        "at capacity",
    ],
    "inconsistent_evaluation": [
        "inconsistent interviews",
        "no rubric",
        "no scorecard",
        "unstructured interviews",
        "interviewer calibration",
        "bias in hiring",
        "unconscious bias",
        "gut feel",
        "going on gut",
        "subjective feedback",
        "different standards",
        "no consistency",
        "lack of structure",
        "interviewers not aligned",
        "no interview guide",
        "ad hoc interviews",
        "interview quality",
        "evaluation criteria",
        "not calibrated",
        "hiring managers disagree",
        "feedback quality",
        "poor feedback",
        "vague feedback",
    ],
    "quality_of_hire": [
        "quality of hire",
        "bad hires",
        "wrong hires",
        "mis-hire",
        "mishire",
        "hiring mistakes",
        "early attrition",
        "turnover",
        "new hire turnover",
        "90 day attrition",
        "not the right fit",
        "culture fit",
        "performance after hire",
        "underperforming hires",
        "regrettable hires",
        "failed hires",
        "high turnover",
        "retention issues",
        "not retaining",
        "losing new hires",
        "onboarding failures",
        "predictive validity",
    ],
    "candidate_experience": [
        "candidate experience",
        "candidate feedback",
        "ghosting candidates",
        "candidates ghosting",
        "no response",
        "lack of communication",
        "employer brand",
        "employer branding",
        "glassdoor reviews",
        "bad reviews",
        "candidate nps",
        "candidate satisfaction",
        "drop off rate",
        "application drop-off",
        "candidate drop-off",
        "long application",
        "poor experience",
        "candidate complaints",
        "slow response",
        "no feedback to candidates",
    ],
    "sourcing_pipeline": [
        "top of funnel",
        "top-of-funnel",
        "pipeline is dry",
        "thin pipeline",
        "not enough candidates",
        "candidate pool",
        "sourcing strategy",
        "sourcing channels",
        "passive candidates",
        "talent pool",
        "not finding candidates",
        "hard to find",
        "difficult to source",
        "niche roles",
        "hard to fill",
        "difficult roles",
        "talent shortage",
        "talent scarcity",
        "applicant quality",
        "poor applicant quality",
        "wrong candidates applying",
        "inbound not working",
        "job board performance",
        "job posting",
    ],
}


# -----------------------------------------------------------------------------
# 3. OWNERSHIP / FIRST-PERSON LANGUAGE
# Scoring weight: Up to 25 points
#
# RATIONALE: This is the most critical differentiator in the entire system.
# It's the mechanism that separates PERSONAL PAIN from OBSERVED TRENDS.
#
# Example of HIGH SIGNAL (personal ownership):
#   "My team is completely overwhelmed with the volume of applications."
#
# Example of LOW SIGNAL (analytical observation):
#   "Many HR teams are overwhelmed with the volume of applications."
#
# PROXIMITY SCORING: The scorer doesn't just check if these phrases exist in
# the document -- it checks if they appear WITHIN a defined window (N words)
# of a pain keyword. This proximity check is the core "signal vs. noise"
# algorithm. A document with "my team" in paragraph 1 and pain words in
# paragraph 5 scores lower than one where they appear in the same sentence.
#
# TIERS:
#   - STRONG (15 pts each, capped at 25): Direct first-person plural
#   - MODERATE (8 pts each, capped at 15): First-person singular about team
#   - WEAK (3 pts each, capped at 8): Implicit ownership signals
# -----------------------------------------------------------------------------
OWNERSHIP_LANGUAGE = {
    "strong": [
        "my team",
        "our team",
        "we are",
        "we're",
        "we have",
        "we've",
        "we need",
        "we struggle",
        "we're struggling",
        "we are struggling",
        "our pipeline",
        "our process",
        "our hiring",
        "our recruiting",
        "our recruiters",
        "our company",
        "our organization",
        "our candidates",
        "my recruiters",
        "my hiring team",
        "my organization",
        "my company",
        "we can't",
        "we cannot",
        "we don't",
        "we do not",
        "we are losing",
        "we're losing",
        "we are failing",
        "we're failing",
    ],
    "moderate": [
        "i'm seeing",
        "i am seeing",
        "i've noticed",
        "i have noticed",
        "i'm dealing",
        "i am dealing",
        "i'm facing",
        "i am facing",
        "in my experience",
        "at my company",
        "at my org",
        "in my role",
        "as a chro",
        "as a recruiter",
        "as a talent leader",
        "as a people leader",
        "i need to",
        "i need a",
        "i'm looking for",
        "i am looking for",
        "i'm trying to",
        "i am trying to",
        "i can't find",
        "i cannot find",
        "i'm struggling",
        "i am struggling",
        "i oversee",
        "i lead",
        "i manage",
    ],
    "weak": [
        "internally",
        "in-house",
        "our efforts",
        "our initiatives",
        "our strategy",
        "building our",
        "scaling our",
        "growing our",
        "fixing our",
        "improving our",
        "overhauling our",
        "transforming our",
        "rebuilding our",
    ],
}


# -----------------------------------------------------------------------------
# 4. ANALYST / NOISE SIGNALS
# Scoring weight: PENALTY of up to -20 points
#
# RATIONALE: These phrases strongly suggest the author is OBSERVING or REPORTING
# on trends rather than experiencing them. A high concentration of these
# phrases should reduce the final score significantly, even if pain keywords
# are present.
#
# This is the "noise filter" -- the mechanism that prevents market reports,
# vendor whitepapers, and analyst commentary from scoring as high-signal leads.
# -----------------------------------------------------------------------------
ANALYST_NOISE_SIGNALS = [
    "according to",
    "research shows",
    "studies show",
    "data shows",
    "survey says",
    "report finds",
    "report shows",
    "analysts say",
    "analysts predict",
    "experts say",
    "experts predict",
    "industry data",
    "industry trends",
    "market trends",
    "market research",
    "companies are",
    "organizations are",
    "employers are",
    "hr teams are",
    "recruiters are",
    "many companies",
    "most companies",
    "many organizations",
    "most hr teams",
    "many hr leaders",
    "hr leaders report",
    "chros say",
    "talent leaders say",
    "in this article",
    "in this post",
    "today we explore",
    "in this guide",
    "we will discuss",
    "let's explore",
    "let's discuss",
    "in this piece",
    "this report",
    "this study",
    "this whitepaper",
    "published by",
    "sponsored by",
    "will need to",
    "will have to",
    "in the future",
    "years from now",
    "the future of hiring",
    "future of work",
    "emerging trend",
    "emerging challenge",
    "predicted to",
    "expected to",
    "forecasted to",
]


# -----------------------------------------------------------------------------
# 5. URGENCY AMPLIFIERS
# Scoring weight: Up to 10 bonus points
#
# RATIONALE: These words amplify the severity of pain signals. A person saying
# "we're struggling a bit" is lower priority than "we're desperately struggling."
# Urgency amplifiers boost the score when found near pain themes.
# -----------------------------------------------------------------------------
URGENCY_AMPLIFIERS = [
    "desperately",
    "urgently",
    "critical",
    "critically",
    "emergency",
    "crisis",
    "massive",
    "severe",
    "significant",
    "serious",
    "major",
    "huge",
    "enormous",
    "unprecedented",
    "never been worse",
    "at a breaking point",
    "breaking point",
    "on the verge",
    "completely",
    "totally",
    "absolutely",
    "cannot cope",
    "falling apart",
    "broken",
    "failing",
    "right now",
    "immediately",
    "asap",
    "as soon as possible",
    "this quarter",
    "this year",
    "in q1",
    "in q2",
    "in q3",
    "in q4",
]
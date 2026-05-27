# Hiring Pain / Intent Detector

A locally-runnable, zero-API-cost system that reads unstructured text — LinkedIn posts, HR blog excerpts, podcast transcripts — and detects whether the author is personally experiencing hiring pain, or just reporting on it. Built entirely with Python standard library, regex, and heuristic scoring. No LLMs. No cloud.

---

## Setup and Run

### Prerequisites
- Python 3.7 or higher
- pip

### 1. Clone / download the project
```
hiring_pain_detector/
├── app.py
├── main.py
├── sample_data.json
├── requirements.txt
├── templates/
│   └── index.html
├── signals/
│   ├── __init__.py
│   ├── detector.py
│   ├── scorer.py
│   └── themes.py
└── utils/
    ├── __init__.py
    └── io.py
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn jinja2 python-multipart
```
The core detection logic (`signals/`, `utils/`) uses **zero third-party packages** — only Python's built-in `re`, `json`, `datetime`, `argparse`, `os`, and `sys`. The only installs above are for the web UI layer.

### 3a. Run as a web app (recommended)
```bash
python app.py
```
Then open your browser to:

| URL | Purpose |
|---|---|
| `http://localhost:8000` | Dashboard UI — paste text, see scored results |
| `http://localhost:8000/docs` | Swagger UI — interactive API explorer, auto-generated |
| `http://localhost:8000/redoc` | ReDoc — alternative API documentation |

The dashboard pre-loads all 6 sample posts from `sample_data.json` on startup so you can see results immediately without typing anything.

### 3b. Run as a CLI (no browser needed)
```bash
# Basic run — reads sample_data.json, writes results.json
python main.py

# Custom input/output
python main.py --input my_posts.json --output leads.json

# Only save high-confidence results
python main.py --min-score 70

# Show full score breakdown per record in terminal
python main.py --verbose
```

### 4. Expected output
The system writes a `results.json` file sorted by `signal_score` descending:
```json
[
  {
    "company": "NovaTech Solutions",
    "signal_type": "recruiter_overload",
    "source_url": "https://linkedin.com/posts/...",
    "matched_keywords": ["drowning in resumes", "overwhelmed", "my team"],
    "signal_score": 79,
    "detected_at": "2024-01-15T10:30:00Z",
    "reason": "Author identified as 'chro' (tier: tier_1) | Primary pain theme 'recruiter_overload' detected via: drowning in resumes, overwhelmed | Strong personal ownership language found: 'my team' | HIGH SIGNAL: Strong candidate for outreach."
  }
]
```

### Input file format
Your input JSON must be an array of objects, each with at minimum a `text` field:
```json
[
  {
    "company": "Acme Corp",
    "source_url": "https://linkedin.com/posts/...",
    "text": "The raw post or transcript text to analyze..."
  }
]
```
`company` and `source_url` are optional — they default to `"Unknown"` and `""` if omitted.

---

## Data Ingestion Approach

### Where the data comes from

This system is designed to process text that has already been collected from three source types:

**1. LinkedIn posts (primary source)**
LinkedIn is the highest-value source because HR leaders post directly in their own voice about the problems they are facing in real time. A CHRO writing "my team is drowning in resumes" on LinkedIn is an unsolicited, unprompted admission of pain — the highest-quality signal possible. I modelled the sample dataset (`sample_data.json`) entirely on the language patterns that appear in real LinkedIn posts from CHROs, VPs of Talent, and Heads of Recruiting. The mock posts mirror the informal, first-person tone these leaders use: direct, emotionally charged, and full of ownership language.

**2. HR blogs and editorial content (noise source)**
Sites like SHRM, HR Dive, and vendor-authored content use the same vocabulary — "recruiter burnout," "time-to-hire" — but frame it analytically rather than personally. These became the basis for the analyst noise dictionary (`ANALYST_NOISE_SIGNALS` in `themes.py`). Phrases like `"according to"`, `"research shows"`, `"in this article"` are structural tells that the author is an observer, not a sufferer.

**3. Podcast transcripts (secondary source)**
Podcast transcripts present a middle case: a CHRO being interviewed will use first-person ownership language, but the host's questions and framing will introduce third-person analytical language. The proximity scoring model handles this by checking not just whether ownership and pain words exist in the document, but whether they appear within 50 words of each other — which they will in the CHRO's answers but not in the host's framing.

### What I had to work around

**No live scraping in the system.** The brief required no cloud APIs and no paid services. LinkedIn's API is gated and scraping it violates their ToS. So the system is deliberately designed as a processor, not a collector: you feed it text, it scores it. The ingestion of that text (copy-paste, a separate scraper, an RSS feed, a webhook) is intentionally outside the system boundary. This keeps the tool legally clean and deployable in any environment.

**No NLP library (spaCy, NLTK, etc.).** Keeping dependencies to zero meant I could not use named entity recognition to identify job titles dynamically. Instead I built an explicit two-tier title dictionary in `themes.py` covering 34 job titles across C-suite and manager levels. The trade-off is that an unusual title like "Talent Infrastructure Lead" would be missed, but the coverage of the 34 most common HR decision-maker titles is close to complete for the target use case.

**No sentence tokenizer.** Without NLTK, I could not split text into proper sentences for proximity analysis. Instead the proximity engine works in word-index space: it tokenizes the document into a flat list of words, records the position of every ownership phrase and every pain keyword, then calculates the minimum word-distance between any ownership-pain pair. A window of 50 words (~2-3 sentences) defines "co-located."

---

## Scoring Logic

### How the score is built

The score is a 0–100 integer built from five components that are calculated independently and then combined. Each component has a documented maximum and a documented rationale for its weight.

| Component | Max Points | What it measures |
|---|---|---|
| Job Title Score | 30 | Whether the author holds a role that owns hiring decisions |
| Pain Theme Score | 25 | How many distinct pain categories are present |
| Ownership Language Score | 25 | Whether the author speaks in first person about their own team |
| Urgency Bonus | 10 | Whether the pain is expressed with emotional weight |
| Analyst Noise Penalty | −20 | Whether the text reads like observation rather than experience |

After these five components are summed into a raw score, a **proximity multiplier** (0.70–1.00) is applied. This multiplier is the core "signal vs. noise" gate: it checks whether ownership language and pain keywords appear within 50 words of each other in the document. A document where "my team" and "drowning in resumes" appear in the same sentence gets a multiplier of 1.00. A document where those signals are several paragraphs apart gets 0.70, regardless of how many keywords it contains.

### What a score of 80 means

A score of 80 means the text almost certainly represents a senior HR leader personally describing an active, felt problem in their own organization right now. Concretely, to reach 80 the text must have: a Tier 1 title (30 pts), at least two distinct pain themes (10 pts), multiple strong ownership phrases co-located with pain words (20+ pts), some urgency language (3–6 pts), and no significant analyst noise penalties. The proximity multiplier will be at or near 1.0, meaning ownership and pain are expressed together in the same passage — not in separate sections of a long document.

### What a score of 40 means

A score of 40 is a mixed signal. It typically means one of three things: (a) a Tier 2 title with clear ownership language but only one pain theme, (b) a strong Tier 1 title and clear pain theme but ownership language that appears far from the pain words in the document, or (c) clear pain and ownership language with no recognizable title — perhaps someone who describes their role in a non-standard way. A score of 40 is worth human review but should not trigger automatic outreach.

### What the score cannot capture

**Irony and negation.** The system matches keywords but does not parse sentence polarity. "We have zero problems with time-to-hire" would match `time-to-hire` and contribute positively to the score, when it should contribute nothing. A proper NLP pipeline with dependency parsing would catch this; the current regex approach cannot.

**Past tense vs. present tense.** "We struggled with recruiter burnout last year but fixed it" scores the same as "we are struggling with recruiter burnout right now." The system cannot distinguish resolved pain from active pain.

**Sarcasm and rhetorical questions.** "Oh great, another candidate who ghosted us — not like we have 40 open reqs or anything" contains strong signals but expresses them sarcastically. The scorer would actually score this well (ownership + pain keywords), which in this case would be correct — but the mechanism is pattern matching, not comprehension.

**Authority of the speaker.** A title is matched from the text itself. If someone writes "As a CHRO, I think companies should..." the system scores them as a Tier 1 owner even though they may be speaking about hypotheticals, not their current organization.

---

## Assumptions and Limitations

### Assumptions made that might not hold

**The speaker's title is stated in the text.** The scoring model gives 30 points for a Tier 1 title match, but only if the title appears somewhere in the post. Many LinkedIn posts do not include the author's title — people assume the reader can see their profile. In production, you would need to resolve the author's title from their profile metadata and inject it into the text before processing.

**More ownership phrases = stronger ownership.** The scorer adds points for each unique ownership phrase found. This assumes that a text with five ownership phrases expresses stronger personal commitment than one with two. In practice a single well-placed "my team is broken" is stronger than five generic "we are" mentions scattered across a long article. The count-based model is a simplification.

**Analyst language and personal pain are mutually exclusive enough.** The noise penalty treats analyst phrases as a negative signal against personal pain. But a CHRO who is also analytically articulate might write "research shows this is an industry-wide problem AND we are experiencing it acutely." That text would be penalized unfairly. The current model treats noise and signal as opposing forces; in reality they can co-exist.

**The 50-word proximity window is the right threshold.** The window was chosen by manually reading representative posts and estimating sentence lengths. It has not been empirically validated. A CHRO who writes long, detailed posts might naturally place ownership language and pain keywords more than 50 words apart while still expressing deeply personal pain.

### What the system gets wrong

**Vendors and solution-providers.** A recruiting software vendor writing "we help companies where our clients are overwhelmed with too many reqs" would score moderately well — it contains ownership language ("our clients"), pain keywords ("overwhelmed", "too many reqs"), and possibly a title. The system has no concept of vendor framing versus buyer framing.

**Non-English text.** All word-banks are English only. A CHRO writing in French, Spanish, or Hindi scores 0 regardless of pain intensity.

**Job titles that use non-standard phrasing.** "People Acquisition Lead," "Talent Experience Manager," or "Head of People Success" are real titles that do not appear in the dictionary. These authors score 0 on the title component and are unlikely to breach the high-signal threshold even with strong pain and ownership signals.

### What I would fix first with more time

**1. Negation detection.** This is the highest-impact improvement. A simple regex pass before scoring that detects "no [pain keyword]", "not [pain keyword]", "zero [pain keyword]", or "solved our [pain keyword]" and removes those matches from the scored set would immediately reduce false positives.

**2. Title injection from metadata.** In a real pipeline, the input record would include the author's LinkedIn profile title as a separate field, not extracted from the post text. The detector would check that field directly rather than scanning the raw post, which would make title detection both more reliable and more honest.

**3. Recency signal.** Posts should carry a timestamp. Pain expressed "this quarter" or "right now" should score higher than pain expressed in past tense. A simple tense classifier on the sentence containing the pain keyword — even just checking for present-tense auxiliary verbs ("is", "are", "am") versus past-tense ("was", "were", "had") — would materially improve precision.

**4. Empirical weight calibration.** The scoring weights (30 pts for title, 25 for themes, etc.) were set by reasoning about relative importance, not by training on labeled data. With a dataset of 200+ manually-labeled posts — each tagged as high/medium/low signal by a human recruiter — the weights could be tuned using logistic regression to minimize classification error. This would replace expert judgment with evidence.

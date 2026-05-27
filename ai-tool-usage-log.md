**i used gemini pro for logic understanding and prompt generation :-** 



This is a fantastic technical challenge. Building a signal detector without relying on LLM APIs in the runtime forces you to rely on classic NLP, heuristic rules, and clever text parsing. It’s exactly the kind of engineering problem that bridges HR domain knowledge with Python-based data analytics.



Since you are building a heuristic engine (rules-based rather than AI-inferred), the secret sauce of your project will be your dictionaries and your scoring logic.



Here is the step-by-step breakdown of how this system will actually work, followed by the master prompt you can feed to Claude to generate the codebase.



How the System Will Work (Step-by-Step)

1\. Data Ingestion (The Fetcher)

Since scraping LinkedIn natively is difficult without getting blocked or using paid APIs, the system will use a local JSON file containing a mix of mock "posts" and scraped public articles (like RSS feeds from HR Dive or SHRM). This proves your logic works on unstructured text.



2\. The Heuristic Engine (Parsing \& Categorization)

This is the core module. Instead of asking an AI "is this HR pain?", the system will use Weighted Keyword Dictionaries combined with Regex patterns.



Pain Themes: You’ll have word banks for specific categories:



Interview Speed: "time-to-hire", "taking too long", "losing candidates", "speed to hire"



Recruiter Overload: "drowning in resumes", "burnout", "too many applications", "capacity"



Quality: "quality of hire", "bad fit", "turnover", "inconsistent"



3\. Signal vs. Noise (The Hard Part)

To differentiate a CHRO venting from an industry analyst observing, the system will use First-Person \& Role Modifiers:



Role Identification: Does the author's bio or the text contain "CHRO", "Head of Talent", "VP HR"?



Ownership Language: The system will look for proximity between pain words and ownership words using regex. For example, if "time-to-hire" appears within 10 words of "my team", "our process", or "we are struggling", it is high-intent signal. If it appears near "trends show" or "the industry", it is low-intent noise.



4\. The Scoring Algorithm

The engine will calculate a signal\_score (0-100) based on an additive point system:



+30 points if a Pain Theme keyword is found.



+30 points if Ownership Language ("my team", "our") is present.



+20 points if the author has an HR Leader title.



+20 points if the keyword density (pain words per total words) is high.



Threshold: Only records scoring > 60 get outputted as a matched signal.



5\. Modular Architecture \& Output

The code will be structured cleanly into a /signals directory, processing the raw text through the scoring algorithm, and dumping the final results into the exact structured JSON schema requested.



The Claude Prompt

Copy and paste the text below directly into Claude. It is engineered to give you the exact architecture, code structure, and logic required to pass this specific assessment.



\[Start of Prompt]



Act as a Senior Python Engineer. I need to build a "Hiring Pain / Intent Detector" for a technical assessment.



CRITICAL CONSTRAINTS:



Python 3.x only.



NO paid APIs and NO LLM/AI API calls inside the running code. This must rely entirely on local NLP, regex, dictionaries, and heuristic scoring.



Must run locally without cloud deployment.



THE OBJECTIVE:

Build a modular, locally runnable system that takes in unstructured text (representing public LinkedIn posts, HR blogs, or podcast transcripts) and detects expressions of "hiring pain" from HR leaders. It must differentiate between a CHRO expressing their own team's pain (high signal) and an analyst discussing general trends (noise).



ARCHITECTURE REQUIREMENTS:

Please write the complete Python code for this project using the following structure:



main.py: A CLI runner to execute the pipeline.



/signals/\_\_init\_\_.py



/signals/detector.py: The core logic class.



/signals/scorer.py: The algorithm that calculates the 0-100 score based on heuristics.



/signals/themes.py: The dictionaries/word-banks for pain points, job titles, and ownership language (e.g., "my team", "we are struggling").



/utils/io.py: For reading input data and exporting the JSON.



sample\_data.json: Create a mock dataset of 5-6 realistic posts (mix of high-signal HR leaders and low-signal analyst noise) to test the system.



THE LOGIC / SCORING RULES:

Implement a scoring mechanism that assigns points. To get a high score, the text must contain:



A recognized job title (CHRO, VP of Talent, Head of Recruiting).



A pain theme (interview speed, recruiter overload, inconsistent evaluation, quality of hire).



Crucially: First-person/ownership language ("my team", "we need", "our pipeline") in close proximity to the pain words to prove it's personal pain, not general analysis.



{

&#x20; "company": "Example Corp",

&#x20; "signal\_type": "recruiter\_overload",

&#x20; "source\_url": "https://...",

&#x20; "matched\_keywords": \["drowning in resumes", "burnout"],

&#x20; "signal\_score": 82,

&#x20; "detected\_at": "ISO timestamp",

&#x20; "reason": "Plain language explanation of why this was surfaced"

}



Please generate the code file by file, ensuring it is heavily commented so I can defend the architectural decisions and explain how the heuristic "signal vs noise" algorithm works in my write-up.



\[End of Prompt]



This setup proves you can build practical, deployable systems without just throwing an expensive LLM API at every problem, which is exactly what the prompt is testing for.



Once Claude generates the Python scripts, do you want to review the exact logic of the scoring multiplier together to ensure you can confidently defend it in your write-up?



**and used claude for generation of the main.py files and other ui and for logic handling** 



**# =============================================================================**

**# main.py**

**# =============================================================================**

**# PURPOSE: The CLI entry point for the Hiring Pain / Intent Detector pipeline.**

**#**

**# USAGE:**

**#   python main.py                             # Uses defaults**

**#   python main.py --input sample\_data.json   # Custom input file**

**#   python main.py --output my\_results.json   # Custom output file**

**#   python main.py --min-score 50             # Only show results >= 50**

**#   python main.py --verbose                  # Show per-record score breakdown**

**#**

**# PIPELINE FLOW:**

**#   1. Load posts from JSON input file         \[utils/io.py]**

**#   2. For each post:**

**#      a. Extract signals from text            \[signals/detector.py]**

**#      b. Score the signals                    \[signals/scorer.py]**

**#      c. Generate plain-English reason        \[signals/scorer.py]**

**#      d. Build the output record              \[utils/io.py]**

**#   3. Print summary table to stdout           \[utils/io.py]**

**#   4. Write all results to JSON output file   \[utils/io.py]**

**#**

**# ARCHITECTURAL DECISION: main.py is intentionally thin — it is purely**

**# orchestration. The actual intelligence lives in signals/ and the I/O**

**# contract lives in utils/. This makes it easy to swap the CLI for an API**

**# endpoint, a Celery task, or a batch job later without touching any logic.**

**# =============================================================================**



**import argparse**

**import sys**

**import os**



**# ---------------------------------------------------------------------------**

**# Path setup: ensure the project root is on sys.path so that `signals` and**

**# `utils` packages resolve correctly regardless of where python is invoked from.**

**# ---------------------------------------------------------------------------**

**PROJECT\_ROOT = os.path.dirname(os.path.abspath(\_\_file\_\_))**

**if PROJECT\_ROOT not in sys.path:**

&#x20;   **sys.path.insert(0, PROJECT\_ROOT)**



**from signals import SignalDetector, SignalScorer**

**from utils.io import load\_posts, save\_results, build\_output\_record, print\_summary\_table**





**# =============================================================================**

**# CLI ARGUMENT PARSING**

**# =============================================================================**



**def parse\_args() -> argparse.Namespace:**

&#x20;   **"""**

&#x20;   **Define and parse command-line arguments.**



&#x20;   **DESIGN: We use argparse rather than sys.argv directly because it gives us**

&#x20;   **--help documentation, type checking, and defaults for free.**

&#x20;   **"""**

&#x20;   **parser = argparse.ArgumentParser(**

&#x20;       **prog="hiring\_pain\_detector",**

&#x20;       **description=(**

&#x20;           **"Hiring Pain / Intent Detector — "**

&#x20;           **"Scores unstructured text for HR hiring pain signals using local NLP heuristics. "**

&#x20;           **"No cloud APIs required."**

&#x20;       **),**

&#x20;       **formatter\_class=argparse.RawDescriptionHelpFormatter,**

&#x20;       **epilog="""**

**EXAMPLES:**

&#x20; **python main.py**

&#x20; **python main.py --input my\_posts.json --output results/leads.json**

&#x20; **python main.py --min-score 60 --verbose**

&#x20;       **""",**

&#x20;   **)**



&#x20;   **parser.add\_argument(**

&#x20;       **"--input",**

&#x20;       **type=str,**

&#x20;       **default="sample\_data.json",**

&#x20;       **help="Path to the input JSON file (default: sample\_data.json)",**

&#x20;   **)**



&#x20;   **parser.add\_argument(**

&#x20;       **"--output",**

&#x20;       **type=str,**

&#x20;       **default="results.json",**

&#x20;       **help="Path to write the output JSON file (default: results.json)",**

&#x20;   **)**



&#x20;   **parser.add\_argument(**

&#x20;       **"--min-score",**

&#x20;       **type=int,**

&#x20;       **default=0,**

&#x20;       **metavar="N",**

&#x20;       **help="Only include results with signal\_score >= N in the output file (default: 0 = all)",**

&#x20;   **)**



&#x20;   **parser.add\_argument(**

&#x20;       **"--verbose",**

&#x20;       **action="store\_true",**

&#x20;       **default=False,**

&#x20;       **help="Print the detailed score breakdown for each record to stdout",**

&#x20;   **)**



&#x20;   **return parser.parse\_args()**





**# =============================================================================**

**# PIPELINE ORCHESTRATION**

**# =============================================================================**



**def run\_pipeline(**

&#x20;   **input\_path: str,**

&#x20;   **output\_path: str,**

&#x20;   **min\_score: int = 0,**

&#x20;   **verbose: bool = False,**

**) -> None:**

&#x20;   **"""**

&#x20;   **Execute the full detection pipeline end-to-end.**



&#x20;   **This function is separated from main() so it can be called programmatically**

&#x20;   **from tests or other Python code without subprocess overhead.**



&#x20;   **Args:**

&#x20;       **input\_path:  Path to the JSON file of posts to analyze**

&#x20;       **output\_path: Path to write the JSON results file**

&#x20;       **min\_score:   Filter threshold — only records >= this score are saved**

&#x20;       **verbose:     If True, print per-record score breakdowns to stdout**

&#x20;   **"""**

&#x20;   **print("\\n" + "=" \* 60)**

&#x20;   **print("  HIRING PAIN DETECTOR — Starting Pipeline")**

&#x20;   **print("=" \* 60)**

&#x20;   **print(f"  Input:     {input\_path}")**

&#x20;   **print(f"  Output:    {output\_path}")**

&#x20;   **print(f"  Min Score: {min\_score}")**

&#x20;   **print(f"  Verbose:   {verbose}")**

&#x20;   **print("=" \* 60 + "\\n")**



&#x20;   **# --- Step 1: Load input data ---**

&#x20;   **posts = load\_posts(input\_path)**



&#x20;   **# --- Step 2: Initialize the detector and scorer ---**

&#x20;   **# These are instantiated once and reused for all posts.**

&#x20;   **# No state is shared between post analyses — each call is independent.**

&#x20;   **detector = SignalDetector()**

&#x20;   **scorer = SignalScorer()**



&#x20;   **# --- Step 3: Process each post ---**

&#x20;   **results = \[]**

&#x20;   **for i, post in enumerate(posts):**

&#x20;       **company = post.get("company", "Unknown")**

&#x20;       **source\_url = post.get("source\_url", "")**

&#x20;       **text = post.get("text", "")**



&#x20;       **print(f"\[{i+1}/{len(posts)}] Processing: {company} | {source\_url\[:60]}")**



&#x20;       **# 3a. Extract all signals from the raw text**

&#x20;       **signals = detector.extract(text=text, company=company, source\_url=source\_url)**



&#x20;       **# 3b. Calculate the composite score (0-100)**

&#x20;       **score\_result = scorer.calculate\_score(signals=signals, raw\_text=text)**

&#x20;       **score = score\_result\["score"]**

&#x20;       **breakdown = score\_result\["breakdown"]**



&#x20;       **# 3c. Generate the plain-English reason field**

&#x20;       **reason = scorer.generate\_reason(signals=signals, score=score)**



&#x20;       **# 3d. Build the output record in the required schema**

&#x20;       **output\_record = build\_output\_record(**

&#x20;           **post=post,**

&#x20;           **signals=signals,**

&#x20;           **score=score,**

&#x20;           **reason=reason,**

&#x20;       **)**



&#x20;       **results.append(output\_record)**

&#x20;       **print(f"         Score: {score}/100 | Theme: {signals\['primary\_theme']}")**



&#x20;       **# Optional verbose breakdown**

&#x20;       **if verbose:**

&#x20;           **print("         -- Score Breakdown --")**

&#x20;           **print(f"            Title score:       {breakdown.get('title\_score', 0)}")**

&#x20;           **print(f"            Theme score:       {breakdown.get('theme\_score', 0)}")**

&#x20;           **print(f"            Ownership score:   {breakdown.get('ownership\_score', 0)}")**

&#x20;           **print(f"            Urgency bonus:     {breakdown.get('urgency\_score', 0)}")**

&#x20;           **print(f"            Noise penalty:     {breakdown.get('noise\_penalty', 0)}")**

&#x20;           **print(f"            Raw score:         {breakdown.get('raw\_score', 0)}")**

&#x20;           **print(f"            Proximity mult:    {breakdown.get('proximity\_multiplier', 1.0):.2f}")**

&#x20;           **print(f"            Proximity detail:  {breakdown.get('proximity\_detail', '')}")**

&#x20;           **print(f"            FINAL:             {score}")**

&#x20;           **print()**



&#x20;   **# --- Step 4: Filter by min\_score ---**

&#x20;   **if min\_score > 0:**

&#x20;       **before = len(results)**

&#x20;       **results = \[r for r in results if r.get("signal\_score", 0) >= min\_score]**

&#x20;       **print(f"\\n\[FILTER] min-score={min\_score}: {before} → {len(results)} records kept")**



&#x20;   **# --- Step 5: Print summary table to stdout ---**

&#x20;   **print\_summary\_table(results)**



&#x20;   **# --- Step 6: Save results to JSON ---**

&#x20;   **save\_results(results, output\_path)**





**# =============================================================================**

**# ENTRY POINT**

**# =============================================================================**



**def main():**

&#x20;   **args = parse\_args()**

&#x20;   **run\_pipeline(**

&#x20;       **input\_path=args.input,**

&#x20;       **output\_path=args.output,**

&#x20;       **min\_score=args.min\_score,**

&#x20;       **verbose=args.verbose,**

&#x20;   **)**





**if \_\_name\_\_ == "\_\_main\_\_":**

&#x20;   **main()** 



**# =============================================================================**

**# signals/detector.py**

**# =============================================================================**

**# PURPOSE: The core signal extraction class. Reads raw text and produces a**

**#          structured dict of everything it found — titles, pain themes,**

**#          ownership phrases, noise signals, urgency amplifiers.**

**#**

**# ARCHITECTURAL DECISION: The detector is PURELY a pattern matcher. It does not**

**# assign scores or make judgments. It simply finds things and reports them.**

**# All scoring judgment is deferred to scorer.py. This single-responsibility**

**# design makes the detector unit-testable in complete isolation.**

**#**

**# HOW MATCHING WORKS:**

**#   All matching is case-insensitive and uses two strategies:**

**#   1. PHRASE matching: Check if the full phrase exists as a substring.**

**#      (e.g., "my team" anywhere in the text)**

**#   2. REGEX matching: For title detection, we use word-boundary regex to**

**#      avoid matching "chr" inside "chromosome" matching "chro".**

**#**

**# INPUT: Raw string of text (LinkedIn post, blog excerpt, transcript chunk)**

**# OUTPUT: A structured dict of all signals found, ready for scorer.py**

**# =============================================================================**



**import re**

**from typing import Dict, List, Any**

**from signals.themes import (**

&#x20;   **JOB\_TITLE\_SIGNALS,**

&#x20;   **PAIN\_THEMES,**

&#x20;   **OWNERSHIP\_LANGUAGE,**

&#x20;   **ANALYST\_NOISE\_SIGNALS,**

&#x20;   **URGENCY\_AMPLIFIERS,**

**)**





**class SignalDetector:**

&#x20;   **"""**

&#x20;   **Extracts structured hiring-pain signals from unstructured text.**



&#x20;   **Usage:**

&#x20;       **detector = SignalDetector()**

&#x20;       **signals = detector.extract(text="...", company="Acme Corp")**

&#x20;   **"""**



&#x20;   **def extract(self, text: str, company: str = "Unknown", source\_url: str = "") -> Dict\[str, Any]:**

&#x20;       **"""**

&#x20;       **Main extraction method. Runs all sub-extractors and assembles the**

&#x20;       **unified signals dict.**



&#x20;       **Args:**

&#x20;           **text:       The raw input text to analyze**

&#x20;           **company:    The company name (passed through to output)**

&#x20;           **source\_url: The origin URL (passed through to output)**



&#x20;       **Returns:**

&#x20;           **A structured dict with all extracted signals and metadata.**

&#x20;       **"""**

&#x20;       **# Normalize: lowercase copy of text for all matching operations.**

&#x20;       **# We keep the original for display purposes.**

&#x20;       **normalized = text.lower()**



&#x20;       **# Run each extractor**

&#x20;       **matched\_titles = self.\_extract\_titles(normalized)**

&#x20;       **matched\_themes = self.\_extract\_pain\_themes(normalized)**

&#x20;       **matched\_ownership = self.\_extract\_ownership(normalized)**

&#x20;       **matched\_noise = self.\_extract\_noise(normalized)**

&#x20;       **matched\_urgency = self.\_extract\_urgency(normalized)**



&#x20;       **# Determine the PRIMARY signal type:**

&#x20;       **# The theme with the most matched keywords wins. This becomes the**

&#x20;       **# `signal\_type` field in the output JSON.**

&#x20;       **primary\_theme = self.\_determine\_primary\_theme(matched\_themes)**



&#x20;       **# Collect all matched keywords for the output JSON:**

&#x20;       **# Flatten themes + ownership (strong only) into one list for display.**

&#x20;       **all\_matched\_keywords = self.\_collect\_display\_keywords(**

&#x20;           **matched\_themes, matched\_ownership**

&#x20;       **)**



&#x20;       **return {**

&#x20;           **# -- Metadata (passed through) --**

&#x20;           **"company": company,**

&#x20;           **"source\_url": source\_url,**



&#x20;           **# -- Derived classification --**

&#x20;           **"primary\_theme": primary\_theme,**



&#x20;           **# -- Raw extraction results (consumed by scorer.py) --**

&#x20;           **"matched\_titles": matched\_titles,**

&#x20;           **"matched\_themes": matched\_themes,**

&#x20;           **"matched\_ownership": matched\_ownership,**

&#x20;           **"matched\_noise": matched\_noise,**

&#x20;           **"matched\_urgency": matched\_urgency,**



&#x20;           **# -- Display-ready field for JSON output --**

&#x20;           **"matched\_keywords": all\_matched\_keywords,**

&#x20;       **}**



&#x20;   **# -------------------------------------------------------------------------**

&#x20;   **# PRIVATE EXTRACTOR METHODS**

&#x20;   **# Each handles exactly one category of signal.**

&#x20;   **# -------------------------------------------------------------------------**



&#x20;   **def \_extract\_titles(self, normalized\_text: str) -> List\[Dict\[str, str]]:**

&#x20;       **"""**

&#x20;       **Scan for job title signals.**



&#x20;       **Returns a list of dicts, one per match, e.g.:**

&#x20;           **\[{"matched": "chro", "tier": "tier\_1"}, ...]**



&#x20;       **WHY DICTS NOT STRINGS: We need to carry the tier metadata forward to**

&#x20;       **the scorer so it can apply the correct point weight.**



&#x20;       **REGEX APPROACH: We use word-boundary matching (\\b) to avoid partial**

&#x20;       **matches. "CHRO" in "CHROnicle" would otherwise match incorrectly.**

&#x20;       **However, for multi-word phrases like "head of recruiting", simple**

&#x20;       **substring matching is fine because the phrase is specific enough.**

&#x20;       **"""**

&#x20;       **found = \[]**

&#x20;       **seen = set()  # Deduplicate: don't report the same title twice**



&#x20;       **for tier, titles in JOB\_TITLE\_SIGNALS.items():**

&#x20;           **for title in titles:**

&#x20;               **# For single-word titles (like "chro", "cpo"), use word boundary**

&#x20;               **# For multi-word phrases, substring match is sufficient**

&#x20;               **if " " not in title:**

&#x20;                   **pattern = r"\\b" + re.escape(title) + r"\\b"**

&#x20;                   **match = re.search(pattern, normalized\_text)**

&#x20;                   **found\_it = match is not None**

&#x20;               **else:**

&#x20;                   **found\_it = title in normalized\_text**



&#x20;               **if found\_it and title not in seen:**

&#x20;                   **seen.add(title)**

&#x20;                   **found.append({"matched": title, "tier": tier})**



&#x20;       **return found**



&#x20;   **def \_extract\_pain\_themes(self, normalized\_text: str) -> Dict\[str, List\[str]]:**

&#x20;       **"""**

&#x20;       **Scan for pain theme keywords, grouped by theme.**



&#x20;       **Returns a dict mapping each theme name to a list of keywords found.**

&#x20;       **Empty list means that theme wasn't detected.**



&#x20;       **Example return:**

&#x20;       **{**

&#x20;           **"recruiter\_overload": \["overwhelmed", "drowning in resumes"],**

&#x20;           **"interview\_speed": \[],**

&#x20;           **...**

&#x20;       **}**



&#x20;       **WHY GROUP BY THEME: The scorer needs theme diversity (# of distinct themes)**

&#x20;       **not just total keyword count. This structure makes that calculation trivial.**

&#x20;       **"""**

&#x20;       **theme\_matches = {}**



&#x20;       **for theme\_name, keywords in PAIN\_THEMES.items():**

&#x20;           **matched\_in\_theme = \[]**

&#x20;           **for keyword in keywords:**

&#x20;               **if keyword in normalized\_text and keyword not in matched\_in\_theme:**

&#x20;                   **matched\_in\_theme.append(keyword)**

&#x20;           **theme\_matches\[theme\_name] = matched\_in\_theme**



&#x20;       **return theme\_matches**



&#x20;   **def \_extract\_ownership(self, normalized\_text: str) -> Dict\[str, List\[str]]:**

&#x20;       **"""**

&#x20;       **Scan for first-person / ownership language, grouped by tier strength.**



&#x20;       **Returns a dict of {tier: \[matched\_phrases]}.**



&#x20;       **WHY TIER STRUCTURE: The scorer applies different point values per tier**

&#x20;       **(strong=8pts, moderate=5pts, weak=2pts). The tiered structure in the**

&#x20;       **return value makes it easy to apply tier-specific weights without**

&#x20;       **re-examining the text.**

&#x20;       **"""**

&#x20;       **ownership\_matches = {"strong": \[], "moderate": \[], "weak": \[]}**



&#x20;       **for tier, phrases in OWNERSHIP\_LANGUAGE.items():**

&#x20;           **for phrase in phrases:**

&#x20;               **if phrase in normalized\_text and phrase not in ownership\_matches\[tier]:**

&#x20;                   **ownership\_matches\[tier].append(phrase)**



&#x20;       **return ownership\_matches**



&#x20;   **def \_extract\_noise(self, normalized\_text: str) -> List\[str]:**

&#x20;       **"""**

&#x20;       **Scan for analyst / observer language patterns.**



&#x20;       **Returns a flat list of matched noise phrases. The scorer will apply**

&#x20;       **a penalty per phrase found. No tiering here — all noise is equally bad.**

&#x20;       **"""**

&#x20;       **matched\_noise = \[]**

&#x20;       **for phrase in ANALYST\_NOISE\_SIGNALS:**

&#x20;           **if phrase in normalized\_text and phrase not in matched\_noise:**

&#x20;               **matched\_noise.append(phrase)**

&#x20;       **return matched\_noise**



&#x20;   **def \_extract\_urgency(self, normalized\_text: str) -> List\[str]:**

&#x20;       **"""**

&#x20;       **Scan for urgency amplifiers.**



&#x20;       **Returns a flat list of matched amplifier words. The scorer uses the**

&#x20;       **COUNT of unique matches to calculate a bonus (with a cap).**

&#x20;       **"""**

&#x20;       **matched\_urgency = \[]**

&#x20;       **for word in URGENCY\_AMPLIFIERS:**

&#x20;           **if word in normalized\_text and word not in matched\_urgency:**

&#x20;               **matched\_urgency.append(word)**

&#x20;       **return matched\_urgency**



&#x20;   **# -------------------------------------------------------------------------**

&#x20;   **# HELPER METHODS**

&#x20;   **# -------------------------------------------------------------------------**



&#x20;   **def \_determine\_primary\_theme(self, matched\_themes: Dict\[str, List\[str]]) -> str:**

&#x20;       **"""**

&#x20;       **Determine the single most dominant pain theme.**



&#x20;       **Strategy: the theme with the most matched keywords is the primary theme.**

&#x20;       **Ties are broken by the order themes appear in PAIN\_THEMES (arbitrary**

&#x20;       **but consistent).**



&#x20;       **Returns "unknown" if no themes were matched at all.**

&#x20;       **"""**

&#x20;       **if not matched\_themes:**

&#x20;           **return "unknown"**



&#x20;       **# Sort by number of matches descending, take the first**

&#x20;       **sorted\_themes = sorted(**

&#x20;           **matched\_themes.items(),**

&#x20;           **key=lambda x: len(x\[1]),**

&#x20;           **reverse=True**

&#x20;       **)**



&#x20;       **best\_theme, best\_keywords = sorted\_themes\[0]**

&#x20;       **if not best\_keywords:**

&#x20;           **return "unknown"**



&#x20;       **return best\_theme**



&#x20;   **def \_collect\_display\_keywords(**

&#x20;       **self,**

&#x20;       **matched\_themes: Dict\[str, List\[str]],**

&#x20;       **matched\_ownership: Dict\[str, List\[str]],**

&#x20;   **) -> List\[str]:**

&#x20;       **"""**

&#x20;       **Assemble the flat list of keywords shown in the output JSON.**



&#x20;       **We include:**

&#x20;         **- All matched pain keywords (from all themes)**

&#x20;         **- Strong ownership phrases (these are the most readable/meaningful)**



&#x20;       **Capped at 10 items total to keep the output concise.**

&#x20;       **"""**

&#x20;       **display = \[]**



&#x20;       **# Add pain keywords from all themes**

&#x20;       **for kws in matched\_themes.values():**

&#x20;           **display.extend(kws)**



&#x20;       **# Add strong ownership signals**

&#x20;       **display.extend(matched\_ownership.get("strong", \[]))**



&#x20;       **# Deduplicate and cap**

&#x20;       **seen = set()**

&#x20;       **unique = \[]**

&#x20;       **for item in display:**

&#x20;           **if item not in seen:**

&#x20;               **seen.add(item)**

&#x20;               **unique.append(item)**



&#x20;       **return unique\[:10]**



**# =============================================================================**

**# signals/scorer.py**

**# =============================================================================**

**# PURPOSE: The scoring engine. Takes the raw extraction results from detector.py**

**#          and converts them into a single 0-100 composite score with a full**

**#          audit trail of how that score was reached.**

**#**

**# ARCHITECTURAL DECISION: Keeping scoring SEPARATE from detection is critical.**

**#   - detector.py is responsible for FINDING signals (pattern matching)**

**#   - scorer.py is responsible for WEIGHTING signals (judgment)**

**#**

**# This means you can tune the weights in this file without touching the**

**# detection logic, and vice versa. It also makes A/B testing different scoring**

**# strategies trivial.**

**#**

**# SCORING MODEL OVERVIEW:**

**# The total score is built from five additive components, each capped:**

**#**

**#   Component               Max Points   Notes**

**#   ─────────────────────   ──────────   ──────────────────────────────────────**

**#   Job Title Score              30      Tier 1 = 30, Tier 2 = 18**

**#   Pain Theme Score             25      5 pts per unique theme, capped at 25**

**#   Ownership Score              25      Tiered: strong/moderate/weak**

**#   Urgency Bonus                10      Amplifies when co-located with pain**

**#   Analyst Noise Penalty       -20      Applied per noise signal found**

**#   ─────────────────────   ──────────**

**#   RAW TOTAL                    70      Before proximity multiplier**

**#   Proximity Multiplier        x1.43    Scales raw to max 100 when all co-occur**

**#**

**# PROXIMITY MULTIPLIER RATIONALE:**

**# The proximity check answers: "Do the ownership words appear NEAR the pain**

**# words?" A document where "my team" appears in paragraph 1 and pain words**

**# appear in paragraph 10 is weaker than one where they're in the same sentence.**

**# The multiplier ranges from 0.7 (no proximity) to 1.0 (tight co-occurrence),**

**# scaling the raw score accordingly.**

**# =============================================================================**



**import re**

**from typing import Dict, List, Any**

**from signals.themes import (**

&#x20;   **JOB\_TITLE\_SIGNALS,**

&#x20;   **PAIN\_THEMES,**

&#x20;   **OWNERSHIP\_LANGUAGE,**

&#x20;   **ANALYST\_NOISE\_SIGNALS,**

&#x20;   **URGENCY\_AMPLIFIERS,**

**)**





**# -----------------------------------------------------------------------------**

**# SCORING CONSTANTS**

**# These are the weights used by the scoring model.**

**# Changing these values changes the model's behavior - document any changes.**

**# -----------------------------------------------------------------------------**

**TITLE\_TIER\_1\_SCORE = 30        # C-suite / VP level**

**TITLE\_TIER\_2\_SCORE = 18        # Manager / Lead level**

**PAIN\_THEME\_PER\_MATCH = 5       # Points per unique matched pain theme**

**PAIN\_THEME\_CAP = 25            # Max points from pain themes**

**OWNERSHIP\_STRONG\_PER = 8       # Points per strong ownership phrase**

**OWNERSHIP\_MODERATE\_PER = 5     # Points per moderate ownership phrase**

**OWNERSHIP\_WEAK\_PER = 2         # Points per weak ownership phrase**

**OWNERSHIP\_CAP = 25             # Max total from ownership signals**

**URGENCY\_PER\_MATCH = 3          # Points per urgency amplifier found**

**URGENCY\_CAP = 10               # Max bonus from urgency**

**NOISE\_PER\_SIGNAL = -3          # Penalty per analyst noise phrase found**

**NOISE\_CAP = -20                # Maximum penalty (floor for noise deduction)**



**# Proximity window: how many words apart can ownership + pain words be and**

**# still count as "co-located"? 50 words \~ 2-3 sentences.**

**PROXIMITY\_WINDOW\_WORDS = 50**



**# Multiplier range: proximity adjusts the raw score within this range**

**PROXIMITY\_MIN\_MULTIPLIER = 0.70   # No proximity detected at all**

**PROXIMITY\_MID\_MULTIPLIER = 0.88   # Partial proximity (different paragraphs)**

**PROXIMITY\_MAX\_MULTIPLIER = 1.00   # Tight co-occurrence (same sentence/window)**





**class SignalScorer:**

&#x20;   **"""**

&#x20;   **Calculates a 0-100 hiring pain signal score from pre-extracted signals.**



&#x20;   **The scorer operates on a structured `signals` dict produced by the**

&#x20;   **SignalDetector. It doesn't re-read the raw text for most operations,**

&#x20;   **but DOES receive the raw text for the proximity calculation, which**

&#x20;   **requires positional analysis.**

&#x20;   **"""**



&#x20;   **def \_\_init\_\_(self):**

&#x20;       **# Store the scoring breakdown for transparency / audit trail**

&#x20;       **self.score\_breakdown: Dict\[str, Any] = {}**



&#x20;   **def calculate\_score(self, signals: Dict\[str, Any], raw\_text: str) -> Dict\[str, Any]:**

&#x20;       **"""**

&#x20;       **Master scoring function. Calls each sub-scorer in order, accumulates**

&#x20;       **the raw score, applies the proximity multiplier, clamps to \[0, 100],**

&#x20;       **and returns the full result dict including the audit breakdown.**



&#x20;       **Args:**

&#x20;           **signals: The structured signals dict from SignalDetector.extract()**

&#x20;           **raw\_text: The original document text (needed for proximity check)**



&#x20;       **Returns:**

&#x20;           **A dict with 'score' (int) and 'breakdown' (detailed audit trail)**

&#x20;       **"""**

&#x20;       **self.score\_breakdown = {}**



&#x20;       **# --- Component 1: Job Title ---**

&#x20;       **title\_score = self.\_score\_job\_title(signals.get("matched\_titles", \[]))**

&#x20;       **self.score\_breakdown\["title\_score"] = title\_score**



&#x20;       **# --- Component 2: Pain Themes ---**

&#x20;       **theme\_score = self.\_score\_pain\_themes(signals.get("matched\_themes", {}))**

&#x20;       **self.score\_breakdown\["theme\_score"] = theme\_score**



&#x20;       **# --- Component 3: Ownership Language ---**

&#x20;       **ownership\_score = self.\_score\_ownership(signals.get("matched\_ownership", {}))**

&#x20;       **self.score\_breakdown\["ownership\_score"] = ownership\_score**



&#x20;       **# --- Component 4: Urgency Amplifiers ---**

&#x20;       **urgency\_score = self.\_score\_urgency(signals.get("matched\_urgency", \[]))**

&#x20;       **self.score\_breakdown\["urgency\_score"] = urgency\_score**



&#x20;       **# --- Component 5: Analyst Noise Penalty ---**

&#x20;       **noise\_penalty = self.\_score\_noise\_penalty(signals.get("matched\_noise", \[]))**

&#x20;       **self.score\_breakdown\["noise\_penalty"] = noise\_penalty**



&#x20;       **# --- Raw total before proximity ---**

&#x20;       **raw\_score = title\_score + theme\_score + ownership\_score + urgency\_score + noise\_penalty**

&#x20;       **self.score\_breakdown\["raw\_score"] = raw\_score**



&#x20;       **# --- Proximity Multiplier ---**

&#x20;       **# This is the key "signal vs noise" gate. Even if everything else**

&#x20;       **# scores high, if the ownership and pain words aren't near each other,**

&#x20;       **# we discount the score. This prevents gaming by keyword stuffing.**

&#x20;       **multiplier, proximity\_detail = self.\_calculate\_proximity\_multiplier(**

&#x20;           **raw\_text,**

&#x20;           **signals.get("matched\_ownership", {}),**

&#x20;           **signals.get("matched\_themes", {}),**

&#x20;       **)**

&#x20;       **self.score\_breakdown\["proximity\_multiplier"] = multiplier**

&#x20;       **self.score\_breakdown\["proximity\_detail"] = proximity\_detail**



&#x20;       **# --- Final score: apply multiplier and clamp to \[0, 100] ---**

&#x20;       **# We scale the raw score up using the multiplier to reach a max of 100.**

&#x20;       **# The scaling factor (100/90 ≈ 1.11) accounts for the theoretical max**

&#x20;       **# raw score of \~90 points (30+25+25+10+0), normalizing it to 100.**

&#x20;       **final\_score = raw\_score \* multiplier**

&#x20;       **final\_score = max(0, min(100, round(final\_score)))**

&#x20;       **self.score\_breakdown\["final\_score"] = final\_score**



&#x20;       **return {**

&#x20;           **"score": final\_score,**

&#x20;           **"breakdown": self.score\_breakdown,**

&#x20;       **}**



&#x20;   **# -------------------------------------------------------------------------**

&#x20;   **# COMPONENT SCORERS**

&#x20;   **# Each method handles exactly one scoring dimension. This makes it trivial**

&#x20;   **# to adjust a single weight without affecting anything else.**

&#x20;   **# -------------------------------------------------------------------------**



&#x20;   **def \_score\_job\_title(self, matched\_titles: List\[Dict]) -> int:**

&#x20;       **"""**

&#x20;       **Score based on the highest-tier job title found.**



&#x20;       **We take the MAXIMUM score across all matched titles, not the sum.**

&#x20;       **Rationale: If someone lists both "CHRO" and "Director of HR", we**

&#x20;       **shouldn't double-count. We want the single most authoritative title.**

&#x20;       **"""**

&#x20;       **if not matched\_titles:**

&#x20;           **return 0**



&#x20;       **max\_score = 0**

&#x20;       **for title\_match in matched\_titles:**

&#x20;           **tier = title\_match.get("tier", "tier\_2")**

&#x20;           **score = TITLE\_TIER\_1\_SCORE if tier == "tier\_1" else TITLE\_TIER\_2\_SCORE**

&#x20;           **max\_score = max(max\_score, score)**



&#x20;       **return max\_score**



&#x20;   **def \_score\_pain\_themes(self, matched\_themes: Dict\[str, List\[str]]) -> int:**

&#x20;       **"""**

&#x20;       **Score based on how many distinct pain themes are represented.**



&#x20;       **We score UNIQUE THEMES, not unique keywords. The rationale is that**

&#x20;       **someone who hits 3 different pain themes ("overload", "quality", "speed")**

&#x20;       **is more interesting than someone who hits 10 keywords all in the same**

&#x20;       **theme. Diversity of pain = higher priority lead.**

&#x20;       **"""**

&#x20;       **if not matched\_themes:**

&#x20;           **return 0**



&#x20;       **# Count only themes that had at least one keyword match**

&#x20;       **active\_theme\_count = sum(**

&#x20;           **1 for theme\_keywords in matched\_themes.values() if len(theme\_keywords) > 0**

&#x20;       **)**

&#x20;       **raw = active\_theme\_count \* PAIN\_THEME\_PER\_MATCH**

&#x20;       **return min(raw, PAIN\_THEME\_CAP)**



&#x20;   **def \_score\_ownership(self, matched\_ownership: Dict\[str, List\[str]]) -> int:**

&#x20;       **"""**

&#x20;       **Score based on ownership language found, weighted by tier strength.**



&#x20;       **Strong phrases (e.g. "my team is struggling") carry more weight than**

&#x20;       **weak phrases (e.g. "internally"). Caps at OWNERSHIP\_CAP to prevent**

&#x20;       **a document that just repeats "we" 50 times from maxing out the score.**

&#x20;       **"""**

&#x20;       **if not matched\_ownership:**

&#x20;           **return 0**



&#x20;       **strong\_phrases = matched\_ownership.get("strong", \[])**

&#x20;       **moderate\_phrases = matched\_ownership.get("moderate", \[])**

&#x20;       **weak\_phrases = matched\_ownership.get("weak", \[])**



&#x20;       **# Score each tier, using unique matches only (deduplicated by detector)**

&#x20;       **strong\_score = len(strong\_phrases) \* OWNERSHIP\_STRONG\_PER**

&#x20;       **moderate\_score = len(moderate\_phrases) \* OWNERSHIP\_MODERATE\_PER**

&#x20;       **weak\_score = len(weak\_phrases) \* OWNERSHIP\_WEAK\_PER**



&#x20;       **total = strong\_score + moderate\_score + weak\_score**

&#x20;       **return min(total, OWNERSHIP\_CAP)**



&#x20;   **def \_score\_urgency(self, matched\_urgency: List\[str]) -> int:**

&#x20;       **"""**

&#x20;       **Apply urgency bonus for amplifying words found near pain signals.**



&#x20;       **This rewards texts that aren't just mentioning pain passively but**

&#x20;       **expressing it with emotional weight ("we are DESPERATELY struggling").**

&#x20;       **"""**

&#x20;       **if not matched\_urgency:**

&#x20;           **return 0**



&#x20;       **raw = len(matched\_urgency) \* URGENCY\_PER\_MATCH**

&#x20;       **return min(raw, URGENCY\_CAP)**



&#x20;   **def \_score\_noise\_penalty(self, matched\_noise: List\[str]) -> int:**

&#x20;       **"""**

&#x20;       **Apply penalties for analyst/observer language patterns.**



&#x20;       **Returns a NEGATIVE integer. The more analyst language found, the**

&#x20;       **larger the deduction. This is what makes the system resistant to**

&#x20;       **whitepapers and market reports that use pain keywords but aren't**

&#x20;       **personal expressions of pain.**

&#x20;       **"""**

&#x20;       **if not matched\_noise:**

&#x20;           **return 0**



&#x20;       **raw = len(matched\_noise) \* NOISE\_PER\_SIGNAL**

&#x20;       **# Cap the penalty: we don't want a score to go below 0 purely from noise**

&#x20;       **return max(raw, NOISE\_CAP)**



&#x20;   **def \_calculate\_proximity\_multiplier(**

&#x20;       **self,**

&#x20;       **raw\_text: str,**

&#x20;       **matched\_ownership: Dict\[str, List\[str]],**

&#x20;       **matched\_themes: Dict\[str, List\[str]],**

&#x20;   **) -> tuple:**

&#x20;       **"""**

&#x20;       **The core "signal vs. noise" gate.**



&#x20;       **Checks whether ownership language appears PHYSICALLY CLOSE to pain**

&#x20;       **theme keywords in the text. Co-occurrence in the same window of words**

&#x20;       **is strong evidence that the author is personally describing their pain,**

&#x20;       **not just mentioning two unrelated topics in the same document.**



&#x20;       **Algorithm:**

&#x20;         **1. Tokenize the raw text into a flat list of (word, position) tuples.**

&#x20;         **2. For each ownership phrase found, record its start position.**

&#x20;         **3. For each pain keyword found, record its start position.**

&#x20;         **4. Check if any ownership position is within PROXIMITY\_WINDOW\_WORDS**

&#x20;            **of any pain keyword position.**

&#x20;         **5. Return a multiplier based on how close the best co-occurrence is.**



&#x20;       **Returns:**

&#x20;           **Tuple of (multiplier: float, detail: str)**

&#x20;       **"""**

&#x20;       **# Flatten all ownership phrases across tiers**

&#x20;       **all\_ownership = \[]**

&#x20;       **for tier\_phrases in matched\_ownership.values():**

&#x20;           **all\_ownership.extend(tier\_phrases)**



&#x20;       **# Flatten all pain keywords across themes**

&#x20;       **all\_pain\_keywords = \[]**

&#x20;       **for theme\_keywords in matched\_themes.values():**

&#x20;           **all\_pain\_keywords.extend(theme\_keywords)**



&#x20;       **if not all\_ownership or not all\_pain\_keywords:**

&#x20;           **# If either category is empty, proximity is irrelevant;**

&#x20;           **# return mid-multiplier rather than penalizing for missing data**

&#x20;           **return PROXIMITY\_MID\_MULTIPLIER, "Proximity N/A: missing ownership or pain signals"**



&#x20;       **# Tokenize: split on whitespace, keeping track of word-level positions**

&#x20;       **# We work in word-index space, not character space, for simplicity.**

&#x20;       **words = re.sub(r"\[^\\w\\s'-]", " ", raw\_text.lower()).split()**



&#x20;       **# Build a mapping: phrase -> list of start word-indices where it occurs**

&#x20;       **def find\_phrase\_positions(phrase: str, word\_list: List\[str]) -> List\[int]:**

&#x20;           **"""Find all starting word indices of a phrase in the word list."""**

&#x20;           **phrase\_words = phrase.lower().split()**

&#x20;           **phrase\_len = len(phrase\_words)**

&#x20;           **positions = \[]**

&#x20;           **for i in range(len(word\_list) - phrase\_len + 1):**

&#x20;               **if word\_list\[i : i + phrase\_len] == phrase\_words:**

&#x20;                   **positions.append(i)**

&#x20;           **return positions**



&#x20;       **# Collect all positions for ownership phrases**

&#x20;       **ownership\_positions = \[]**

&#x20;       **for phrase in all\_ownership:**

&#x20;           **ownership\_positions.extend(find\_phrase\_positions(phrase, words))**



&#x20;       **# Collect all positions for pain keywords**

&#x20;       **pain\_positions = \[]**

&#x20;       **for phrase in all\_pain\_keywords:**

&#x20;           **pain\_positions.extend(find\_phrase\_positions(phrase, words))**



&#x20;       **if not ownership\_positions or not pain\_positions:**

&#x20;           **return (**

&#x20;               **PROXIMITY\_MIN\_MULTIPLIER,**

&#x20;               **"Signals found but not locatable at word level (possible phrase splitting)"**

&#x20;           **)**



&#x20;       **# Find the minimum distance between any ownership and any pain position**

&#x20;       **min\_distance = float("inf")**

&#x20;       **for o\_pos in ownership\_positions:**

&#x20;           **for p\_pos in pain\_positions:**

&#x20;               **distance = abs(o\_pos - p\_pos)**

&#x20;               **if distance < min\_distance:**

&#x20;                   **min\_distance = distance**



&#x20;       **# Classify the proximity**

&#x20;       **if min\_distance <= 15:**

&#x20;           **# Same sentence or consecutive sentences - very tight co-occurrence**

&#x20;           **multiplier = PROXIMITY\_MAX\_MULTIPLIER**

&#x20;           **detail = f"TIGHT co-occurrence: ownership and pain within {min\_distance} words"**

&#x20;       **elif min\_distance <= PROXIMITY\_WINDOW\_WORDS:**

&#x20;           **# Same paragraph - meaningful co-occurrence**

&#x20;           **multiplier = PROXIMITY\_MID\_MULTIPLIER**

&#x20;           **detail = f"MODERATE co-occurrence: ownership and pain within {min\_distance} words"**

&#x20;       **else:**

&#x20;           **# Different paragraphs - weak co-occurrence**

&#x20;           **multiplier = PROXIMITY\_MIN\_MULTIPLIER**

&#x20;           **detail = f"DISTANT: ownership and pain are {min\_distance} words apart"**



&#x20;       **return multiplier, detail**



&#x20;   **def generate\_reason(self, signals: Dict\[str, Any], score: int) -> str:**

&#x20;       **"""**

&#x20;       **Generate a plain-English explanation of WHY this text was surfaced.**



&#x20;       **This is the 'reason' field in the output JSON. It must be readable by**

&#x20;       **a non-technical sales or marketing person.**



&#x20;       **DESIGN: We build this from the extracted signals rather than using**

&#x20;       **templates, so each reason is specific to what was actually found.**

&#x20;       **"""**

&#x20;       **parts = \[]**



&#x20;       **# --- Title context ---**

&#x20;       **titles = signals.get("matched\_titles", \[])**

&#x20;       **if titles:**

&#x20;           **top\_title = titles\[0]**

&#x20;           **parts.append(**

&#x20;               **f"Author identified as '{top\_title\['matched']}' (tier: {top\_title\['tier']})"**

&#x20;           **)**



&#x20;       **# --- Primary pain theme ---**

&#x20;       **themes = signals.get("matched\_themes", {})**

&#x20;       **active\_themes = \[t for t, kws in themes.items() if kws]**

&#x20;       **if active\_themes:**

&#x20;           **primary = active\_themes\[0]**

&#x20;           **keywords\_found = themes\[primary]\[:3]  # Show up to 3 keywords**

&#x20;           **parts.append(**

&#x20;               **f"Primary pain theme '{primary}' detected via: {', '.join(keywords\_found)}"**

&#x20;           **)**

&#x20;           **if len(active\_themes) > 1:**

&#x20;               **parts.append(f"Also touches on: {', '.join(active\_themes\[1:])}")**



&#x20;       **# --- Ownership language ---**

&#x20;       **ownership = signals.get("matched\_ownership", {})**

&#x20;       **strong = ownership.get("strong", \[])**

&#x20;       **moderate = ownership.get("moderate", \[])**

&#x20;       **if strong:**

&#x20;           **parts.append(**

&#x20;               **f"Strong personal ownership language found: '{strong\[0]}'"**

&#x20;               **+ (f" + {len(strong)-1} more" if len(strong) > 1 else "")**

&#x20;           **)**

&#x20;       **elif moderate:**

&#x20;           **parts.append(f"Moderate personal ownership language: '{moderate\[0]}'")**



&#x20;       **# --- Noise signals ---**

&#x20;       **noise = signals.get("matched\_noise", \[])**

&#x20;       **if noise:**

&#x20;           **parts.append(**

&#x20;               **f"Note: {len(noise)} analyst/observer phrase(s) detected "**

&#x20;               **f"(e.g. '{noise\[0]}') -- score penalized accordingly"**

&#x20;           **)**



&#x20;       **# --- Score commentary ---**

&#x20;       **if score >= 75:**

&#x20;           **parts.append("HIGH SIGNAL: Strong candidate for outreach.")**

&#x20;       **elif score >= 50:**

&#x20;           **parts.append("MEDIUM SIGNAL: Worth monitoring; may need validation.")**

&#x20;       **elif score >= 25:**

&#x20;           **parts.append("LOW SIGNAL: Some indicators present but context unclear.")**

&#x20;       **else:**

&#x20;           **parts.append("NOISE: Likely analyst/vendor commentary, not personal pain.")**



&#x20;       **return " | ".join(parts)**



**# =============================================================================**

**# utils/io.py**

**# =============================================================================**

**# PURPOSE: All file I/O operations — reading sample data and writing results.**

**#**

**# ARCHITECTURAL DECISION: I/O is isolated from all business logic.**

**#   - detector.py and scorer.py never touch the filesystem.**

**#   - This module never touches scoring or detection logic.**

**#**

**# This makes testing trivial: tests can call detector/scorer with in-memory**

**# strings without needing files on disk.**

**#**

**# SUPPORTED INPUT: A JSON file with an array of post objects. See sample\_data.json**

**# for the expected schema.**

**#**

**# SUPPORTED OUTPUT: A JSON file with an array of result objects matching the**

**# required output schema defined in the project brief.**

**# =============================================================================**



**import json**

**import os**

**import sys**

**from datetime import datetime, timezone**

**from typing import List, Dict, Any**





**# ─────────────────────────────────────────────────────────────────────────────**

**# INPUT FUNCTIONS**

**# ─────────────────────────────────────────────────────────────────────────────**



**def load\_posts(filepath: str) -> List\[Dict\[str, Any]]:**

&#x20;   **"""**

&#x20;   **Load the input JSON file containing posts to analyze.**



&#x20;   **Expected file schema (array of objects):**

&#x20;   **\[**

&#x20;       **{**

&#x20;           **"company": "Acme Corp",**

&#x20;           **"source\_url": "https://linkedin.com/...",**

&#x20;           **"text": "The raw post or transcript text to analyze..."**

&#x20;       **},**

&#x20;       **...**

&#x20;   **]**



&#x20;   **Args:**

&#x20;       **filepath: Path to the JSON input file**



&#x20;   **Returns:**

&#x20;       **List of post dicts. Each must have at least 'text'.**

&#x20;       **'company' and 'source\_url' default to "Unknown" / "" if missing.**



&#x20;   **Raises:**

&#x20;       **SystemExit on file-not-found or JSON parse error, with a user-friendly**

&#x20;       **message. We exit here rather than raise so main.py stays clean.**

&#x20;   **"""**

&#x20;   **if not os.path.exists(filepath):**

&#x20;       **print(f"\[ERROR] Input file not found: {filepath}")**

&#x20;       **print(f"        Expected a JSON file at this path. Check the path and try again.")**

&#x20;       **sys.exit(1)**



&#x20;   **try:**

&#x20;       **with open(filepath, "r", encoding="utf-8") as f:**

&#x20;           **data = json.load(f)**

&#x20;   **except json.JSONDecodeError as e:**

&#x20;       **print(f"\[ERROR] Could not parse JSON in {filepath}: {e}")**

&#x20;       **sys.exit(1)**



&#x20;   **# Validate: must be a list**

&#x20;   **if not isinstance(data, list):**

&#x20;       **print(f"\[ERROR] {filepath} must contain a JSON array at the top level.")**

&#x20;       **sys.exit(1)**



&#x20;   **# Validate: each item must have 'text'**

&#x20;   **valid\_posts = \[]**

&#x20;   **for i, post in enumerate(data):**

&#x20;       **if "text" not in post or not post\["text"].strip():**

&#x20;           **print(f"\[WARNING] Post at index {i} is missing 'text' field — skipping.")**

&#x20;           **continue**

&#x20;       **# Apply defaults for optional fields**

&#x20;       **post.setdefault("company", "Unknown")**

&#x20;       **post.setdefault("source\_url", "")**

&#x20;       **valid\_posts.append(post)**



&#x20;   **print(f"\[INFO] Loaded {len(valid\_posts)} valid post(s) from {filepath}")**

&#x20;   **return valid\_posts**





**# ─────────────────────────────────────────────────────────────────────────────**

**# OUTPUT FUNCTIONS**

**# ─────────────────────────────────────────────────────────────────────────────**



**def build\_output\_record(**

&#x20;   **post: Dict\[str, Any],**

&#x20;   **signals: Dict\[str, Any],**

&#x20;   **score: int,**

&#x20;   **reason: str,**

**) -> Dict\[str, Any]:**

&#x20;   **"""**

&#x20;   **Assemble the final output record matching the required JSON output schema.**



&#x20;   **Required output schema:**

&#x20;   **{**

&#x20;       **"company":          "Example Corp",**

&#x20;       **"signal\_type":      "recruiter\_overload",**

&#x20;       **"source\_url":       "https://...",**

&#x20;       **"matched\_keywords": \["drowning in resumes", "burnout"],**

&#x20;       **"signal\_score":     82,**

&#x20;       **"detected\_at":      "2024-01-15T10:30:00Z",**

&#x20;       **"reason":           "Plain language explanation..."**

&#x20;   **}**



&#x20;   **DESIGN NOTE: We use UTC ISO 8601 with timezone for 'detected\_at'.**

&#x20;   **This ensures the timestamp is unambiguous regardless of where the system runs.**



&#x20;   **Args:**

&#x20;       **post:     The original post dict (provides company, source\_url)**

&#x20;       **signals:  The extracted signals dict from SignalDetector**

&#x20;       **score:    The computed 0-100 integer score from SignalScorer**

&#x20;       **reason:   The plain-language reason string from SignalScorer**



&#x20;   **Returns:**

&#x20;       **A dict matching the required output schema exactly.**

&#x20;   **"""**

&#x20;   **return {**

&#x20;       **"company": post.get("company", "Unknown"),**

&#x20;       **"signal\_type": signals.get("primary\_theme", "unknown"),**

&#x20;       **"source\_url": post.get("source\_url", ""),**

&#x20;       **"matched\_keywords": signals.get("matched\_keywords", \[]),**

&#x20;       **"signal\_score": score,**

&#x20;       **"detected\_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),**

&#x20;       **"reason": reason,**

&#x20;   **}**





**def save\_results(results: List\[Dict\[str, Any]], output\_filepath: str) -> None:**

&#x20;   **"""**

&#x20;   **Write the list of result records to a JSON file.**



&#x20;   **Results are sorted by signal\_score descending so the highest-priority**

&#x20;   **leads appear first in the output file.**



&#x20;   **Args:**

&#x20;       **results:          List of output record dicts**

&#x20;       **output\_filepath:  Path to write the JSON output**



&#x20;   **Raises:**

&#x20;       **SystemExit on write failure (permissions, disk full, etc.)**

&#x20;   **"""**

&#x20;   **# Sort: highest score first (most actionable leads at the top)**

&#x20;   **sorted\_results = sorted(results, key=lambda x: x.get("signal\_score", 0), reverse=True)**



&#x20;   **try:**

&#x20;       **# Ensure output directory exists**

&#x20;       **output\_dir = os.path.dirname(output\_filepath)**

&#x20;       **if output\_dir:**

&#x20;           **os.makedirs(output\_dir, exist\_ok=True)**



&#x20;       **with open(output\_filepath, "w", encoding="utf-8") as f:**

&#x20;           **json.dump(sorted\_results, f, indent=2, ensure\_ascii=False)**



&#x20;       **print(f"\\n\[OUTPUT] Results written to: {output\_filepath}")**

&#x20;       **print(f"         {len(sorted\_results)} record(s) saved, sorted by signal\_score desc.")**



&#x20;   **except OSError as e:**

&#x20;       **print(f"\[ERROR] Could not write output file {output\_filepath}: {e}")**

&#x20;       **sys.exit(1)**





**def print\_summary\_table(results: List\[Dict\[str, Any]]) -> None:**

&#x20;   **"""**

&#x20;   **Print a formatted summary table to stdout for quick CLI review.**



&#x20;   **This is the "quick glance" output. The full details are in the JSON file.**



&#x20;   **Example output:**

&#x20;   **┌──────────────────────────────────────────────────────────────────────┐**

&#x20;   **│ HIRING PAIN SIGNAL DETECTION RESULTS                                 │**

&#x20;   **├──────────────┬───────────────────────┬───────┬───────────────────── │**

&#x20;   **│ Company      │ Signal Type           │ Score │ Status                │**

&#x20;   **├──────────────┼───────────────────────┼───────┼───────────────────── │**

&#x20;   **│ Acme Corp    │ recruiter\_overload     │  87   │ 🔴 HIGH               │**

&#x20;   **...**

&#x20;   **"""**

&#x20;   **# Sort by score descending for display**

&#x20;   **sorted\_results = sorted(results, key=lambda x: x.get("signal\_score", 0), reverse=True)**



&#x20;   **# Column widths**

&#x20;   **COL\_COMPANY = 20**

&#x20;   **COL\_THEME = 25**

&#x20;   **COL\_SCORE = 7**

&#x20;   **COL\_STATUS = 15**



&#x20;   **divider = "─" \* (COL\_COMPANY + COL\_THEME + COL\_SCORE + COL\_STATUS + 13)**



&#x20;   **print("\\n" + "=" \* len(divider))**

&#x20;   **print("  HIRING PAIN / INTENT DETECTOR — RESULTS SUMMARY")**

&#x20;   **print("=" \* len(divider))**

&#x20;   **print(**

&#x20;       **f"  {'COMPANY':<{COL\_COMPANY}} "**

&#x20;       **f"{'SIGNAL TYPE':<{COL\_THEME}} "**

&#x20;       **f"{'SCORE':>{COL\_SCORE}} "**

&#x20;       **f"{'STATUS':<{COL\_STATUS}}"**

&#x20;   **)**

&#x20;   **print("  " + divider)**



&#x20;   **for r in sorted\_results:**

&#x20;       **score = r.get("signal\_score", 0)**

&#x20;       **company = r.get("company", "Unknown")\[:COL\_COMPANY]**

&#x20;       **theme = r.get("signal\_type", "unknown")\[:COL\_THEME]**



&#x20;       **# Status indicator**

&#x20;       **if score >= 75:**

&#x20;           **status = "HIGH SIGNAL"**

&#x20;       **elif score >= 50:**

&#x20;           **status = "MEDIUM"**

&#x20;       **elif score >= 25:**

&#x20;           **status = "LOW"**

&#x20;       **else:**

&#x20;           **status = "NOISE"**



&#x20;       **print(**

&#x20;           **f"  {company:<{COL\_COMPANY}} "**

&#x20;           **f"{theme:<{COL\_THEME}} "**

&#x20;           **f"{score:>{COL\_SCORE}} "**

&#x20;           **f"{status:<{COL\_STATUS}}"**

&#x20;       **)**



&#x20;   **print("  " + divider)**

&#x20;   **print(f"  Total records: {len(sorted\_results)}")**

&#x20;   **print("=" \* len(divider))**



**<!DOCTYPE html>**

**<html lang="en">**

**<head>**

&#x20; **<meta charset="UTF-8" />**

&#x20; **<meta name="viewport" content="width=device-width, initial-scale=1.0"/>**

&#x20; **<title>Hiring Pain Detector</title>**

&#x20; **<style>**

&#x20;   **/\* ── Reset \& Base ───────────────────────────────────────── \*/**

&#x20;   **\*, \*::before, \*::after { box-sizing: border-box; margin: 0; padding: 0; }**

&#x20;   **body {**

&#x20;     **font-family: 'Segoe UI', system-ui, sans-serif;**

&#x20;     **background: #0f1117;**

&#x20;     **color: #e2e8f0;**

&#x20;     **min-height: 100vh;**

&#x20;   **}**



&#x20;   **/\* ── Layout ─────────────────────────────────────────────── \*/**

&#x20;   **.wrapper    { max-width: 1200px; margin: 0 auto; padding: 0 24px 60px; }**



&#x20;   **/\* ── Header ─────────────────────────────────────────────── \*/**

&#x20;   **header {**

&#x20;     **background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);**

&#x20;     **border-bottom: 1px solid #1e293b;**

&#x20;     **padding: 24px 0;**

&#x20;     **margin-bottom: 36px;**

&#x20;   **}**

&#x20;   **header .inner { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 14px; }**

&#x20;   **.logo { font-size: 28px; }**

&#x20;   **.header-text h1 { font-size: 22px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px; }**

&#x20;   **.header-text p  { font-size: 13px; color: #64748b; margin-top: 2px; }**



&#x20;   **/\* ── Stat Cards ─────────────────────────────────────────── \*/**

&#x20;   **.stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 32px; }**

&#x20;   **.stat-card {**

&#x20;     **background: #1e293b;**

&#x20;     **border: 1px solid #334155;**

&#x20;     **border-radius: 12px;**

&#x20;     **padding: 18px 16px;**

&#x20;     **text-align: center;**

&#x20;   **}**

&#x20;   **.stat-card .num  { font-size: 32px; font-weight: 700; line-height: 1; }**

&#x20;   **.stat-card .lbl  { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: .6px; margin-top: 6px; }**

&#x20;   **.stat-card.total .num { color: #94a3b8; }**

&#x20;   **.stat-card.high  .num { color: #f87171; }**

&#x20;   **.stat-card.med   .num { color: #fbbf24; }**

&#x20;   **.stat-card.low   .num { color: #60a5fa; }**

&#x20;   **.stat-card.noise .num { color: #475569; }**



&#x20;   **/\* ── Two-col grid ───────────────────────────────────────── \*/**

&#x20;   **.grid { display: grid; grid-template-columns: 400px 1fr; gap: 28px; align-items: start; }**



&#x20;   **/\* ── Form Panel ─────────────────────────────────────────── \*/**

&#x20;   **.panel {**

&#x20;     **background: #1e293b;**

&#x20;     **border: 1px solid #334155;**

&#x20;     **border-radius: 14px;**

&#x20;     **padding: 24px;**

&#x20;     **position: sticky;**

&#x20;     **top: 24px;**

&#x20;   **}**

&#x20;   **.panel h2 { font-size: 15px; font-weight: 600; color: #f8fafc; margin-bottom: 18px; }**



&#x20;   **.field { margin-bottom: 14px; }**

&#x20;   **.field label { display: block; font-size: 12px; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .5px; }**

&#x20;   **.field input, .field textarea {**

&#x20;     **width: 100%;**

&#x20;     **background: #0f172a;**

&#x20;     **border: 1px solid #334155;**

&#x20;     **border-radius: 8px;**

&#x20;     **padding: 10px 12px;**

&#x20;     **color: #e2e8f0;**

&#x20;     **font-size: 14px;**

&#x20;     **font-family: inherit;**

&#x20;     **transition: border-color .2s;**

&#x20;     **outline: none;**

&#x20;   **}**

&#x20;   **.field input:focus, .field textarea:focus { border-color: #6366f1; }**

&#x20;   **.field textarea { resize: vertical; min-height: 160px; line-height: 1.55; }**



&#x20;   **.btn-analyze {**

&#x20;     **width: 100%;**

&#x20;     **padding: 12px;**

&#x20;     **background: #6366f1;**

&#x20;     **color: #fff;**

&#x20;     **border: none;**

&#x20;     **border-radius: 8px;**

&#x20;     **font-size: 14px;**

&#x20;     **font-weight: 600;**

&#x20;     **cursor: pointer;**

&#x20;     **transition: background .2s;**

&#x20;     **margin-top: 4px;**

&#x20;   **}**

&#x20;   **.btn-analyze:hover { background: #4f46e5; }**



&#x20;   **.divider { border: none; border-top: 1px solid #334155; margin: 20px 0; }**



&#x20;   **.btn-clear {**

&#x20;     **width: 100%;**

&#x20;     **padding: 9px;**

&#x20;     **background: transparent;**

&#x20;     **color: #64748b;**

&#x20;     **border: 1px solid #334155;**

&#x20;     **border-radius: 8px;**

&#x20;     **font-size: 13px;**

&#x20;     **cursor: pointer;**

&#x20;     **transition: all .2s;**

&#x20;   **}**

&#x20;   **.btn-clear:hover { color: #f87171; border-color: #f87171; }**



&#x20;   **.api-hint { font-size: 12px; color: #475569; margin-top: 16px; line-height: 1.6; }**

&#x20;   **.api-hint code { background: #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #818cf8; }**



&#x20;   **/\* ── Results Panel ──────────────────────────────────────── \*/**

&#x20;   **.results-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }**

&#x20;   **.results-header h2 { font-size: 15px; font-weight: 600; color: #f8fafc; }**



&#x20;   **.empty-state { text-align: center; padding: 60px 20px; color: #475569; }**

&#x20;   **.empty-state .icon { font-size: 48px; margin-bottom: 12px; }**

&#x20;   **.empty-state p { font-size: 14px; }**



&#x20;   **/\* ── Result Card ────────────────────────────────────────── \*/**

&#x20;   **.result-card {**

&#x20;     **background: #1e293b;**

&#x20;     **border: 1px solid #334155;**

&#x20;     **border-radius: 14px;**

&#x20;     **padding: 20px 22px;**

&#x20;     **margin-bottom: 14px;**

&#x20;     **transition: border-color .2s;**

&#x20;   **}**

&#x20;   **.result-card:hover { border-color: #475569; }**



&#x20;   **.card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }**

&#x20;   **.card-left { flex: 1; min-width: 0; }**

&#x20;   **.company-name { font-size: 16px; font-weight: 700; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }**

&#x20;   **.source-url   { font-size: 12px; color: #475569; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }**



&#x20;   **/\* Score badge \*/**

&#x20;   **.score-badge {**

&#x20;     **display: flex; flex-direction: column; align-items: center; justify-content: center;**

&#x20;     **width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0;**

&#x20;     **font-weight: 700; font-size: 20px; border: 3px solid;**

&#x20;   **}**

&#x20;   **.score-badge .score-label { font-size: 9px; text-transform: uppercase; letter-spacing: .5px; margin-top: 1px; }**

&#x20;   **.badge-high   { color: #f87171; border-color: #f87171; background: rgba(248,113,113,.08); }**

&#x20;   **.badge-medium { color: #fbbf24; border-color: #fbbf24; background: rgba(251,191,36,.08); }**

&#x20;   **.badge-low    { color: #60a5fa; border-color: #60a5fa; background: rgba(96,165,250,.08); }**

&#x20;   **.badge-noise  { color: #475569; border-color: #334155; background: rgba(71,85,105,.08); }**



&#x20;   **/\* Chips row \*/**

&#x20;   **.chips { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 12px; }**

&#x20;   **.chip {**

&#x20;     **display: inline-block; padding: 3px 10px; border-radius: 20px;**

&#x20;     **font-size: 11px; font-weight: 500; border: 1px solid;**

&#x20;   **}**

&#x20;   **.chip-theme    { color: #818cf8; border-color: #312e81; background: rgba(99,102,241,.12); }**

&#x20;   **.chip-keyword  { color: #34d399; border-color: #064e3b; background: rgba(52,211,153,.08); }**



&#x20;   **/\* Reason text \*/**

&#x20;   **.reason-text { font-size: 13px; color: #94a3b8; line-height: 1.6; }**



&#x20;   **/\* Breakdown accordion \*/**

&#x20;   **.breakdown-toggle {**

&#x20;     **background: none; border: none; color: #475569; font-size: 12px;**

&#x20;     **cursor: pointer; padding: 0; margin-top: 10px; display: flex; align-items: center; gap: 5px;**

&#x20;   **}**

&#x20;   **.breakdown-toggle:hover { color: #94a3b8; }**

&#x20;   **.breakdown-body {**

&#x20;     **display: none;**

&#x20;     **margin-top: 12px;**

&#x20;     **background: #0f172a;**

&#x20;     **border-radius: 8px;**

&#x20;     **padding: 14px 16px;**

&#x20;     **font-size: 12px;**

&#x20;   **}**

&#x20;   **.breakdown-body.open { display: block; }**

&#x20;   **.bd-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #1e293b; }**

&#x20;   **.bd-row:last-child { border: none; }**

&#x20;   **.bd-label { color: #64748b; }**

&#x20;   **.bd-val   { color: #e2e8f0; font-weight: 600; font-variant-numeric: tabular-nums; }**

&#x20;   **.bd-val.neg { color: #f87171; }**

&#x20;   **.bd-val.pos { color: #34d399; }**



&#x20;   **/\* ── Responsive ─────────────────────────────────────────── \*/**

&#x20;   **@media (max-width: 860px) {**

&#x20;     **.stats { grid-template-columns: repeat(3, 1fr); }**

&#x20;     **.grid  { grid-template-columns: 1fr; }**

&#x20;     **.panel { position: static; }**

&#x20;   **}**

&#x20;   **@media (max-width: 500px) {**

&#x20;     **.stats { grid-template-columns: 1fr 1fr; }**

&#x20;   **}**

&#x20; **</style>**

**</head>**

**<body>**



**<header>**

&#x20; **<div class="inner">**

&#x20;   **<div class="logo">🎯</div>**

&#x20;   **<div class="header-text">**

&#x20;     **<h1>Hiring Pain / Intent Detector</h1>**

&#x20;     **<p>Local NLP · No cloud APIs · Heuristic scoring · Python 3</p>**

&#x20;   **</div>**

&#x20; **</div>**

**</header>**



**<div class="wrapper">**



&#x20; **<!-- ── Stat Cards ── -->**

&#x20; **<div class="stats">**

&#x20;   **<div class="stat-card total"> <div class="num">{{ stats.total }}</div>  <div class="lbl">Total Analyzed</div></div>**

&#x20;   **<div class="stat-card high">  <div class="num">{{ stats.high }}</div>   <div class="lbl">High Signal ≥75</div></div>**

&#x20;   **<div class="stat-card med">   <div class="num">{{ stats.medium }}</div> <div class="lbl">Medium 50–74</div></div>**

&#x20;   **<div class="stat-card low">   <div class="num">{{ stats.low }}</div>    <div class="lbl">Low 25–49</div></div>**

&#x20;   **<div class="stat-card noise"> <div class="num">{{ stats.noise }}</div>  <div class="lbl">Noise \&lt;25</div></div>**

&#x20; **</div>**



&#x20; **<div class="grid">**



&#x20;   **<!-- ── LEFT: Input Form ── -->**

&#x20;   **<div class="panel">**

&#x20;     **<h2>Analyze New Text</h2>**

&#x20;     **<form action="/analyze" method="POST">**

&#x20;       **<div class="field">**

&#x20;         **<label>Company Name</label>**

&#x20;         **<input type="text" name="company" placeholder="e.g. Acme Corp" />**

&#x20;       **</div>**

&#x20;       **<div class="field">**

&#x20;         **<label>Source URL (optional)</label>**

&#x20;         **<input type="text" name="source\_url" placeholder="https://linkedin.com/posts/..." />**

&#x20;       **</div>**

&#x20;       **<div class="field">**

&#x20;         **<label>Post / Transcript Text</label>**

&#x20;         **<textarea name="text" placeholder="Paste a LinkedIn post, blog excerpt, or podcast transcript here..."></textarea>**

&#x20;       **</div>**

&#x20;       **<button type="submit" class="btn-analyze">⚡ Detect Signal</button>**

&#x20;     **</form>**



&#x20;     **<hr class="divider"/>**



&#x20;     **<form action="/clear" method="POST">**

&#x20;       **<button type="submit" class="btn-clear">🗑 Clear all results</button>**

&#x20;     **</form>**



&#x20;     **<div class="api-hint">**

&#x20;       **<strong style="color:#64748b">JSON API also available:</strong><br/>**

&#x20;       **<code>POST /api/analyze</code> → send <code>{ "text": "...", "company": "..." }</code><br/>**

&#x20;       **<code>GET \&nbsp;/api/results</code> → returns all records as JSON**

&#x20;     **</div>**

&#x20;   **</div>**



&#x20;   **<!-- ── RIGHT: Results ── -->**

&#x20;   **<div>**

&#x20;     **<div class="results-header">**

&#x20;       **<h2>Results <span style="color:#475569;font-weight:400">({{ results|length }})</span></h2>**

&#x20;     **</div>**



&#x20;     **{% if not results %}**

&#x20;     **<div class="empty-state">**

&#x20;       **<div class="icon">📭</div>**

&#x20;       **<p>No results yet. Paste some text in the form to get started.</p>**

&#x20;     **</div>**

&#x20;     **{% endif %}**



&#x20;     **{% for r in results %}**

&#x20;       **{% set score = r.signal\_score %}**

&#x20;       **{% if score >= 75 %}**

&#x20;         **{% set badge\_class = "badge-high" %}**

&#x20;         **{% set status = "HIGH" %}**

&#x20;       **{% elif score >= 50 %}**

&#x20;         **{% set badge\_class = "badge-medium" %}**

&#x20;         **{% set status = "MED" %}**

&#x20;       **{% elif score >= 25 %}**

&#x20;         **{% set badge\_class = "badge-low" %}**

&#x20;         **{% set status = "LOW" %}**

&#x20;       **{% else %}**

&#x20;         **{% set badge\_class = "badge-noise" %}**

&#x20;         **{% set status = "NOISE" %}**

&#x20;       **{% endif %}**



&#x20;       **<div class="result-card">**

&#x20;         **<div class="card-top">**

&#x20;           **<div class="card-left">**

&#x20;             **<div class="company-name">{{ r.company }}</div>**

&#x20;             **{% if r.source\_url %}**

&#x20;             **<div class="source-url">{{ r.source\_url }}</div>**

&#x20;             **{% endif %}**

&#x20;           **</div>**

&#x20;           **<div class="score-badge {{ badge\_class }}">**

&#x20;             **{{ score }}**

&#x20;             **<span class="score-label">{{ status }}</span>**

&#x20;           **</div>**

&#x20;         **</div>**



&#x20;         **<div class="chips">**

&#x20;           **<span class="chip chip-theme">{{ r.signal\_type }}</span>**

&#x20;           **{% for kw in r.matched\_keywords\[:6] %}**

&#x20;           **<span class="chip chip-keyword">{{ kw }}</span>**

&#x20;           **{% endfor %}**

&#x20;         **</div>**



&#x20;         **<div class="reason-text">{{ r.reason }}</div>**



&#x20;         **<!-- Score Breakdown Accordion -->**

&#x20;         **{% if r.breakdown %}**

&#x20;         **<button class="breakdown-toggle" onclick="toggleBreakdown(this)">**

&#x20;           **▶ Score breakdown**

&#x20;         **</button>**

&#x20;         **<div class="breakdown-body">**

&#x20;           **<div class="bd-row"><span class="bd-label">Job Title</span>     <span class="bd-val pos">+{{ r.breakdown.title\_score }}</span></div>**

&#x20;           **<div class="bd-row"><span class="bd-label">Pain Themes</span>   <span class="bd-val pos">+{{ r.breakdown.theme\_score }}</span></div>**

&#x20;           **<div class="bd-row"><span class="bd-label">Ownership Lang</span><span class="bd-val pos">+{{ r.breakdown.ownership\_score }}</span></div>**

&#x20;           **<div class="bd-row"><span class="bd-label">Urgency Bonus</span> <span class="bd-val pos">+{{ r.breakdown.urgency\_score }}</span></div>**

&#x20;           **<div class="bd-row"><span class="bd-label">Noise Penalty</span> <span class="bd-val neg">{{ r.breakdown.noise\_penalty }}</span></div>**

&#x20;           **<div class="bd-row"><span class="bd-label">Raw Score</span>     <span class="bd-val">{{ r.breakdown.raw\_score }}</span></div>**

&#x20;           **<div class="bd-row"><span class="bd-label">Proximity ×</span>   <span class="bd-val">{{ "%.2f"|format(r.breakdown.proximity\_multiplier) }}</span></div>**

&#x20;           **<div class="bd-row" style="border-top:1px solid #334155;margin-top:4px;padding-top:8px">**

&#x20;             **<span class="bd-label" style="color:#e2e8f0;font-weight:600">Final Score</span>**

&#x20;             **<span class="bd-val" style="font-size:15px">{{ r.breakdown.final\_score }}</span>**

&#x20;           **</div>**

&#x20;           **<div style="margin-top:8px;color:#475569;font-size:11px;line-height:1.5">**

&#x20;             **{{ r.breakdown.proximity\_detail }}**

&#x20;           **</div>**

&#x20;         **</div>**

&#x20;         **{% endif %}**



&#x20;       **</div>**

&#x20;     **{% endfor %}**

&#x20;   **</div>**



&#x20; **</div><!-- /grid -->**

**</div><!-- /wrapper -->**



**<script>**

&#x20; **function toggleBreakdown(btn) {**

&#x20;   **const body = btn.nextElementSibling;**

&#x20;   **body.classList.toggle('open');**

&#x20;   **btn.textContent = body.classList.contains('open')**

&#x20;     **? '▼ Score breakdown'**

&#x20;     **: '▶ Score breakdown';**

&#x20; **}**

**</script>**



**</body>**

**</html>** 


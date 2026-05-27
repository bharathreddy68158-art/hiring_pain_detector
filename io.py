# =============================================================================
# utils/io.py
# =============================================================================
# PURPOSE: All file I/O operations — reading sample data and writing results.
#
# ARCHITECTURAL DECISION: I/O is isolated from all business logic.
#   - detector.py and scorer.py never touch the filesystem.
#   - This module never touches scoring or detection logic.
#
# This makes testing trivial: tests can call detector/scorer with in-memory
# strings without needing files on disk.
#
# SUPPORTED INPUT: A JSON file with an array of post objects. See sample_data.json
# for the expected schema.
#
# SUPPORTED OUTPUT: A JSON file with an array of result objects matching the
# required output schema defined in the project brief.
# =============================================================================

import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# INPUT FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def load_posts(filepath: str) -> List[Dict[str, Any]]:
    """
    Load the input JSON file containing posts to analyze.

    Expected file schema (array of objects):
    [
        {
            "company": "Acme Corp",
            "source_url": "https://linkedin.com/...",
            "text": "The raw post or transcript text to analyze..."
        },
        ...
    ]

    Args:
        filepath: Path to the JSON input file

    Returns:
        List of post dicts. Each must have at least 'text'.
        'company' and 'source_url' default to "Unknown" / "" if missing.

    Raises:
        SystemExit on file-not-found or JSON parse error, with a user-friendly
        message. We exit here rather than raise so main.py stays clean.
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] Input file not found: {filepath}")
        print(f"        Expected a JSON file at this path. Check the path and try again.")
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Could not parse JSON in {filepath}: {e}")
        sys.exit(1)

    # Validate: must be a list
    if not isinstance(data, list):
        print(f"[ERROR] {filepath} must contain a JSON array at the top level.")
        sys.exit(1)

    # Validate: each item must have 'text'
    valid_posts = []
    for i, post in enumerate(data):
        if "text" not in post or not post["text"].strip():
            print(f"[WARNING] Post at index {i} is missing 'text' field — skipping.")
            continue
        # Apply defaults for optional fields
        post.setdefault("company", "Unknown")
        post.setdefault("source_url", "")
        valid_posts.append(post)

    print(f"[INFO] Loaded {len(valid_posts)} valid post(s) from {filepath}")
    return valid_posts


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_output_record(
    post: Dict[str, Any],
    signals: Dict[str, Any],
    score: int,
    reason: str,
) -> Dict[str, Any]:
    """
    Assemble the final output record matching the required JSON output schema.

    Required output schema:
    {
        "company":          "Example Corp",
        "signal_type":      "recruiter_overload",
        "source_url":       "https://...",
        "matched_keywords": ["drowning in resumes", "burnout"],
        "signal_score":     82,
        "detected_at":      "2024-01-15T10:30:00Z",
        "reason":           "Plain language explanation..."
    }

    DESIGN NOTE: We use UTC ISO 8601 with timezone for 'detected_at'.
    This ensures the timestamp is unambiguous regardless of where the system runs.

    Args:
        post:     The original post dict (provides company, source_url)
        signals:  The extracted signals dict from SignalDetector
        score:    The computed 0-100 integer score from SignalScorer
        reason:   The plain-language reason string from SignalScorer

    Returns:
        A dict matching the required output schema exactly.
    """
    return {
        "company": post.get("company", "Unknown"),
        "signal_type": signals.get("primary_theme", "unknown"),
        "source_url": post.get("source_url", ""),
        "matched_keywords": signals.get("matched_keywords", []),
        "signal_score": score,
        "detected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "reason": reason,
    }


def save_results(results: List[Dict[str, Any]], output_filepath: str) -> None:
    """
    Write the list of result records to a JSON file.

    Results are sorted by signal_score descending so the highest-priority
    leads appear first in the output file.

    Args:
        results:          List of output record dicts
        output_filepath:  Path to write the JSON output

    Raises:
        SystemExit on write failure (permissions, disk full, etc.)
    """
    # Sort: highest score first (most actionable leads at the top)
    sorted_results = sorted(results, key=lambda x: x.get("signal_score", 0), reverse=True)

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(sorted_results, f, indent=2, ensure_ascii=False)

        print(f"\n[OUTPUT] Results written to: {output_filepath}")
        print(f"         {len(sorted_results)} record(s) saved, sorted by signal_score desc.")

    except OSError as e:
        print(f"[ERROR] Could not write output file {output_filepath}: {e}")
        sys.exit(1)


def print_summary_table(results: List[Dict[str, Any]]) -> None:
    """
    Print a formatted summary table to stdout for quick CLI review.

    This is the "quick glance" output. The full details are in the JSON file.

    Example output:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ HIRING PAIN SIGNAL DETECTION RESULTS                                 │
    ├──────────────┬───────────────────────┬───────┬───────────────────── │
    │ Company      │ Signal Type           │ Score │ Status                │
    ├──────────────┼───────────────────────┼───────┼───────────────────── │
    │ Acme Corp    │ recruiter_overload     │  87   │ 🔴 HIGH               │
    ...
    """
    # Sort by score descending for display
    sorted_results = sorted(results, key=lambda x: x.get("signal_score", 0), reverse=True)

    # Column widths
    COL_COMPANY = 20
    COL_THEME = 25
    COL_SCORE = 7
    COL_STATUS = 15

    divider = "─" * (COL_COMPANY + COL_THEME + COL_SCORE + COL_STATUS + 13)

    print("\n" + "=" * len(divider))
    print("  HIRING PAIN / INTENT DETECTOR — RESULTS SUMMARY")
    print("=" * len(divider))
    print(
        f"  {'COMPANY':<{COL_COMPANY}} "
        f"{'SIGNAL TYPE':<{COL_THEME}} "
        f"{'SCORE':>{COL_SCORE}} "
        f"{'STATUS':<{COL_STATUS}}"
    )
    print("  " + divider)

    for r in sorted_results:
        score = r.get("signal_score", 0)
        company = r.get("company", "Unknown")[:COL_COMPANY]
        theme = r.get("signal_type", "unknown")[:COL_THEME]

        # Status indicator
        if score >= 75:
            status = "HIGH SIGNAL"
        elif score >= 50:
            status = "MEDIUM"
        elif score >= 25:
            status = "LOW"
        else:
            status = "NOISE"

        print(
            f"  {company:<{COL_COMPANY}} "
            f"{theme:<{COL_THEME}} "
            f"{score:>{COL_SCORE}} "
            f"{status:<{COL_STATUS}}"
        )

    print("  " + divider)
    print(f"  Total records: {len(sorted_results)}")
    print("=" * len(divider))
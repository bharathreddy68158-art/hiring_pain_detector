# =============================================================================
# app.py  —  FastAPI web server
# =============================================================================
# WHY FASTAPI OVER FLASK:
#   1. Async by default (uvicorn ASGI) — handles concurrent requests better
#   2. Auto-generates /docs (Swagger UI) and /redoc with zero extra code
#   3. Pydantic request/response models give you free input validation + clear
#      API contracts — no manual request.get_json() or error handling needed
#   4. Type hints are first-class; your IDE catches bugs before runtime
#   5. Industry standard for modern Python APIs (replaces Flask in most new projects)
#
# USAGE:
#   python app.py
#   → http://localhost:8000        (dashboard UI)
#   → http://localhost:8000/docs   (auto Swagger UI — interactive API explorer)
#   → http://localhost:8000/redoc  (ReDoc alternative docs)
# =============================================================================

import sys, os, json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ── project root on path ────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from signals import SignalDetector, SignalScorer
from utils.io import build_output_record

# ── in-memory results store (lives for the duration of the server process) ──
RESULTS_STORE: List[dict] = []

# ── Jinja2 templates (reads from ./templates/) ──────────────────────────────
templates = Jinja2Templates(directory=os.path.join(PROJECT_ROOT, "templates"))


# =============================================================================
# PYDANTIC MODELS
# These define the exact shape of every request and response body.
# FastAPI uses them to: validate inputs, generate Swagger docs, and serialize
# outputs — all automatically. No manual validation code needed.
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Request body for POST /api/analyze"""
    text:       str
    company:    Optional[str] = "Unknown"
    source_url: Optional[str] = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "company":    "Acme Corp",
                "source_url": "https://linkedin.com/posts/example",
                "text":       "As CHRO, my team is overwhelmed. We're drowning in resumes and our time-to-hire has hit 60 days. We urgently need a solution."
            }
        }
    }


class SignalResult(BaseModel):
    """Response body — matches the required output JSON schema exactly."""
    company:          str
    signal_type:      str
    source_url:       str
    matched_keywords: List[str]
    signal_score:     int
    detected_at:      str
    reason:           str


# =============================================================================
# LIFESPAN — runs once on startup to pre-load sample data
# (FastAPI's modern replacement for @app.on_event("startup"))
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load sample_data.json so the dashboard isn't empty on first open."""
    _preload_sample_data()
    yield   # server runs here
    # (shutdown logic would go after yield if needed)


# =============================================================================
# APP INSTANCE
# =============================================================================

app = FastAPI(
    title="Hiring Pain / Intent Detector",
    description=(
        "Detects expressions of hiring pain from HR leaders in unstructured text "
        "(LinkedIn posts, HR blogs, podcast transcripts). "
        "Uses local NLP heuristics — **no cloud APIs, no LLMs**.\n\n"
        "Score 75–100 = High Signal 🔴 | 50–74 = Medium 🟡 | 25–49 = Low 🔵 | 0–24 = Noise ⚪"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# ROUTES — UI
# =============================================================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """
    Main dashboard. Renders the HTML template with all current results.
    `include_in_schema=False` hides this HTML route from the Swagger docs
    (only JSON endpoints belong there).
    """
    stats = {
        "total":  len(RESULTS_STORE),
        "high":   sum(1 for r in RESULTS_STORE if r["signal_score"] >= 75),
        "medium": sum(1 for r in RESULTS_STORE if 50 <= r["signal_score"] < 75),
        "low":    sum(1 for r in RESULTS_STORE if 25 <= r["signal_score"] < 50),
        "noise":  sum(1 for r in RESULTS_STORE if r["signal_score"] < 25),
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"results": RESULTS_STORE, "stats": stats}
    )


@app.post("/analyze", response_class=RedirectResponse, include_in_schema=False)
async def analyze_form(
    text:       str = Form(...),
    company:    str = Form("Unknown"),
    source_url: str = Form(""),
):
    """
    Handles the HTML form submission from the dashboard.
    Uses FastAPI's Form() — requires python-multipart (installed).
    After analysis, redirects back to / so the user sees updated results.
    """
    if text.strip():
        record = _run_analysis(text.strip(), company.strip(), source_url.strip())
        RESULTS_STORE.append(record)
        RESULTS_STORE.sort(key=lambda x: x["signal_score"], reverse=True)
    # 303 See Other is the correct redirect code after a POST (prevents re-submit on refresh)
    return RedirectResponse(url="/", status_code=303)


@app.post("/clear", response_class=RedirectResponse, include_in_schema=False)
async def clear_results():
    """Clear all in-memory results and redirect to dashboard."""
    RESULTS_STORE.clear()
    return RedirectResponse(url="/", status_code=303)


# =============================================================================
# ROUTES — JSON API
# These are the endpoints that appear in /docs (Swagger UI).
# Pydantic models handle validation and serialization automatically.
# =============================================================================

@app.post(
    "/api/analyze",
    response_model=SignalResult,
    summary="Analyze a single text for hiring pain signals",
    tags=["Detection"],
)
async def api_analyze(payload: AnalyzeRequest):
    """
    Submit text for hiring pain / intent detection.

    Returns a scored result record with:
    - **signal_score** (0–100): composite heuristic score
    - **signal_type**: dominant pain theme detected
    - **matched_keywords**: the specific phrases that triggered the score
    - **reason**: plain-English explanation of why this was surfaced
    """
    record = _run_analysis(payload.text, payload.company, payload.source_url)
    RESULTS_STORE.append(record)
    RESULTS_STORE.sort(key=lambda x: x["signal_score"], reverse=True)
    # Return only the SignalResult fields (strip internal breakdown dict)
    return {k: v for k, v in record.items() if k != "breakdown"}


@app.get(
    "/api/results",
    response_model=List[SignalResult],
    summary="Get all analyzed results (sorted by score)",
    tags=["Detection"],
)
async def api_results():
    """
    Returns all results stored in the current session, sorted by
    **signal_score** descending (highest priority leads first).
    """
    return [{k: v for k, v in r.items() if k != "breakdown"} for r in RESULTS_STORE]


@app.delete(
    "/api/results",
    summary="Clear all results",
    tags=["Detection"],
)
async def api_clear():
    """Clear all stored results. Useful for resetting between test runs."""
    RESULTS_STORE.clear()
    return {"message": "All results cleared.", "count": 0}


@app.get(
    "/api/health",
    summary="Health check",
    tags=["Meta"],
)
async def health():
    """Simple health check endpoint. Returns server status and result count."""
    return {
        "status":        "ok",
        "results_count": len(RESULTS_STORE),
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# HELPERS
# =============================================================================

def _run_analysis(text: str, company: str, source_url: str) -> dict:
    """
    Core pipeline: detect → score → reason → build record.
    Shared by both the form route and the API route.
    """
    detector     = SignalDetector()
    scorer       = SignalScorer()
    post         = {"text": text, "company": company, "source_url": source_url}
    signals      = detector.extract(text=text, company=company, source_url=source_url)
    score_result = scorer.calculate_score(signals=signals, raw_text=text)
    reason       = scorer.generate_reason(signals=signals, score=score_result["score"])
    record       = build_output_record(post=post, signals=signals,
                                       score=score_result["score"], reason=reason)
    record["breakdown"] = score_result["breakdown"]  # kept for UI accordion only
    return record


def _preload_sample_data():
    """Load sample_data.json into RESULTS_STORE on startup."""
    sample_path = os.path.join(PROJECT_ROOT, "sample_data.json")
    if not os.path.exists(sample_path):
        return
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            posts = json.load(f)
        for post in posts:
            if post.get("text", "").strip():
                RESULTS_STORE.append(
                    _run_analysis(post["text"], post.get("company", "Unknown"), post.get("source_url", ""))
                )
        RESULTS_STORE.sort(key=lambda x: x["signal_score"], reverse=True)
        print(f"[BOOT] Pre-loaded {len(RESULTS_STORE)} sample records.")
    except Exception as e:
        print(f"[BOOT] Could not pre-load sample data: {e}")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n  Hiring Pain Detector — FastAPI")
    print("  Dashboard : http://localhost:8000")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc     : http://localhost:8000/redoc\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
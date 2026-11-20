"""Host-app demo: build your own tool on the Open Sustainability Analyst library.

Shows a custom procurement-style UI that imports ``report_analyst.core.library``,
screens one PDF with a topic question set, and turns grounded answers into a brief.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from report_analyst.core.library import (
    GroundedAnswer,
    analyze_report,
    build_topic_brief,
)

ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = ROOT / "questions" / "water_risk_questions.yaml"
REAL_BRIEF_PATH = ROOT / "data" / "real_brief.json"
TOPIC = "Supplier water-risk brief"

# Optional UI mock only. Default view uses REAL_BRIEF from a live analyze_report run.
MOCK_BRIEF: Dict[str, Any] = {
    "topic": TOPIC,
    "report_name": "Acme Materials, Sustainability Report 2024 (mock)",
    "question_count": 3,
    "answered_count": 3,
    "evidence_backed_count": 2,
    "source": "mock_template",
    "findings": [
        {
            "question_id": "water_1",
            "question": "Does the company disclose quantitative water withdrawal or consumption targets?",
            "answer": (
                "Yes. Acme commits to a 25% reduction in freshwater withdrawal intensity "
                "(m³ / tonne product) by 2030 vs a 2019 baseline, covering manufacturing sites."
            ),
            "confidence": 0.86,
            "evidence": [
                "p.41: “25% reduction in freshwater withdrawal intensity by 2030 (2019 baseline).”",
                "p.42: Target scope covers all manufacturing sites in water-stressed basins.",
            ],
            "gaps": ["No absolute withdrawal target published alongside intensity."],
            "sources": ["p.41", "p.42"],
        },
        {
            "question_id": "water_2",
            "question": "Which sites or basins does the company identify as water-stressed or high-risk?",
            "answer": (
                "Three basins are flagged high risk via WRI Aqueduct: Guadiana (ES), "
                "Sabarmati (IN), and Lower Colorado (US). Two plants sit in those basins."
            ),
            "confidence": 0.81,
            "evidence": [
                "p.44 table: Guadiana, Sabarmati, Lower Colorado listed as “high / extremely high”.",
            ],
            "gaps": ["Facility-level volumes for each basin are not disclosed."],
            "sources": ["p.44"],
        },
        {
            "question_id": "water_3",
            "question": "What evidence is given for water recycling, reuse, or efficiency measures?",
            "answer": (
                "Closed-loop cooling at two European plants cut municipal intake by ~0.4 Mm³ "
                "in 2024. A Sabarmati pilot reuses process water; full rollout is planned for 2026."
            ),
            "confidence": 0.74,
            "evidence": [
                "p.46: “Closed-loop cooling reduced municipal intake by 0.4 million m³ in 2024.”",
            ],
            "gaps": ["Recycling rate (%) for the group is not stated."],
            "sources": ["p.46"],
        },
    ],
}


def _load_real_brief() -> Dict[str, Any]:
    """Load the shipped Siemens brief from a real analyze_report run."""
    return json.loads(REAL_BRIEF_PATH.read_text(encoding="utf-8"))


REAL_BRIEF = _load_real_brief()

app = FastAPI(
    title="Grounded Topic Brief Demo",
    description="Example host app that embeds report-analyst as a library.",
)

_LAST_BRIEF: Optional[Dict[str, Any]] = REAL_BRIEF


def _answers_to_jsonable(answers: List[GroundedAnswer]) -> List[Dict[str, Any]]:
    return [item.to_dict() for item in answers]


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Serve the custom upload + brief UI."""
    return INDEX_HTML


@app.get("/real")
async def real() -> JSONResponse:
    """Siemens FY2023 water-risk brief from a real library analyze_report run."""
    return JSONResponse(REAL_BRIEF)


@app.get("/sample")
async def sample() -> JSONResponse:
    """Synthetic mock template only (not real report data)."""
    return JSONResponse(MOCK_BRIEF)


@app.post("/analyze")
async def analyze(
    report: UploadFile = File(...),
    model: str = Form("gpt-4o-mini"),
) -> JSONResponse:
    """Run the water-risk question set on one uploaded PDF via the library API."""
    global _LAST_BRIEF
    if not report.filename or not report.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF sustainability report.")

    raw = await report.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
        handle.write(raw)
        tmp_path = Path(handle.name)

    try:
        answers = await analyze_report(
            tmp_path,
            QUESTIONS_PATH,
            question_set_id="water_risk",
            model=model or None,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    brief = build_topic_brief(answers, topic=TOPIC)
    brief["report_name"] = report.filename
    _LAST_BRIEF = brief
    return JSONResponse(
        {
            "topic": TOPIC,
            "report_name": report.filename,
            "answers": _answers_to_jsonable(answers),
            "brief": brief,
        }
    )


@app.get("/brief")
async def brief() -> JSONResponse:
    """Return the last grounded brief for downstream product use."""
    if _LAST_BRIEF is None:
        raise HTTPException(status_code=404, detail="Analyze a report first.")
    return JSONResponse(_LAST_BRIEF)


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Supplier water risk brief</title>
  <style>
    :root {
      --ink: #14221c; --muted: #4a5c52; --paper: #f4f0e7; --panel: #fffdf8;
      --line: #d5cdc0; --accent: #0f6b4c; --accent-soft: #d8eee4;
      --warn: #8a5a12; --warn-soft: #f3e6c8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; color: var(--ink);
      background: radial-gradient(circle at 12% 0%, #e4f1ea 0%, transparent 40%),
        linear-gradient(180deg, #efe9dc 0%, var(--paper) 45%, #e7e1d4 100%);
      min-height: 100vh;
    }
    main { max-width: 760px; margin: 0 auto; padding: 1.75rem 1.1rem 4rem; }
    .eyebrow {
      text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem;
      color: var(--accent); font-weight: 700; margin: 0 0 0.4rem;
    }
    h1 {
      font-family: "Fraunces", "Palatino Linotype", serif;
      font-size: clamp(1.7rem, 4vw, 2.35rem); line-height: 1.15; margin: 0 0 0.5rem;
    }
    .lede { color: var(--muted); font-size: 1.02rem; line-height: 1.5; margin: 0 0 1.25rem; max-width: 34rem; }
    .upload {
      display: flex; flex-wrap: wrap; gap: 0.65rem; align-items: center;
      background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
      padding: 0.85rem 1rem; margin-bottom: 1.25rem;
    }
    .upload label.file { flex: 1 1 220px; font-weight: 600; font-size: 0.92rem; }
    .upload input[type="file"] { width: 100%; margin-top: 0.25rem; }
    details.advanced { flex: 1 1 100%; color: var(--muted); font-size: 0.85rem; }
    details.advanced input {
      width: min(240px, 100%); margin-top: 0.35rem; padding: 0.45rem 0.6rem;
      border: 1px solid var(--line); border-radius: 8px; background: #fff;
    }
    button {
      appearance: none; border: 0; border-radius: 999px; background: var(--accent);
      color: #fff; font-weight: 700; padding: 0.7rem 1.15rem; cursor: pointer;
    }
    button.ghost { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
    button:disabled { opacity: 0.55; cursor: wait; }
    .status { width: 100%; color: var(--muted); font-size: 0.9rem; min-height: 1.2rem; margin: 0; }
    .brief {
      background: var(--panel); border: 1px solid var(--line); border-radius: 16px;
      padding: 1.35rem 1.25rem 1.5rem; box-shadow: 0 10px 30px rgba(20, 34, 28, 0.05);
    }
    .brief-head h2 {
      font-family: "Fraunces", "Palatino Linotype", serif;
      font-size: 1.45rem; margin: 0 0 0.25rem; line-height: 1.2;
    }
    .report-name { color: var(--muted); margin: 0; font-size: 0.95rem; }
    .stats { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 1rem 0 0.25rem; }
    .chip {
      display: inline-block; background: var(--accent-soft); color: var(--accent);
      border-radius: 999px; padding: 0.2rem 0.65rem; font-size: 0.75rem; font-weight: 700;
    }
    .chip.warn { background: var(--warn-soft); color: var(--warn); }
    .chip.sample { background: #e8eef8; color: #2a4a7a; }
    .finding { border-top: 1px solid var(--line); padding: 1.1rem 0 0.2rem; margin-top: 1rem; }
    .finding h3 { margin: 0 0 0.45rem; font-size: 1rem; line-height: 1.35; }
    .finding .answer { margin: 0 0 0.75rem; line-height: 1.5; font-size: 1.02rem; }
    .block-label {
      font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
      font-weight: 700; color: var(--muted); margin: 0 0 0.35rem;
    }
    .quote {
      margin: 0 0 0.45rem; padding: 0.65rem 0.8rem; border-left: 3px solid var(--accent);
      background: #f4faf7; border-radius: 0 8px 8px 0; color: var(--muted);
      font-size: 0.92rem; line-height: 1.45;
    }
    .gap {
      margin: 0 0 0.35rem; padding: 0.55rem 0.75rem; background: var(--warn-soft);
      border-radius: 8px; color: var(--warn); font-size: 0.9rem;
    }
    .raw { margin-top: 1.25rem; }
    .raw pre {
      margin: 0.5rem 0 0; white-space: pre-wrap; word-break: break-word;
      font-size: 0.8rem; line-height: 1.4; background: #f7f3ea; border-radius: 8px;
      padding: 0.85rem; border: 1px solid var(--line); max-height: 220px; overflow: auto;
    }
    a { color: var(--accent); }
  </style>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Sans:wght@400;600;700&display=swap" rel="stylesheet" />
</head>
<body>
  <main>
    <p class="eyebrow">Open Sustainability Analyst · library</p>
    <h1>Supplier water risk brief</h1>
    <p class="lede">Build your own tool on OSA: your UI, grounded answers from the report.</p>
    <form id="form" class="upload">
      <label class="file" for="report">
        Supplier report (PDF)
        <input id="report" name="report" type="file" accept="application/pdf" required />
      </label>
      <button id="run" type="submit">Generate brief</button>
      <button id="realBtn" class="ghost" type="button">Siemens (real)</button>
      <button id="mockBtn" class="ghost" type="button">Mock template</button>
      <details class="advanced">
        <summary>Advanced</summary>
        <label for="model">Model</label><br />
        <input id="model" name="model" type="text" value="gpt-4o-mini" />
      </details>
      <p class="status" id="status">Real Siemens FY2023 brief below. Upload a PDF for a new live run.</p>
    </form>
    <article class="brief" id="brief" aria-live="polite"></article>
  </main>
  <script>
    const form = document.getElementById("form");
    const statusEl = document.getElementById("status");
    const briefEl = document.getElementById("brief");
    const runBtn = document.getElementById("run");
    const realBtn = document.getElementById("realBtn");
    const mockBtn = document.getElementById("mockBtn");
    function escapeHtml(value) {
      return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;").replaceAll('"', "&quot;");
    }
    function asText(item) {
      if (item == null) return "";
      if (typeof item === "string") return item;
      if (typeof item === "object" && item.text) return String(item.text);
      return JSON.stringify(item);
    }
    function renderBrief(brief, { mode = "real" } = {}) {
      const findings = brief.findings || [];
      const gapsTotal = findings.reduce((n, f) => n + ((f.gaps || []).length), 0);
      const modeChip = mode === "mock"
        ? `<span class="chip sample">Mock template</span>`
        : mode === "upload"
          ? `<span class="chip">Live upload</span>`
          : `<span class="chip">Real analysis</span>`;
      const chips = [
        modeChip,
        `<span class="chip">${brief.answered_count || 0} / ${brief.question_count || findings.length} answered</span>`,
        `<span class="chip">${brief.evidence_backed_count || 0} with evidence</span>`,
        gapsTotal ? `<span class="chip warn">${gapsTotal} gaps</span>` : "",
      ].join("");
      const findingsHtml = findings.map((f, i) => {
        const evidence = (f.evidence || []).map((e) => `<p class="quote">${escapeHtml(asText(e))}</p>`).join("");
        const gaps = (f.gaps || []).map((g) => `<p class="gap">${escapeHtml(asText(g))}</p>`).join("");
        return `<section class="finding">
            <h3>${i + 1}. ${escapeHtml(f.question || f.question_id)}</h3>
            <p class="answer">${escapeHtml(f.answer || "No clear answer in the report.")}</p>
            ${evidence ? `<p class="block-label">Evidence</p>${evidence}` : ""}
            ${gaps ? `<p class="block-label">Gaps</p>${gaps}` : ""}
          </section>`;
      }).join("");
      const jsonHref = mode === "mock" ? "/sample" : mode === "upload" ? "/brief" : "/real";
      briefEl.innerHTML = `
        <div class="brief-head">
          <h2>${escapeHtml(brief.topic || "Water risk brief")}</h2>
          <p class="report-name">${escapeHtml(brief.report_name || "Untitled report")}</p>
        </div>
        <div class="stats">${chips}</div>
        ${findingsHtml || "<p>No findings yet.</p>"}
        <details class="raw">
          <summary>JSON for your product</summary>
          <pre>${escapeHtml(JSON.stringify(brief, null, 2))}</pre>
          <p><a href="${jsonHref}" target="_blank" rel="noopener">Open JSON</a></p>
        </details>`;
    }
    async function loadReal() {
      const response = await fetch("/real");
      renderBrief(await response.json(), { mode: "real" });
      statusEl.textContent = "Real Siemens FY2023 brief (from analyze_report). Upload a PDF for a new live run.";
    }
    async function loadMock() {
      const response = await fetch("/sample");
      renderBrief(await response.json(), { mode: "mock" });
      statusEl.textContent = "Mock template only (not a real report). Switch back to Siemens (real) or upload a PDF.";
    }
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const fileInput = document.getElementById("report");
      if (!fileInput.files.length) return;
      const data = new FormData();
      data.append("report", fileInput.files[0]);
      data.append("model", document.getElementById("model").value);
      statusEl.textContent = "Analyzing…";
      runBtn.disabled = true;
      try {
        const response = await fetch("/analyze", { method: "POST", body: data });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "Analysis failed");
        renderBrief(payload.brief, { mode: "upload" });
        statusEl.textContent = `Ready: ${payload.report_name}`;
        briefEl.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (err) {
        statusEl.textContent = err.message || String(err);
      } finally {
        runBtn.disabled = false;
      }
    });
    realBtn.addEventListener("click", () => { loadReal(); });
    mockBtn.addEventListener("click", () => { loadMock(); });
    loadReal();
  </script>
</body>
</html>
"""


def main() -> None:
    """Run with uvicorn from this folder."""
    import uvicorn

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Set OPENAI_API_KEY or GOOGLE_API_KEY before analyzing a live report.")
    uvicorn.run("app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()

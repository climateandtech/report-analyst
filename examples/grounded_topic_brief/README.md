# Grounded topic brief (build-your-own-tool demo)

Example host app: your UI, OSA as the analysis library, grounded brief from one PDF.

Default view is a **real** Siemens FY2023 water-risk brief (`data/real_brief.json` from `analyze_report`). A **Mock template** button exists for UI wiring only.

## Just do it

1. Copy this folder.
2. Agent skill: **`osa-library-host-app`** (`.claude/skills/…`; also `.agents/` / `.cursor/`). Else paste [`PROMPT.md`](PROMPT.md).
3. Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` (skill: `references/api-keys.md`). Analysis key ≠ coding-agent subscription.
4. Restyle with [`STYLE.md`](STYLE.md) / skill `references/style.md` (shadcn-flavoured, not a full install).
5. Swap `questions/water_risk_questions.yaml` for your topic.
6. Run:

```bash
pip install -r requirements.txt fastapi uvicorn python-multipart
export OPENAI_API_KEY=...   # or GOOGLE_API_KEY
cd examples/grounded_topic_brief
python app.py
```

Open http://127.0.0.1:8765

## Library surface

```python
from report_analyst.core.library import analyze_report, build_topic_brief

answers = await analyze_report("supplier.pdf", "questions/water_risk_questions.yaml")
brief = build_topic_brief(answers, topic="Supplier water-risk brief")
```

Built-in sets work too: `await analyze_report("report.pdf", "tcfd")`.

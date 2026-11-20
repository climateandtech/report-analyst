---
name: osa-library-host-app
description: >-
  Build a custom host app on Open Sustainability Analyst (report-analyst) as a
  Python library using analyze_report and build_topic_brief, including LLM API
  key setup (OPENAI_API_KEY or GOOGLE_API_KEY). Use when the user wants their
  own tool or UI on OSA, a grounded topic brief, report-analyst library embed,
  host app scaffold, API token/env setup for analysis, or shadcn-style restyle
  of the example. Triggers include: build with OSA library, custom tool on
  report-analyst, grounded topic brief, examples/grounded_topic_brief, set up
  OpenAI key for OSA.
license: Apache-2.0
metadata:
  author: climateandtech
  version: "1.1"
---

# OSA library host app

Ship a small custom product UI on `report_analyst.core.library`. Do not clone the Streamlit analyst app.

Works with any coding agent (Cursor, Claude Code, Copilot, etc.). Invoke by name `osa-library-host-app` when the client supports skills; otherwise follow these steps from the repo copy under `.claude/skills/osa-library-host-app/`.

## Instructions

1. **API key (required for live analysis)** — see [references/api-keys.md](references/api-keys.md). At least one of `OPENAI_API_KEY` or `GOOGLE_API_KEY` must be set in the process env (or `.env` loaded by the host). Never commit keys. Never print key values in chat.
2. Prefer copying `examples/grounded_topic_brief/` over a blank scaffold.
3. Call the library:

```python
from report_analyst.core.library import analyze_report, build_topic_brief

answers = await analyze_report("report.pdf", "questions/<topic>_questions.yaml")
brief = build_topic_brief(answers, topic="<Topic> brief")
```

4. Add `questions/<topic>_questions.yaml` (3–5 questions: `id`, `text`, `guidelines`).
5. UI: one PDF upload, readable brief (answer / evidence / gaps), `GET /brief` for JSON.
6. Style with [references/style.md](references/style.md). Short copy. No em dashes. Illustrative shadcn primitives only (not a full design-system install).

## One-liner

Copy the example folder, set an LLM API key, rename the topic YAML, keep library calls, restyle with references/style.md, ship.

## Out of scope

- Full Streamlit OSA redesign
- Full shadcn/Next monorepo unless the user asks
- Rebuilding retrieval/prompting from scratch when the library already does it

## References

- API keys: [references/api-keys.md](references/api-keys.md)
- Example app: `examples/grounded_topic_brief/`
- Human paste prompts: `examples/grounded_topic_brief/PROMPT.md`
- Style tokens: [references/style.md](references/style.md)

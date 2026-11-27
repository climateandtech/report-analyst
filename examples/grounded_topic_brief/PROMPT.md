# Prompt guide (Cursor / Claude / Copilot)

Prefer the Agent Skill **`osa-library-host-app`** at `.claude/skills/osa-library-host-app/` (also `.agents/skills/` and `.cursor/skills/`). Paste the prompts below when you are not using that skill.

Goal: ship a small custom tool on OSA, not rebuild the analyst UI.

## 0. Set the LLM API key

```text
Help me set OPENAI_API_KEY or GOOGLE_API_KEY for a report-analyst host app.
Use a local .env (not committed). Confirm the key is present without printing it.
This is for OSA analysis, not my coding-agent subscription.
```

## 1. Scaffold the host app

```text
Build a small FastAPI (or Next.js) app that embeds Open Sustainability Analyst
as a library. Use report_analyst.core.library.analyze_report and build_topic_brief.
One PDF upload, one topic question YAML, render a readable brief with answer /
evidence / gaps. Keep the UI custom. Do not clone the Streamlit app.
```

## 2. Add a topic question set

```text
Add questions/<topic>_questions.yaml for <TOPIC>. Three to five questions,
each with id, text, and short guidelines. Wire app.py to that YAML path.
```

## 3. Consume the brief in a second screen

```text
After analyze_report, call build_topic_brief and show a second view that only
uses the brief JSON (no raw LLM chat). Include a GET /brief endpoint.
```

## 4. Style it

```text
Follow examples/grounded_topic_brief/STYLE.md. Short copy, no em dashes.
shadcn-style primitives: Card, Badge, Button. Keep it illustrative, not a
full design system install.
```

## 5. One-liner if you are in a hurry

```text
Copy examples/grounded_topic_brief, rename the topic YAML, keep the library
calls, restyle with STYLE.md. Ship.
```

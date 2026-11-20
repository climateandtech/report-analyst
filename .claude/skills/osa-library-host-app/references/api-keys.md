# LLM API keys for OSA host apps

Live `analyze_report` calls need an LLM provider key in the **host process** environment. Sample/demo JSON in the example UI can render without a key; generating a brief from a PDF cannot.

## What to set

| Env var | Provider | Notes |
|---------|----------|--------|
| `OPENAI_API_KEY` | OpenAI | Common default; models like `gpt-4o-mini` |
| `GOOGLE_API_KEY` | Google Gemini | Alternative if you prefer Gemini |
| `OPENAI_API_MODEL` | OpenAI | Optional; default often `gpt-4o-mini` |

At least one of `OPENAI_API_KEY` or `GOOGLE_API_KEY` is required.

## Setup steps (agent should do / guide)

1. Ask which provider they want (OpenAI or Google). Do not assume Claude or any coding-agent vendor key is the analysis key. OSA analysis uses OpenAI/Gemini (or whatever the analyzer is configured for), not the Cursor/Claude chat subscription.
2. Point them to create a key:
   - OpenAI: https://platform.openai.com/api-keys
   - Google AI Studio: https://aistudio.google.com/apikey
3. Put the key in a local env file **outside git**, e.g. repo-root `.env` (copy from `.env.example` if present):

```bash
cp .env.example .env   # if the file exists
# then edit .env — set OPENAI_API_KEY=... or GOOGLE_API_KEY=...
```

Or export for one shell session:

```bash
export OPENAI_API_KEY=...          # your key; do not paste into chat logs
# or: export GOOGLE_API_KEY=...
```

4. Confirm presence without leaking secrets:

```bash
python -c "import os; print('openai', bool(os.getenv('OPENAI_API_KEY'))); print('google', bool(os.getenv('GOOGLE_API_KEY')))"
```

5. Restart the host app so it inherits the env (`python app.py` / uvicorn).

## Deploy / Streamlit / Render

Same variable names in the platform secrets UI (Streamlit Secrets, Render Environment, etc.). Name the keys exactly `OPENAI_API_KEY` or `GOOGLE_API_KEY`.

## Safety

- Never commit `.env` or paste raw keys into commits, PRs, or chat.
- If a key was exposed, tell the user to rotate it at the provider.
- Prefer `bool(os.getenv(...))` checks over printing values.

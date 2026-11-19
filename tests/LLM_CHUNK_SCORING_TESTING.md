# LLM chunk scoring testing

## Bug

`DocumentAnalyzer.score_chunk_relevance` / `score_chunk_relevance_batch` called
`llm.achat(prompt=...)`. LlamaIndex OpenAI requires `achat(messages=[ChatMessage, ...])`.
Exceptions were swallowed, so enabling “LLM scoring” in OSA stored `0.0` for every chunk.

Related: even when scores existed, `_analyze_chunks` did not pass them into the answer
prompt (`computed_score` / `relevance_score`), and candidates were not re-ordered by
LLM score after embedding retrieval.

## Coverage

| Tier | File | What it asserts |
| --- | --- | --- |
| Unit | `tests/test_llm_chunk_scoring.py` | Messages-only LLM stub; scoring returns model values; answer prompt shows `llm_score` |
| Unit | `tests/test_analyzer.py::test_score_chunk_relevance` | `achat` called without `prompt=` |
| Functional | `tests/test_llm_chunk_scoring_functional.py` | `process_document(..., use_llm_scoring=True)` yields non-zero scores and re-ranks the numeric target chunk first |

## Run

```bash
PYTHONPATH=. ./venv/bin/pytest \
  tests/test_llm_chunk_scoring.py \
  tests/test_llm_chunk_scoring_functional.py \
  tests/test_analyzer.py::test_score_chunk_relevance -q
```

These tests fail on `main` before the fix (silent `0.0`) and pass after.

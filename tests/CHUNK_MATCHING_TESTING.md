# Chunk matching tests

The matcher compares report-analyst chunks with ClimRetrieve evidence while
preserving the direction of containment and recognizing changed chunk
boundaries.

Partial token overlap never counts as a benchmark hit. Single-chunk hits require
full ordered ground-truth containment. Split hits require adjacent retrieved
chunks which, after removing their duplicated overlap, reconstruct the complete
ground-truth token sequence in order.

## Offline unit and functional tests

```bash
PYTHONPATH=. venv/bin/pytest -q \
  tests/test_text_overlap.py \
  tests/test_library_eval.py \
  tests/test_library_eval_functional.py
```

`tests/fixtures/ct_reit_chunk_matching.json` contains real text from the CT REIT
2022 ESG report. OpenAI embeddings map the selected candidates for the question
"Does the company have any engagements with industry peers in relation to
climate change?" at chunk sizes 200 and 400. Embedding vectors and API
credentials are deliberately not stored.

Behavioral matcher and functional benchmark tests load these extracted report
chunks and the ClimRetrieve text from the fixture; they do not construct
fictional report evidence.

The fixture covers:

- exact text;
- a report-analyst chunk containing ClimRetrieve evidence;
- the reverse containment direction;
- one 400-token chunk split across two adjacent 200-token chunks;
- two 200-token chunks merged into one 400-token chunk;
- an unrelated real report chunk.

## Regenerate the fixture

```bash
PYTHONPATH=. venv/bin/python scripts/generate_chunk_match_fixture.py
```

This requires `OPENAI_API_KEY`. The report and labels are downloaded from the
public ClimRetrieve repository into ignored `notebooks/data/` paths.

## Opt-in live test

```bash
CHUNK_MATCH_FIXTURE_E2E=1 PYTHONPATH=. \
  venv/bin/pytest -q tests/test_chunk_match_fixture_e2e.py
```

The live test calls OpenAI and is skipped during normal test runs.

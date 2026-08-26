# Repeated-analysis robustness evaluation

Run the same report questions `N` times without using stored analysis answers:

```bash
PYTHONPATH=. ./venv/bin/python scripts/evaluate_analysis_robustness.py \
  --labels notebooks/data/ClimRetrieve_base.xlsx \
  --reports-dir notebooks/data/climretrieve_pdfs \
  --output-dir evaluation_output \
  --runs 5 \
  --top-k 5 10 \
  --chunk-sizes 300 500 800 \
  --reports 10 \
  --questions 16
```

Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` first. Use `--model` to override the
configured model.

The script calls `DocumentAnalyzer.process_document` directly, so it never
loads stored analysis answers. It also sets `analyzer.use_cache = False`.
Document chunks and embeddings may still be reused because they are
deterministic inputs to the repeated LLM analysis.

## Incremental checkpoints

`save_analysis` keeps only the latest database result for a configuration.
The evaluator therefore persists every returned result before starting the
next run:

- `all_results.csv`: one denormalized table containing answer and chunk fields
- `raw_analysis_runs.jsonl`: complete raw result, including answer and chunks
- `analysis_runs.csv`: one answer row per run
- `chunk_scores.csv`: one selected-chunk row per run

If a later run overwrites the database row or the evaluation is interrupted,
all completed runs remain in these files.

Every invocation gets a random `evaluation_id`. Each analysis gets a
deterministic `run_uid` derived from that evaluation ID, report, question,
configuration, and sequential run number. This prevents collisions when CSVs
from separate evaluations are combined while keeping IDs reproducible within
one evaluation. `evaluation_manifest.json` records the evaluation ID and CLI
arguments.

`--chunk-sizes` is optional. When omitted, the evaluator uses the single
`--chunk-size` value (default: 500). Configuration IDs include both factors,
for example `cs300_k5` and `cs500_k10`. Range CSVs are grouped by chunk size,
top-k, and configuration; `chunk_size_answer_score_delta.csv` and
`topk_answer_score_delta.csv` isolate the first pair supplied for each factor.

Pass `--overwrite` to replace an existing evaluation directory.

## Summaries and plots

The evaluator produces:

- `answer_score_boxplot.png` and `answer_score_ranges.csv`
- `chunk_llm_score_boxplot.png` and `chunk_llm_score_ranges.csv`
- `chunk_selection_boxplot.png` and `chunk_selection_ranges.csv`
- answer-score stability and top-k deltas
- retrieved/cited chunk consistency, top-k containment, and citation subset rate
- `yes_no_answer_comparison.csv` and `yes_no_answer_metrics.csv` for explicit
  OSA versus ClimRetrieve yes/no answers

Chunk selection is represented by pairwise Jaccard similarity between the
selected chunk sets from repeated runs. Range CSVs contain count, mean,
standard deviation, minimum, quartiles, median, maximum, and max-minus-min.

## Chunk boundary matching

Retrieval exports classify text matches as `exact`,
`retrieved_contains_ground_truth`, `ground_truth_contains_retrieved`,
`partial_overlap`, or `no_match`. They also include Jaccard and directional
coverage values. `partial_overlap` is diagnostic and does not count as a
ground-truth hit. A hit requires full ordered ground-truth containment in one
retrieved chunk or across an overlap-deduplicated contiguous chunk window. The
group matcher additionally distinguishes split, merged, and many-to-many chunk
boundaries.

METEOR, BERTScore, or embedding similarity may be exported as diagnostic
candidate-ranking signals, but they must not independently turn partial
evidence into a hit. For verbatim report-source labels, ordered full
ground-truth coverage remains the acceptance rule.

`tests/fixtures/ct_reit_chunk_matching.json` contains embedding-mapped,
real-report examples at chunk sizes 200 and 400. See
`tests/CHUNK_MATCHING_TESTING.md` for fixture provenance and regeneration.
The paper-ready formulas, relevance threshold, split-rank rule, and confidence
interval procedure are specified in `docs/CHUNK_RETRIEVAL_PAPER_METHOD.md`.

## Typed answer comparison

ClimRetrieve answers are free text, but most begin with an explicit `YES` or
`NO`. The evaluator conservatively parses only a leading yes/no marker; it does
not infer a label from narrative answers. Full expert and OSA answer text stays
in `all_results.csv`.

For clean model output, use the typed-answer prompt behavior merged in
[report-analyst PR #89](https://github.com/climateandtech/report-analyst/pull/89).
Questions whose guidelines declare
`- ANSWER type: classification — exactly one of Yes / No / Unclear / Not disclosed`
then return a classification in `ANSWER`, while reasoning remains in
`EVIDENCE`. `Unclear` and `Not disclosed` remain unscored in the binary
yes/no metrics and are preserved in the CSV.

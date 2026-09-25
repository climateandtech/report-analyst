# Library evaluation (OSA vs ClimRetrieve)

Unit tests in `test_text_overlap.py`, `test_library_eval.py`, `test_robustness.py`,
and `test_analyzer_retrieve_chunks.py` cover matching, report selection, IR table
construction, selected-chunk / score robustness, CSV export, and the retrieval-only
analyzer API.

Robustness helpers in `library_eval.py`:

- Retrieved sets: `retrieved_chunk_ids`, `retrieved_chunk_consistency`,
  `pairwise_chunk_selection`, `topk_retrieved_containment`,
  `citations_are_subset`, `citation_subset_rate`
- Scores: `build_analysis_run_rows`, `score_distribution_summary`,
  `score_stability`, `score_range`, `topk_score_delta`,
  `question_configuration_summary`
- Chunk exports: `build_chunk_dataset_rows` writes one vector-free row per
  generated chunk with its document, configuration, order, page, and text.
- Citations: `cited_chunk_ids`, `citation_consistency`

Functional coverage is in `test_library_eval_functional.py`: helpers produce CSVs
that `EvaluationEngine.compare_flexible_datasets` can score.

`test_analysis_robustness_script.py` proves each run is appended to raw JSONL and
both flattened CSVs. Live PDF/LLM runs are available through
`scripts/evaluate_analysis_robustness.py` and the notebook; they are not part of
CI. The notebook batches selected questions into one document pass per
configuration/run and defaults to a bounded one-report, five-question run.

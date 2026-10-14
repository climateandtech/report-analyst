# Loading results

--8<-- "snippets/core.md"

These loaders turn a CSV or SQLite export into a benchmark dataset. ClimRetrieve files are detected and rewritten into `query_id` / `chunk_id` / `position` / `score` before scoring.

::: report_analyst.core.benchmark.retrieval_results_loader.load_flexible_dataset_from_csv

::: report_analyst.core.benchmark.retrieval_results_loader.detect_dataset_type

::: report_analyst.core.benchmark.retrieval_results_loader.load_retrieval_results_from_csv

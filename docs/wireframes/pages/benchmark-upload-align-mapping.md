# Benchmark · Upload and map
Prepare a dataset for evaluation.

::: card {#tabs}
[Upload & map]* [Evaluation] [Results] [Annotation]
:::

::: card {#steps}
### 1. Upload · 2. Align · 3. Review mapping

Upload your system output, align it with the benchmark format, then confirm the detected fields before evaluation.
:::

::: card {#upload}
### Upload dataset

[Drop CSV, Excel, YAML or JSON here____________________] [Browse files]

Selected file: **chunks_Microsoft_2024.csv**  ·  1,240 rows  ·  Uploaded just now

Supported ranking fields: query/item ID, report ID, chunk ID, position/rank, optional score.
:::

::: card {#benchmark}
### Benchmark format

Reference set: [ClimRetrieve v1________________v]

- 16 benchmark questions
- 4 expected question types
- Ground-truth labels managed by the benchmark owner

[Download sample format]
:::

::: callout {for:upload side:left}
your dataset
:::

::: callout {for:benchmark side:right}
reference structure
:::

::: card {#align}
### Align columns

| Your column | Benchmark field | Status |
|---|---|---|
| [query_id________v] | Query / question ID | ✓ matched |
| [report_id_______v] | Report ID | ✓ matched |
| [chunk_id________v] | Retrieved chunk ID | ✓ matched |
| [position________v] | Rank / position | ✓ matched |
| [score___________v] | Relevance score | Optional |

[Auto-detect fields]  [Validate alignment]*
:::

::: callout {for:align side:left}
map once,
reuse later
:::

::: card {#mapping}
### Mapping preview

16 / 16 benchmark questions found · 1,240 / 1,240 rows valid · 0 errors

| Question ID | Report | Top retrieved chunks | Question type |
|---|---|---|---|
| TCFD-01 | Microsoft 2024 | chunk_014, chunk_088, chunk_102 | Governance |
| TCFD-02 | Microsoft 2024 | chunk_031, chunk_044, chunk_090 | Strategy |
| TCFD-03 | Microsoft 2024 | chunk_052, chunk_067, chunk_071 | Risk |

### Dataset name
[Microsoft retrieval · v2________________________]

[Save dataset]*  [Continue to evaluation]*
:::

::: callout {for:mapping side:right}
the user sees
the mapped result
:::


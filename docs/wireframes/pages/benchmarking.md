# Benchmarking
Evaluate retrieval and extraction against reference datasets.

::: card {#tabs}
[Datasets] [Evaluate]* [Results] [Annotate]
:::

::: callout {for:tabs side:left}
tabs
:::

::: card {#mode}
Evaluation type

- (x) Ranking (retrieval)
- ( ) Classification
- ( ) Both

:::

::: callout {for:mode side:left}
mode
:::

::: grid-2 {.start}

### Reference (ground truth)
[DB: TCFD gold labels v1___________v]
- DB: TCFD gold labels v1
- Uploaded: microsoft_gt_aligned.csv

### Benchmark (results)
[DB: Microsoft 2024 run A___________v]
- DB: Microsoft 2024 run A
- Uploaded: microsoft_bm_aligned.csv

:::

Evaluation name
[eval-20250312-1430___________]

::: card {#metrics}
#### Ranking configuration

Top K
[10___]

K values for metrics
[1,3,5,10___________]

[Run ranking evaluation]*
:::

::: callout {for:metrics side:left}
metrics
:::

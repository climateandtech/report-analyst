# Benchmarking
Evaluate retrieval and extraction against a gold set.

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

### Ground truth / Benchmark {#gt}
[ClimRetrieve___________v]
- ClimRetrieve
- ClimRetrieve report-level

Expert-annotated relevant chunks.

### Chunks downloaded via CSV {#chunks}
[chunks_Microsoft_2024.csv___________v]
- chunks_Microsoft_2024.csv
- chunks_data.csv

Export from Analysis → Download chunks data.

:::

::: callout {for:gt side:left}
gold labels
(ClimRetrieve)
:::

::: callout {for:chunks side:right}
your retrieval
export
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

# Benchmark · Results
Review metrics and compare saved evaluations.

::: card {#tabs}
[Upload & map] [Evaluation] [Results]* [Annotation]
:::

::: card {#summary}
### Microsoft retrieval · v2
ClimRetrieve v1 · Ranking · Completed 02 Sep 2026, 14:32

**12 / 16 questions evaluated** · 75% coverage · 4 excluded

Higher values indicate that relevant chunks were ranked earlier and the result is more accurate against the reference set.
:::

### Result
| MAP | MRR | Precision@5 | Recall@10 |
|---|---|---|---|
| 0.742 | 0.833 | 0.780 | 0.910 |



::: callout {for:map side:left}
primary ranking score
:::

::: card {#compare}
### Compare evaluations

Select saved runs to compare side by side.

| Evaluation | Dataset | Questions | MAP | MRR | Precision@5 |
|---|---|---:|---:|---:|---:|
| [x] Microsoft v2 | Microsoft retrieval · v2 | 12/16 | **0.742** | **0.833** | **0.780** |
| [x] Northwind v1 | Northwind retrieval · v1 | 16/16 | 0.681 | 0.750 | 0.702 |
| [ ] Chunks baseline | chunks_data.csv | 10/16 | 0.554 | 0.600 | 0.571 |

### Metric comparison

| Metric | Microsoft v2 | Northwind v1 | Difference |
|---|---:|---:|---:|
| MAP | 0.742 | 0.681 | +0.061 |
| MRR | 0.833 | 0.750 | +0.083 |
| Precision@5 | 0.780 | 0.702 | +0.078 |

[Open question-level comparison]  [Save comparison]  [Export CSV]

::: callout {for:compare side:right}
spot meaningful
differences
:::

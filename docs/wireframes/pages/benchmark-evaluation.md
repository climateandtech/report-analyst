# Benchmark · Evaluation
Run a ranking evaluation against a shared benchmark.

::: card {#tabs}
[Upload & map] [Evaluation]* [Results] [Annotation]
:::

::: card {#mode}
### Evaluation mode

- (x) Ranking
- ( ) Classification

Ranking compares the order of retrieved chunks. Classification compares one predicted label per question.
:::

::: callout {for:mode side:left}
choose a track
:::

::: card {#benchmark}
### Benchmark set
[ClimRetrieve v1________________v]
- ClimRetrieve v1
- ClimRetrieve report-level
- ClimateFinanceBench

16 questions · 4 question types · shared reference set
::

::: card {#dataset}
### Your dataset
[Microsoft retrieval · v2____________v]
- Microsoft retrieval · v2
- chunks_data.csv
- Northwind retrieval · v1

Saved from Upload & map · ranking format validated
::

::: callout {for:benchmark side:left}
same questions
for every run
::

::: callout {for:dataset side:right}
your configured
dataset
:::

::: card {#coverage}
### Question matching

**12 / 16 questions will be evaluated**

███████████████░░░ 75%

12 questions have matching IDs and compatible question types. 4 questions are not present in your dataset and will be excluded.

| Match status | Questions | Action |
|---|---:|---|
| Ready to evaluate | 12 | Included |
| Missing from dataset | 3 | Excluded |
| Type mismatch | 1 | Excluded |

Higher question coverage generally gives a more reliable and accurate benchmark result.
:::

::: callout {for:coverage side:left}
coverage affects
confidence
:::

::: card {#ranking}
### Ranking configuration

Ranking output: (x) Ordered chunks per question  ( ) Relevance scores only

K values: [1, 3, 5, 10________________v]

Evaluation name: [Microsoft v2 · ClimRetrieve v1________________]

[Review matched questions]  [Start evaluation]*
::

::: callout {for:ranking side:right}
MAP · MRR · Precision@K · Recall@K
::

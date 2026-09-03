# Report Analyst
Analysis parameters tailored to your configurations.

::: grid-2 {.start}

### Report

[Microsoft Sustainability Report 2024.pdf___________v]{#report}
- Microsoft Sustainability Report 2024.pdf
- Northwind TCFD 2023.pdf

Uploaded, 12.03.2025

### Analysis configuration

Question set
[TCFD___________v]
- TCFD
- GRI
- ESRS

Climate-related financial disclosures.

#### Processing steps {#steps}
Chunk — Embed — Map — **Answer**

|Stored| Chunking
|Stored| Embedding
|New|{.primary} Question mapping
|New|{.primary} Question answering

Top K
[5___]

Chunk size
[500___]

Overlap
[20___]

LLM Model
[gpt-4o-mini___________v]
- gpt-4o-mini
- gpt-4o
- gemini-2.5-flash

Scoring

- [x] LLM Scoring
- [x] Batch Scoring

:::

::: callout {for:report side:left}
report select
:::

::: callout {for:steps side:left}
step cache
:::

## Select questions

[Select all]*

| Select | QID | Question |
|--------|-----|----------|
| [x] | TCFD-1 | Describe the board’s oversight of climate-related risks and opportunities. |
| [x] | TCFD-2 | Describe management’s role in assessing and managing climate-related risks. |
| [ ] | TCFD-3 | Describe the climate-related risks and opportunities identified over the short, medium, and long term. |
| [x] | TCFD-4 | Describe the impact of climate-related risks on the organization’s businesses, strategy, and financial planning. |

[Analyze selected questions]*{#run} [Reanalyze]

::: callout {for:run side:left}
run
:::

::: alert
Analysis in progress… 3 of 3 questions
:::

## Analysis results

| QID | Score | Analysis | Key evidence |
|-----|-------|----------|--------------|
| TCFD-1 | 8.2 | Board reviews climate risk quarterly via the Sustainability Committee… | p. 14 — “Board oversight” |
| TCFD-2 | 7.4 | Management owns the climate risk register; CRO reports monthly… | p. 18 — “Management role” |
| TCFD-4 | 6.1 | Strategy impacts described qualitatively; limited financial quantification… | p. 22 — “Financial planning” |

[Download analysis results] [Download chunks data] [Open PDF viewer]

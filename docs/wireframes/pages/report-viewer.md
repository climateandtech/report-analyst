# PDF viewer

::: grid-2 {.start}

### Chunks

Question
[Q1 How does org…___________v]{#question}
- All Questions
- Q1 How does org…
- Q2 What targets…

[x] Show evidence only{#evidence}

::: card {#chunk-3}
|Evidence|{.success} |Page 12|

“…risk management framework is reviewed quarterly by the board…”

Sim: 0.850 · LLM: 0.920
:::

::: card
|Page 14|

“…Performance metrics for transition plans are disclosed in section 4…”

Sim: 0.710
:::

### PDF

::: card {.document #pdf}
[Previous]  Page 12 of 84  [Next]

**3. Governance**

::: card {.retrieved}
The Board Sustainability Committee meets quarterly to review climate risk and opportunities.
:::

::: card {.evidence #cite}
|Evidence|{.success}
“…risk management framework is reviewed quarterly by the board…”
:::

::: card {.retrieved}
The committee reports to the full board after each sitting.
:::

::: card {.retrieved}
Management’s role is described in section 3.2. The CRO owns the climate risk register.
:::
:::

:::

::: callout {for:question side:left}
restrict chunks
and overlays
to one question
:::

::: callout {for:evidence side:left}
hide retrieved
boxes that were
not cited
:::

::: callout {for:chunk-3 side:left}
click a chunk:
PDF jumps to
that page
:::

::: callout {for:cite side:right}
hover a box:
similarity,
LLM score, order
:::

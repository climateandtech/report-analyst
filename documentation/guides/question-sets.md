# Question sets

A question set is the framework the analyst asks against. Each question has an id, the question text, and guidelines that tell the model what to look for and what to leave out.

## Answer types (read this first)

Every question is one of three answer modes. The mode is set by the **first** guidelines line. If that line is missing, the answer is free-form prose (the historical default for TCFD, Everest, Lucia, and similar).

| Mode | `ANSWER type` line | What `ANSWER` must be | Typical use |
| --- | --- | --- | --- |
| **Free-form** | *(omit the line)* | Short narrative prose | Strategy, actions, qualitative disclosure |
| **Classification** (yes/no) | `ANSWER type: classification — …` | Exactly one label from the allowed set (usually Yes / No / Unclear / Not disclosed) | Presence of a plan, policy, target, or commitment |
| **Quantity** (numerical) | `ANSWER type: quantity — …` | A number **with unit**, or Unclear / Not disclosed | Emissions, intensities, prices, volumes |

Typed modes matter: when PromptManager sees an `ANSWER type` line, it stops forcing the default “~60-word prose” answer rules for that question.

### Classification (yes/no-style)

```yaml
guidelines: |
  - ANSWER type: classification — exactly one of Yes / No / Unclear / Not disclosed
  - …extra evidence rules…
```

- Pick **one** label from the list in the type line.
- Put supporting detail in `EVIDENCE`, not in a long prose `ANSWER`.
- `Not disclosed` means the report does not say; it is not the same as `No`.

In-repo example (classification only on core questions): `climretrieve_questions.yaml`.

### Quantity (numerical)

```yaml
guidelines: |
  - ANSWER type: quantity — numeric value with unit (tCO2e, %, EUR/t, etc.) or Unclear / Not disclosed if not reported
  - …scope / year / basis rules…
```

- Return a **numeric value and its unit** (for example `12345 tCO2e`, `12.3 %`).
- Zero can be a valid quantity when the report states zero.
- If the figure is missing, use `Unclear` or `Not disclosed` per the type line — do not invent a number.

### Mixed sets (classification + quantity)

One question set may mix modes per question. The canonical in-repo example is **ESRS E1 Climate**:

| File | Id | Modes |
| --- | --- | --- |
| `esrs_e1_climate_questions.yaml` | `esrs_e1_climate` | classification **and** quantity |
| `esrs_e1_climate_examples_questions.yaml` | `esrs_e1_climate_examples` | same, plus few-shot `Example:` bullets |

Do **not** treat Everest/Lucia “Respond with clear Yes or No” or “use the exact number” prose as typed answers — those sets predate `ANSWER type` and still run under free-form rules unless you add the type line.

## Built-in files

Built-in sets live in `report_analyst/questionsets/`:

| File | Set | Dominant answer mode |
| --- | --- | --- |
| `esrs_e1_climate_questions.yaml` | ESRS E1 Climate | **classification + quantity** (typed) |
| `esrs_e1_climate_examples_questions.yaml` | ESRS E1 Climate (examples) | **classification + quantity** (typed) |
| `climretrieve_questions.yaml` | ClimRetrieve | **classification** on core questions; IR follow-ups free-form |
| `climretrieve_complete_questions.yaml` | ClimRetrieve Complete | **classification** |
| `climretrieve_complete_6_questions.yaml` | ClimRetrieve Complete, six questions | **classification** |
| `tcfd_questions.yaml` | TCFD | free-form |
| `lucia_questions.yaml` | Lucia | free-form |
| `denali_questions.yaml` | Denali | free-form |
| `kilimanjaro_questions.yaml` | Kilimanjaro | free-form |
| `everest_questions.yaml` | Everest | free-form |

The loader reads every `*_questions.yaml` file on `QUESTIONSETS_PATH`, or `report_analyst/questionsets/` when that variable is unset. The id is the filename without `_questions`.

To change a framework, edit the YAML in a fork and deploy that fork. The product site has a [customize frameworks](https://opensustainabilityanalyst.com/en/esrs-analysis-customize-frameworks) guide. The loader itself is documented under [question sets in the API reference](../reference/question-sets.md).

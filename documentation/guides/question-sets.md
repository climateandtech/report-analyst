# Question sets

A question set is the framework the analyst asks against. Each question has an id, the question text, and guidelines that tell the model what to look for and what to leave out.

Built-in sets live in `report_analyst/questionsets/`:

| File | Set |
| --- | --- |
| `tcfd_questions.yaml` | TCFD |
| `climretrieve_questions.yaml` | ClimRetrieve |
| `climretrieve_complete_questions.yaml` | ClimRetrieve Complete |
| `climretrieve_complete_6_questions.yaml` | ClimRetrieve Complete, six questions |
| `lucia_questions.yaml` | Lucia |
| `denali_questions.yaml` | Denali |
| `kilimanjaro_questions.yaml` | Kilimanjaro |
| `everest_questions.yaml` | Everest |

The loader reads every `*_questions.yaml` file on `QUESTIONSETS_PATH`, or `report_analyst/questionsets/` when that variable is unset. The id is the filename without `_questions`.

To change a framework, edit the YAML in a fork and deploy that fork. The product site has a [customize frameworks](https://opensustainabilityanalyst.com/en/esrs-analysis-customize-frameworks) guide. The loader itself is documented under [question sets in the API reference](../reference/question-sets.md).

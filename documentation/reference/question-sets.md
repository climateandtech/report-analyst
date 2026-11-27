# Question sets

--8<-- "snippets/core.md"

`QuestionSetLoader` reads `*_questions.yaml` and exposes each set by id.

Answer modes are declared per question in guidelines:

| Mode | Guideline cue | Guide |
| --- | --- | --- |
| Free-form | no `ANSWER type` line | [Question sets](../guides/question-sets.md#answer-types-read-this-first) |
| Classification (yes/no) | `ANSWER type: classification` | [Classification](../guides/question-sets.md#classification-yesno-style) |
| Quantity (numerical) | `ANSWER type: quantity` | [Quantity](../guides/question-sets.md#quantity-numerical) |

Mixed example: ESRS E1 (`esrs_e1_climate`). See the [question sets guide](../guides/question-sets.md) for the full file table.

::: report_analyst.core.question_loader.QuestionSet

::: report_analyst.core.question_loader.QuestionSetLoader

::: report_analyst.core.question_loader.get_question_loader

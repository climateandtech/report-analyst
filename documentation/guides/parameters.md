# Parameters

These settings are on **Report Analyst**, under the analysis configuration. A stored result is tied to the combination you used, so changing one of them is a new run.

| Setting | Default | Effect |
| --- | --- | --- |
| Chunk size | 500 | Length of each passage, in tokens. Larger chunks keep more context in one passage and produce fewer of them. |
| Chunk overlap | 20 | Tokens repeated between neighbouring passages, so a sentence on a boundary is not cut in half. |
| Top K | 5 | How many passages are retrieved for each question before the model answers. |
| Model | First available model | The LLM that writes the answer. OpenAI models need `OPENAI_API_KEY`. Gemini models need `GOOGLE_API_KEY`. |
| LLM scoring | Off | A second model pass that scores retrieved passages for the question. Leave it off unless you want that extra call. |
| Batch scoring | Off | Score passages together instead of one at a time. Only applies when LLM scoring is on. |

The processing step (Chunk, Embed, Map, or Answer) is separate from these numbers. See [report analysis](report-analysis.md).

Retrieval for benchmarking uses the same chunk size, overlap, and top K. Those fields are on `RetrievalConfig` in the [benchmark models](../reference/benchmark-models.md).

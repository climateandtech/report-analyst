# Report analysis

A run takes a PDF, a question set, and a processing step, then stores answers with evidence.

## Run an analysis

1. Open **Upload Report** and add a sustainability report PDF. Reports already on this machine appear in the list.
2. Open **Report Analyst**. Choose the report and a question set (TCFD, ESRS-oriented sets, and others).
3. Set the processing step. The default is **Answer**, which runs the whole pipeline.
4. Select the questions to ask, then start the analysis.

Stored runs stay available under **All Results**. Pick the report and configuration there to read answers, scores, evidence, and gaps without running the model again.

## Processing steps

Each step includes the ones before it.

| Step | What it does |
| --- | --- |
| Chunk | Split the PDF into passages. |
| Embed | Turn those passages into vectors so they can be searched. |
| Map | Attach the closest passages to each question. |
| Answer | Ask the model and store the answer, score, evidence, and gaps. |

Answering calls the LLM and uses API credit. Chunk, Embed, and Map do not write answers.

## Read the result

Each question returns an answer, a score, the evidence passages, and any gaps. Open [chunk highlighting](chunk-highlighting.md) to see an evidence passage outlined on the PDF page. The settings that produced the run are covered in [parameters](parameters.md).

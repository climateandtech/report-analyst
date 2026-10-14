# Analysis workflow

--8<-- "snippets/core.md"

One question moves through retrieval, optional LLM scoring, the answer, and evidence assignment. The Report Analyst steps Chunk, Embed, Map, and Answer line up with this pipeline. Map retrieves and attaches passages. Answer runs the question analysis and evidence assignment.

::: report_analyst.core.workflow_engine.WorkflowStep

::: report_analyst.core.workflow_engine.WorkflowContext

::: report_analyst.core.workflow_engine.WorkflowEngine

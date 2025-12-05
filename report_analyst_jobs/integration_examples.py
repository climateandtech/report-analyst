"""
Integration Examples

Examples showing how to integrate the analysis toolkit into different execution environments.
Copy these patterns to integrate analysis into your own systems.
"""

import json
from typing import Any, Dict

# ===== AWS LAMBDA INTEGRATION =====


def lambda_handler(event, context):
    """
    AWS Lambda function handler.

    Deploy this function to AWS Lambda to process analysis jobs.

    Event format:
    {
        "document_id": "doc123",
        "question_set_id": "tcfd",
        "selected_questions": ["q1", "q2"],
        "model_name": "gpt-4o-mini",
        "use_search_backend": true,
        "configuration": {...}
    }
    """
    import asyncio

    from .analysis_toolkit import analyze_document_standalone

    try:
        # Extract parameters from event
        document_id = event["document_id"]
        question_set_id = event["question_set_id"]
        selected_questions = event["selected_questions"]
        model_name = event.get("model_name", "gpt-4o-mini")
        use_search_backend = event.get("use_search_backend", False)
        configuration = event.get("configuration", {})

        # Run analysis
        result = asyncio.run(
            analyze_document_standalone(
                document_id=document_id,
                question_set_id=question_set_id,
                selected_questions=selected_questions,
                model_name=model_name,
                use_search_backend=use_search_backend,
                configuration=configuration,
            )
        )

        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "status": "failed"}),
        }


# ===== CELERY INTEGRATION =====


def create_celery_tasks(celery_app):
    """
    Create Celery tasks for document analysis.

    Usage:
    from celery import Celery
    app = Celery('report-analyst')
    create_celery_tasks(app)

    # Then call:
    result = analyze_document_task.delay(doc_id, question_set_id, questions)
    """

    @celery_app.task(bind=True)
    def analyze_document_task(
        self,
        document_id: str,
        question_set_id: str,
        selected_questions: list,
        model_name: str = "gpt-4o-mini",
        use_search_backend: bool = False,
        configuration: dict = None,
    ):
        """Celery task for document analysis"""
        from .analysis_toolkit import analyze_document_sync

        try:
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"current": 0, "total": 100, "status": "Starting analysis"},
            )

            # Run analysis
            result = analyze_document_sync(
                document_id=document_id,
                question_set_id=question_set_id,
                selected_questions=selected_questions,
                model_name=model_name,
                use_search_backend=use_search_backend,
                configuration=configuration or {},
            )

            return result

        except Exception as e:
            self.update_state(state="FAILURE", meta={"error": str(e)})
            raise

    @celery_app.task(bind=True)
    def analyze_document_with_progress_task(
        self,
        document_id: str,
        question_set_id: str,
        selected_questions: list,
        model_name: str = "gpt-4o-mini",
        use_search_backend: bool = False,
        configuration: dict = None,
    ):
        """Celery task with progress reporting"""
        import asyncio

        from .analysis_toolkit import analyze_document_with_progress

        async def progress_callback(step, progress, message):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": int(progress * 100),
                    "total": 100,
                    "status": message,
                    "step": step,
                },
            )

        try:
            result = asyncio.run(
                analyze_document_with_progress(
                    document_id=document_id,
                    question_set_id=question_set_id,
                    selected_questions=selected_questions,
                    progress_callback=progress_callback,
                    model_name=model_name,
                    use_search_backend=use_search_backend,
                    configuration=configuration or {},
                )
            )

            return result

        except Exception as e:
            self.update_state(state="FAILURE", meta={"error": str(e)})
            raise


# ===== NATS INTEGRATION =====


async def nats_worker_handler(msg):
    """
    NATS message handler for document analysis.

    Usage:
    import nats

    nc = await nats.connect("nats://localhost:4222")
    await nc.subscribe("analysis.requests", cb=nats_worker_handler)
    """
    from .analysis_toolkit import analyze_document_standalone

    try:
        # Parse message
        data = json.loads(msg.data.decode())

        # Run analysis
        result = await analyze_document_standalone(
            document_id=data["document_id"],
            question_set_id=data["question_set_id"],
            selected_questions=data["selected_questions"],
            model_name=data.get("model_name", "gpt-4o-mini"),
            use_search_backend=data.get("use_search_backend", False),
            configuration=data.get("configuration", {}),
        )

        # Send result back
        if msg.reply:
            await msg.respond(json.dumps(result).encode())

    except Exception as e:
        error_response = {"status": "failed", "error": str(e)}
        if msg.reply:
            await msg.respond(json.dumps(error_response).encode())


# ===== FASTAPI BACKGROUND TASKS =====


def create_fastapi_endpoints(app):
    """
    Create FastAPI endpoints with background tasks.

    Usage:
    from fastapi import FastAPI
    app = FastAPI()
    create_fastapi_endpoints(app)
    """
    from fastapi import BackgroundTasks

    from .analysis_toolkit import analyze_document_sync

    @app.post("/analyze-document")
    async def analyze_document_endpoint(
        analysis_request: dict, background_tasks: BackgroundTasks
    ):
        """FastAPI endpoint with background task"""

        def run_analysis():
            result = analyze_document_sync(
                document_id=analysis_request["document_id"],
                question_set_id=analysis_request["question_set_id"],
                selected_questions=analysis_request["selected_questions"],
                model_name=analysis_request.get("model_name", "gpt-4o-mini"),
                use_search_backend=analysis_request.get("use_search_backend", False),
                configuration=analysis_request.get("configuration", {}),
            )
            # Store result somewhere (database, cache, etc.)
            print(f"Analysis completed: {result}")

        background_tasks.add_task(run_analysis)

        return {"message": "Analysis started", "status": "processing"}


# ===== SEARCH BACKEND INTEGRATION =====


class SearchBackendAnalysisIntegration:
    """
    Integration class for search backend.

    Usage:
    integration = SearchBackendAnalysisIntegration()
    result = await integration.analyze_document(doc_id, question_set_id, questions)
    """

    def __init__(self, search_backend_config: Dict[str, Any] = None):
        self.config = search_backend_config or {}

    async def analyze_document(
        self,
        document_id: str,
        question_set_id: str,
        selected_questions: list,
        model_name: str = "gpt-4o-mini",
        configuration: dict = None,
    ):
        """Analyze document using search backend for chunks"""
        from .analysis_toolkit import analyze_document_standalone

        return await analyze_document_standalone(
            document_id=document_id,
            question_set_id=question_set_id,
            selected_questions=selected_questions,
            model_name=model_name,
            use_search_backend=True,  # Always use search backend
            configuration=configuration or {},
        )

    def create_celery_task(self, celery_app):
        """Create Celery task for search backend"""

        @celery_app.task(bind=True)
        def search_backend_analysis_task(
            self,
            document_id: str,
            question_set_id: str,
            selected_questions: list,
            model_name: str = "gpt-4o-mini",
            configuration: dict = None,
        ):
            """Search backend analysis task"""
            import asyncio

            async def run_analysis():
                return await self.analyze_document(
                    document_id=document_id,
                    question_set_id=question_set_id,
                    selected_questions=selected_questions,
                    model_name=model_name,
                    configuration=configuration or {},
                )

            try:
                result = asyncio.run(run_analysis())
                return result
            except Exception as e:
                self.update_state(state="FAILURE", meta={"error": str(e)})
                raise

        return search_backend_analysis_task


# ===== SIMPLE SCRIPT INTEGRATION =====


def run_analysis_script():
    """
    Simple script example.

    Usage:
    python -c "from report_analyst_jobs.integration_examples import run_analysis_script; run_analysis_script()"
    """
    import asyncio

    from .analysis_toolkit import analyze_document_standalone

    async def main():
        result = await analyze_document_standalone(
            document_id="example_doc",
            question_set_id="tcfd",
            selected_questions=["governance_1", "strategy_1"],
            model_name="gpt-4o-mini",
            use_search_backend=False,
        )

        print(f"Analysis result: {result}")

    asyncio.run(main())


# ===== CONFIGURATION EXAMPLES =====

INTEGRATION_CONFIGS = {
    "lambda_deployment": {
        "description": "AWS Lambda deployment configuration",
        "runtime": "python3.9",
        "handler": "lambda_handler",
        "timeout": 300,
        "memory": 1024,
        "environment": {"REPORT_ANALYST_CONFIG": "/opt/config.json"},
    },
    "celery_deployment": {
        "description": "Celery worker configuration",
        "broker": "redis://localhost:6379",
        "backend": "redis://localhost:6379",
        "imports": ["report_analyst_jobs.integration_examples"],
        "task_routes": {
            "analyze_document_task": {"queue": "analysis"},
            "analyze_document_with_progress_task": {"queue": "analysis"},
        },
    },
    "nats_deployment": {
        "description": "NATS worker configuration",
        "servers": ["nats://localhost:4222"],
        "subjects": ["analysis.requests"],
        "queue_group": "analysis_workers",
    },
}

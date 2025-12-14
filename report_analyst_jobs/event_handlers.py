"""
Event Handlers for Event Router

Handler functions that can be referenced in event_routing.yaml
"""

import logging
from typing import Any, Dict

from report_analyst_jobs.event_router import EventContext
from report_analyst_jobs.nats_integration import DocumentReadyEvent

logger = logging.getLogger(__name__)


async def handle_document_ready(ctx: EventContext):
    """Handler for document.ready events"""
    try:
        event = DocumentReadyEvent(**ctx.data)
        logger.info(f"Processing document.ready for resource {event.resource_id}")

        # TODO: Integrate with existing document.ready processing logic
        # This could call the DocumentReadyProcessingConfig flow

        await ctx.message.ack()
    except Exception as e:
        logger.error(f"Error handling document.ready: {e}", exc_info=True)
        await ctx.message.ack()  # Ack even on error to avoid redelivery loops


async def handle_analysis_job(ctx: EventContext):
    """Handler for analysis.job.submit events"""
    try:
        job_data = ctx.data
        logger.info(f"Processing analysis job: {job_data.get('id')}")

        # TODO: Integrate with existing analysis job processing logic

        await ctx.message.ack()
    except Exception as e:
        logger.error(f"Error handling analysis job: {e}", exc_info=True)
        await ctx.message.ack()


async def handle_llm_request(ctx: EventContext):
    """Handler for llm.request events"""
    try:
        request_data = ctx.data
        logger.info(f"Processing LLM request: {request_data.get('request_id')}")

        # TODO: Integrate with existing LLM request processing logic

        await ctx.message.ack()
    except Exception as e:
        logger.error(f"Error handling LLM request: {e}", exc_info=True)
        await ctx.message.ack()


async def handle_external_service_ready(ctx: EventContext):
    """Handler for external.service.ready events"""
    try:
        service_data = ctx.data
        logger.info(
            f"Processing external service ready: {service_data.get('service_id')}"
        )

        # TODO: Integrate with existing external service handler

        await ctx.message.ack()
    except Exception as e:
        logger.error(f"Error handling external service ready: {e}", exc_info=True)
        await ctx.message.ack()


async def handle_external_service_analysis(ctx: EventContext):
    """Handler for external.service.analysis.request events"""
    try:
        request_data = ctx.data
        logger.info(
            f"Processing external service analysis request: {request_data.get('request_id')}"
        )

        # TODO: Integrate with existing external service analysis logic

        await ctx.message.ack()
    except Exception as e:
        logger.error(f"Error handling external service analysis: {e}", exc_info=True)
        await ctx.message.ack()

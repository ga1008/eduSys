import asyncio
from celery_app import celery_app
from app.core.llm_router import llm_router_instance
from app.llm_providers.base_provider import LLMRequest, Message as LLMMessage  # Renamed to avoid conflict
from app.schemas import AIRequest  # Keep AIRequest for API, LLMRequest for internal
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ai_service.generate_long_response",
                 default_retry_delay=60, max_retries=2,
                 time_limit=1800, soft_time_limit=1700)  # 30 min hard, 28 min soft
def generate_ai_response_task(self, request_data: dict):
    """
    Celery task to generate AI response.
    request_data is a dictionary representation of AIRequest.
    """
    logger.info(f"Celery task received: {request_data}")
    try:
        # Deserialize messages properly
        messages = [LLMMessage(**msg) for msg in request_data.get("messages", [])]

        llm_req = LLMRequest(
            messages=messages,
            model=request_data.get("model"),
            use_reasoning_model=request_data.get("use_reasoning_model", True),  # Default to reasoning for async
            stream=request_data.get("stream", False),  # Stream not really applicable for Celery result
            timeout=request_data.get("timeout", 1500),  # Longer timeout for Celery tasks
            max_tokens=request_data.get("max_tokens"),
            temperature=request_data.get("temperature"),
            response_format=request_data.get("response_format")
        )

        provider_name = request_data.get("provider")

        # Run the async function in an event loop for Celery
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            llm_router_instance.get_llm_response(llm_req, provider_name=provider_name)
        )
        # loop.close() # Avoid closing if other tasks might use it, or manage loop per task

        logger.info(f"Celery task result: {result.model_dump()}")
        return result.model_dump()  # Return Pydantic model as dict

    except Exception as e:
        logger.error(f"Celery task failed: {e}", exc_info=True)
        # self.retry(exc=e) # Celery's built-in retry mechanism
        # For now, just return error state
        return {
            "content": None,
            "error": f"Task execution failed: {str(e)}",
            "provider_name": provider_name,
            "model_used": llm_req.model or "default_reasoning"
        }

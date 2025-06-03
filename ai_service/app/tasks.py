# ai_service/app/tasks.py
# import asyncio # MODIFIED: Removed asyncio import
import logging

from app.core.config import settings
from app.core.llm_router import llm_router_instance
from app.llm_providers.base_provider import LLMRequest, Message as LLMMessage
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ai_service.generate_long_response",
                 default_retry_delay=60, max_retries=2,
                 time_limit=1800, soft_time_limit=1700)
def generate_ai_response_task(self, ai_payload: dict):
    """
    Celery task to generate AI response.
    ai_payload is a dictionary representation of an AIRequest model.
    """
    logger.info(f"Celery task received with payload: {ai_payload}")

    try:
        messages_data = ai_payload.get("messages", [])
        if not isinstance(messages_data, list):
            raise ValueError("Payload 'messages' field must be a list.")

        messages = [LLMMessage(**msg) for msg in messages_data]

        llm_req = LLMRequest(
            messages=messages,
            model=ai_payload.get("model"),
            use_reasoning_model=ai_payload.get("use_reasoning_model", True),
            stream=ai_payload.get("stream", False),
            timeout=ai_payload.get("timeout", 1500),
            max_tokens=ai_payload.get("max_tokens"),
            temperature=ai_payload.get("temperature"),
            response_format=ai_payload.get("response_format")
        )

        provider_name = ai_payload.get("provider")

        # MODIFIED: Directly call the synchronous method
        result_model_instance = llm_router_instance.get_llm_response(
            llm_req, provider_name=provider_name
        )

        logger.info(f"LLM响应已获取，准备返回结果")
        result_dict = result_model_instance.model_dump()
        logger.info(f"结果已序列化为字典")
        return result_dict

    except ValueError as ve:
        logger.error(f"Celery task failed due to ValueError: {ve}", exc_info=True)
        # Ensure the returned dict structure matches LLMResponse for consistency if possible
        # or a defined error structure for Celery tasks.
        return {
            "content": None,
            "error": f"Task input data error: {str(ve)}",
            "provider_name": ai_payload.get("provider"),
            "model_used": ai_payload.get("model") or (
                settings.DS_MODEL_R if ai_payload.get("use_reasoning_model") else settings.DS_MODEL)  # Example default
        }
    except Exception as e:
        logger.error(f"Celery task failed: {e}", exc_info=True)
        return {
            "content": None,
            "error": f"Task execution failed: {str(e)}",
            "provider_name": ai_payload.get("provider"),
            "model_used": ai_payload.get("model") or (
                settings.DS_MODEL_R if ai_payload.get("use_reasoning_model") else settings.DS_MODEL)  # Example default
        }

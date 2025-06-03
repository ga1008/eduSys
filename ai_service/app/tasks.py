# ai_service/app/tasks.py
import asyncio
# AIRequest 是在 schemas.py 中定义的，用于 FastAPI 的请求体模型
# from .schemas import AIRequest # 这个导入在当前任务中不是直接使用，但保持清晰
import logging

from app.core.llm_router import llm_router_instance
# LLMMessage 是在 base_provider.py 中定义的 Pydantic 模型，用于消息结构
from app.llm_providers.base_provider import LLMRequest, Message as LLMMessage
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ai_service.generate_long_response",
                 default_retry_delay=60, max_retries=2,
                 time_limit=1800, soft_time_limit=1700)
def generate_ai_response_task(self, ai_payload: dict):  # 参数名修改为 ai_payload 以更清晰
    """
    Celery task to generate AI response.
    ai_payload is a dictionary representation of an AIRequest model.
    """
    # submission_id 不会直接传递到这个AI服务的Celery任务中，除非AIRequest模型包含它
    # Django后端在收到task_id后，会将task_id与submission_id关联起来
    logger.info(f"Celery task received with payload: {ai_payload}")

    try:
        messages_data = ai_payload.get("messages", [])
        if not isinstance(messages_data, list):
            raise ValueError("Payload 'messages' field must be a list.")

        messages = [LLMMessage(**msg) for msg in messages_data]

        llm_req = LLMRequest(
            messages=messages,
            model=ai_payload.get("model"),
            use_reasoning_model=ai_payload.get("use_reasoning_model", True),  # 默认为True，因为通常异步用于推理模型
            stream=ai_payload.get("stream", False),
            timeout=ai_payload.get("timeout", 1500),  # 给异步任务更长的超时
            max_tokens=ai_payload.get("max_tokens"),
            temperature=ai_payload.get("temperature"),
            response_format=ai_payload.get("response_format")
        )

        provider_name = ai_payload.get("provider")

        result_model_instance = asyncio.run(
            llm_router_instance.get_llm_response(llm_req, provider_name=provider_name)
        )

        logger.info(f"Celery task processed. Result: {result_model_instance.model_dump(exclude_none=True)}")
        return result_model_instance.model_dump()

    except ValueError as ve:
        logger.error(f"Celery task failed due to ValueError: {ve}", exc_info=True)
        return {
            "content": None,
            "error": f"Task input data error: {str(ve)}",
            "provider_name": ai_payload.get("provider"),
            "model_used": ai_payload.get("model") or (
                "default_reasoning" if ai_payload.get("use_reasoning_model") else "default")
        }
    except Exception as e:
        logger.error(f"Celery task failed: {e}", exc_info=True)
        return {
            "content": None,
            "error": f"Task execution failed: {str(e)}",
            "provider_name": ai_payload.get("provider"),
            "model_used": ai_payload.get("model") or (
                "default_reasoning" if ai_payload.get("use_reasoning_model") else "default")
        }

# ai_service/app/tasks.py
import asyncio
from ..celery_app import celery_app
from .core.llm_router import llm_router_instance
# LLMMessage 是在 base_provider.py 中定义的 Pydantic 模型，用于消息结构
from .llm_providers.base_provider import LLMRequest, Message as LLMMessage
# AIRequest 是在 schemas.py 中定义的，用于 FastAPI 的请求体模型
# from .schemas import AIRequest # 这个导入在当前任务中不是直接使用，但保持清晰
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ai_service.generate_long_response",
                 default_retry_delay=60, max_retries=2,
                 time_limit=1800, soft_time_limit=1700)
def generate_ai_response_task(self, request_data: dict):
    """
    Celery task to generate AI response.
    request_data is a dictionary representation of an object similar to AIRequest.
    """
    logger.info(
        f"Celery task received for submission_id {request_data.get('submission_id')}: {request_data.get('request_data')}")  # 调整日志输出

    # 从 request_data 中获取真正的 AI 请求体
    actual_ai_payload = request_data.get("request_data")
    if not actual_ai_payload:
        logger.error("Celery task failed: 'request_data' key missing in task payload.")
        return {
            "content": None,
            "error": "Task payload missing 'request_data'.",
            "provider_name": None,
            "model_used": None
        }

    submission_id_for_log = request_data.get('submission_id', 'Unknown')

    try:
        # 反序列化消息
        messages_data = actual_ai_payload.get("messages", [])
        if not isinstance(messages_data, list):  # 基本类型检查
            raise ValueError("Payload 'messages' field must be a list.")

        messages = [LLMMessage(**msg) for msg in messages_data]

        llm_req = LLMRequest(
            messages=messages,
            model=actual_ai_payload.get("model"),
            use_reasoning_model=actual_ai_payload.get("use_reasoning_model", True),
            stream=actual_ai_payload.get("stream", False),
            timeout=actual_ai_payload.get("timeout", 1500),
            max_tokens=actual_ai_payload.get("max_tokens"),
            temperature=actual_ai_payload.get("temperature"),
            response_format=actual_ai_payload.get("response_format")
        )

        provider_name = actual_ai_payload.get("provider")

        # 使用 asyncio.run() 来执行异步函数
        # 这会自动处理事件循环的创建和关闭
        # 注意: asyncio.run() 不能在已经运行的事件循环中调用。
        # Celery + eventlet 通常不会在 worker 的主执行路径中运行 asyncio 循环。
        result_model_instance = asyncio.run(
            llm_router_instance.get_llm_response(llm_req, provider_name=provider_name)
        )

        logger.info(
            f"Celery task for submission_id {submission_id_for_log} result: {result_model_instance.model_dump(exclude_none=True)}")
        return result_model_instance.model_dump()  # 返回Pydantic模型为字典

    except ValueError as ve:  # 更具体的错误捕获，例如Pydantic验证错误
        logger.error(f"Celery task for submission_id {submission_id_for_log} failed due to ValueError: {ve}",
                     exc_info=True)
        return {
            "content": None,
            "error": f"Task input data error: {str(ve)}",
            "provider_name": actual_ai_payload.get("provider"),  # 尝试从原始payload获取
            "model_used": actual_ai_payload.get("model") or (
                "default_reasoning" if actual_ai_payload.get("use_reasoning_model") else "default")
        }
    except Exception as e:
        logger.error(f"Celery task for submission_id {submission_id_for_log} failed: {e}", exc_info=True)
        # self.retry(exc=e) # 可以启用Celery的内置重试
        return {
            "content": None,
            "error": f"Task execution failed: {str(e)}",
            "provider_name": actual_ai_payload.get("provider"),  # 尝试从原始payload获取
            "model_used": actual_ai_payload.get("model") or (
                "default_reasoning" if actual_ai_payload.get("use_reasoning_model") else "default")
        }
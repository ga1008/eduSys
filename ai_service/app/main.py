from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import uvicorn

from app.core.config import settings  # Ensure this path is correct
from app.core.llm_router import llm_router_instance
from app.schemas import AIRequest, AIResponse, MessageInput, HealthCheckResponse
from app.llm_providers.base_provider import LLMRequest as InternalLLMRequest, Message as InternalMessage
from app.tasks import generate_ai_response_task
from celery_app import celery_app  # Import celery_app for task status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Auxiliary Service", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    logger.info("AI Service starting up...")
    logger.info(f"Loaded settings. Default timeout: {settings.DEFAULT_TIMEOUT}s")
    if not llm_router_instance.providers:
        logger.error("CRITICAL: No LLM providers were initialized on startup!")
    else:
        logger.info(f"Initialized {len(llm_router_instance.providers)} LLM providers.")
        for provider in llm_router_instance.providers:
            logger.info(f"Provider loaded: {getattr(provider, 'provider_name', 'UnknownProvider')} "
                        f"- Default: {provider.default_model}, Reasoning: {provider.reasoning_model}")


@app.post("/api/v1/chat/completions", response_model=AIResponse)
async def chat_completions(request: AIRequest = Body(...)):
    logger.info(f"Received API request: {request.model_dump(exclude_none=True)}")

    internal_messages = [InternalMessage(**msg.model_dump()) for msg in request.messages]
    llm_req = InternalLLMRequest(
        messages=internal_messages,
        model=request.model,
        use_reasoning_model=request.use_reasoning_model,
        stream=request.stream,  # For synchronous, stream is typically False
        timeout=request.timeout or (30 if not request.use_reasoning_model else settings.DEFAULT_TIMEOUT),
        # Shorter for non-reasoning
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        response_format=request.response_format
    )

    if request.use_reasoning_model or (request.timeout and request.timeout > 60):  # Threshold for using Celery
        # For long tasks, use Celery. The API key is in .env, Celery worker will load it.
        # Send dict representation of AIRequest to Celery task
        task = generate_ai_response_task.apply_async(
            args=[request.model_dump(exclude_none=True)],
            queue='ai_long_running_queue'  # Route to the long running queue
        )
        logger.info(f"Dispatched to Celery task ID: {task.id}")
        return AIResponse(
            success=True,
            task_id=task.id,
            content="Task dispatched for long processing. Check status with task_id."
        )
    else:
        # For short tasks, process synchronously
        response = await llm_router_instance.get_llm_response(llm_req, provider_name=request.provider)
        if response.error:
            # Consider raising HTTPException for specific errors
            logger.error(f"Error from LLM router: {response.error}")
            return AIResponse(
                success=False,
                error=response.error,
                provider_name=response.provider_name,
                model_used=response.model_used
            )
        return AIResponse(
            success=True,
            content=response.content,
            provider_name=response.provider_name,
            model_used=response.model_used
        )


@app.get("/api/v1/task_status/{task_id}", response_model=AIResponse)
async def get_task_status(task_id: str):
    task_result = celery_app.AsyncResult(task_id)
    if task_result.ready():
        if task_result.successful():
            result_data = task_result.result  # This should be the dict from the task
            return AIResponse(
                success=True,
                content=result_data.get("content"),
                error=result_data.get("error"),
                provider_name=result_data.get("provider_name"),
                model_used=result_data.get("model_used"),
                task_id=task_id
            )
        else:
            # Task failed, result might be an exception object or the dict we returned on failure
            error_info = str(task_result.result) if task_result.result else "Task failed with no specific error."
            try:
                # If task returns a dict on failure
                failure_details = task_result.result if isinstance(task_result.result, dict) else {}
                error_info = failure_details.get("error", error_info)
            except Exception:
                pass  # Keep original error_info
            logger.error(
                f"Celery Task {task_id} failed. Result: {task_result.result}, Traceback: {task_result.traceback}")
            return AIResponse(success=False, error=f"Task failed: {error_info}", task_id=task_id)
    else:
        return AIResponse(success=False, error="Task not ready or does not exist.",
                          content=f"Status: {task_result.status}", task_id=task_id)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    active_providers_names = [
        getattr(p, 'provider_name', 'UnknownProvider') for p in llm_router_instance.providers if p.api_key
        # Check if API key is loaded
    ]
    if not active_providers_names and llm_router_instance.providers:  # Providers exist but no keys
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy",
                     "detail": "No active LLM providers due to missing API keys or initialization issues.",
                     "active_providers": []}
        )
    elif not llm_router_instance.providers:  # No providers at all
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "detail": "No LLM providers loaded.", "active_providers": []}
        )
    return HealthCheckResponse(active_providers=active_providers_names)

# For local debugging:
# if __name__ == "__main__":
#     # Ensure .env is loaded relative to this script if run directly for testing
#     # This is typically handled by the main execution context (e.g. when you run uvicorn from project root)
#     # from dotenv import load_dotenv as load_env_local
#     # import os
#     # script_dir = os.path.dirname(os.path.abspath(__file__))
#     # project_root_for_main = os.path.dirname(os.path.dirname(script_dir)) # up two levels for eduSys/.env
#     # env_path_for_main = os.path.join(project_root_for_main, '.env')
#     # if os.path.exists(env_path_for_main):
#     #     load_env_local(env_path_for_main)
#     #     print(f"Developer mode: Loaded .env from {env_path_for_main}")
#     # else:
#     #     print(f"Developer mode: .env not found at {env_path_for_main}")

#     uvicorn.run(app, host="0.0.0.0", port=8080)

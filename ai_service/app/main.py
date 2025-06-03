from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import uvicorn

from app.core.config import settings
from app.core.llm_router import llm_router_instance
from app.schemas import AIRequest, AIResponse, MessageInput, HealthCheckResponse
from app.llm_providers.base_provider import LLMRequest as InternalLLMRequest, Message as InternalMessage
from app.tasks import generate_ai_response_task
from celery_app import celery_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Auxiliary Service", version="0.1.0")


@app.on_event("startup")
async def startup_event():  # This can remain async, not directly calling the modified LLM logic
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
async def chat_completions(request: AIRequest = Body(...)):  # Endpoint can remain async
    logger.info(f"Received API request: {request.model_dump(exclude_none=True)}")

    internal_messages = [InternalMessage(**msg.model_dump()) for msg in request.messages]
    llm_req = InternalLLMRequest(
        messages=internal_messages,
        model=request.model,
        use_reasoning_model=request.use_reasoning_model,
        stream=request.stream,
        timeout=request.timeout or (30 if not request.use_reasoning_model else settings.DEFAULT_TIMEOUT),
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        response_format=request.response_format
    )

    if request.use_reasoning_model or (request.timeout and request.timeout > 60):
        task = generate_ai_response_task.apply_async(
            args=[request.model_dump(exclude_none=True)],
            queue='ai_long_running_queue'
        )
        logger.info(f"Dispatched to Celery task ID: {task.id}")
        return AIResponse(
            success=True,
            task_id=task.id,
            content="Task dispatched for long processing. Check status with task_id."
        )
    else:
        # MODIFIED: Removed await for the synchronous call
        response = llm_router_instance.get_llm_response(llm_req, provider_name=request.provider)
        if response.error:
            logger.error(f"Error from LLM router: {response.error}")
            # Return 500 for internal LLM errors for clearer client-side handling
            # HTTPException might be better here if you want FastAPI to handle status codes directly
            return JSONResponse(
                status_code=500,  # Or a more specific error code
                content=AIResponse(
                    success=False,
                    error=response.error,
                    provider_name=response.provider_name,
                    model_used=response.model_used
                ).model_dump(exclude_none=True)
            )
        return AIResponse(
            success=True,
            content=response.content,
            provider_name=response.provider_name,
            model_used=response.model_used
        )


@app.get("/api/v1/task_status/{task_id}", response_model=AIResponse)
async def get_task_status(task_id: str):  # This can remain async
    task_result = celery_app.AsyncResult(task_id)
    if task_result.ready():
        if task_result.successful():
            result_data = task_result.result
            return AIResponse(
                success=True,
                content=result_data.get("content"),
                error=result_data.get("error"),
                provider_name=result_data.get("provider_name"),
                model_used=result_data.get("model_used"),
                task_id=task_id
            )
        else:
            error_info = str(task_result.result) if task_result.result else "Task failed with no specific error."
            failure_details = {}
            if isinstance(task_result.result, dict):
                failure_details = task_result.result
            elif hasattr(task_result.result, 'args') and task_result.result.args:  # type: ignore
                error_info = str(task_result.result.args[0])  # type: ignore

            final_error_message = failure_details.get("error", error_info)
            logger.error(
                f"Celery Task {task_id} failed. Result: {task_result.result}, Traceback: {task_result.traceback}")
            return AIResponse(success=False, error=f"Task failed: {final_error_message}", task_id=task_id,
                              provider_name=failure_details.get("provider_name"),
                              model_used=failure_details.get("model_used"))
    else:
        return AIResponse(success=False, error="Task not ready or does not exist.",
                          content=f"Status: {task_result.status}", task_id=task_id)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():  # This can remain async
    active_providers_names = [
        getattr(p, 'provider_name', 'UnknownProvider') for p in llm_router_instance.providers if p.api_key
    ]
    if not active_providers_names and llm_router_instance.providers:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy",
                     "detail": "No active LLM providers due to missing API keys or initialization issues.",
                     "active_providers": []}
        )
    elif not llm_router_instance.providers:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "detail": "No LLM providers loaded.", "active_providers": []}
        )
    return HealthCheckResponse(active_providers=active_providers_names)

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8080)

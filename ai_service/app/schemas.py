from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict


class MessageInput(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class AIRequest(BaseModel):
    messages: List[MessageInput] = Field(...,
                                         description="List of message objects, e.g., [{'role': 'system', 'content': 'You are an assistant.'}, {'role': 'user', 'content': 'Hello!'}]")
    provider: Optional[str] = Field(None,
                                    description="Specify AI provider (e.g., 'DeepSeek', 'SiliconFlow', 'VolcEngine'). If None, will use a default.")
    model: Optional[str] = Field(None,
                                 description="Specify a model name. Overrides provider's default or reasoning model selection.")
    use_reasoning_model: bool = Field(False,
                                      description="Set to true to use the provider's designated reasoning model (MODEL_R).")
    stream: bool = Field(False,
                         description="Whether to use streaming response. (Currently placeholder for Celery, FastAPI synchronous calls won't stream)")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds.")
    max_tokens: Optional[int] = Field(None, description="Max tokens to generate.")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature.")
    response_format: Optional[Dict[str, str]] = Field(None,
                                                      description="OpenAI style response_format, e.g. {\"type\": \"json_object\"}")


class AIResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    provider_name: Optional[str] = None
    model_used: Optional[str] = None
    task_id: Optional[str] = None  # For Celery tasks


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    active_providers: List[str]

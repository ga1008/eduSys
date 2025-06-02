from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None  # 如果不提供，则使用Provider的默认模型
    use_reasoning_model: bool = False  # 是否使用推理能力更强的模型 (MODEL_R)
    stream: bool = False
    timeout: Optional[int] = None  # 请求超时时间
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    response_format: Optional[Dict[str, str]] = None  # e.g. {"type": "json_object"}


class LLMResponse(BaseModel):
    content: Optional[str] = None
    error: Optional[str] = None
    provider_name: Optional[str] = None
    model_used: Optional[str] = None


class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, base_url: str, default_model: str, reasoning_model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.reasoning_model = reasoning_model

    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        pass

    def get_model_name(self, use_reasoning_model: bool) -> str:
        return self.reasoning_model if use_reasoning_model else self.default_model

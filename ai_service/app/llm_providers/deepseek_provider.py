from openai import OpenAI, AsyncOpenAI
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse, Message
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            api_key=settings.DS_API_KEY,
            base_url=settings.DS_BASE_URL,
            default_model=settings.DS_MODEL,
            reasoning_model=settings.DS_MODEL_R
        )
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.provider_name = "DeepSeek"

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        model_to_use = request.model or self.get_model_name(request.use_reasoning_model)
        messages_dict = [msg.model_dump() for msg in request.messages]

        try:
            logger.info(f"[{self.provider_name}] Requesting model: {model_to_use} with messages: {messages_dict}")
            completion = await self.client.chat.completions.create(
                model=model_to_use,
                messages=messages_dict,
                stream=request.stream,  # 流式输出暂未完全支持，此处仅传递参数
                timeout=request.timeout or settings.DEFAULT_TIMEOUT,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                response_format=request.response_format
            )
            content = completion.choices[0].message.content
            logger.info(f"[{self.provider_name}] Response: {content[:200]}...")  # Log first 200 chars
            return LLMResponse(content=content, provider_name=self.provider_name, model_used=model_to_use)
        except Exception as e:
            logger.error(f"[{self.provider_name}] Error generating response: {e}")
            return LLMResponse(error=str(e), provider_name=self.provider_name, model_used=model_to_use)

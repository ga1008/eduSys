from openai import AsyncOpenAI
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse, Message
from app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)


class VolcEngineProvider(BaseLLMProvider):
    def __init__(self):
        # VolcEngine SDK uses ARK_API_KEY from env
        # Ensure it's set in config.py or here
        if not os.getenv("ARK_API_KEY") and settings.VC_API_KEY:
            os.environ["ARK_API_KEY"] = settings.VC_API_KEY

        super().__init__(
            api_key=os.getenv("ARK_API_KEY", settings.VC_API_KEY),  # API key is read from env by SDK
            base_url=settings.VC_BASE_URL,
            default_model=settings.VC_MODEL,
            reasoning_model=settings.VC_MODEL_R
        )
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.provider_name = "VolcEngine"

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        model_to_use = request.model or self.get_model_name(request.use_reasoning_model)
        messages_dict = [msg.model_dump() for msg in request.messages]

        try:
            logger.info(f"[{self.provider_name}] Requesting model: {model_to_use} with messages: {messages_dict}")
            completion = await self.client.chat.completions.create(
                model=model_to_use,
                messages=messages_dict,
                stream=request.stream,
                timeout=request.timeout or settings.DEFAULT_TIMEOUT,
                max_tokens=request.max_tokens,
                temperature=request.temperature
                # VolcEngine SDK might not support response_format in the same way
            )
            content = completion.choices[0].message.content
            logger.info(f"[{self.provider_name}] Response: {content[:200]}...")
            return LLMResponse(content=content, provider_name=self.provider_name, model_used=model_to_use)
        except Exception as e:
            logger.error(f"[{self.provider_name}] Error generating response: {e}")
            return LLMResponse(error=str(e), provider_name=self.provider_name, model_used=model_to_use)

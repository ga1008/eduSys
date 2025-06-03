from openai import OpenAI  # MODIFIED: Import synchronous OpenAI client
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse, Message
from app.core.config import settings
import os
import logging

logger = logging.getLogger(__name__)


class VolcEngineProvider(BaseLLMProvider):
    def __init__(self):
        if not os.getenv("ARK_API_KEY") and settings.VC_API_KEY:
            os.environ["ARK_API_KEY"] = settings.VC_API_KEY

        super().__init__(
            api_key=os.getenv("ARK_API_KEY", settings.VC_API_KEY),
            base_url=settings.VC_BASE_URL,
            default_model=settings.VC_MODEL,
            reasoning_model=settings.VC_MODEL_R
        )
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)  # MODIFIED: Use synchronous client
        self.provider_name = "VolcEngine"

    def generate_response(self, request: LLMRequest) -> LLMResponse:  # MODIFIED: Removed async
        model_to_use = request.model or self.get_model_name(request.use_reasoning_model)
        messages_dict = [msg.model_dump() for msg in request.messages]

        try:
            logger.info(f"[{self.provider_name}] Requesting model: {model_to_use} with messages: {messages_dict}")
            completion = self.client.chat.completions.create(  # MODIFIED: Removed await
                model=model_to_use,
                messages=messages_dict,  # type: ignore
                stream=request.stream,
                timeout=request.timeout or settings.DEFAULT_TIMEOUT,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            content = completion.choices[0].message.content
            logger.info(f"[{self.provider_name}] Response: {content[:200]}...")
            return LLMResponse(content=content, provider_name=self.provider_name, model_used=model_to_use)
        except Exception as e:
            logger.error(f"[{self.provider_name}] Error generating response: {e}")
            return LLMResponse(error=str(e), provider_name=self.provider_name, model_used=model_to_use)


if __name__ == "__main__":
    # import asyncio # MODIFIED: Not needed for sync test

    # async def test_volcengine(): # MODIFIED: No longer async
    def test_volcengine_sync():
        provider = VolcEngineProvider()
        request_data = LLMRequest(
            messages=[Message(role="user", content="Hello, 你好吗?")],
            model=settings.VC_MODEL,  # Use model from settings for consistency
            use_reasoning_model=False,
            stream=False,
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
        response = provider.generate_response(request_data)  # MODIFIED: Direct call
        print(response)


    test_volcengine_sync()  # MODIFIED: Call sync function

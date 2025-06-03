from openai import OpenAI  # MODIFIED: Import synchronous OpenAI client
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse, Message
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SiliconFlowProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            api_key=settings.SF_API_KEY,
            base_url=settings.SF_BASE_URL,
            default_model=settings.SF_MODEL,
            reasoning_model=settings.SF_MODEL_R
        )
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)  # MODIFIED: Use synchronous client
        self.provider_name = "SiliconFlow"

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
                temperature=request.temperature,
                response_format=request.response_format
            )
            content = completion.choices[0].message.content
            logger.info(f"[{self.provider_name}] Response: {content[:200]}...")
            return LLMResponse(content=content, provider_name=self.provider_name, model_used=model_to_use)
        except Exception as e:
            logger.error(f"[{self.provider_name}] Error generating response: {e}")
            return LLMResponse(error=str(e), provider_name=self.provider_name, model_used=model_to_use)


if __name__ == "__main__":
    # import asyncio # MODIFIED: Not needed for sync test

    # async def test_siliconflow(): # MODIFIED: No longer async
    def test_siliconflow_sync():
        provider = SiliconFlowProvider()
        request_data = LLMRequest(
            messages=[Message(role="user", content="Hello, 你好吗?")],
            model="Pro/deepseek-ai/DeepSeek-V3",  # Ensure this model is available or use settings
            use_reasoning_model=False,
            stream=False,
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
        response = provider.generate_response(request_data)  # MODIFIED: Direct call
        print(response)


    test_siliconflow_sync()  # MODIFIED: Call sync function

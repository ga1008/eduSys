import logging
import re

from bs4 import BeautifulSoup
from openai import OpenAI  # MODIFIED: Import synchronous OpenAI client

from app.core.config import settings
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


def strip_html_tags(html_content: str) -> str:
    """
    Strips HTML tags from content and attempts to retain basic text structure.
    """
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        for p_tag in soup.find_all('p'):
            p_tag.append('\n')
        for br_tag in soup.find_all('br'):
            br_tag.replace_with('\n')

        plain_text = soup.get_text(separator=' ')
        plain_text = re.sub(r'\s*\n\s*', '\n', plain_text)
        plain_text = re.sub(r'[ \t]+', ' ', plain_text)
        return plain_text.strip()
    except Exception as e:
        logger.warning(f"BeautifulSoup failed to parse HTML: {e}. Returning raw content.")
        return html_content


class DeepSeekProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(
            api_key=settings.DS_API_KEY,
            base_url=settings.DS_BASE_URL,
            default_model=settings.DS_MODEL,
            reasoning_model=settings.DS_MODEL_R
        )
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)  # MODIFIED: Use synchronous client
        self.provider_name = "DeepSeek"

    def generate_response(self, request: LLMRequest) -> LLMResponse:  # MODIFIED: Removed async
        model_to_use = request.model or self.get_model_name(request.use_reasoning_model)

        processed_messages_for_api = []
        for msg in request.messages:
            content_to_send = msg.content
            if request.response_format and request.response_format.get("type") == "json_object":
                if msg.role in ["system", "user"]:
                    stripped_content = strip_html_tags(msg.content)
                    if msg.role == "system" and stripped_content != msg.content:
                        logger.info(
                            f"[{self.provider_name}] System prompt (HTML stripped for JSON mode): {stripped_content[:300]}...")
                    content_to_send = stripped_content
            processed_messages_for_api.append({"role": msg.role, "content": content_to_send})

        logger.info(
            f"[{self.provider_name}] Requesting model: {model_to_use} with processed messages: {processed_messages_for_api}")

        try:
            completion = self.client.chat.completions.create(  # MODIFIED: Removed await
                model=model_to_use,
                messages=processed_messages_for_api,
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
            logger.error(f"[{self.provider_name}] Error generating response: {e}", exc_info=True)
            error_detail = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):  # type: ignore
                error_detail = f"Status {e.response.status_code}: {e.response.text}"  # type: ignore
            elif hasattr(e, 'message'):  # type: ignore
                error_detail = e.message  # type: ignore

            return LLMResponse(error=error_detail, provider_name=self.provider_name, model_used=model_to_use)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # from app.core.config import settings # settings is already imported above

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(BASE_DIR)
    load_dotenv(os.path.join(BASE_DIR, '.env'))

    provider = DeepSeekProvider()
    test_request = LLMRequest(
        messages=[
            {"role": "system", "content": "<p>这是一个系统提示</p>"},  # type: ignore
            {"role": "user", "content": "<p>请帮我生成一个响应</p>"}  # type: ignore
        ],
        model="deepseek-chat",
        use_reasoning_model=False,
        stream=False,
        timeout=30,
        max_tokens=100,
        temperature=0.7
    )

    # import asyncio # MODIFIED: Not needed for sync test
    response = provider.generate_response(test_request)  # MODIFIED: Direct call
    print(response)

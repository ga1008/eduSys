import random
import time  # MODIFIED: Import time for sleep
from typing import List, Optional
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse
from app.llm_providers import get_provider_instances
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self):
        self.providers: List[BaseLLMProvider] = get_provider_instances()
        if not self.providers:
            logger.error("No LLM providers initialized. AI service will not function.")
        self.current_provider_index = 0  # For round-robin

    # MODIFIED: Changed from async def to def
    def get_llm_response(self, request: LLMRequest, provider_name: Optional[str] = None) -> LLMResponse:
        if not self.providers:
            return LLMResponse(error="No LLM providers available.")

        selected_providers: List[BaseLLMProvider] = []

        if provider_name:
            for p in self.providers:
                if hasattr(p, 'provider_name') and p.provider_name.lower() == provider_name.lower():
                    selected_providers = [p]
                    break
            if not selected_providers:
                return LLMResponse(error=f"Provider '{provider_name}' not found or not initialized.")
        else:
            start_index = self.current_provider_index
            for i in range(len(self.providers)):
                idx = (start_index + i) % len(self.providers)
                selected_providers.append(self.providers[idx])
            self.current_provider_index = (start_index + 1) % len(self.providers)

        last_error = "No providers attempted."
        for attempt in range(settings.RETRY_ATTEMPTS + 1):
            for provider_to_try in selected_providers:
                logger.info(
                    f"Attempt {attempt + 1}/{settings.RETRY_ATTEMPTS + 1} using provider: {getattr(provider_to_try, 'provider_name', 'UnknownProvider')}")
                try:
                    # MODIFIED: Removed await as provider's generate_response is now synchronous
                    response = provider_to_try.generate_response(request)
                    if response.content and not response.error:
                        return response
                    else:
                        last_error = response.error or "Provider returned empty content."
                        logger.warning(
                            f"Provider {getattr(provider_to_try, 'provider_name', 'UnknownProvider')} failed: {last_error}")
                except Exception as e:
                    last_error = str(e)
                    logger.error(
                        f"Exception with provider {getattr(provider_to_try, 'provider_name', 'UnknownProvider')}: {last_error}",
                        exc_info=True)  # Added exc_info for better debugging

                if provider_name and getattr(provider_to_try, 'provider_name', '').lower() == provider_name.lower():
                    if attempt < settings.RETRY_ATTEMPTS:
                        time.sleep(1)  # MODIFIED: Replaced asyncio.sleep with time.sleep
                        continue
                    else:
                        return LLMResponse(
                            error=f"Provider {provider_name} failed after {settings.RETRY_ATTEMPTS + 1} attempts: {last_error}")

            if not provider_name and attempt < settings.RETRY_ATTEMPTS:
                logger.info(f"All providers in current selection failed. Retrying (attempt {attempt + 2})...")
                time.sleep(1)  # MODIFIED: Replaced asyncio.sleep with time.sleep
            elif not provider_name:
                break

        return LLMResponse(error=f"All attempts failed. Last error: {last_error}")


llm_router_instance = LLMRouter()

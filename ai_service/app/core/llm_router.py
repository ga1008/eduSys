import random
import asyncio
from typing import List, Optional
from app.llm_providers.base_provider import BaseLLMProvider, LLMRequest, LLMResponse
from app.llm_providers import get_provider_instances  # Import the function
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self):
        self.providers: List[BaseLLMProvider] = get_provider_instances()  # Initialize here
        if not self.providers:
            logger.error("No LLM providers initialized. AI service will not function.")
            # raise RuntimeError("No LLM providers could be initialized.")
        self.current_provider_index = 0  # For round-robin

    async def get_llm_response(self, request: LLMRequest, provider_name: Optional[str] = None) -> LLMResponse:
        if not self.providers:
            return LLMResponse(error="No LLM providers available.")

        selected_providers: List[BaseLLMProvider] = []

        if provider_name:
            for p in self.providers:
                # Assuming provider_name attribute is set in each provider class
                if hasattr(p, 'provider_name') and p.provider_name.lower() == provider_name.lower():
                    selected_providers = [p]
                    break
            if not selected_providers:
                return LLMResponse(error=f"Provider '{provider_name}' not found or not initialized.")
        else:
            # Simple round-robin for default provider selection if no specific one is requested
            # Start with the current_provider_index and try all available in order
            start_index = self.current_provider_index
            for i in range(len(self.providers)):
                idx = (start_index + i) % len(self.providers)
                selected_providers.append(self.providers[idx])
            # Update current_provider_index for next call for better distribution
            self.current_provider_index = (start_index + 1) % len(self.providers)

        last_error = "No providers attempted."
        for attempt in range(settings.RETRY_ATTEMPTS + 1):  # Initial attempt + retries
            for provider_to_try in selected_providers:  # Try chosen provider or iterate through for fallback
                logger.info(
                    f"Attempt {attempt + 1}/{settings.RETRY_ATTEMPTS + 1} using provider: {getattr(provider_to_try, 'provider_name', 'UnknownProvider')}")
                try:
                    response = await provider_to_try.generate_response(request)
                    if response.content and not response.error:
                        return response
                    else:
                        last_error = response.error or "Provider returned empty content."
                        logger.warning(
                            f"Provider {getattr(provider_to_try, 'provider_name', 'UnknownProvider')} failed: {last_error}")
                except Exception as e:
                    last_error = str(e)
                    logger.error(
                        f"Exception with provider {getattr(provider_to_try, 'provider_name', 'UnknownProvider')}: {last_error}")

                # If a specific provider was requested and failed, don't try others unless for retries on the same provider
                if provider_name and getattr(provider_to_try, 'provider_name', '').lower() == provider_name.lower():
                    if attempt < settings.RETRY_ATTEMPTS:  # Only retry on the same provider if specified
                        await asyncio.sleep(1)  # Simple backoff
                        continue  # Retry the same provider
                    else:
                        return LLMResponse(
                            error=f"Provider {provider_name} failed after multiple attempts: {last_error}")

            # If no specific provider was named, and we are in a retry loop with multiple providers
            if not provider_name and attempt < settings.RETRY_ATTEMPTS:
                logger.info(f"All providers in current selection failed. Retrying (attempt {attempt + 2})...")
                await asyncio.sleep(1)  # Simple backoff
            elif not provider_name:  # exhausted retries on all providers
                break

        return LLMResponse(error=f"All attempts failed. Last error: {last_error}")


llm_router_instance = LLMRouter()

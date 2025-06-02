from app.llm_providers.deepseek_provider import DeepSeekProvider
from app.llm_providers.siliconflow_provider import SiliconFlowProvider
from app.llm_providers.volcengine_provider import VolcEngineProvider

# List of available providers
# Order matters for default selection or round-robin
PROVIDER_CLASSES = [
    DeepSeekProvider,
    SiliconFlowProvider,
    VolcEngineProvider,
]


def get_provider_instances():
    instances = []
    for provider_class in PROVIDER_CLASSES:
        try:
            instances.append(provider_class())
        except Exception as e:
            print(f"Failed to initialize provider {provider_class.__name__}: {e}")
    return instances

# Initialize providers once
# providers = get_provider_instances() # This might be better done in llm_router or main app setup

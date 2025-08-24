"""
AI Model Adapters Package
Unified adapter supporting multiple domestic and international AI models
"""

from .base_adapter import (
    BaseAPIAdapter,
    ModelProvider,
    ModelConfig,
    APIMessage,
    APIResponse,
    AdapterFactory,
    PREDEFINED_MODELS,
    get_model_config,
    get_provider_models
)

# Import all adapter implementations to trigger automatic registration
from .deepseek_adapter import DeepSeekAdapter
from .qwen_adapter import QwenAdapter
from .kimi_adapter import KimiAdapter
from .doubao_adapter import DoubaoAdapter

__all__ = [
    "BaseAPIAdapter",
    "ModelProvider", 
    "ModelConfig",
    "APIMessage",
    "APIResponse",
    "AdapterFactory",
    "PREDEFINED_MODELS",
    "get_model_config",
    "get_provider_models",
    "DeepSeekAdapter",
    "QwenAdapter",
    "KimiAdapter",
    "DoubaoAdapter"
]
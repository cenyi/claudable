"""
AI Model Adapters Package
支持多种国产和国际AI大模型的统一适配器
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

# 导入所有适配器实现，触发自动注册
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
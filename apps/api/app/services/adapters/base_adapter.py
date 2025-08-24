"""
Base API Adapter for Multi-Model Support
Unified Base Adapter Class Supporting Multiple AI Models
"""
import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Callable, Dict, Any, AsyncGenerator, List
from enum import Enum
import httpx
from pydantic import BaseModel


class ModelProvider(str, Enum):
    """Supported Model Providers"""
    CLAUDE = "claude"
    CURSOR = "cursor"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"
    DOUBAO = "doubao"


class ModelConfig(BaseModel):
    """Model Configuration"""
    provider: ModelProvider
    model_id: str
    display_name: str
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 0.9
    context_window: Optional[int] = None
    supports_streaming: bool = True
    supports_images: bool = False
    api_endpoint: Optional[str] = None
    api_key_env: str  # Environment variable name, e.g. "DEEPSEEK_API_KEY"


class APIMessage(BaseModel):
    """Unified API Message Format"""
    role: str  # "system", "user", "assistant"
    content: str
    images: Optional[List[str]] = None  # Base64 encoded images


class APIResponse(BaseModel):
    """Unified API Response Format"""
    message_id: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None


class BaseAPIAdapter(ABC):
    """Base API Adapter Class"""
    
    def __init__(self, config: ModelConfig, api_key: str):
        self.config = config
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate if the API key is valid"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[APIMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> AsyncGenerator[APIResponse, None]:
        """Chat completion with streaming support"""
        pass
    
    @abstractmethod
    def _prepare_request_payload(
        self,
        messages: List[APIMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare API request payload"""
        pass
    
    @abstractmethod
    def _parse_response(self, response_data: Dict[str, Any]) -> APIResponse:
        """Parse API response"""
        pass
    
    @abstractmethod
    def _parse_stream_chunk(self, chunk: str) -> Optional[APIResponse]:
        """Parse streaming response chunk"""
        pass
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request"""
        headers = self._get_headers()
        return await self.client.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
    
    def normalize_role(self, role: str) -> str:
        """Normalize role name"""
        role_mapping = {
            "model": "assistant",
            "ai": "assistant",
            "human": "user",
            "bot": "assistant",
            "system": "system"
        }
        return role_mapping.get(role.lower(), role.lower())
    
    def format_error_message(self, error: Exception, context: str = "") -> str:
        """Format error message"""
        return f"[{self.config.provider.value.upper()}] {context}: {str(error)}"


class AdapterFactory:
    """Adapter Factory Class"""
    
    _adapters: Dict[ModelProvider, type] = {}
    
    @classmethod
    def register_adapter(cls, provider: ModelProvider, adapter_class: type):
        """Register adapter"""
        cls._adapters[provider] = adapter_class
    
    @classmethod
    def create_adapter(
        cls,
        provider: ModelProvider,
        config: ModelConfig,
        api_key: str
    ) -> BaseAPIAdapter:
        """Create adapter instance"""
        if provider not in cls._adapters:
            raise ValueError(f"Unsupported provider: {provider}")
        
        adapter_class = cls._adapters[provider]
        return adapter_class(config, api_key)
    
    @classmethod
    def get_supported_providers(cls) -> List[ModelProvider]:
        """Get list of supported providers"""
        return list(cls._adapters.keys())


# Predefined model configurations
PREDEFINED_MODELS = {
    # DeepSeek Models
    ModelProvider.DEEPSEEK: [
        ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-coder",
            display_name="DeepSeek Coder",
            description="Professional code generation model",
            max_tokens=4096,
            context_window=16384,
            api_endpoint="https://api.deepseek.com/v1/chat/completions",
            api_key_env="DEEPSEEK_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-chat",
            display_name="DeepSeek Chat",
            description="General conversation model",
            max_tokens=4096,
            context_window=16384,
            api_endpoint="https://api.deepseek.com/v1/chat/completions",
            api_key_env="DEEPSEEK_API_KEY"
        )
    ],
    
    # Qwen Models
    ModelProvider.QWEN: [
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_id="qwen-max",
            display_name="Qwen-Max",
            description="Most powerful general model",
            max_tokens=2048,
            context_window=8192,
            api_endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key_env="QWEN_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_id="qwen-plus",
            display_name="Qwen-Plus",
            description="Balanced performance and cost model",
            max_tokens=2048,
            context_window=8192,
            api_endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key_env="QWEN_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_id="qwen2.5-coder-32b-instruct",
            display_name="Qwen-Coder",
            description="Professional code generation model",
            max_tokens=4096,
            context_window=32768,
            api_endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key_env="QWEN_API_KEY"
        )
    ],
    
    # Kimi Models
    ModelProvider.KIMI: [
        ModelConfig(
            provider=ModelProvider.KIMI,
            model_id="moonshot-v1-8k",
            display_name="Kimi K2 8K",
            description="8K context window",
            max_tokens=4096,
            context_window=8192,
            api_endpoint="https://api.moonshot.cn/v1/chat/completions",
            api_key_env="KIMI_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.KIMI,
            model_id="moonshot-v1-32k",
            display_name="Kimi K2 32K",
            description="32K context window",
            max_tokens=4096,
            context_window=32768,
            api_endpoint="https://api.moonshot.cn/v1/chat/completions",
            api_key_env="KIMI_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.KIMI,
            model_id="moonshot-v1-128k",
            display_name="Kimi K2 128K",
            description="128K context window",
            max_tokens=4096,
            context_window=131072,
            api_endpoint="https://api.moonshot.cn/v1/chat/completions",
            api_key_env="KIMI_API_KEY"
        )
    ],
    
    # Doubao Models
    ModelProvider.DOUBAO: [
        ModelConfig(
            provider=ModelProvider.DOUBAO,
            model_id="ep-20241224053255-w6rj2",
            display_name="Doubao Seed",
            description="ByteDance Doubao Model",
            max_tokens=4096,
            context_window=16384,
            api_endpoint="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            api_key_env="DOUBAO_API_KEY"
        )
    ]
}


def get_model_config(provider: ModelProvider, model_id: str) -> Optional[ModelConfig]:
    """Get model configuration"""
    models = PREDEFINED_MODELS.get(provider, [])
    for model in models:
        if model.model_id == model_id:
            return model
    return None


def get_provider_models(provider: ModelProvider) -> List[ModelConfig]:
    """Get all models of a provider"""
    return PREDEFINED_MODELS.get(provider, [])
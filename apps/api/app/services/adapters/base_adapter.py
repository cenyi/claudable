"""
Base API Adapter for Multi-Model Support
支持多种AI大模型的统一适配器基类
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
    """支持的模型提供商"""
    CLAUDE = "claude"
    CURSOR = "cursor"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"
    DOUBAO = "doubao"


class ModelConfig(BaseModel):
    """模型配置"""
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
    api_key_env: str  # 环境变量名，如 "DEEPSEEK_API_KEY"


class APIMessage(BaseModel):
    """统一的API消息格式"""
    role: str  # "system", "user", "assistant"
    content: str
    images: Optional[List[str]] = None  # base64编码的图片


class APIResponse(BaseModel):
    """统一的API响应格式"""
    message_id: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None


class BaseAPIAdapter(ABC):
    """API适配器基类"""
    
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
        """验证API密钥是否有效"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
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
        """聊天补全，支持流式响应"""
        pass
    
    @abstractmethod
    def _prepare_request_payload(
        self,
        messages: List[APIMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """准备API请求载荷"""
        pass
    
    @abstractmethod
    def _parse_response(self, response_data: Dict[str, Any]) -> APIResponse:
        """解析API响应"""
        pass
    
    @abstractmethod
    def _parse_stream_chunk(self, chunk: str) -> Optional[APIResponse]:
        """解析流式响应块"""
        pass
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
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
        """发起HTTP请求"""
        headers = self._get_headers()
        return await self.client.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
    
    def normalize_role(self, role: str) -> str:
        """标准化角色名称"""
        role_mapping = {
            "model": "assistant",
            "ai": "assistant",
            "human": "user",
            "bot": "assistant",
            "system": "system"
        }
        return role_mapping.get(role.lower(), role.lower())
    
    def format_error_message(self, error: Exception, context: str = "") -> str:
        """格式化错误消息"""
        return f"[{self.config.provider.value.upper()}] {context}: {str(error)}"


class AdapterFactory:
    """适配器工厂类"""
    
    _adapters: Dict[ModelProvider, type] = {}
    
    @classmethod
    def register_adapter(cls, provider: ModelProvider, adapter_class: type):
        """注册适配器"""
        cls._adapters[provider] = adapter_class
    
    @classmethod
    def create_adapter(
        cls,
        provider: ModelProvider,
        config: ModelConfig,
        api_key: str
    ) -> BaseAPIAdapter:
        """创建适配器实例"""
        if provider not in cls._adapters:
            raise ValueError(f"Unsupported provider: {provider}")
        
        adapter_class = cls._adapters[provider]
        return adapter_class(config, api_key)
    
    @classmethod
    def get_supported_providers(cls) -> List[ModelProvider]:
        """获取支持的提供商列表"""
        return list(cls._adapters.keys())


# 预定义的模型配置
PREDEFINED_MODELS = {
    # DeepSeek 模型
    ModelProvider.DEEPSEEK: [
        ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-coder",
            display_name="DeepSeek Coder",
            description="专业的代码生成模型",
            max_tokens=4096,
            context_window=16384,
            api_endpoint="https://api.deepseek.com/v1/chat/completions",
            api_key_env="DEEPSEEK_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-chat",
            display_name="DeepSeek Chat",
            description="通用对话模型",
            max_tokens=4096,
            context_window=16384,
            api_endpoint="https://api.deepseek.com/v1/chat/completions",
            api_key_env="DEEPSEEK_API_KEY"
        )
    ],
    
    # 通义千问模型
    ModelProvider.QWEN: [
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_id="qwen-max",
            display_name="通义千问-Max",
            description="最强大的通用模型",
            max_tokens=2048,
            context_window=8192,
            api_endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key_env="QWEN_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_id="qwen-plus",
            display_name="通义千问-Plus",
            description="平衡性能和成本的模型",
            max_tokens=2048,
            context_window=8192,
            api_endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key_env="QWEN_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_id="qwen2.5-coder-32b-instruct",
            display_name="通义千问-Coder",
            description="专业代码生成模型",
            max_tokens=4096,
            context_window=32768,
            api_endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key_env="QWEN_API_KEY"
        )
    ],
    
    # Kimi 模型
    ModelProvider.KIMI: [
        ModelConfig(
            provider=ModelProvider.KIMI,
            model_id="moonshot-v1-8k",
            display_name="Kimi K2 8K",
            description="8K上下文窗口",
            max_tokens=4096,
            context_window=8192,
            api_endpoint="https://api.moonshot.cn/v1/chat/completions",
            api_key_env="KIMI_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.KIMI,
            model_id="moonshot-v1-32k",
            display_name="Kimi K2 32K",
            description="32K上下文窗口",
            max_tokens=4096,
            context_window=32768,
            api_endpoint="https://api.moonshot.cn/v1/chat/completions",
            api_key_env="KIMI_API_KEY"
        ),
        ModelConfig(
            provider=ModelProvider.KIMI,
            model_id="moonshot-v1-128k",
            display_name="Kimi K2 128K",
            description="128K上下文窗口",
            max_tokens=4096,
            context_window=131072,
            api_endpoint="https://api.moonshot.cn/v1/chat/completions",
            api_key_env="KIMI_API_KEY"
        )
    ],
    
    # 豆包模型
    ModelProvider.DOUBAO: [
        ModelConfig(
            provider=ModelProvider.DOUBAO,
            model_id="ep-20241224053255-w6rj2",
            display_name="豆包 Seed",
            description="字节跳动豆包模型",
            max_tokens=4096,
            context_window=16384,
            api_endpoint="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            api_key_env="DOUBAO_API_KEY"
        )
    ]
}


def get_model_config(provider: ModelProvider, model_id: str) -> Optional[ModelConfig]:
    """获取模型配置"""
    models = PREDEFINED_MODELS.get(provider, [])
    for model in models:
        if model.model_id == model_id:
            return model
    return None


def get_provider_models(provider: ModelProvider) -> List[ModelConfig]:
    """获取提供商的所有模型"""
    return PREDEFINED_MODELS.get(provider, [])
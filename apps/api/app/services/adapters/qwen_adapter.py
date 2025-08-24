"""
Qwen (通义千问) API Adapter
支持阿里云通义千问系列模型的API适配器
"""
import json
import uuid
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx

from .base_adapter import BaseAPIAdapter, ModelProvider, ModelConfig, APIMessage, APIResponse


class QwenAdapter(BaseAPIAdapter):
    """通义千问API适配器"""
    
    def __init__(self, config: ModelConfig, api_key: str):
        super().__init__(config, api_key)
        self.base_url = config.api_endpoint or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    async def validate_api_key(self) -> bool:
        """验证API密钥是否有效"""
        try:
            # 发送一个简单的测试请求
            test_messages = [
                APIMessage(role="user", content="你好")
            ]
            
            payload = self._prepare_request_payload(
                messages=test_messages,
                model=self.config.model_id
            )
            
            response = await self._make_request(
                "POST",
                self.base_url,
                json=payload
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        # 通义千问没有专门的模型列表API，返回预定义的模型
        return [
            "qwen-max",
            "qwen-plus", 
            "qwen-turbo",
            "qwen2.5-coder-32b-instruct",
            "qwen-max-longcontext"
        ]
    
    async def chat_completion(
        self,
        messages: List[APIMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> AsyncGenerator[APIResponse, None]:
        """聊天补全，支持流式响应"""
        
        payload = self._prepare_request_payload(
            messages=messages,
            model=model or self.config.model_id,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            stream=stream
        )
        
        try:
            if stream:
                async for response in self._stream_completion(payload):
                    yield response
            else:
                response = await self._single_completion(payload)
                yield response
        except Exception as e:
            error_response = APIResponse(
                message_id=str(uuid.uuid4()),
                content=self.format_error_message(e, "Chat completion failed"),
                role="assistant",
                finish_reason="error"
            )
            yield error_response
    
    async def _single_completion(self, payload: Dict[str, Any]) -> APIResponse:
        """非流式补全"""
        response = await self._make_request(
            "POST",
            self.base_url,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return self._parse_response(data)
    
    async def _stream_completion(self, payload: Dict[str, Any]) -> AsyncGenerator[APIResponse, None]:
        """流式补全"""
        # 启用流式输出
        payload["parameters"]["incremental_output"] = True
        
        async with self.client.stream(
            "POST",
            self.base_url,
            headers=self._get_headers(),
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    chunk = line[5:].strip()  # Remove "data:" prefix
                    if chunk:
                        try:
                            parsed_response = self._parse_stream_chunk(chunk)
                            if parsed_response:
                                yield parsed_response
                        except Exception:
                            continue  # Skip invalid chunks
    
    def _prepare_request_payload(
        self,
        messages: List[APIMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """准备API请求载荷"""
        
        # 转换消息格式为通义千问格式
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": self.normalize_role(msg.role),
                "content": msg.content
            }
            formatted_messages.append(formatted_msg)
        
        # 通义千问的请求格式
        payload = {
            "model": model or self.config.model_id,
            "input": {
                "messages": formatted_messages
            },
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "result_format": "message"
            }
        }
        
        # 流式输出配置
        if kwargs.get("stream", False):
            payload["parameters"]["stream"] = True
            payload["parameters"]["incremental_output"] = True
        
        return payload
    
    def _parse_response(self, response_data: Dict[str, Any]) -> APIResponse:
        """解析API响应"""
        output = response_data.get("output", {})
        
        if "choices" in output and len(output["choices"]) > 0:
            choice = output["choices"][0]
            message = choice.get("message", {})
            
            content = message.get("content", "")
            finish_reason = choice.get("finish_reason", "stop")
        else:
            # 处理其他格式的响应
            content = output.get("text", "")
            finish_reason = output.get("finish_reason", "stop")
        
        return APIResponse(
            message_id=response_data.get("request_id", str(uuid.uuid4())),
            content=content,
            role="assistant",
            finish_reason=finish_reason,
            usage=response_data.get("usage"),
            model=response_data.get("model")
        )
    
    def _parse_stream_chunk(self, chunk: str) -> Optional[APIResponse]:
        """解析流式响应块"""
        try:
            data = json.loads(chunk)
            
            output = data.get("output", {})
            
            if "choices" in output and len(output["choices"]) > 0:
                choice = output["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                if content:
                    return APIResponse(
                        message_id=data.get("request_id", str(uuid.uuid4())),
                        content=content,
                        role="assistant",
                        finish_reason=choice.get("finish_reason"),
                        model=data.get("model")
                    )
            elif "text" in output:
                # 处理其他格式的流式响应
                content = output.get("text", "")
                if content:
                    return APIResponse(
                        message_id=data.get("request_id", str(uuid.uuid4())),
                        content=content,
                        role="assistant",
                        finish_reason=output.get("finish_reason"),
                        model=data.get("model")
                    )
            
            return None
        except json.JSONDecodeError:
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Claudable/1.0.0",
            "X-DashScope-SSE": "enable"  # 启用SSE流式输出
        }


# 注册Qwen适配器
from .base_adapter import AdapterFactory
AdapterFactory.register_adapter(ModelProvider.QWEN, QwenAdapter)
"""
API Adapter CLI for National AI Models
支持国产AI大模型的API适配器CLI类
"""
import asyncio
import json
import os
import uuid
import tiktoken
from datetime import datetime
from typing import Optional, Callable, Dict, Any, AsyncGenerator, List
import tempfile
from sqlalchemy.orm import Session as DBSession

from app.models.messages import Message
from app.models.sessions import Session
from app.core.websocket.manager import manager as ws_manager
from app.core.terminal_ui import ui

from .unified_manager import BaseCLI, MODEL_MAPPING, CLIType
from app.services.adapters import (
    AdapterFactory, 
    ModelProvider, 
    ModelConfig, 
    APIMessage, 
    APIResponse,
    get_model_config,
    get_provider_models
)


class ConversationHistory:
    """持久化对话历史管理类"""
    
    def __init__(self, db: DBSession):
        self.db = db
        self._token_encoder = None
    
    def _get_token_encoder(self):
        """获取token编码器（懒加载）"""
        if self._token_encoder is None:
            try:
                # 使用cl100k_base编码器（适用于大多数模型）
                self._token_encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                # 降级到简单字符计数
                self._token_encoder = None
        return self._token_encoder
    
    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        encoder = self._get_token_encoder()
        if encoder:
            try:
                return len(encoder.encode(text))
            except Exception:
                pass
        # 降级估算：1 token ≈ 4 characters
        return len(text) // 4
    
    def save_conversation(self, project_id: str, provider: ModelProvider, messages: List[APIMessage]):
        """保存对话历史到数据库"""
        try:
            from app.models.conversation_history import ConversationHistoryModel
            
            # 清除旧的对话历史
            self.db.query(ConversationHistoryModel).filter(
                ConversationHistoryModel.project_id == project_id,
                ConversationHistoryModel.provider == provider.value
            ).delete()
            
            # 保存新的对话历史
            for i, msg in enumerate(messages):
                history_record = ConversationHistoryModel(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    provider=provider.value,
                    sequence_number=i,
                    role=msg.role,
                    content=msg.content,
                    images=json.dumps(msg.images) if msg.images else None,
                    created_at=datetime.utcnow()
                )
                self.db.add(history_record)
            
            self.db.commit()
            ui.debug(f"Saved {len(messages)} messages for {provider.value} in project {project_id}", "Conversation")
            
        except Exception as e:
            ui.error(f"Failed to save conversation history: {e}", "Conversation")
            self.db.rollback()
    
    def load_conversation(self, project_id: str, provider: ModelProvider) -> List[APIMessage]:
        """从数据库加载对话历史"""
        try:
            from app.models.conversation_history import ConversationHistoryModel
            
            records = self.db.query(ConversationHistoryModel).filter(
                ConversationHistoryModel.project_id == project_id,
                ConversationHistoryModel.provider == provider.value
            ).order_by(ConversationHistoryModel.sequence_number).all()
            
            messages = []
            for record in records:
                images = None
                if record.images:
                    try:
                        images = json.loads(record.images)
                    except Exception:
                        pass
                
                messages.append(APIMessage(
                    role=record.role,
                    content=record.content,
                    images=images
                ))
            
            ui.debug(f"Loaded {len(messages)} messages for {provider.value} from project {project_id}", "Conversation")
            return messages
            
        except Exception as e:
            ui.error(f"Failed to load conversation history: {e}", "Conversation")
            return []
    
    def clear_conversation(self, project_id: str, provider: ModelProvider):
        """清空对话历史"""
        try:
            from app.models.conversation_history import ConversationHistoryModel
            
            deleted_count = self.db.query(ConversationHistoryModel).filter(
                ConversationHistoryModel.project_id == project_id,
                ConversationHistoryModel.provider == provider.value
            ).delete()
            
            self.db.commit()
            ui.info(f"Cleared {deleted_count} messages for {provider.value} in project {project_id}", "Conversation")
            
        except Exception as e:
            ui.error(f"Failed to clear conversation history: {e}", "Conversation")
            self.db.rollback()
    
    def optimize_conversation_for_context_window(
        self, 
        messages: List[APIMessage], 
        context_window: int, 
        max_tokens_ratio: float = 0.7
    ) -> List[APIMessage]:
        """智能优化对话历史以适应上下文窗口"""
        if not messages:
            return messages
        
        max_tokens = int(context_window * max_tokens_ratio)
        
        # 始终保留系统消息
        system_messages = [msg for msg in messages if msg.role == "system"]
        non_system_messages = [msg for msg in messages if msg.role != "system"]
        
        # 计算系统消息的token数
        system_tokens = sum(self.count_tokens(msg.content) for msg in system_messages)
        available_tokens = max_tokens - system_tokens
        
        if available_tokens <= 0:
            ui.warning("System messages exceed token limit, using minimal context", "Conversation")
            return system_messages[-1:] if system_messages else []
        
        # 从最新的消息开始，逐步添加直到达到token限制
        optimized_messages = []
        current_tokens = 0
        
        for msg in reversed(non_system_messages):
            msg_tokens = self.count_tokens(msg.content)
            if msg.images:
                # 图片大约消耗1000 tokens
                msg_tokens += len(msg.images) * 1000
            
            if current_tokens + msg_tokens > available_tokens:
                break
            
            optimized_messages.insert(0, msg)
            current_tokens += msg_tokens
        
        # 确保对话的连贯性：如果有用户消息，必须有对应的助手回复
        final_messages = system_messages.copy()
        
        # 按对话轮次组织消息
        i = 0
        while i < len(optimized_messages):
            if optimized_messages[i].role == "user":
                final_messages.append(optimized_messages[i])
                # 查找对应的助手回复
                if i + 1 < len(optimized_messages) and optimized_messages[i + 1].role == "assistant":
                    final_messages.append(optimized_messages[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        ui.info(f"Optimized conversation: {len(messages)} -> {len(final_messages)} messages (~{current_tokens} tokens)", "Conversation")
        return final_messages


class APIAdapterCLI(BaseCLI):
    """API适配器CLI实现"""
    
    def __init__(self, provider: ModelProvider, db: Optional[DBSession] = None):
        # 映射Provider到CLIType
        cli_type_mapping = {
            ModelProvider.DEEPSEEK: CLIType.DEEPSEEK,
            ModelProvider.QWEN: CLIType.QWEN,
            ModelProvider.KIMI: CLIType.KIMI,
            ModelProvider.DOUBAO: CLIType.DOUBAO
        }
        
        cli_type = cli_type_mapping.get(provider)
        if not cli_type:
            raise ValueError(f"Unsupported provider: {provider}")
            
        super().__init__(cli_type)
        self.provider = provider
        self.session_storage = {}  # 简单的会话存储
        self.db = db
        
        # 使用新的对话历史管理器
        if db:
            self.conversation_manager = ConversationHistory(db)
        else:
            self.conversation_manager = None
            self.conversation_history = {}  # 降级到内存存储
    
    async def check_availability(self) -> Dict[str, Any]:
        """检查API适配器是否可用"""
        try:
            # 检查环境变量中是否有API密钥
            models = get_provider_models(self.provider)
            if not models:
                return {
                    "available": False,
                    "configured": False,
                    "error": f"No models configured for {self.provider.value}"
                }
            
            # 检查第一个模型的API密钥
            first_model = models[0]
            api_key = os.getenv(first_model.api_key_env)
            
            if not api_key:
                return {
                    "available": False,
                    "configured": False,
                    "error": f"API key not found for {self.provider.value}. Please set {first_model.api_key_env} environment variable."
                }
            
            # 尝试创建适配器并验证API密钥
            try:
                adapter = AdapterFactory.create_adapter(self.provider, first_model, api_key)
                async with adapter:
                    is_valid = await adapter.validate_api_key()
                    
                if is_valid:
                    return {
                        "available": True,
                        "configured": True,
                        "mode": "API",
                        "models": [model.model_id for model in models],
                        "default_models": [models[0].model_id] if models else []
                    }
                else:
                    return {
                        "available": False,
                        "configured": False,
                        "error": f"Invalid API key for {self.provider.value}"
                    }
            except Exception as e:
                return {
                    "available": False,
                    "configured": False,
                    "error": f"Failed to validate {self.provider.value} API: {str(e)}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "configured": False,
                "error": f"Error checking {self.provider.value} availability: {str(e)}"
            }
    
    async def execute_with_streaming(
        self,
        instruction: str,
        project_path: str,
        session_id: Optional[str] = None,
        log_callback: Optional[Callable] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        is_initial_prompt: bool = False
    ) -> AsyncGenerator[Message, None]:
        """执行指令并流式返回消息"""
        
        try:
            # 获取模型配置
            if model:
                model_config = get_model_config(self.provider, model)
                if not model_config:
                    # 如果没有找到配置，使用第一个可用模型
                    models = get_provider_models(self.provider)
                    model_config = models[0] if models else None
            else:
                models = get_provider_models(self.provider)
                model_config = models[0] if models else None
            
            if not model_config:
                error_msg = f"No model configuration found for {self.provider.value}"
                ui.error(error_msg, "API Adapter")
                yield self._create_error_message(error_msg, session_id)
                return
            
            # 获取API密钥
            api_key = os.getenv(model_config.api_key_env)
            if not api_key:
                error_msg = f"API key not found for {self.provider.value}. Please set {model_config.api_key_env}"
                ui.error(error_msg, "API Adapter")
                yield self._create_error_message(error_msg, session_id)
                return
            
            ui.info(f"Using {self.provider.value} model: {model_config.model_id}", "API Adapter")
            
            # 创建适配器
            adapter = AdapterFactory.create_adapter(self.provider, model_config, api_key)
            
            async with adapter:
                # 获取项目id
                project_id = project_path.split("/")[-1] if "/" in project_path else project_path.split("\\")[-1] if "\\" in project_path else project_path
                
                # 获取对话历史（使用新的管理器）
                if self.conversation_manager:
                    conversation = self.conversation_manager.load_conversation(project_id, self.provider)
                else:
                    # 降级到内存存储
                    if project_id not in self.conversation_history:
                        self.conversation_history[project_id] = []
                    conversation = self.conversation_history[project_id]
                
                # 如果是初始提示，清空对话历史
                if is_initial_prompt:
                    conversation.clear()
                    if self.conversation_manager:
                        self.conversation_manager.clear_conversation(project_id, self.provider)
                    ui.info(f"Starting new conversation for {self.provider.value}", "API Adapter")
                
                # 添加系统提示（仅在新对话时）
                if not conversation:
                    system_prompt = self._get_system_prompt()
                    if system_prompt:
                        conversation.append(APIMessage(role="system", content=system_prompt))
                
                # 添加用户消息
                user_message = APIMessage(role="user", content=instruction)
                
                # 添加图片支持（如果支持）
                if images and model_config.supports_images:
                    for img in images:
                        if "base64" in img:
                            user_message.images = user_message.images or []
                            user_message.images.append(img["base64"])
                
                conversation.append(user_message)
                
                # 使用智能对话优化（基于token计算）
                if self.conversation_manager:
                    messages = self.conversation_manager.optimize_conversation_for_context_window(
                        conversation, 
                        model_config.context_window or 4096
                    )
                else:
                    # 降级到简单的消息数量限制
                    max_history_length = self._get_max_history_length(model_config)
                    if len(conversation) > max_history_length:
                        system_messages = [msg for msg in conversation if msg.role == "system"]
                        recent_messages = conversation[-(max_history_length - len(system_messages)):]
                        messages = system_messages + recent_messages
                        ui.info(f"Truncated conversation history to {len(messages)} messages", "API Adapter")
                    else:
                        messages = conversation.copy()
                
                # 流式聊天补全
                assistant_content = ""
                async for api_response in adapter.chat_completion(
                    messages=messages,
                    model=model_config.model_id,
                    stream=True
                ):
                    # 收集助手回复内容
                    if api_response.content:
                        assistant_content += api_response.content
                    
                    # 转换为统一消息格式
                    message = self._convert_api_response_to_message(
                        api_response, 
                        project_id,
                        session_id
                    )
                    
                    # 发送日志回调
                    if log_callback:
                        await log_callback("text", {
                            "content": api_response.content,
                            "role": api_response.role
                        })
                    
                    yield message
                
                # 将助手回复添加到对话历史
                if assistant_content.strip():
                    assistant_message = APIMessage(role="assistant", content=assistant_content.strip())
                    conversation.append(assistant_message)
                    
                    # 保存到持久化存储
                    if self.conversation_manager:
                        self.conversation_manager.save_conversation(project_id, self.provider, conversation)
                    else:
                        self.conversation_history[project_id] = conversation
                    
                    ui.debug(f"Saved assistant response to conversation history ({len(assistant_content)} chars)", "API Adapter")
                    
        except Exception as e:
            error_msg = f"Error executing {self.provider.value} API: {str(e)}"
            ui.error(error_msg, "API Adapter")
            yield self._create_error_message(error_msg, session_id)
    
    async def get_session_id(self, project_id: str) -> Optional[str]:
        """获取项目的会话ID"""
        return self.session_storage.get(project_id)
    
    async def set_session_id(self, project_id: str, session_id: str) -> None:
        """设置项目的会话ID"""
        self.session_storage[project_id] = session_id
    
    def _convert_api_response_to_message(
        self, 
        api_response: APIResponse, 
        project_id: str, 
        session_id: Optional[str]
    ) -> Message:
        """将API响应转换为统一消息格式"""
        return Message(
            id=api_response.message_id,
            project_id=project_id,
            role=api_response.role,
            message_type="chat",
            content=api_response.content,
            metadata_json={
                "provider": self.provider.value,
                "model": api_response.model,
                "finish_reason": api_response.finish_reason,
                "usage": api_response.usage
            },
            session_id=session_id,
            created_at=datetime.utcnow()
        )
    
    def _create_error_message(self, error_msg: str, session_id: Optional[str]) -> Message:
        """创建错误消息"""
        return Message(
            id=str(uuid.uuid4()),
            project_id="unknown",
            role="assistant",
            message_type="error",
            content=f"❌ {error_msg}",
            metadata_json={
                "provider": self.provider.value,
                "error": True
            },
            session_id=session_id,
            created_at=datetime.utcnow()
        )
    
    def _get_system_prompt(self) -> Optional[str]:
        """获取系统提示"""
        # 为不同的提供商定制系统提示
        system_prompts = {
            ModelProvider.DEEPSEEK: "You are a helpful AI assistant specialized in code generation and software development. Please provide clear, well-documented, and efficient code solutions.",
            ModelProvider.QWEN: "你是一个专业的AI编程助手，擅长代码生成和软件开发。请提供清晰、有文档和高效的代码解决方案。",
            ModelProvider.KIMI: "你是一个智能的AI助手，擅长处理复杂的编程任务和长文档分析。请提供详细的代码解释和解决方案。",
            ModelProvider.DOUBAO: "你是一个高效的AI编程助手，擅长代码生成和问题解决。请提供简洁明了的代码和解释。"
        }
        return system_prompts.get(self.provider)
    
    def _get_max_history_length(self, model_config: ModelConfig) -> int:
        """获取最大对话历史长度"""
        # 根据模型的上下文窗口调整对话历史长度
        context_window = model_config.context_window or 4096
        
        if context_window >= 128000:  # 128K+
            return 50  # 允许更长的对话历史
        elif context_window >= 32000:  # 32K+
            return 30
        elif context_window >= 8000:   # 8K+
            return 20
        else:  # 4K
            return 10
    
    def clear_conversation_history(self, project_id: str) -> None:
        """清空指定项目的对话历史"""
        if self.conversation_manager:
            self.conversation_manager.clear_conversation(project_id, self.provider)
        else:
            if project_id in self.conversation_history:
                self.conversation_history[project_id].clear()
        ui.info(f"Cleared conversation history for project {project_id}", "API Adapter")
    
    def get_conversation_summary(self, project_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        if self.conversation_manager:
            conversation = self.conversation_manager.load_conversation(project_id, self.provider)
        else:
            conversation = self.conversation_history.get(project_id, [])
        
        user_messages = [msg for msg in conversation if msg.role == "user"]
        assistant_messages = [msg for msg in conversation if msg.role == "assistant"]
        
        return {
            "total_messages": len(conversation),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "has_system_prompt": any(msg.role == "system" for msg in conversation),
            "provider": self.provider.value
        }


# 模型映射已在unified_manager.py中更新，无需额外类定义
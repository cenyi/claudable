    def clear_conversation(self, project_id: str, provider: ModelProvider):
        """Clear conversation history"""
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
        """Intelligently optimize conversation history to fit context window"""
        if not messages:
            return messages
        
        max_tokens = int(context_window * max_tokens_ratio)
        
        # Always preserve system messages
        system_messages = [msg for msg in messages if msg.role == "system"]
        non_system_messages = [msg for msg in messages if msg.role != "system"]
        
        # Calculate token count for system messages
        system_tokens = sum(self.count_tokens(msg.content) for msg in system_messages)
        available_tokens = max_tokens - system_tokens
        
        if available_tokens <= 0:
            ui.warning("System messages exceed token limit, using minimal context", "Conversation")
            return system_messages[-1:] if system_messages else []
        
        # Start from the latest messages and add until token limit is reached
        optimized_messages = []
        current_tokens = 0
        
        for msg in reversed(non_system_messages):
            msg_tokens = self.count_tokens(msg.content)
            if msg.images:
                # Images consume approximately 1000 tokens each
                msg_tokens += len(msg.images) * 1000
            
            if current_tokens + msg_tokens > available_tokens:
                break
            
            optimized_messages.insert(0, msg)
            current_tokens += msg_tokens
        
        # Ensure conversation coherence: if there's a user message, there must be a corresponding assistant reply
        final_messages = system_messages.copy()
        
        # Organize messages by conversation turns
        i = 0
        while i < len(optimized_messages):
            if optimized_messages[i].role == "user":
                final_messages.append(optimized_messages[i])
                # Find corresponding assistant reply
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
    """API Adapter CLI Implementation"""
    
    def __init__(self, provider: ModelProvider, db: Optional[DBSession] = None):
        # Map Provider to CLIType
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
        self.session_storage = {}  # Simple session storage
        self.db = db
        
        # Use the new conversation history manager
        if db:
            self.conversation_manager = ConversationHistory(db)
        else:
            self.conversation_manager = None
            self.conversation_history = {}  # Fall back to memory storage
    
    async def check_availability(self) -> Dict[str, Any]:
        """Check if API adapter is available"""
        try:
            # Check if API key is in environment variables
            models = get_provider_models(self.provider)
            if not models:
                return {
                    "available": False,
                    "configured": False,
                    "error": f"No models configured for {self.provider.value}"
                }
            
            # Check API key for the first model
            first_model = models[0]
            api_key = os.getenv(first_model.api_key_env)
            
            if not api_key:
                return {
                    "available": False,
                    "configured": False,
                    "error": f"API key not found for {self.provider.value}. Please set {first_model.api_key_env} environment variable."
                }
            
            # Try to create adapter and validate API key
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
        """Execute instruction and stream messages"""
        
        try:
            # Get model configuration
            if model:
                model_config = get_model_config(self.provider, model)
                if not model_config:
                    # If no configuration found, use the first available model
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
            
            # Get API key
            api_key = os.getenv(model_config.api_key_env)
            if not api_key:
                error_msg = f"API key not found for {self.provider.value}. Please set {model_config.api_key_env}"
                ui.error(error_msg, "API Adapter")
                yield self._create_error_message(error_msg, session_id)
                return
            
            ui.info(f"Using {self.provider.value} model: {model_config.model_id}", "API Adapter")
            
            # Create adapter
            adapter = AdapterFactory.create_adapter(self.provider, model_config, api_key)
            
            async with adapter:
                # Get project ID
                project_id = project_path.split("/")[-1] if "/" in project_path else project_path.split("\\")[-1] if "\\" in project_path else project_path
                
                # Get conversation history (using the new manager)
                if self.conversation_manager:
                    conversation = self.conversation_manager.load_conversation(project_id, self.provider)
                else:
                    # Fall back to memory storage
                    if project_id not in self.conversation_history:
                        self.conversation_history[project_id] = []
                    conversation = self.conversation_history[project_id]
                
                # If this is an initial prompt, clear conversation history
                if is_initial_prompt:
                    conversation.clear()
                    if self.conversation_manager:
                        self.conversation_manager.clear_conversation(project_id, self.provider)
                    ui.info(f"Starting new conversation for {self.provider.value}", "API Adapter")
                
                # Add system prompt (only for new conversations)
                if not conversation:
                    system_prompt = self._get_system_prompt()
                    if system_prompt:
                        conversation.append(APIMessage(role="system", content=system_prompt))
                
                # Add user message
                user_message = APIMessage(role="user", content=instruction)
                
                # Add image support (if supported)
                if images and model_config.supports_images:
                    for img in images:
                        if "base64" in img:
                            user_message.images = user_message.images or []
                            user_message.images.append(img["base64"])
                
                conversation.append(user_message)
                
                # Use intelligent conversation optimization (based on token calculation)
                if self.conversation_manager:
                    messages = self.conversation_manager.optimize_conversation_for_context_window(
                        conversation, 
                        model_config.context_window or 4096
                    )
                else:
                    # Fall back to simple message count limit
                    max_history_length = self._get_max_history_length(model_config)
                    if len(conversation) > max_history_length:
                        system_messages = [msg for msg in conversation if msg.role == "system"]
                        recent_messages = conversation[-(max_history_length - len(system_messages)):]
                        messages = system_messages + recent_messages
                        ui.info(f"Truncated conversation history to {len(messages)} messages", "API Adapter")
                    else:
                        messages = conversation.copy()
                
                # Stream chat completion
                assistant_content = ""
                async for api_response in adapter.chat_completion(
                    messages=messages,
                    model=model_config.model_id,
                    stream=True
                ):
                    # Collect assistant response content
                    if api_response.content:
                        assistant_content += api_response.content
                    
                    # Convert to unified message format
                    message = self._convert_api_response_to_message(
                        api_response, 
                        project_id,
                        session_id
                    )
                    
                    # Send log callback
                    if log_callback:
                        await log_callback("text", {
                            "content": api_response.content,
                            "role": api_response.role
                        })
                    
                    yield message
                
                # Add assistant response to conversation history
                if assistant_content.strip():
                    assistant_message = APIMessage(role="assistant", content=assistant_content.strip())
                    conversation.append(assistant_message)
                    
                    # Save to persistent storage
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
        """Get session ID for project"""
        return self.session_storage.get(project_id)
    
    async def set_session_id(self, project_id: str, session_id: str) -> None:
        """Set session ID for project"""
        self.session_storage[project_id] = session_id
    
    def _convert_api_response_to_message(
        self, 
        api_response: APIResponse, 
        project_id: str, 
        session_id: Optional[str]
    ) -> Message:
        """Convert API response to unified message format"""
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
        """Create error message"""
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
        """Get system prompt"""
        # Customize system prompts for different providers
        system_prompts = {
            ModelProvider.DEEPSEEK: "You are a helpful AI assistant specialized in code generation and software development. Please provide clear, well-documented, and efficient code solutions.",
            ModelProvider.QWEN: "You are a professional AI programming assistant, skilled in code generation and software development. Please provide clear, well-documented, and efficient code solutions.",
            ModelProvider.KIMI: "You are an intelligent AI assistant, skilled in handling complex programming tasks and long document analysis. Please provide detailed code explanations and solutions.",
            ModelProvider.DOUBAO: "You are an efficient AI programming assistant, skilled in code generation and problem solving. Please provide concise and clear code and explanations."
        }
        return system_prompts.get(self.provider)
    
    def _get_max_history_length(self, model_config: ModelConfig) -> int:
        """Get maximum conversation history length"""
        # Adjust conversation history length based on model's context window
        context_window = model_config.context_window or 4096
        
        if context_window >= 128000:  # 128K+
            return 50  # Allow longer conversation history
        elif context_window >= 32000:  # 32K+
            return 30
        elif context_window >= 8000:   # 8K+
            return 20
        else:  # 4K
            return 10
    
    def clear_conversation_history(self, project_id: str) -> None:
        """Clear conversation history for specified project"""
        if self.conversation_manager:
            self.conversation_manager.clear_conversation(project_id, self.provider)
        else:
            if project_id in self.conversation_history:
                self.conversation_history[project_id].clear()
        ui.info(f"Cleared conversation history for project {project_id}", "API Adapter")
    
    def get_conversation_summary(self, project_id: str) -> Dict[str, Any]:
        """Get conversation summary"""
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
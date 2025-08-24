"""
API Configuration Manager
Manage API configuration and keys for domestic AI models
"""
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.env_vars import EnvVar
from app.core.crypto import secret_box
from app.core.config import settings
from app.services.adapters import ModelProvider, get_provider_models, get_model_config


class APIConfigManager:
    """API Configuration Manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_cache = {}
    
    def get_api_key(self, provider: ModelProvider, project_id: Optional[str] = None) -> Optional[str]:
        """Get API key"""
        
        # First look in project environment variables
        if project_id:
            project_key = self._get_project_api_key(provider, project_id)
            if project_key:
                return project_key
        
        # Then look in global environment variables
        return self._get_global_api_key(provider)
    
    def set_api_key(
        self, 
        provider: ModelProvider, 
        api_key: str, 
        project_id: Optional[str] = None,
        scope: str = "global"
    ) -> bool:
        """Set API key"""
        
        try:
            if project_id and scope == "project":
                return self._set_project_api_key(provider, api_key, project_id)
            else:
                return self._set_global_api_key(provider, api_key)
        except Exception as e:
            print(f"Error setting API key for {provider.value}: {e}")
            return False
    
    def validate_api_key(self, provider: ModelProvider, api_key: str) -> bool:
        """Validate if the API key is valid"""
        
        try:
            models = get_provider_models(provider)
            if not models:
                return False
            
            # Use the first model's configuration for validation
            model_config = models[0]
            
            # Create adapter for validation
            from app.services.adapters import AdapterFactory
            
            async def async_validate():
                adapter = AdapterFactory.create_adapter(provider, model_config, api_key)
                async with adapter:
                    return await adapter.validate_api_key()
            
            import asyncio
            return asyncio.run(async_validate())
            
        except Exception as e:
            print(f"Error validating API key for {provider.value}: {e}")
            return False
    
    def get_provider_config(self, provider: ModelProvider) -> Dict[str, Any]:
        """Get provider configuration"""
        
        models = get_provider_models(provider)
        api_key = self.get_api_key(provider)
        
        return {
            "provider": provider.value,
            "available_models": [
                {
                    "id": model.model_id,
                    "name": model.display_name,
                    "description": model.description,
                    "context_window": model.context_window,
                    "max_tokens": model.max_tokens
                }
                for model in models
            ],
            "has_api_key": bool(api_key),
            "configured": bool(api_key)
        }
    
    def get_all_providers_config(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for all providers"""
        
        providers_config = {}
        
        for provider in [ModelProvider.DEEPSEEK, ModelProvider.QWEN, ModelProvider.KIMI, ModelProvider.DOUBAO]:
            providers_config[provider.value] = self.get_provider_config(provider)
        
        return providers_config
    
    def _get_project_api_key(self, provider: ModelProvider, project_id: str) -> Optional[str]:
        """Get API key from project environment variables"""
        
        # Get the corresponding environment variable name
        models = get_provider_models(provider)
        if not models:
            return None
            
        env_key = models[0].api_key_env
        
        try:
            # Find project environment variable from database
            env_var = self.db.query(EnvVar).filter(
                EnvVar.project_id == project_id,
                EnvVar.key == env_key
            ).first()
            
            if env_var:
                # Decrypt environment variable value
                return secret_box.decrypt(env_var.value_encrypted)
            
        except Exception as e:
            print(f"Error getting project API key for {provider.value}: {e}")
        
        return None
    
    def _get_global_api_key(self, provider: ModelProvider) -> Optional[str]:
        """Get API key from global environment variables"""
        
        models = get_provider_models(provider)
        if not models:
            return None
            
        env_key = models[0].api_key_env
        return os.getenv(env_key)
    
    def _set_project_api_key(self, provider: ModelProvider, api_key: str, project_id: str) -> bool:
        """Set API key in project environment variables"""
        
        models = get_provider_models(provider)
        if not models:
            return False
            
        env_key = models[0].api_key_env
        
        try:
            # Find or create environment variable
            env_var = self.db.query(EnvVar).filter(
                EnvVar.project_id == project_id,
                EnvVar.key == env_key
            ).first()
            
            if env_var:
                # Update existing environment variable
                env_var.value_encrypted = secret_box.encrypt(api_key)
            else:
                # Create new environment variable
                import uuid
                env_var = EnvVar(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    key=env_key,
                    value_encrypted=secret_box.encrypt(api_key),
                    scope="runtime",
                    var_type="string",
                    is_secret=True,
                    description=f"API key for {provider.value}"
                )
                self.db.add(env_var)
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error setting project API key for {provider.value}: {e}")
            self.db.rollback()
            return False
    
    def _set_global_api_key(self, provider: ModelProvider, api_key: str) -> bool:
        """Set API key in global environment variables"""
        
        models = get_provider_models(provider)
        if not models:
            return False
            
        env_key = models[0].api_key_env
        
        try:
            # Write to OS environment variable (only valid in current process)

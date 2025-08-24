"""
API Configuration Manager
管理国产AI大模型的API配置和密钥
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
    """API配置管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_cache = {}
    
    def get_api_key(self, provider: ModelProvider, project_id: Optional[str] = None) -> Optional[str]:
        """获取API密钥"""
        
        # 首先从项目环境变量中查找
        if project_id:
            project_key = self._get_project_api_key(provider, project_id)
            if project_key:
                return project_key
        
        # 然后从全局环境变量中查找
        return self._get_global_api_key(provider)
    
    def set_api_key(
        self, 
        provider: ModelProvider, 
        api_key: str, 
        project_id: Optional[str] = None,
        scope: str = "global"
    ) -> bool:
        """设置API密钥"""
        
        try:
            if project_id and scope == "project":
                return self._set_project_api_key(provider, api_key, project_id)
            else:
                return self._set_global_api_key(provider, api_key)
        except Exception as e:
            print(f"Error setting API key for {provider.value}: {e}")
            return False
    
    def validate_api_key(self, provider: ModelProvider, api_key: str) -> bool:
        """验证API密钥是否有效"""
        
        try:
            models = get_provider_models(provider)
            if not models:
                return False
            
            # 使用第一个模型的配置进行验证
            model_config = models[0]
            
            # 创建适配器进行验证
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
        """获取提供商配置"""
        
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
        """获取所有提供商的配置"""
        
        providers_config = {}
        
        for provider in [ModelProvider.DEEPSEEK, ModelProvider.QWEN, ModelProvider.KIMI, ModelProvider.DOUBAO]:
            providers_config[provider.value] = self.get_provider_config(provider)
        
        return providers_config
    
    def _get_project_api_key(self, provider: ModelProvider, project_id: str) -> Optional[str]:
        """从项目环境变量中获取API密钥"""
        
        # 获取对应的环境变量名
        models = get_provider_models(provider)
        if not models:
            return None
            
        env_key = models[0].api_key_env
        
        try:
            # 从数据库中查找项目环境变量
            env_var = self.db.query(EnvVar).filter(
                EnvVar.project_id == project_id,
                EnvVar.key == env_key
            ).first()
            
            if env_var:
                # 解密环境变量值
                return secret_box.decrypt(env_var.value_encrypted)
            
        except Exception as e:
            print(f"Error getting project API key for {provider.value}: {e}")
        
        return None
    
    def _get_global_api_key(self, provider: ModelProvider) -> Optional[str]:
        """从全局环境变量中获取API密钥"""
        
        models = get_provider_models(provider)
        if not models:
            return None
            
        env_key = models[0].api_key_env
        return os.getenv(env_key)
    
    def _set_project_api_key(self, provider: ModelProvider, api_key: str, project_id: str) -> bool:
        """设置项目环境变量中的API密钥"""
        
        models = get_provider_models(provider)
        if not models:
            return False
            
        env_key = models[0].api_key_env
        
        try:
            # 查找或创建环境变量
            env_var = self.db.query(EnvVar).filter(
                EnvVar.project_id == project_id,
                EnvVar.key == env_key
            ).first()
            
            if env_var:
                # 更新现有环境变量
                env_var.value_encrypted = secret_box.encrypt(api_key)
            else:
                # 创建新环境变量
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
        """设置全局环境变量中的API密钥"""
        
        models = get_provider_models(provider)
        if not models:
            return False
            
        env_key = models[0].api_key_env
        
        try:
            # 写入操作系统环境变量（仅在当前进程中有效）
            os.environ[env_key] = api_key
            
            # 可选：写入.env文件以持久化
            env_file_path = Path(settings.projects_root).parent / ".env"
            self._update_env_file(env_file_path, env_key, api_key)
            
            return True
            
        except Exception as e:
            print(f"Error setting global API key for {provider.value}: {e}")
            return False
    
    def _update_env_file(self, env_file_path: Path, key: str, value: str):
        """更新.env文件"""
        
        try:
            # 读取现有内容
            lines = []
            if env_file_path.exists():
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # 查找并更新现有的键
            key_found = False
            new_lines = []
            
            for line in lines:
                if line.strip().startswith(f"{key}="):
                    new_lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    new_lines.append(line)
            
            # 如果键不存在，添加新行
            if not key_found:
                new_lines.append(f"{key}={value}\n")
            
            # 写回文件
            env_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
        except Exception as e:
            print(f"Error updating .env file: {e}")


def get_config_manager(db: Session) -> APIConfigManager:
    """获取API配置管理器实例"""
    return APIConfigManager(db)
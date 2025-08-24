"""
API Configuration REST Endpoints
国产AI大模型配置管理的REST API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.api.deps import get_db
from app.services.api_config_manager import get_config_manager
from app.services.adapters import ModelProvider

router = APIRouter(prefix="/api/config", tags=["config"])


class APIKeyRequest(BaseModel):
    provider: str
    api_key: str
    scope: str = "global"  # "global" or "project"


class APIKeyValidationRequest(BaseModel):
    provider: str
    api_key: str


class APIKeyResponse(BaseModel):
    success: bool
    message: str


class ProviderConfigResponse(BaseModel):
    provider: str
    available_models: list
    has_api_key: bool
    configured: bool


class AllProvidersConfigResponse(BaseModel):
    providers: Dict[str, ProviderConfigResponse]


@router.get("/providers", response_model=AllProvidersConfigResponse)
async def get_all_providers_config(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取所有提供商的配置"""
    try:
        config_manager = get_config_manager(db)
        providers_config = config_manager.get_all_providers_config(project_id)
        
        return AllProvidersConfigResponse(providers=providers_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers config: {str(e)}")


@router.get("/providers/{provider}", response_model=ProviderConfigResponse)
async def get_provider_config(
    provider: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取特定提供商的配置"""
    try:
        # 验证提供商
        try:
            model_provider = ModelProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        config_manager = get_config_manager(db)
        provider_config = config_manager.get_provider_config(model_provider)
        
        return ProviderConfigResponse(**provider_config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider config: {str(e)}")


@router.post("/api-key", response_model=APIKeyResponse)
async def set_api_key(
    request: APIKeyRequest,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """设置API密钥"""
    try:
        # 验证提供商
        try:
            model_provider = ModelProvider(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")
        
        config_manager = get_config_manager(db)
        
        # 如果是项目级别的设置，需要项目ID
        if request.scope == "project" and not project_id:
            raise HTTPException(status_code=400, detail="Project ID is required for project-level API key")
        
        success = config_manager.set_api_key(
            provider=model_provider,
            api_key=request.api_key,
            project_id=project_id if request.scope == "project" else None,
            scope=request.scope
        )
        
        if success:
            return APIKeyResponse(
                success=True,
                message=f"API key for {request.provider} has been set successfully"
            )
        else:
            return APIKeyResponse(
                success=False,
                message=f"Failed to set API key for {request.provider}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set API key: {str(e)}")


@router.post("/api-key/validate", response_model=APIKeyResponse)
async def validate_api_key(
    request: APIKeyValidationRequest,
    db: Session = Depends(get_db)
):
    """验证API密钥"""
    try:
        # 验证提供商
        try:
            model_provider = ModelProvider(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")
        
        config_manager = get_config_manager(db)
        
        is_valid = config_manager.validate_api_key(
            provider=model_provider,
            api_key=request.api_key
        )
        
        if is_valid:
            return APIKeyResponse(
                success=True,
                message=f"API key for {request.provider} is valid"
            )
        else:
            return APIKeyResponse(
                success=False,
                message=f"API key for {request.provider} is invalid"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate API key: {str(e)}")


@router.get("/api-key/{provider}")
async def check_api_key_status(
    provider: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """检查API密钥状态"""
    try:
        # 验证提供商
        try:
            model_provider = ModelProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        config_manager = get_config_manager(db)
        api_key = config_manager.get_api_key(model_provider, project_id)
        
        return {
            "provider": provider,
            "has_api_key": bool(api_key),
            "scope": "project" if project_id and api_key else "global"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check API key status: {str(e)}")


@router.delete("/api-key/{provider}")
async def remove_api_key(
    provider: str,
    project_id: Optional[str] = None,
    scope: str = "global",
    db: Session = Depends(get_db)
):
    """删除API密钥"""
    try:
        # 验证提供商
        try:
            model_provider = ModelProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        config_manager = get_config_manager(db)
        
        if scope == "project" and project_id:
            # 删除项目级别的API密钥
            from app.models.env_vars import EnvVar
            from app.services.adapters import get_provider_models
            
            models = get_provider_models(model_provider)
            if models:
                env_key = models[0].api_key_env
                env_var = db.query(EnvVar).filter(
                    EnvVar.project_id == project_id,
                    EnvVar.key == env_key
                ).first()
                
                if env_var:
                    db.delete(env_var)
                    db.commit()
        else:
            # 删除全局环境变量（从操作系统环境变量中移除）
            from app.services.adapters import get_provider_models
            import os
            
            models = get_provider_models(model_provider)
            if models:
                env_key = models[0].api_key_env
                if env_key in os.environ:
                    del os.environ[env_key]
        
        return APIKeyResponse(
            success=True,
            message=f"API key for {provider} has been removed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove API key: {str(e)}")
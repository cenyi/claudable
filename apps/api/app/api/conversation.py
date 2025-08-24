"""
Conversation Management API
Conversation History Management for Domestic AI Models
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from app.api.deps import get_db
from app.models.projects import Project as ProjectModel
from app.services.adapters import ModelProvider

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


class ConversationSummaryResponse(BaseModel):
    total_messages: int
    user_messages: int
    assistant_messages: int
    has_system_prompt: bool
    provider: str


class ConversationClearResponse(BaseModel):
    success: bool
    message: str


def get_api_adapter_cli(provider: ModelProvider, db: Session):
    """Get API adapter CLI instance"""
    from app.services.cli.api_adapter_cli import APIAdapterCLI
    return APIAdapterCLI(provider, db)


@router.get("/{project_id}/summary")
async def get_conversation_summary(
    project_id: str,
    provider: str,
    db: Session = Depends(get_db)
) -> ConversationSummaryResponse:
    """Get conversation history summary"""
    
    # Validate project exists
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate provider
    try:
        model_provider = ModelProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    try:
        cli = get_api_adapter_cli(model_provider, db)
        summary = cli.get_conversation_summary(project_id)
        
        return ConversationSummaryResponse(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation summary: {str(e)}")


@router.delete("/{project_id}/history")
async def clear_conversation_history(
    project_id: str,
    provider: str,
    db: Session = Depends(get_db)
) -> ConversationClearResponse:
    """Clear conversation history"""
    
    # Validate project exists
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate provider
    try:
        model_provider = ModelProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    try:
        cli = get_api_adapter_cli(model_provider, db)
        cli.clear_conversation_history(project_id)
        
        return ConversationClearResponse(
            success=True,
            message=f"Conversation history cleared for {provider} in project {project_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation history: {str(e)}")


@router.get("/{project_id}/providers")
async def get_active_providers(
    project_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Dict[str, Any]]:
    """Get active AI providers and their conversation status for the project"""
    
    # Validate project exists
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        providers_info = {}
        
        for provider in [ModelProvider.DEEPSEEK, ModelProvider.QWEN, ModelProvider.KIMI, ModelProvider.DOUBAO]:
            try:
                cli = get_api_adapter_cli(provider, db)
                summary = cli.get_conversation_summary(project_id)
                
                providers_info[provider.value] = {
                    "active": summary["total_messages"] > 0,
                    "summary": summary
                }
            except Exception:
                providers_info[provider.value] = {
                    "active": False,
                    "summary": None
                }
        
        return providers_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers info: {str(e)}")


@router.get("/{project_id}/stats")
async def get_conversation_stats(
    project_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get conversation statistics (including token usage)"""
    
    # Validate project exists
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        providers_stats = []
        
        for provider in [ModelProvider.DEEPSEEK, ModelProvider.QWEN, ModelProvider.KIMI, ModelProvider.DOUBAO]:
            try:
                cli = get_api_adapter_cli(provider, db)
                summary = cli.get_conversation_summary(project_id)
                
                # Estimate token usage
                if cli.conversation_manager and summary["total_messages"] > 0:
                    conversation = cli.conversation_manager.load_conversation(project_id, provider)
                    estimated_tokens = sum(cli.conversation_manager.count_tokens(msg.content) for msg in conversation)
                    
                    # Get model configuration
                    from app.services.adapters import get_provider_models
                    models = get_provider_models(provider)
                    context_window = models[0].context_window if models else 4096
                    
                    usage_percentage = (estimated_tokens / context_window) * 100 if context_window > 0 else 0
                    
                    providers_stats.append({
                        "provider": provider.value,
                        "total_messages": summary["total_messages"],
                        "estimated_tokens": estimated_tokens,
                        "context_window": context_window,
                        "usage_percentage": min(usage_percentage, 100),
                        "optimization_applied": usage_percentage > 70,  # Assume optimization when over 70%
                        "last_optimization": datetime.utcnow().isoformat() if usage_percentage > 70 else None
                    })
                else:
                    providers_stats.append({
                        "provider": provider.value,
                        "total_messages": 0,
                        "estimated_tokens": 0,
                        "context_window": 4096,
                        "usage_percentage": 0,
                        "optimization_applied": False,
                        "last_optimization": None
                    })
                    
            except Exception as e:
                # Continue processing other providers if one fails
                continue
        
        return {
            "project_id": project_id,
            "providers": providers_stats,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation stats: {str(e)}")


@router.post("/{project_id}/reset-all")
async def reset_all_conversations(
    project_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Reset conversation history for all AI providers in the project"""
    
    # Validate project exists
    project = db.get(ProjectModel, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        cleared_providers = []
        
        for provider in [ModelProvider.DEEPSEEK, ModelProvider.QWEN, ModelProvider.KIMI, ModelProvider.DOUBAO]:
            try:
                cli = get_api_adapter_cli(provider, db)
                summary = cli.get_conversation_summary(project_id)
                
                if summary["total_messages"] > 0:
                    cli.clear_conversation_history(project_id)
                    cleared_providers.append(provider.value)
            except Exception:
                continue
        
        return {
            "success": True,
            "message": f"Cleared conversation history for {len(cleared_providers)} providers",
            "cleared_providers": cleared_providers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset conversations: {str(e)}")
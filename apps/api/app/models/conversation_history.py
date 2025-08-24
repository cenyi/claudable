"""
Conversation History Database Model
Persistent Storage of Multi-turn Conversation History for Domestic AI Models
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.sql import func
from app.db.base import Base


class ConversationHistoryModel(Base):
    """Conversation History Model"""
    __tablename__ = "conversation_history"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)  # deepseek, qwen, kimi, doubao
    sequence_number = Column(Integer, nullable=False)  # Message sequence in conversation
    role = Column(String, nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    images = Column(Text, nullable=True)  # JSON format image data
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Composite index for better query performance
    __table_args__ = (
        Index('idx_project_provider', 'project_id', 'provider'),
        Index('idx_project_provider_sequence', 'project_id', 'provider', 'sequence_number'),
    )
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, project_id={self.project_id}, provider={self.provider}, role={self.role})>"
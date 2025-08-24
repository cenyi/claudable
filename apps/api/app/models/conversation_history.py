"""
对话历史数据库模型
支持国产AI模型的多轮对话历史持久化存储
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.sql import func
from app.db.base import Base


class ConversationHistoryModel(Base):
    """对话历史模型"""
    __tablename__ = "conversation_history"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)  # deepseek, qwen, kimi, doubao
    sequence_number = Column(Integer, nullable=False)  # 消息在对话中的顺序
    role = Column(String, nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    images = Column(Text, nullable=True)  # JSON格式的图片数据
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 复合索引，提高查询性能
    __table_args__ = (
        Index('idx_project_provider', 'project_id', 'provider'),
        Index('idx_project_provider_sequence', 'project_id', 'provider', 'sequence_number'),
    )
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, project_id={self.project_id}, provider={self.provider}, role={self.role})>"
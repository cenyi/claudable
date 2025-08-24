#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加对话历史表
支持国产AI模型的持久化对话历史存储
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.base import Base
from app.models.conversation_history import ConversationHistoryModel


def create_conversation_history_table():
    """创建对话历史表"""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # 创建表
        Base.metadata.create_all(bind=engine, tables=[ConversationHistoryModel.__table__])
        
        print("✅ Successfully created conversation_history table")
        
        # 验证表是否创建成功
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_history'"))
            if result.fetchone():
                print("✅ Verified conversation_history table exists")
            else:
                print("❌ Failed to verify conversation_history table")
                
    except Exception as e:
        print(f"❌ Error creating conversation_history table: {e}")
        return False
        
    return True


if __name__ == "__main__":
    print("🔄 Starting database migration for conversation history...")
    success = create_conversation_history_table()
    if success:
        print("🎉 Database migration completed successfully!")
    else:
        print("💥 Database migration failed!")
        sys.exit(1)
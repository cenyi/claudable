#!/usr/bin/env python3
"""
Database Migration Script - Add Conversation History Table
Persistent conversation history storage supporting domestic AI models
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.base import Base
from app.models.conversation_history import ConversationHistoryModel


def create_conversation_history_table():
    """Create conversation history table"""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create table
        Base.metadata.create_all(bind=engine, tables=[ConversationHistoryModel.__table__])
        
        print("✅ Successfully created conversation_history table")
        
        # Verify table creation
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
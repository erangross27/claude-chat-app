"""
Database setup and models for Claude Chat Application.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://claude_user:claude_secure_2024@postgres:5432/claude_chat"
)

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Conversation(Base):
    """Conversation model to store chat sessions."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Message model to store individual chat messages."""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model = Column(String(100))  # Claude model used for assistant messages
    temperature = Column(String(10))  # Temperature setting used
    thinking_enabled = Column(Boolean, default=False)  # Whether thinking was enabled
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to conversation
    conversation = relationship("Conversation", back_populates="messages")

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    """Get a database session for direct use."""
    return SessionLocal()

"""
Database models for Claude Chat application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Conversation(Base):
    """Model for chat conversations."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    model = Column(String(50), nullable=False)  # claude-3-opus, claude-3-sonnet, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', model='{self.model}')>"


class Message(Base):
    """Model for individual chat messages."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"

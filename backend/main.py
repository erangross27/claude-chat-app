"""
FastAPI backend for Claude Chat Application.
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import anthropic
import uvicorn

# Import database models and functions
from database import (
    get_db, create_tables, get_db_session,
    Conversation, Message
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")
except ImportError:
    # python-dotenv not installed, that's fine
    pass

app = FastAPI(title="Claude Chat API", version="2.0")

# Enable CORS for all origins (since we're serving the frontend from the same server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since frontend is served from same server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React static files (for production build)
static_dir = os.getenv('STATIC_DIR', Path(__file__).parent / 'static')
if Path(static_dir).exists():
    # Mount the nested static directory that contains CSS and JS
    nested_static_dir = Path(static_dir) / 'static'
    if nested_static_dir.exists():
        app.mount("/static", StaticFiles(directory=nested_static_dir), name="static")
    else:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.1
    enable_thinking: bool = False
    conversation_id: Optional[str] = None
    enable_web_search: bool = False

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime

# Database models for API responses
class ConversationCreate(BaseModel):
    title: str

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model: Optional[str] = None
    temperature: Optional[str] = None
    thinking_enabled: bool = False
    created_at: datetime

class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

# Global variables
claude_client: Optional[anthropic.Anthropic] = None
active_connections: List[WebSocket] = []

# Claude models configuration - Latest Claude 4 models
CLAUDE_MODELS = {
    "claude-sonnet-4-20250514": {
        "name": "Claude 4 Sonnet",
        "max_tokens": 64000,
        "supports_thinking": True,
        "context_window": 200000,
        "description": "High-performance model with exceptional reasoning capabilities"
    },
    "claude-opus-4-20250514": {
        "name": "Claude 4 Opus",
        "max_tokens": 32000,
        "supports_thinking": True,
        "context_window": 200000,
        "description": "Our most capable and intelligent model yet"
    }
}

@app.on_event("startup")
async def startup_event():
    """Initialize the Claude client and database on startup."""
    global claude_client
    
    # Initialize database tables
    try:
        create_tables()
        logger.info("✅ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't fail startup if database initialization fails
        # This allows the app to start even if PostgreSQL is not ready yet
    
    # Try to get API key from environment variable
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not found!")
        logger.error("Please set the environment variable with:")
        logger.error("Windows: set ANTHROPIC_API_KEY=your_api_key_here")
        logger.error("Or create a .env file in the backend directory with:")
        logger.error("ANTHROPIC_API_KEY=your_api_key_here")
        raise RuntimeError("API key is required. Please set ANTHROPIC_API_KEY environment variable.")
    
    # Validate API key format
    if not api_key.startswith('sk-ant-'):
        logger.warning("API key doesn't start with 'sk-ant-', please verify it's correct")
    
    try:
        claude_client = anthropic.Anthropic(api_key=api_key)
        logger.info("✅ Claude client initialized successfully")
        logger.info(f"🔑 Using API key: {api_key[:12]}...")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Claude client: {e}")
        raise

@app.get("/")
async def root():
    """Serve the React app or health check."""
    static_dir = os.getenv('STATIC_DIR', Path(__file__).parent / 'static')
    index_file = Path(static_dir) / 'index.html'
    
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {"message": "Claude Chat API is running", "version": "2.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    if not claude_client:
        raise HTTPException(status_code=503, detail="Claude client not initialized")
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/models")
async def get_models():
    """Get available Claude models."""
    return {"models": CLAUDE_MODELS}

# Database API endpoints for conversation management
@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation."""
    try:
        db_conversation = Conversation(
            title=conversation.title
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        return ConversationResponse(
            id=db_conversation.id,
            title=db_conversation.title,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(db: Session = Depends(get_db)):
    """Get all conversations ordered by updated_at desc."""
    try:
        conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@app.get("/conversations/search", response_model=List[ConversationResponse])
async def search_conversations(q: str, db: Session = Depends(get_db)):
    """Search conversations by title and message content."""
    try:
        if not q or len(q.strip()) < 2:
            return []
            
        search_term = f"%{q.strip().lower()}%"
        
        # Search in conversation titles and message content
        conversations = db.query(Conversation).join(Message, Conversation.id == Message.conversation_id, isouter=True).filter(
            (Conversation.title.ilike(search_term)) | 
            (Message.content.ilike(search_term))
        ).distinct().order_by(Conversation.updated_at.desc()).all()
        
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to search conversations")

@app.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get a specific conversation with all messages."""
    try:
        logger.info(f"Loading conversation: {conversation_id}")
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages ordered by created_at
        messages_query = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at)
        messages = messages_query.all()
        
        logger.info(f"Found {len(messages)} messages for conversation {conversation_id}")
        
        message_responses = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                model=msg.model,
                temperature=msg.temperature,
                thinking_enabled=msg.thinking_enabled or False,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_responses
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        db.delete(conversation)
        db.commit()
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, title_data: dict, db: Session = Depends(get_db)):
    """Update conversation title."""
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation.title = title_data.get("title", conversation.title)
        conversation.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation title {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update conversation title")

@app.post("/conversations/{conversation_id}/generate-title")
async def generate_conversation_title(conversation_id: str, db: Session = Depends(get_db)):
    """Generate a conversation title using Claude based on the conversation content."""
    if not claude_client:
        raise HTTPException(status_code=500, detail="Claude client not initialized")
    
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get the first few messages from the conversation
        messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).limit(5).all()
        
        if not messages:
            return {"title": "New Chat"}
        
        # Prepare conversation content for title generation
        conversation_content = ""
        for msg in messages:
            conversation_content += f"{msg.role}: {msg.content}\n"
        
        # Generate title using Claude
        title_prompt = f"""Based on this conversation, generate a concise title that captures the main topic. 
        The title should be EXACTLY 4 words or less, no punctuation, just the core topic.

        Conversation:
        {conversation_content[:1000]}...

        Title (4 words max):"""
        
        try:
            response_text = ""
            with claude_client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=20,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": title_prompt}]
                }]
            ) as stream:
                for text in stream.text_stream:
                    response_text += text
            
            # Clean up the generated title
            generated_title = response_text.strip().replace('"', '').replace("'", "")
            # Limit to 4 words
            title_words = generated_title.split()[:4]
            final_title = " ".join(title_words)
            
            # Update the conversation title
            conversation.title = final_title
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
            return {"title": final_title}
            
        except Exception as claude_error:
            logger.error(f"Error generating title with Claude: {claude_error}")
            # Fallback to first message excerpt
            first_message = messages[0].content[:30] + "..." if len(messages[0].content) > 30 else messages[0].content
            conversation.title = first_message
            db.commit()
            return {"title": first_message}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating conversation title {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate conversation title")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Non-streaming chat endpoint."""
    if not claude_client:
        raise HTTPException(status_code=500, detail="Claude client not initialized")
    
    try:
        # Save user message if conversation_id is provided
        if request.conversation_id:
            logger.info(f"💾 Saving user message to conversation {request.conversation_id}")
            user_message = Message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.message,
                model=None,  # User messages don't have a model
                temperature=str(request.temperature),
                thinking_enabled=request.enable_thinking
            )
            db.add(user_message)
            try:
                db.commit()
                logger.info(f"✅ User message saved successfully")
            except Exception as commit_error:
                logger.error(f"❌ Failed to save user message: {commit_error}")
                db.rollback()
                raise
        
        # Prepare conversation history
        messages = []
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": [{"type": "text", "text": msg.content}]
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": request.message}]
        })
        
        # Get model configuration
        model_config = CLAUDE_MODELS.get(request.model, CLAUDE_MODELS["claude-sonnet-4-20250514"])
        
        # Make API call
        api_params = {
            "model": request.model,
            "max_tokens": model_config["max_tokens"],
            "temperature": request.temperature,
            "messages": messages
        }
        
        # Add thinking parameter if supported and enabled
        if request.enable_thinking and model_config.get("supports_thinking", False):
            api_params["thinking"] = True
            
        # Add web search tool if enabled
        if request.enable_web_search:
            api_params["tools"] = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        
        # Use streaming to avoid the 10-minute timeout warning
        response_text = ""
        with claude_client.messages.stream(**api_params) as stream:
            for text in stream.text_stream:
                response_text += text
        
        # Save assistant message if conversation_id is provided
        if request.conversation_id and response_text:
            logger.info(f"💾 Saving assistant message to conversation {request.conversation_id}")
            assistant_message = Message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=response_text,
                model=request.model,
                temperature=str(request.temperature),
                thinking_enabled=request.enable_thinking
            )
            db.add(assistant_message)
            
            # Update conversation timestamp
            conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
            if conversation:
                conversation.updated_at = datetime.utcnow()
            
            try:
                db.commit()
                logger.info(f"✅ Assistant message saved successfully")
            except Exception as commit_error:
                logger.error(f"❌ Failed to save assistant message: {commit_error}")
                db.rollback()
        
        return ChatResponse(
            message=response_text,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("✅ WebSocket connection accepted")
    
    try:
        while True:
            # Receive message from client
            logger.info("🔄 Waiting for WebSocket message...")
            data = await websocket.receive_json()
            logger.info(f"📥 Received WebSocket data: {data}")
            
            # Process the chat request
            await process_streaming_chat(websocket, data)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("❌ WebSocket client disconnected")
    except Exception as e:
        logger.error(f"💥 WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

async def process_streaming_chat(websocket: WebSocket, data: Dict[str, Any]):
    """Process streaming chat request."""
    logger.info(f"🚀 Processing streaming chat with data: {data}")
    
    if not claude_client:
        await websocket.send_json({"type": "error", "message": "Claude client not initialized"})
        return
    
    try:
        # Extract request data
        message = data.get("message", "")
        conversation_history = data.get("conversation_history", [])
        model = data.get("model", "claude-sonnet-4-20250514")
        temperature = data.get("temperature", 0.1)
        enable_thinking = data.get("enable_thinking", False)
        enable_web_search = data.get("enable_web_search", False)
        conversation_id = data.get("conversation_id")  # Optional conversation ID
        
        logger.info(f"📨 Message: {message[:100]}...")
        logger.info(f"🗂️ Conversation ID: {conversation_id}")
        logger.info(f"🤖 Model: {model}")
        
        # Get database session
        db = get_db_session()
        
        try:
            # If conversation_id is provided, save the user message
            if conversation_id:
                logger.info(f"💾 Saving user message to conversation {conversation_id}")
                user_message = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    model=None,  # User messages don't have a model
                    temperature=str(temperature),
                    thinking_enabled=enable_thinking
                )
                db.add(user_message)
                try:
                    db.commit()
                    logger.info(f"✅ User message saved successfully")
                except Exception as commit_error:
                    logger.error(f"❌ Failed to save user message: {commit_error}")
                    db.rollback()
                    raise
        
            # Prepare messages
            messages = []
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}]
                })
            
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": message}]
            })
            
            # Get model configuration
            model_config = CLAUDE_MODELS.get(model, CLAUDE_MODELS["claude-sonnet-4-20250514"])
            
            # Send status update
            await websocket.send_json({"type": "status", "message": f"Processing with {model_config['name']}..."})
            
            # Prepare streaming parameters with model-specific timeouts
            stream_params = {
                "model": model,
                "max_tokens": model_config["max_tokens"],
                "temperature": temperature,
                "messages": messages
            }
            
            # Add thinking parameter if supported and enabled
            if enable_thinking and model_config.get("supports_thinking", False):
                stream_params["thinking"] = True
                
            # Add web search tool if enabled
            if enable_web_search:
                stream_params["tools"] = [{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5
                }]
            
            # Stream response with timeout handling
            try:
                response_sent = False
                with claude_client.messages.stream(**stream_params) as stream:
                    full_response = ""
                    chunk_count = 0
                    
                    for text in stream.text_stream:
                        full_response += text
                        chunk_count += 1
                        
                        # Send chunk update
                        await websocket.send_json({
                            "type": "chunk",
                            "content": text,
                            "full_message": full_response
                        })
                        
                        # For Opus model, add small delay to prevent overwhelming
                        if model == "claude-opus-4-20250514" and chunk_count % 10 == 0:
                            await asyncio.sleep(0.01)  # 10ms delay every 10 chunks
                    
                    # Send completion signal only once and save assistant message
                    if not response_sent:
                        await websocket.send_json({
                            "type": "complete",
                            "message": full_response,
                            "timestamp": datetime.now().isoformat()
                        })
                        response_sent = True
                        logger.info(f"✅ Completed {model} response with {len(full_response)} characters")
                        
                        # Save assistant message to database if conversation_id is provided
                        if conversation_id and full_response:
                            logger.info(f"💾 Saving assistant message to conversation {conversation_id}")
                            assistant_message = Message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=full_response,
                                model=model,
                                temperature=str(temperature),
                                thinking_enabled=enable_thinking
                            )
                            db.add(assistant_message)
                            
                            # Update conversation timestamp
                            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                            if conversation:
                                conversation.updated_at = datetime.utcnow()
                            
                            try:
                                db.commit()
                                logger.info(f"✅ Assistant message saved successfully")
                            except Exception as commit_error:
                                logger.error(f"❌ Failed to save assistant message: {commit_error}")
                                db.rollback()
                    
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Request timed out for {model_config['name']}. Please try again."
                })
            except Exception as stream_error:
                logger.error(f"Streaming error for {model}: {stream_error}")
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Streaming error with {model_config['name']}: {str(stream_error)}"
                })
        finally:
            try:
                db.close()
                logger.info("🔒 Database session closed")
            except Exception as close_error:
                logger.error(f"Error closing database session: {close_error}")
                
    except Exception as e:
        logger.error(f"Streaming chat error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

# Catch-all route for React app - MUST BE LAST!
@app.get("/{path:path}")
async def serve_react_app(path: str):
    """Serve React app for any non-API route."""
    # Skip API routes
    if path.startswith("conversations") or path.startswith("chat") or path.startswith("ws") or path.startswith("health") or path.startswith("models"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    static_dir = os.getenv('STATIC_DIR', Path(__file__).parent / 'static')
    file_path = Path(static_dir) / path
    index_file = Path(static_dir) / 'index.html'
    
    # If the file exists, serve it
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    # Otherwise, serve index.html (for React routing)
    elif index_file.exists():
        return FileResponse(index_file)
    else:
        return {"message": "Claude Chat API is running", "version": "2.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

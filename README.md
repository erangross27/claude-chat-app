# Claude Chat Application

A modern, full-stack chat interface for Claude 4 models with React frontend, FastAPI backend, and PostgreSQL database. Fully containerized with Docker and Docker Compose for easy deployment.

## Features

- 🤖 **Claude 4 Models**: Support for Claude 4 Sonnet and Claude 4 Opus
- 🚀 **Real-time Streaming**: WebSocket-based streaming responses  
- 🎯 **Extended Thinking**: Advanced reasoning capabilities
- 🌐 **Web Search**: Integrated web search functionality
- 📋 **Copy Code**: One-click copy for code blocks
- 💾 **Persistent Conversations**: PostgreSQL database storage
- 🔍 **Conversation Search**: Find past conversations easily
- 🌍 **RTL/LTR Support**: Right-to-left language support
- 🎨 **Modern UI**: Full-screen responsive design
- 🐳 **Docker Ready**: Multi-container deployment with Docker Compose

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Anthropic API key

### Setup

1. **Set your API key** (required):
   ```powershell
   # Temporary (current session only)
   $env:ANTHROPIC_API_KEY = "your_api_key_here"
   
   # Permanent (all future sessions)
   setx ANTHROPIC_API_KEY "your_api_key_here"
   ```

2. **Optional: Set database password**:
   ```powershell
   # Optional - defaults to 'claude_secure_2024' if not set
   setx POSTGRES_PASSWORD "your_secure_password_here"
   ```

3. **Start the application**:
   ```powershell
   # Quick start (recommended)
   .\start_docker_compose.bat
   
   # Or manually with Docker Compose
   docker-compose up --build
   ```

4. **Access the application**:
   ```
   http://localhost:8000
   ```

The application will automatically:
- Start PostgreSQL database
- Build and run the React frontend
- Start the FastAPI backend
- Set up all necessary database tables

## Usage

1. **Select Model**: Choose between Claude 4 Sonnet (fast) or Claude 4 Opus (most capable)
2. **Create Conversations**: Start new conversations or continue existing ones
3. **Extended Thinking**: Toggle advanced reasoning mode for complex problems
4. **Temperature**: Adjust response creativity (0.1 = focused, 1.0 = creative)
5. **Web Search**: Enable web search for current information
6. **Streaming**: Real-time response streaming via WebSocket
7. **Copy Code**: Click the copy button on any code block
8. **Search History**: Use the search feature to find past conversations
9. **RTL Support**: Interface automatically adapts for right-to-left languages

## Models

| Model | Max Tokens | Best For |
|-------|------------|----------|
| **Claude 4 Sonnet** | 64,000 | High performance, fast responses |
| **Claude 4 Opus** | 32,000 | Maximum intelligence, complex reasoning |

## Troubleshooting

### Docker Issues
- Ensure Docker Desktop is running
- Check API key is set: `echo $env:ANTHROPIC_API_KEY`
- Rebuild if needed: `docker build -t claude-chat-app .`

### Common Fixes
- **Blank page**: Wait for container to fully start (check logs)
- **WebSocket errors**: Refresh browser or restart container
- **API errors**: Verify API key is valid and has credits

## Development

The application consists of:
- **Frontend**: React 18 with WebSocket streaming
- **Backend**: FastAPI with Anthropic SDK
- **Container**: Multi-stage Docker build

Built for reliability and ease of deployment on any Windows machine with Docker.

## 🛠 Architecture

```
├── backend/           # FastAPI Python backend
│   ├── main.py       # FastAPI application with Claude 4 integration
│   ├── database.py   # Database connection and setup
│   ├── models.py     # SQLAlchemy models for conversations/messages
│   ├── requirements.txt
│   └── static/       # Built React frontend files (auto-generated)
├── frontend/         # React frontend
│   ├── src/
│   │   ├── App.js    # Main React component with streaming
│   │   ├── App.css   # Modern styling with RTL support
│   │   └── index.js  # React entry point
│   ├── package.json
│   └── public/       # Static assets
├── Dockerfile        # Multi-stage build (Node.js + Python)
├── docker-compose.yml # Multi-service setup with PostgreSQL
├── *.bat            # Windows batch files for easy startup
└── README.md
```

## 🔧 API Endpoints

- `GET /` - Serves React frontend
- `GET /health` - Health check
- `GET /models` - Available Claude 4 models
- `POST /chat` - Send chat message (non-streaming)
- `WebSocket /ws` - Streaming chat connection
- `GET /conversations` - List all conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}` - Get specific conversation with messages
- `DELETE /conversations/{id}` - Delete conversation
- `GET /conversations/search` - Search conversations by title/content

## 🎨 Modern UI Features

This React + FastAPI + PostgreSQL solution provides:
- ✅ Real-time streaming responses
- ✅ Copy-to-clipboard for code blocks
- ✅ Model selection (Claude 4 Sonnet/Opus)
- ✅ Extended thinking mode
- ✅ Temperature control
- ✅ Web search integration
- ✅ Persistent conversation history
- ✅ Conversation search functionality
- ✅ RTL/LTR language support
- ✅ Full-screen responsive design
- ✅ Professional, modern appearance

## 🚀 Deployment

### Docker Compose (Recommended)
The application uses Docker Compose to manage multiple services:
- **PostgreSQL**: Database for persistent storage
- **Claude Chat App**: React frontend + FastAPI backend in one container

### For Development
If you want to modify the code:
1. Make changes to frontend or backend files
2. Rebuild and restart: `docker-compose up --build`
3. The application will be available at `http://localhost:8000`

### Database
- **PostgreSQL 15** with persistent volume storage
- Automatic database initialization and table creation
- Default credentials can be customized via environment variables

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | - | Your Anthropic API key |
| `POSTGRES_PASSWORD` | No | `claude_secure_2024` | PostgreSQL database password |
| `DATABASE_URL` | No | Auto-generated | PostgreSQL connection string |

Example setup:
```powershell
# Windows PowerShell - Required
$env:ANTHROPIC_API_KEY = "your_api_key_here"

# Optional - customize database password
$env:POSTGRES_PASSWORD = "your_secure_password"
```

## 🎯 What Makes This Special

- **Complete Solution**: Full-stack app with database persistence
- **One-Click Deploy**: Run `start_docker_compose.bat` and you're done
- **Production Ready**: Multi-service architecture with health checks
- **Persistent Storage**: All conversations saved in PostgreSQL
- **Modern Stack**: React 18 + FastAPI + PostgreSQL 15
- **RTL Support**: Works with Hebrew, Arabic, and other RTL languages
- **Latest Claude 4**: Support for the newest and most capable models
- **Cross-Platform**: Docker ensures it works anywhere

## 📄 License

This project is open source and available under the MIT License.

---

**Enjoy your modern, full-featured Claude chat application with persistent conversations!** 🎉

# RADIRA Web Chat Interface

Antarmuka web chat untuk RADIRA AI Autonomous Agent yang memungkinkan interaksi real-time melalui browser.

## Fitur Utama

### 🎨 **Modern Web Interface**
- UI yang clean dan modern dengan dark theme
- Responsive design untuk desktop dan mobile
- Real-time messaging dengan WebSocket
- Typing indicators dan status updates

### 🤖 **Multi-Orchestrator Support**
- **Function Calling Mode** - Claude-like pure LLM reasoning
- **Dual Orchestrator** - Anti-looping mechanisms
- **Classic Orchestrator** - Legacy ReAct-based

### 🧠 **Semantic Memory**
- Optional ChromaDB integration
- Learn from past experiences
- Context-aware responses

### 🛡️ **Safety Controls**
- Configurable confirmation modes
- Sandbox mode support
- Real-time execution monitoring

### 📊 **Statistics & Monitoring**
- Token usage tracking
- Iteration counts
- Tool execution statistics

## Struktur File

```
radira/
├── web_chat.py              # FastAPI backend server
├── web/
│   ├── index.html          # Main HTML interface
│   └── static/
│       ├── style.css       # UI styling
│       └── app.js          # Frontend JavaScript
```

## Instalasi & Setup

### 1. Prerequisites

Pastikan semua dependencies sudah terinstall:

```bash
pip install -r requirements.txt
```

Dependencies utama yang diperlukan:
- `fastapi>=0.109.2` - Web framework
- `uvicorn>=0.27.1` - ASGI server
- `websockets` - WebSocket support (included in uvicorn)

### 2. Konfigurasi Environment

Pastikan file `.env` sudah dikonfigurasi dengan benar:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
WORKING_DIRECTORY=./workspace
SANDBOX_MODE=true
```

## Menjalankan Web Chat

### Method 1: Direct Run

```bash
python web_chat.py
```

Server akan berjalan di: **http://localhost:8000**

### Method 2: Custom Configuration

```bash
# Custom port
python web_chat.py --port 8080

# Custom host
python web_chat.py --host 127.0.0.1 --port 8080

# Development mode with auto-reload
python web_chat.py --reload
```

### Method 3: Production (Uvicorn)

```bash
uvicorn web_chat:app --host 0.0.0.0 --port 8000 --workers 4
```

## Cara Menggunakan

### 1. **Start the Server**

```bash
python web_chat.py
```

Output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     RADIRA Web Chat initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. **Open Browser**

Buka browser dan akses: **http://localhost:8000**

### 3. **Configure Settings (Optional)**

Klik tombol **Settings** untuk mengatur:

- **Orchestrator Mode**:
  - Function Calling (recommended) - Claude-like reasoning
  - Dual Orchestrator - Anti-looping mechanisms
  - Classic - Legacy mode

- **Semantic Memory**:
  - Enable/disable ChromaDB memory
  - Learn from past interactions

- **Confirmation Mode**:
  - Auto - Smart decision making
  - Yes - Always execute without asking
  - No - Always ask for confirmation

### 4. **Start Chatting**

Klik **Start Chatting** atau konfigurasi settings terlebih dahulu.

### 5. **Send Tasks**

Contoh tasks yang bisa dikirim:

```
Create a landing page for a coffee shop
```

```
List all Python files in the current directory
```

```
Generate a React todo app with Tailwind CSS
```

```
Write a Python function to calculate fibonacci numbers
```

```
Run git status
```

## API Endpoints

### Session Management

#### Create New Session
```http
POST /api/session/new
Content-Type: application/json

{
  "config": {
    "orchestrator_type": "function_calling",
    "enable_memory": false,
    "confirmation_mode": "auto"
  }
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "config": {...},
  "message": "Session created successfully"
}
```

#### Get Session Info
```http
GET /api/session/{session_id}
```

#### Delete Session
```http
DELETE /api/session/{session_id}
```

#### Reset Session
```http
POST /api/session/{session_id}/reset
```

### Tools

#### List Available Tools
```http
GET /api/tools
```

### WebSocket

#### Chat Connection
```
ws://localhost:8000/ws/{session_id}
```

**Message Types:**

Client to Server:
```json
{
  "type": "message",
  "content": "Your task here"
}
```

Server to Client:
```json
{
  "type": "assistant_message",
  "content": "Response from AI"
}
```

```json
{
  "type": "status",
  "message": "Processing your request..."
}
```

```json
{
  "type": "stats",
  "data": {
    "iteration": 2,
    "tokens": 1234,
    "tools_used": 3
  }
}
```

## Architecture Overview

### Backend (FastAPI)

```
web_chat.py
├── Session Management
│   ├── Create/Delete sessions
│   ├── Store agent instances
│   └── Manage session state
│
├── WebSocket Handler
│   ├── Real-time messaging
│   ├── Status updates
│   └── Error handling
│
└── Tool Integration
    └── All 7 RADIRA tools
```

### Frontend (Vanilla JS)

```
app.js
├── RadiraChat Class
│   ├── Session management
│   ├── WebSocket handling
│   ├── UI updates
│   └── Message handling
│
└── Event Listeners
    ├── User input
    ├── Settings
    └── Connection status
```

## Available Tools

Semua tools dari CLI version tersedia:

1. **file_system** - File operations (read, write, list, search)
2. **terminal** - Execute shell commands
3. **web_generator** - Generate web applications (HTML/React/Vue)
4. **code_generator** - Generate code (Python, Java, Rust, Go, etc.)
5. **web_search** - Web search capabilities
6. **pentest** - Basic penetration testing
7. **enhanced_pentest** - Advanced pentesting with AI payloads

## Troubleshooting

### Port Already in Use

```bash
# Use different port
python web_chat.py --port 8080
```

### ChromaDB Connection Issues

Jika memory mode enabled dan ChromaDB error:

```bash
# Check ChromaDB installation
pip install chromadb==0.5.0

# Disable telemetry (already handled in code)
export ANONYMIZED_TELEMETRY=False
```

### WebSocket Connection Failed

1. Check firewall settings
2. Ensure server is running
3. Check browser console for errors
4. Try different browser

### Session Not Found

- Sessions are stored in memory
- Restarting server will clear all sessions
- Create new session after server restart

## Development

### Enable Debug Mode

```bash
# Auto-reload on code changes
python web_chat.py --reload
```

### Check Logs

Server logs akan menampilkan:
- Session creation/deletion
- WebSocket connections
- Tool executions
- Errors and exceptions

## Security Considerations

### Production Deployment

1. **HTTPS/WSS**: Use SSL certificates
2. **Authentication**: Add user authentication
3. **Rate Limiting**: Implement request throttling
4. **CORS**: Configure allowed origins
5. **Sandbox Mode**: Keep enabled in production

### Environment Variables

```env
# Required
GROQ_API_KEY=your_key_here

# Recommended for production
SANDBOX_MODE=true
MAX_ITERATIONS=10
COMMAND_TIMEOUT_SECONDS=30
```

## Performance Tips

1. **Use Function Calling Mode** - Faster and more efficient
2. **Disable Memory** - If not needed, reduces overhead
3. **Worker Processes** - Use multiple workers in production
4. **Connection Pooling** - For high traffic scenarios

## Differences from CLI Version

### Web Chat Advantages:
- ✅ Multi-user support (separate sessions)
- ✅ No terminal required
- ✅ Better accessibility
- ✅ Real-time status updates
- ✅ Persistent UI state

### CLI Advantages:
- ✅ Richer console output (colors, tables)
- ✅ Better for scripting
- ✅ Lower latency
- ✅ More control over execution

## Future Enhancements

Planned features:
- [ ] User authentication & authorization
- [ ] Session persistence (database storage)
- [ ] File upload/download interface
- [ ] Streaming LLM responses (token by token)
- [ ] Conversation export (JSON/Markdown)
- [ ] Multiple concurrent sessions per user
- [ ] Admin dashboard
- [ ] Usage analytics

## Support

Untuk pertanyaan atau issues:
1. Check logs di terminal
2. Check browser console untuk frontend errors
3. Refer to main RADIRA documentation

## Credits

**RADIRA Web Chat Interface**
- Created by: Nerrow
- Based on: RADIRA AI Autonomous Agent
- Framework: FastAPI + WebSocket + Vanilla JS
- Version: 1.0.0

---

**Enjoy using RADIRA Web Chat! 🤖✨**

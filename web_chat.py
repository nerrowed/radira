"""Web Chat Interface for RADIRA AI Agent.

This module provides a FastAPI-based web interface with WebSocket support
for real-time chat interactions with the RADIRA autonomous agent.
"""

# Disable ChromaDB telemetry BEFORE any imports
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "none"

import sys
import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Reduce verbose logging
logging.getLogger("chromadb.api.segment").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("groq._base_client").setLevel(logging.WARNING)

from agent.tools.registry import get_registry
from agent.tools.filesystem import FileSystemTool
from agent.tools.terminal import TerminalTool
from agent.tools.web_generator import WebGeneratorTool
from agent.tools.code_generator import CodeGeneratorTool
from agent.tools.web_search import WebSearchTool
from agent.tools.pentest import PentestTool
from agent.tools.enhanced_pentest import EnhancedPentestTool
from agent.utils.workspace import setup_workspace
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="RADIRA Web Chat", version="1.0.0")

# Session storage
sessions: Dict[str, dict] = {}


class Message(BaseModel):
    """Chat message model."""
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: str


class SessionConfig(BaseModel):
    """Session configuration model."""
    orchestrator_type: str = "function_calling"  # function_calling, dual, classic
    enable_memory: bool = False
    confirmation_mode: str = "auto"  # yes, no, auto
    model: str = "llama-3.1-70b-versatile"


class SessionCreate(BaseModel):
    """Session creation request."""
    config: Optional[SessionConfig] = None


class ChatMessage(BaseModel):
    """Chat message request."""
    message: str
    session_id: str


class ConfirmAction(BaseModel):
    """Action confirmation request."""
    session_id: str
    confirmed: bool


def get_orchestrator_class(orchestrator_type: str):
    """Get orchestrator class by type."""
    if orchestrator_type == "function_calling":
        from agent.core.function_orchestrator import FunctionOrchestrator
        return FunctionOrchestrator
    elif orchestrator_type == "dual":
        from agent.core.dual_orchestrator import DualOrchestrator
        return DualOrchestrator
    else:
        from agent.core.orchestrator import AgentOrchestrator
        return AgentOrchestrator


def get_agent_state(agent, orchestrator_type: str) -> Dict[str, Any]:
    """Get agent state/stats compatible with all orchestrator types.

    Args:
        agent: Orchestrator instance
        orchestrator_type: Type of orchestrator

    Returns:
        Normalized state dictionary
    """
    if orchestrator_type == "function_calling":
        # FunctionOrchestrator uses get_stats()
        stats = agent.get_stats()
        return {
            "iteration": stats.get("total_iterations", 0),
            "max_iterations": agent.max_iterations,
            "token_stats": {
                "total_tokens": stats.get("total_tokens_used", 0),
                "prompt_tokens": 0,  # Not tracked separately
                "completion_tokens": 0  # Not tracked separately
            },
            "tool_stats": {},  # FunctionOrchestrator doesn't track per-tool stats
            "messages_count": stats.get("messages_in_history", 0),
            "functions_available": stats.get("functions_available", 0)
        }
    else:
        # DualOrchestrator and ClassicOrchestrator use get_state()
        return agent.get_state()


def setup_tools():
    """Register all available tools."""
    workspace_dirs = setup_workspace()
    logger.info(f"Workspace ready: {workspace_dirs['base']}")

    registry = get_registry()

    # Register tools
    tools = [
        FileSystemTool(working_directory=settings.working_directory),
        TerminalTool(working_directory=settings.working_directory),
        WebGeneratorTool(output_directory=settings.working_directory),
        CodeGeneratorTool(output_directory=settings.working_directory),
        WebSearchTool(max_results=5),
        PentestTool(working_directory=settings.working_directory),
        EnhancedPentestTool(working_directory=settings.working_directory)
    ]

    for tool in tools:
        registry.register(tool)
        logger.info(f"Registered tool: {tool.name}")

    return registry


@app.on_event("startup")
async def startup_event():
    """Initialize tools on startup."""
    try:
        setup_tools()
        logger.info("RADIRA Web Chat initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")


@app.get("/")
async def get_index():
    """Serve the main chat interface."""
    html_file = Path(__file__).parent / "web" / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>RADIRA Web Chat</title></head>
                <body>
                    <h1>RADIRA Web Chat</h1>
                    <p>Frontend file not found. Please create web/index.html</p>
                </body>
            </html>
            """
        )


@app.post("/api/session/new")
async def create_session(request: SessionCreate):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())

    config = request.config or SessionConfig()

    try:
        # Get orchestrator class
        OrchestratorClass = get_orchestrator_class(config.orchestrator_type)

        # Initialize orchestrator
        if config.orchestrator_type == "function_calling":
            agent = OrchestratorClass(
                verbose=True,
                enable_memory=config.enable_memory,
                confirmation_mode=config.confirmation_mode
            )
        else:
            agent = OrchestratorClass(verbose=True)

        # Store session
        sessions[session_id] = {
            "id": session_id,
            "agent": agent,
            "config": config.dict(),
            "history": [],
            "created_at": datetime.now().isoformat(),
            "pending_confirmation": None
        }

        logger.info(f"Created session {session_id} with {config.orchestrator_type} orchestrator")

        return {
            "session_id": session_id,
            "config": config.dict(),
            "message": "Session created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    # Get agent state
    state = get_agent_state(session["agent"], session["config"]["orchestrator_type"])

    return {
        "session_id": session_id,
        "config": session["config"],
        "created_at": session["created_at"],
        "history": session["history"],
        "state": {
            "iteration": state["iteration"],
            "max_iterations": state["max_iterations"],
            "token_stats": state["token_stats"],
            "tool_stats": state.get("tool_stats", {})
        }
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    logger.info(f"Deleted session {session_id}")

    return {"message": "Session deleted successfully"}


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset session state."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    session["agent"].reset()
    session["history"] = []

    return {"message": "Session reset successfully"}


@app.get("/api/tools")
async def list_tools():
    """List all available tools."""
    registry = get_registry()
    tools = registry.list_tools()

    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "is_dangerous": tool.is_dangerous
            }
            for tool in tools
        ]
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    # Check if session exists
    if session_id not in sessions:
        await websocket.send_json({
            "type": "error",
            "message": "Session not found. Please create a new session."
        })
        await websocket.close()
        return

    session = sessions[session_id]

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to RADIRA. Session ID: {session_id}",
            "orchestrator": session["config"]["orchestrator_type"]
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "message":
                user_message = data.get("content", "")

                # DEBUG: Log received message
                logger.info(f"[Session {session_id[:8]}] Received message: {user_message!r}")

                # Add to history
                session["history"].append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })

                # Send acknowledgment
                await websocket.send_json({
                    "type": "user_message",
                    "content": user_message
                })

                try:
                    # Send thinking status
                    await websocket.send_json({
                        "type": "status",
                        "message": "Processing your request..."
                    })

                    # Execute task
                    agent = session["agent"]
                    logger.info(f"[Session {session_id[:8]}] Executing with {session['config']['orchestrator_type']} orchestrator")
                    result = agent.run(user_message)
                    logger.info(f"[Session {session_id[:8]}] Result: {result!r}")

                    # Add to history
                    session["history"].append({
                        "role": "assistant",
                        "content": result,
                        "timestamp": datetime.now().isoformat()
                    })

                    # Send result
                    await websocket.send_json({
                        "type": "assistant_message",
                        "content": result
                    })

                    # Send stats
                    state = get_agent_state(agent, session["config"]["orchestrator_type"])

                    # Calculate tools used based on orchestrator type
                    tools_used = 0
                    if session["config"]["orchestrator_type"] == "function_calling":
                        tools_used = state.get("iteration", 0)  # Use iteration count as proxy
                    else:
                        tools_used = sum(
                            stats["execution_count"]
                            for stats in state.get("tool_stats", {}).values()
                        )

                    await websocket.send_json({
                        "type": "stats",
                        "data": {
                            "iteration": state["iteration"],
                            "tokens": state["token_stats"]["total_tokens"],
                            "tools_used": tools_used
                        }
                    })

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error: {str(e)}"
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
        except:
            pass


# Mount static files
static_dir = Path(__file__).parent / "web" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def main():
    """Run the web chat server."""
    import argparse

    parser = argparse.ArgumentParser(description="RADIRA Web Chat Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    logger.info(f"Starting RADIRA Web Chat on {args.host}:{args.port}")
    logger.info(f"Open http://localhost:{args.port} in your browser")

    uvicorn.run(
        "web_chat:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

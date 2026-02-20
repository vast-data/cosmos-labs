"""
Research Assistant API
FastAPI application for research assistant with RAG backend integration
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI

from config import API_TITLE, API_DESCRIPTION, API_VERSION, AGENT_INSTRUCTIONS
from api.routes.auth import AuthRouter
from api.routes.tools import ToolsRouter
from api.routes.collections import CollectionsRouter
from api.routes.sessions import SessionsRouter
from api.routes.prompts import PromptsRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Register routes
app.post("/api/v1/login", response_model=None)(AuthRouter.login)
app.get("/api/auth/login/nvlogin")(AuthRouter.azure_ad_login)
app.get("/api/auth/callback/nvlogin")(AuthRouter.azure_ad_callback)
app.get("/api/v1/auth/exchange-session")(AuthRouter.exchange_session_token)
app.get("/api/v1/tools", response_model=None)(ToolsRouter.get_tools)
app.get("/api/v1/collections", response_model=None)(CollectionsRouter.get_collections)
app.get("/api/v1/fullcollections", response_model=None)(CollectionsRouter.get_full_collections)
app.post("/api/v1/collections", response_model=None)(CollectionsRouter.create_collection_endpoint)
app.delete("/api/v1/collections", response_model=None)(CollectionsRouter.delete_collections_endpoint)
app.post("/api/v1/documents")(CollectionsRouter.upload_document_endpoint)
app.get("/api/v1/documents", response_model=None)(CollectionsRouter.list_documents_endpoint)
app.post("/api/v1/prompt", response_model=None)(PromptsRouter.send_prompt)
app.post("/api/v1/prompt/stream")(PromptsRouter.send_prompt_stream)
app.get("/api/v1/sessions", response_model=None)(SessionsRouter.list_sessions)
app.get("/api/v1/sessions/{session_id}", response_model=None)(SessionsRouter.get_session)
app.patch("/api/v1/sessions/{session_id}", response_model=None)(SessionsRouter.update_session)

@app.get("/api/v1/system-prompt")
async def get_system_prompt():
    """Get the default system prompt/instructions for the agent"""
    return {"system_prompt": AGENT_INSTRUCTIONS}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

"""
Pydantic models for API requests and responses
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    base_url: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    jwt_token: str  # Same as access_token, for clarity
    jwt_payload: Dict[str, Any]  # Decoded JWT payload


class CollectionItem(BaseModel):
    id: str
    description: str
    num_entities: int = 0


class CollectionsResponse(BaseModel):
    collections: List[CollectionItem]


class PromptRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None
    collections: Optional[List[str]] = None
    session_name: Optional[str] = None  # Optional session name, defaults to "My Session" for new sessions
    tools: Optional[List[str]] = None  # Optional list of tool names to use (e.g., ["retrieve_chunks", "duckduckgo_search"])
    internet_search: Optional[bool] = None  # If False, do not use DuckDuckGo. If missing or True, use DuckDuckGo.
    system_prompt: Optional[str] = None  # Optional custom system prompt to override the default AGENT_INSTRUCTIONS
    # Agent/No agent - ignoring for now
    # Agent response preference - ignoring for now


class PromptResponse(BaseModel):
    session_id: str
    response: Dict[str, Any]


class SessionItem(BaseModel):
    session_id: str
    created_at: int
    updated_at: int
    summary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[str]] = None  # Citations from retrieve_chunks tool calls
    collection_metadata: Optional[Dict[str, Any]] = None  # Collection metadata from retrieve_chunks tool calls


class SessionsResponse(BaseModel):
    sessions: List[SessionItem]
    total: int


class SessionResponse(BaseModel):
    session_id: str
    created_at: int
    updated_at: int
    summary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[str]] = None  # Citations from retrieve_chunks tool calls
    collection_metadata: Optional[Dict[str, Any]] = None  # Collection metadata from retrieve_chunks tool calls
    tool_events: Optional[List[Dict[str, Any]]] = None  # tool_start and tool_ended events from all runs


class CreateCollectionRequest(BaseModel):
    collection_name: str
    is_public: bool = True


class CreateCollectionResponse(BaseModel):
    message: str
    collection_name: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class DeleteCollectionsRequest(BaseModel):
    collection_names: List[str]


class DeleteCollectionsResponse(BaseModel):
    message: str
    deleted_collections: List[str]
    result: Optional[Dict[str, Any]] = None


class UploadDocumentRequest(BaseModel):
    collection_name: str
    allowed_groups: Optional[List[str]] = None
    is_public: bool = False


class UpdateSessionRequest(BaseModel):
    summary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolItem(BaseModel):
    name: str
    description: str
    category: str


class ToolsResponse(BaseModel):
    tools: List[ToolItem]


class FullCollectionItem(BaseModel):
    """Collection with full metadata from VastDB"""
    name: str
    num_chunks: int
    num_unique_files: int
    total_doc_size_bytes: int
    total_doc_size_mb: float


class FullCollectionsResponse(BaseModel):
    """Response with full collection details"""
    collections: List[FullCollectionItem]
    total: int


class DocumentItem(BaseModel):
    """Document item in list"""
    document_name: str


class ListDocumentsResponse(BaseModel):
    """Response for listing documents"""
    message: str
    total_documents: int
    documents: List[DocumentItem]


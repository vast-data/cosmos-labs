"""
Agent service
Handles agent creation and management with VastDB storage
"""

import os
import sys
import logging
import importlib.util
from typing import Optional, Dict, Any, List, Callable, Tuple
import httpx

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reasoning import ReasoningTools

from config import (
    AGENT_TEMPERATURE, AGENT_MARKDOWN,
    AGENT_NAME, AGENT_INSTRUCTIONS, RAG_BASE_URL,
    RAG_SSL_VERIFY, RAG_TIMEOUT,
    AGENT_OPENAI_API_KEY, AGENT_OPENAI_BASE_URL, AGENT_OPENAI_MODEL_ID,
    MODEL_PROVIDER, GOOGLE_API_KEY, GEMINI_MODEL_ID
)

logger = logging.getLogger(__name__)

# Agent cache: store agents per user_id to maintain session state
_agent_cache: Dict[str, Agent] = {}

# Shared singletons: avoid recreating expensive objects on every request
_shared_storage: Optional[Any] = None
_shared_model: Optional[Any] = None
_shared_model_provider: Optional[str] = None

# Import VastDBStorage from local lib directory
VastDBStorage = None
try:
    # Try direct import first (simpler and more reliable)
    try:
        from lib.vastdb_storage import VastDBStorage as VastDBStorageDirect
        VastDBStorage = VastDBStorageDirect
        logger.info("Successfully imported VastDBStorage via direct import")
    except ImportError:
        # Fallback to file-based import
        vastdb_path = os.path.join(os.path.dirname(__file__), '..', 'lib', 'vastdb_storage.py')
        if os.path.exists(vastdb_path):
            spec = importlib.util.spec_from_file_location("vastdb_storage", vastdb_path)
            vastdb_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vastdb_module)
            VastDBStorage = vastdb_module.VastDBStorage
            logger.info("Successfully imported VastDBStorage via file import")
        else:
            logger.warning(f"vastdb_storage.py not found in lib directory: {vastdb_path}")
except Exception as e:
    logger.error(f"Failed to import VastDBStorage: {e}", exc_info=True)



def _get_namespace_from_rag_url() -> str:
    """
    Extract namespace from RAG_BASE_URL.
    
    From RAG_BASE_URL like http://backend-webserver.research-assistant:8080:
    - Extract 'research-assistant'
    
    Returns:
        namespace string (e.g., "research-assistant")
    """
    import re
    
    if not RAG_BASE_URL:
        return "research-assistant"
    
    # Pattern: http://backend-webserver.<namespace>:8080
    match = re.search(r'\.([^:./]+)(?::\d+)?/?$', RAG_BASE_URL)
    if match:
        return match.group(1)  # e.g., "research-assistant"
    
    return "research-assistant"


def _get_session_bucket_and_schema() -> Tuple[str, str]:
    """
    Derive session bucket and schema from RAG_BASE_URL.
    Used by VastDBStorage for session persistence.
    
    From RAG_BASE_URL like http://backend-webserver.research-assistant:8080:
    - Extract 'research-assistant'
    - Add '-bucket' suffix → 'research-assistant-bucket'
    - Add '-schema' suffix → 'research-assistant-schema'
    
    Returns:
        Tuple of (bucket_name, schema_name)
    """
    namespace = _get_namespace_from_rag_url()
    return f"{namespace}-bucket", f"{namespace}-schema"


def _get_collections_bucket_and_schema() -> Tuple[str, str]:
    """
    Derive collections bucket and schema from RAG_BASE_URL.
    
    From RAG_BASE_URL like http://backend-webserver.research-assistant:8080:
    - Extract 'research-assistant'
    - Add '-bucket' suffix → 'research-assistant-bucket'
    - Add '-schema' suffix → 'research-assistant-schema'
    
    Returns:
        Tuple of (bucket_name, schema_name)
    """
    return _get_session_bucket_and_schema()  # Same logic


def get_collection_metadata(collection_name: str) -> Dict[str, Any]:
    """
    Get collection metadata (num_chunks, num_unique_files, total_doc_size) from VastDB.
    
    Chunks are stored in a shared 'chunks' table with a 'collection_name' column.
    Files are tracked via the VastDB catalog.
    
    Args:
        collection_name: Name of the collection
    
    Returns:
        Dictionary with num_chunks, num_unique_files, total_doc_size_bytes, total_doc_size_mb
    """
    import os
    import vastdb
    from ibis import _
    
    try:
        endpoint = os.getenv("VASTDB_ENDPOINT")
        access_key = os.getenv("VASTDB_ACCESS_KEY")
        secret_key = os.getenv("VASTDB_SECRET_KEY")
        bucket_name, schema_name = _get_collections_bucket_and_schema()
        
        if not all([endpoint, access_key, secret_key, bucket_name]):
            logger.warning("VastDB environment variables not configured for collection metadata")
            return {"num_chunks": 0, "num_unique_files": 0, "total_doc_size_bytes": 0, "total_doc_size_mb": 0.0}
        
        session = vastdb.connect(
            endpoint=endpoint,
            access=access_key,
            secret=secret_key,
            ssl_verify=False
        )
        
        with session.transaction() as tx:
            bucket_obj = tx.bucket(bucket_name)
            is_syncengine = collection_name.startswith("syncengine.")
            
            num_chunks = 0
            try:
                chunks_table = bucket_obj.schema(schema_name).table("chunks")
                if chunks_table:
                    try:
                        reader = chunks_table.select(["collection_name"])
                        result = reader.read_all()
                        df = result.to_pandas()
                        num_chunks = len(df[df["collection_name"] == collection_name])
                        logger.info(f"Found {num_chunks} chunks for collection {collection_name} (from {len(df)} total)")
                    except Exception as select_err:
                        logger.warning(f"Could not select from chunks table: {select_err}")
                        stats = chunks_table.stats
                        if stats and stats.num_rows > 0:
                            num_chunks = stats.num_rows
                            logger.info(f"Using total chunks count as fallback: {num_chunks}")
            except Exception as e:
                logger.warning(f"Error querying chunks table for {collection_name}: {e}")
                try:
                    lookup_schema = schema_name
                    lookup_table_name = collection_name
                    if not is_syncengine and '__' in collection_name:
                        parts = collection_name.split('__', 1)
                        if len(parts) == 2:
                            lookup_schema = parts[0]
                            lookup_table_name = parts[1]
                    table = bucket_obj.schema(lookup_schema).table(lookup_table_name)
                    if table:
                        stats = table.stats
                        num_chunks = stats.num_rows if stats else 0
                except Exception:
                    pass
            
            num_unique_files = 0
            total_doc_size = 0
            
            try:
                cat = tx.catalog()
                
                if is_syncengine:
                    predicate = _.parent_path.startswith(f"/{collection_name}/") & (_.element_type == "FILE")
                    logger.info(f"Looking for syncengine files at catalog path: /{collection_name}/")
                else:
                    s3_bucket = os.getenv("VASTDB_S3_BUCKET", bucket_name)
                    predicate = _.parent_path.startswith(f"/{s3_bucket}/{collection_name}/") & (_.element_type == "FILE")
                
                reader = cat.select(["name", "size", "parent_path", "element_type"], predicate=predicate)
                result = reader.read_all()
                df = result.to_pandas()
                
                if len(df) > 0:
                    num_unique_files = len(df)
                    total_doc_size = int(df["size"].sum())
                    logger.info(f"Found {num_unique_files} files, {total_doc_size} bytes for collection {collection_name}")
                else:
                    logger.info(f"No files found in catalog for collection {collection_name}")
                    try:
                        all_reader = cat.select(["parent_path"], predicate=(_.element_type == "FILE"))
                        all_result = all_reader.read_all()
                        all_df = all_result.to_pandas()
                        search_term = collection_name.split(".")[-1] if "." in collection_name else collection_name
                        matching = all_df[all_df["parent_path"].str.contains(search_term, case=False, na=False)]
                        if len(matching) > 0:
                            sample_paths = matching["parent_path"].unique()[:5]
                            logger.info(f"Debug: Found {len(matching)} files with '{search_term}' in path. Sample paths: {list(sample_paths)}")
                    except Exception as debug_err:
                        logger.debug(f"Debug catalog scan failed: {debug_err}")
                    
            except Exception as e:
                logger.warning(f"Catalog query failed for {collection_name}: {e}")
            
            return {
                "num_chunks": num_chunks,
                "num_unique_files": num_unique_files,
                "total_doc_size_bytes": total_doc_size,
                "total_doc_size_mb": round(total_doc_size / (1024 * 1024), 2) if total_doc_size else 0.0
            }
    except Exception as e:
        logger.warning(f"Error getting collection metadata for {collection_name}: {e}")
        return {"num_chunks": 0, "num_unique_files": 0, "total_doc_size_bytes": 0, "total_doc_size_mb": 0.0}


def create_retrieve_chunks_tool(token: str, base_url: str, target_collection: Optional[str] = None):
    """
    Create a retrieve_chunks tool that calls the /api/v1/retrieve endpoint.
    
    Args:
        token: JWT token for authentication
        base_url: Base URL of the RAG API
        target_collection: Collection to search in (if None, user must select one)
    
    Returns:
        Function that can be used as an agent tool
    """
    def retrieve_chunks(
        prompt: str,
        collection_name: str = "",
        with_rerank: bool = True,
        number_of_docs: int = 10,
        top_k_from_vectorstore: int = 30
    ) -> Dict[str, Any]:
        """
        Retrieve relevant document chunks from the knowledge base using similarity search.
        
        Args:
            prompt: The search query/prompt to find relevant documents (REQUIRED)
            collection_name: Name of the collection to search in (ignored - uses pre-configured collection)
            with_rerank: Whether to use reranking to improve results (default: True)
            number_of_docs: Number of documents to return after reranking (default: 10)
            top_k_from_vectorstore: Number of documents to retrieve from vector store before reranking (default: 30)
        
        Returns:
            Dictionary containing retrieved chunks
        """
        base_url_clean = base_url.rstrip('/')
        client = httpx.Client(
            base_url=base_url_clean,
            verify=RAG_SSL_VERIFY,
            timeout=RAG_TIMEOUT
        )
        
        try:
            actual_collection_name = target_collection
            if not actual_collection_name:
                return {"error": "No collection selected. Please select a collection before sending prompts."}

            logger.info(f"Calling retrieve_chunks with collection_name='{actual_collection_name}'")

            payload: Dict[str, Any] = {
                "collection_name": actual_collection_name,
                "prompt": prompt,
                "with_rerank": with_rerank,
                "number_of_docs": number_of_docs,
                "top_k_from_vectorstore": top_k_from_vectorstore,
                "extra_metadata_fields": ["source-url", "source-title"],
            }

            response = client.post(
                "/api/v1/retrieve",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list):
                result = {"chunks": result}

            try:
                metadata = get_collection_metadata(actual_collection_name)
                logger.info(f"Got collection metadata: {metadata}")
                result["collection_metadata"] = metadata
            except Exception as e:
                logger.warning(f"Failed to get collection metadata: {e}", exc_info=True)

            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Retrieve chunks failed: {e.response.status_code} - {e.response.text}")
            return {
                "error": f"Failed to retrieve chunks: {e.response.status_code}",
                "detail": e.response.text
            }
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}", exc_info=True)
            return {
                "error": f"Error retrieving chunks: {str(e)}"
            }
        finally:
            client.close()
    
    return retrieve_chunks


def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get list of all available tools with their names and descriptions.
    
    Returns:
        List of tool dictionaries with 'name' and 'description' fields
    """
    tools = []
    
    # retrieve_chunks tool
    tools.append({
        "name": "retrieve_chunks",
        "description": "Search internal knowledge base (RAG) for documents and information",
        "category": "rag"
    })
    
    # DuckDuckGo tools (check what methods it provides)
    try:
        duckduckgo_tools = DuckDuckGoTools()
        # DuckDuckGoTools typically provides 'search' method
        tools.append({
            "name": "duckduckgo_search",
            "description": "Search the internet for current/recent information, news, or information not in knowledge base",
            "category": "internet"
        })
    except Exception:
        pass
    
    # Reasoning )
    try:
        reasoning_tools = ReasoningTools()
        # ReasoningTools typically provides 'think' and 'analyze' methods
        tools.append({
            "name": "think",
            "description": "Use reasoning to break down complex problems step-by-step",
            "category": "reasoning"
        })
        tools.append({
            "name": "analyze",
            "description": "Analyze and evaluate information systematically",
            "category": "reasoning"
        })
    except Exception:
        pass
    
    return tools


def filter_tools(tools: List[Any], allowed_tool_names: Optional[List[str]] = None) -> List[Any]:
    """
    Filter tools list based on allowed tool names.
    
    Args:
        tools: List of tool objects/functions
        allowed_tool_names: Optional list of tool names to allow. If None, all tools are returned.
    
    Returns:
        Filtered list of tools
    """
    if not allowed_tool_names:
        return tools
    
    # Map tool names to actual tools
    # retrieve_chunks is a function
    # DuckDuckGoTools and ReasoningTools are objects with methods
    filtered = []
    
    for tool in tools:
        # Check if it's the retrieve_chunks function
        if callable(tool) and tool.__name__ == "retrieve_chunks":
            if "retrieve_chunks" in allowed_tool_names:
                filtered.append(tool)
        # Check if it's DuckDuckGoTools
        elif isinstance(tool, type(DuckDuckGoTools())) if DuckDuckGoTools else False:
            if "duckduckgo_search" in allowed_tool_names:
                filtered.append(tool)
        # Check if it's ReasoningTools
        elif isinstance(tool, type(ReasoningTools())) if ReasoningTools else False:
            if "think" in allowed_tool_names or "analyze" in allowed_tool_names:
                filtered.append(tool)
    
    return filtered


def get_or_create_agent(user_id: str, token: str, session_id: Optional[str] = None, tool_hooks: Optional[List[Callable]] = None, allowed_tools: Optional[List[str]] = None, collection_name: Optional[str] = None, internet_search: Optional[bool] = None, custom_instructions: Optional[str] = None) -> Optional[Agent]:
    """
    Get or create an Agent instance for the user with VastDB storage.
    
    Uses NVIDIA API (OpenAI-compatible) for model inference.
    
    Args:
        user_id: User ID from JWT token (will be converted to string)
        token: JWT token for RAG backend authentication
        session_id: Optional session_id - if provided, creates agent with this session_id in constructor
        tool_hooks: Optional list of tool hooks for monitoring tool execution
        allowed_tools: Optional list of tool names to use (e.g., ["retrieve_chunks", "duckduckgo_search"])
        collection_name: Optional collection name to use for RAG queries
        internet_search: If False, skip DuckDuckGo tools. If None or True, include them.
    
    Returns:
        Agent instance or None if creation fails
    """
    # Ensure user_id is a string for caching and database queries
    user_id_str = str(user_id)
    
    if session_id:
        logger.debug(f"Creating agent with session_id={session_id}")
    else:
        logger.debug(f"Creating agent for new session")
    
    if not Agent or not VastDBStorage:
        logger.error("Agno modules not available")
        return None
    
    try:
        global _shared_storage, _shared_model, _shared_model_provider

        # Reuse VastDBStorage singleton
        if _shared_storage is None:
            _shared_storage = VastDBStorage()
            logger.info("Created shared VastDBStorage instance")
        storage = _shared_storage

        # Validate API key
        if MODEL_PROVIDER == "gemini":
            if not GOOGLE_API_KEY:
                logger.error("GOOGLE_API_KEY not configured for Gemini provider")
                return None
        elif not AGENT_OPENAI_API_KEY:
            logger.error("AGENT_OPENAI_API_KEY not configured")
            return None
        
        # Create tools list
        tools = []
        
        # Add RAG tools with the user's token
        logger.info(f"Creating retrieve_chunks tool with collection_name={collection_name}")
        retrieve_tool = create_retrieve_chunks_tool(token=token, base_url=RAG_BASE_URL, target_collection=collection_name)
        tools.append(retrieve_tool)
        
        # Add internet search tool (DuckDuckGo) - skip if internet_search=False
        duckduckgo_tools = None
        if internet_search is False:
            logger.info("Skipping DuckDuckGoTools (internet_search=False)")
        else:
            backends_to_try = ['brave', 'duckduckgo', 'auto', None]  # None = default
            
            for backend in backends_to_try:
                try:
                    if backend:
                        duckduckgo_tools = DuckDuckGoTools(backend=backend)
                        logger.info(f"Added DuckDuckGoTools for internet search (using '{backend}' backend)")
                    else:
                        duckduckgo_tools = DuckDuckGoTools()
                        logger.info("Added DuckDuckGoTools for internet search (using default backend)")
                    tools.append(duckduckgo_tools)
                    break
                except Exception as e:
                    logger.warning(f"Failed to add DuckDuckGoTools with backend '{backend}': {e}")
                    continue
            
            if not duckduckgo_tools:
                logger.warning("Could not initialize DuckDuckGoTools with any backend")
        
        # Add thinking/reasoning tools
        try:
            reasoning_tools = ReasoningTools()
            tools.append(reasoning_tools)
            logger.info("Added ReasoningTools for enhanced thinking capabilities")
        except Exception as e:
            logger.warning(f"Failed to add ReasoningTools: {e}")
        
        # Filter tools if allowed_tools is specified
        if allowed_tools:
            filtered_tools = []
            needs_retrieve = False
            needs_duckduckgo = False
            needs_reasoning = False
            
            for tool_name in allowed_tools:
                if tool_name == "retrieve_chunks":
                    needs_retrieve = True
                elif tool_name == "duckduckgo_search":
                    needs_duckduckgo = True
                elif tool_name in ["think", "analyze"]:
                    needs_reasoning = True
            
            # Add tools based on what's needed
            if needs_retrieve:
                filtered_tools.append(retrieve_tool)
                logger.info("Added tool: retrieve_chunks")
            
            if needs_duckduckgo and duckduckgo_tools:
                filtered_tools.append(duckduckgo_tools)
                logger.info("Added tool: duckduckgo_search")
            
            if needs_reasoning and 'reasoning_tools' in locals():
                filtered_tools.append(reasoning_tools)
                logger.info("Added tool: reasoning (think/analyze)")
            
            if filtered_tools:
                tools = filtered_tools
                logger.info(f"Filtered tools to: {[t.__name__ if callable(t) else type(t).__name__ for t in tools]}")
            else:
                logger.warning(f"No valid tools found in allowed_tools={allowed_tools}, using all tools")
        
        # Reuse model singleton (recreate only if provider changed)
        if _shared_model is None or _shared_model_provider != MODEL_PROVIDER:
            if MODEL_PROVIDER == "gemini":
                from agno.models.google import Gemini
                _shared_model = Gemini(
                    id=GEMINI_MODEL_ID,
                    api_key=GOOGLE_API_KEY,
                    temperature=AGENT_TEMPERATURE,
                    generation_config={"max_output_tokens": 65536},
                )
                logger.info(f"Created Gemini model: {GEMINI_MODEL_ID} (max_output_tokens=65536)")
            else:
                openai_model_kwargs = {
                    'id': AGENT_OPENAI_MODEL_ID,
                    'api_key': AGENT_OPENAI_API_KEY,
                    'temperature': AGENT_TEMPERATURE,
                }
                if AGENT_OPENAI_BASE_URL:
                    openai_model_kwargs['base_url'] = AGENT_OPENAI_BASE_URL
                _shared_model = OpenAIChat(**openai_model_kwargs)
                logger.info(f"Created OpenAI model: {AGENT_OPENAI_MODEL_ID}")
            _shared_model_provider = MODEL_PROVIDER
        model = _shared_model
        
        # Use custom instructions if provided, otherwise use default from config
        instructions = custom_instructions if custom_instructions else AGENT_INSTRUCTIONS
        if custom_instructions:
            logger.info(f"Using custom system prompt ({len(custom_instructions)} chars)")
        
        agent_kwargs = {
            'name': AGENT_NAME,
            'model': model,
            'instructions': instructions,
            'db': storage,
            'tools': tools,
            'markdown': AGENT_MARKDOWN,
            'user_id': user_id_str,
            'add_history_to_context': True,
        }
        
        # If session_id is provided, add it to constructor (required for history to work)
        if session_id:
            agent_kwargs['session_id'] = session_id
            logger.info(f"Creating agent with session_id={session_id} in constructor")
        
        # Add tool hooks if provided (for streaming tool usage updates)
        if tool_hooks:
            agent_kwargs['tool_hooks'] = tool_hooks
            logger.info(f"Adding {len(tool_hooks)} tool hook(s) to agent")
        
        agent = Agent(**agent_kwargs)
        
        # Only cache agents without session_id (for new sessions)
        if not session_id:
            _agent_cache[user_id_str] = agent
            logger.info(f"Created and cached new agent for user_id: {user_id_str}")
        else:
            logger.info(f"Created new agent with session_id={session_id} (not cached, for continuing session)")
        
        return agent
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        return None

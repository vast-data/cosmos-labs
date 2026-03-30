"""
Streaming service for Server-Sent Events (SSE)
"""
import logging
import json
import time
import asyncio
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty

from fastapi import HTTPException

from models import PromptRequest
from services.auth import decode_jwt
from services.agent import get_or_create_agent
from api.utils.session_utils import generate_summary_from_prompt

logger = logging.getLogger(__name__)


class StreamingService:
    """Service for handling streaming prompt requests with SSE"""
    
    def __init__(self, user_id: str, token: str):
        self.user_id = user_id
        self.token = token
        self.timing_metrics = {}
        self.event_queue: Queue = Queue()
        self.first_tool_started = False
        self.collected_citations = []  # Store citations from tool calls
        self.collected_collection_metadata = None  # Store collection_metadata from retrieve_chunks
        self.collected_tool_events = []  # Store tool_start and tool_ended events
    
    @staticmethod
    def _extract_source_title(chunk: dict) -> str | None:
        """Extract source-title from chunk's extra_metadata (JSON string or dict)."""
        extra = chunk.get("extra_metadata")
        if not extra:
            return None
        if isinstance(extra, str):
            try:
                import json as _json
                extra = _json.loads(extra)
            except Exception:
                return None
        if isinstance(extra, dict):
            title = extra.get("source-title")
            if title:
                from urllib.parse import unquote
                return unquote(str(title))
        return None

    @staticmethod
    def _extract_source_url(chunk: dict) -> str | None:
        """Extract source-url from chunk's extra_metadata (JSON string or dict)."""
        extra = chunk.get("extra_metadata")
        if not extra:
            return None
        if isinstance(extra, str):
            try:
                import json as _json
                extra = _json.loads(extra)
            except Exception:
                return None
        if isinstance(extra, dict):
            url = extra.get("source-url")
            if url:
                return str(url)
        return None

    def extract_citations(self, function_name: str, result: Any) -> list:
        """Extract citations from retrieve_chunks tool result"""
        citations = []
        if function_name == "retrieve_chunks":
            result_type = type(result).__name__
            logger.info(f"retrieve_chunks result type: {result_type}")
            
            if isinstance(result, dict):
                chunks = []
                if "chunks" in result:
                    chunks = result.get("chunks", [])
                elif "documents" in result:
                    chunks = result.get("documents", [])
                elif "results" in result:
                    chunks = result.get("results", [])
                elif "data" in result:
                    data = result.get("data", [])
                    if isinstance(data, list):
                        chunks = data
                    elif isinstance(data, dict) and "chunks" in data:
                        chunks = data.get("chunks", [])
                
                for idx, chunk in enumerate(chunks):
                    if not isinstance(chunk, dict):
                        continue
                    
                    # Prefer source-title from extra_metadata for citation display
                    display_name = self._extract_source_title(chunk)
                    
                    if not display_name:
                        file_name = (
                            chunk.get("file_name") or
                            chunk.get("filename") or
                            chunk.get("source") or
                            chunk.get("document_id") or
                            chunk.get("id") or
                            None
                        )
                        
                        if not file_name and isinstance(chunk.get("metadata"), dict):
                            metadata = chunk.get("metadata", {})
                            file_name = (
                                metadata.get("file_name") or
                                metadata.get("filename") or
                                metadata.get("source") or
                                None
                            )
                        
                        if file_name:
                            import re
                            filename_match = re.search(r'([^/\\_]+\.(pdf|txt|doc|docx|md|html|json))', str(file_name))
                            if filename_match:
                                file_name = filename_match.group(1)
                            display_name = str(file_name)
                    
                    if display_name and display_name not in citations:
                        citations.append(display_name)
            elif isinstance(result, list):
                logger.info(f"retrieve_chunks result is a list with {len(result)} items")
                for idx, chunk in enumerate(result):
                    if isinstance(chunk, dict):
                        display_name = self._extract_source_title(chunk)
                        
                        if not display_name:
                            file_name = (
                                chunk.get("file_name") or
                                chunk.get("filename") or
                                chunk.get("source") or
                                chunk.get("document_id") or
                                chunk.get("id") or
                                None
                            )
                            
                            if not file_name and isinstance(chunk.get("metadata"), dict):
                                metadata = chunk.get("metadata", {})
                                file_name = (
                                    metadata.get("file_name") or
                                    metadata.get("filename") or
                                    metadata.get("source") or
                                    None
                                )
                            
                            if file_name:
                                import re
                                filename_match = re.search(r'([^/\\_]+\.(pdf|txt|doc|docx|md|html|json))', str(file_name))
                                if filename_match:
                                    file_name = filename_match.group(1)
                                display_name = str(file_name)
                        
                        if display_name and display_name not in citations:
                            citations.append(display_name)
        
        return citations
    
    def extract_chunks(self, function_name: str, result: Any) -> list:
        """Extract actual text chunks from retrieve_chunks tool result"""
        chunks = []
        if function_name != "retrieve_chunks":
            return chunks
        
        raw_chunks = []
        if isinstance(result, dict):
            if "chunks" in result:
                raw_chunks = result.get("chunks", [])
            elif "documents" in result:
                raw_chunks = result.get("documents", [])
            elif "results" in result:
                raw_chunks = result.get("results", [])
            elif "data" in result:
                data = result.get("data", [])
                if isinstance(data, list):
                    raw_chunks = data
                elif isinstance(data, dict) and "chunks" in data:
                    raw_chunks = data.get("chunks", [])
        elif isinstance(result, list):
            raw_chunks = result
        
        for chunk in raw_chunks:
            if not isinstance(chunk, dict):
                continue
            
            chunk_info = {}
            
            # Extract text content
            text = (
                chunk.get("text") or
                chunk.get("content") or
                chunk.get("page_content") or
                chunk.get("chunk_text") or
                ""
            )
            if text:
                chunk_info["text"] = text[:500]  # Limit to 500 chars per chunk
            
            # Extract source-title and source-url from extra_metadata
            source_title = self._extract_source_title(chunk)
            source_url = self._extract_source_url(chunk)

            if source_title:
                chunk_info["source_title"] = source_title
            if source_url:
                chunk_info["source_url"] = source_url

            # Extract source/filename (fallback display name)
            source = (
                chunk.get("source") or
                chunk.get("file_name") or
                chunk.get("filename") or
                chunk.get("document_id") or
                ""
            )
            if not source and isinstance(chunk.get("metadata"), dict):
                metadata = chunk.get("metadata", {})
                source = metadata.get("source") or metadata.get("file_name") or ""
            if source:
                chunk_info["source"] = str(source)
            
            # Extract score if available
            score = chunk.get("score") or chunk.get("similarity") or chunk.get("relevance_score")
            if score is not None:
                chunk_info["score"] = float(score)
            
            if chunk_info:
                chunks.append(chunk_info)
        
        return chunks[:10]  # Limit to top 10 chunks
    
    def create_tool_hook(self, timing_metrics: Dict[str, Any]) -> Callable:
        """Create a tool hook that emits SSE events"""
        def tool_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
            nonlocal timing_metrics
            start_time = time.time()
            
            if not self.first_tool_started:
                self.first_tool_started = True
                timing_metrics["first_tool_start"] = start_time
                time_to_first_tool = start_time - timing_metrics.get("agent_run_start", time.time())
                logger.info(f"⏱️  METRICS: Time to first tool: {time_to_first_tool:.2f}s")
            
            tool_start_event = {
                "type": "tool_start",
                "tool_name": function_name,
                "arguments": arguments,
                "timestamp": start_time
            }
            self.event_queue.put(tool_start_event)
            # Store tool_start event for session saving
            self.collected_tool_events.append(tool_start_event)
            
            try:
                result = function_call(**arguments)
                end_time = time.time()
                duration = end_time - start_time
                
                if self.first_tool_started and timing_metrics.get("first_tool_complete") is None:
                    timing_metrics["first_tool_complete"] = end_time
                    time_to_first_tool_complete = end_time - timing_metrics.get("first_tool_start", start_time)
                    logger.info(f"⏱️  METRICS: First tool completed in: {time_to_first_tool_complete:.2f}s")
                
                citations = self.extract_citations(function_name, result)
                chunks = self.extract_chunks(function_name, result)
                
                # Collect citations for saving to the run
                if citations:
                    self.collected_citations.extend(citations)
                    logger.info(f"📚 Collected {len(citations)} citations from {function_name}, total: {len(self.collected_citations)}")
                
                if function_name == "retrieve_chunks":
                    logger.info(f"retrieve_chunks result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
                    if isinstance(result, dict):
                        if "error" in result:
                            logger.error(f"retrieve_chunks error: {result.get('error')}")
                            logger.error(f"retrieve_chunks detail: {result.get('detail', 'no detail')}")
                        else:
                            # Log successful result structure
                            for key in result.keys():
                                val = result[key]
                                if isinstance(val, list):
                                    logger.info(f"  {key}: list with {len(val)} items")
                                    if len(val) > 0:
                                        logger.info(f"    first item type: {type(val[0])}, keys: {val[0].keys() if isinstance(val[0], dict) else 'N/A'}")
                                else:
                                    logger.info(f"  {key}: {type(val)} = {str(val)[:200]}")
                
                tool_complete_event = {
                    "type": "tool_complete",
                    "tool_name": function_name,
                    "duration": duration,
                    "success": True,
                    "timestamp": end_time
                }
                
                if citations:
                    tool_complete_event["citations"] = citations
                
                if chunks:
                    tool_complete_event["chunks"] = chunks
                
                if function_name == "retrieve_chunks":
                    collection_metadata = None
                    if isinstance(result, dict):
                        collection_metadata = result.get("collection_metadata")
                    
                    if not collection_metadata:
                        try:
                            collection_name = getattr(self, 'collection_name', None)
                            if collection_name:
                                from services.agent import get_collection_metadata
                                collection_metadata = get_collection_metadata(collection_name)
                                logger.info(f"Got collection metadata from collection_name: {collection_metadata}")
                        except Exception as e:
                            logger.warning(f"Failed to get collection metadata: {e}", exc_info=True)
                    
                    if collection_metadata:
                        tool_complete_event["collection_metadata"] = collection_metadata
                        self.collected_collection_metadata = collection_metadata
                
                self.event_queue.put(tool_complete_event)
                
                # Store tool_ended event for session saving (tool_complete is the same as tool_ended)
                tool_ended_event = {
                    "type": "tool_ended",
                    "tool_name": function_name,
                    "duration": duration,
                    "success": True,
                    "timestamp": end_time
                }
                # Copy relevant fields from tool_complete_event
                if citations:
                    tool_ended_event["citations"] = citations
                if chunks:
                    tool_ended_event["chunks"] = chunks
                if function_name == "retrieve_chunks" and collection_metadata:
                    tool_ended_event["collection_metadata"] = collection_metadata
                
                self.collected_tool_events.append(tool_ended_event)
                
                return result
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                # Check if this is a DuckDuckGo error - handle gracefully
                is_duckduckgo_error = (
                    function_name == "duckduckgo_search" or 
                    "ddgs" in str(type(e)).lower() or 
                    "duckduckgo" in str(type(e)).lower() or
                    "No results found" in str(e)
                )
                
                if is_duckduckgo_error:
                    # Handle DuckDuckGo errors gracefully - don't raise, return empty result
                    logger.info(f"DuckDuckGo search returned no results (query may be too specific or service unavailable)")
                    
                    # Send tool_complete event (not tool_error) with success=False
                    tool_complete_event = {
                        "type": "tool_complete",
                        "tool_name": function_name,
                        "duration": duration,
                        "success": False,
                        "error": "No results found",
                        "timestamp": end_time
                    }
                    self.event_queue.put(tool_complete_event)
                    
                    # Store tool_ended event for session saving
                    tool_ended_event = {
                        "type": "tool_ended",
                        "tool_name": function_name,
                        "duration": duration,
                        "success": False,
                        "error": "No results found",
                        "timestamp": end_time
                    }
                    self.collected_tool_events.append(tool_ended_event)
                    
                    # Return empty result instead of raising
                    return []
                else:
                    # For other errors, log and raise as before
                    tool_error_event = {
                        "type": "tool_error",
                        "tool_name": function_name,
                        "duration": duration,
                        "error": str(e),
                        "timestamp": end_time
                    }
                    self.event_queue.put(tool_error_event)
                    
                    # Store tool_error as tool_ended with success=False
                    tool_ended_event = {
                        "type": "tool_ended",
                        "tool_name": function_name,
                        "duration": duration,
                        "success": False,
                        "error": str(e),
                        "timestamp": end_time
                    }
                    self.collected_tool_events.append(tool_ended_event)
                    
                    raise
        
        return tool_hook
    
    def run_agent(self, request: PromptRequest) -> tuple[Any, str, str]:
        """
        Run the agent and return the result, session_id, and response content.
        
        Returns:
            Tuple of (run_result, session_id, response_content)
        """
        request_start_time = time.time()
        self.timing_metrics = {
            "request_received": request_start_time,
            "agent_creation_start": None,
            "agent_creation_end": None,
            "agent_run_start": None,
            "first_tool_start": None,
            "first_tool_complete": None,
            "agent_run_end": None,
            "total_time": None
        }
        
        target_session_id = None
        loaded_session = None
        
        if request.conversation_id and request.conversation_id != "unknown":
            target_session_id = request.conversation_id
            # Use shared storage directly to verify session exists (avoid creating a throwaway agent)
            try:
                from lib.vastdb_storage import VastDBStorage
                from agno.db.base import SessionType
                storage = VastDBStorage()
                loaded_session = storage.get_session(
                    session_id=target_session_id,
                    session_type=SessionType.AGENT,
                    user_id=self.user_id,
                    deserialize=True
                )
                if not loaded_session:
                    logger.warning(f"Session {target_session_id} not found, will create new session")
                    target_session_id = None
                else:
                    logger.info(f"Found existing session: {target_session_id}")
            except Exception as e:
                logger.warning(f"Could not load session {target_session_id}: {e}")
                target_session_id = None
        
        self.timing_metrics["agent_creation_start"] = time.time()
        # Get collection name from request (use first collection if list provided)
        collection_name = None
        if request.collections:
            collection_name = request.collections[0] if isinstance(request.collections, list) else request.collections
        # Store collection_name as instance variable for use in tool_hook
        self.collection_name = collection_name
        logger.info(f"Streaming request collections={request.collections}, resolved collection_name={collection_name}")
        
        agent = get_or_create_agent(
            user_id=self.user_id,
            token=self.token,
            session_id=target_session_id,
            allowed_tools=request.tools,
            collection_name=collection_name,
            internet_search=request.internet_search,
            custom_instructions=request.system_prompt
        )
        self.timing_metrics["agent_creation_end"] = time.time()
        
        if not agent:
            raise HTTPException(status_code=500, detail="Failed to create agent")
        
        # Patch the model client to filter blank text messages BEFORE they reach the LLM
        if hasattr(agent, 'model') and hasattr(agent.model, 'get_client'):
            try:
                model_client = agent.model.get_client()
                original_converse = model_client.converse
                
                def patched_converse(*args, **kwargs):
                    # Filter blank text from messages before sending to the model
                    if 'messages' in kwargs:
                        cleaned_messages = []
                        for msg in kwargs['messages']:
                            if isinstance(msg, dict) and 'content' in msg:
                                content = msg['content']
                                if isinstance(content, list):
                                    cleaned_content = []
                                    for item in content:
                                        if isinstance(item, dict) and 'text' in item:
                                            text = item.get('text')
                                            if text is None or text == '' or (isinstance(text, str) and text.strip() == ''):
                                                logger.info(f"PATCH: Removing blank text item from message")
                                                continue
                                        cleaned_content.append(item)
                                    if cleaned_content:  # Only add message if it has content left
                                        msg = dict(msg)
                                        msg['content'] = cleaned_content
                                        cleaned_messages.append(msg)
                                else:
                                    cleaned_messages.append(msg)
                            else:
                                cleaned_messages.append(msg)
                        kwargs['messages'] = cleaned_messages
                        logger.info(f"PATCH: Sending {len(cleaned_messages)} messages to model")
                    return original_converse(*args, **kwargs)
                
                model_client.converse = patched_converse
                logger.info("Patched model client converse method to filter blank text")
                
                # Also patch converse_stream for streaming requests
                if hasattr(model_client, 'converse_stream'):
                    original_converse_stream = model_client.converse_stream
                    
                    def patched_converse_stream(*args, **kwargs):
                        # Filter blank text from messages before sending to the model
                        if 'messages' in kwargs:
                            cleaned_messages = []
                            for msg in kwargs['messages']:
                                if isinstance(msg, dict) and 'content' in msg:
                                    content = msg['content']
                                    if isinstance(content, list):
                                        cleaned_content = []
                                        for item in content:
                                            if isinstance(item, dict):
                                                # Check for blank text items
                                                if 'text' in item:
                                                    text = item.get('text')
                                                    if text is None or text == '' or (isinstance(text, str) and not text.strip()):
                                                        logger.info(f"STREAM PATCH: Removing blank text item: {item}")
                                                        continue
                                            cleaned_content.append(item)
                                        if cleaned_content:  # Only add message if it has content left
                                            msg = dict(msg)
                                            msg['content'] = cleaned_content
                                            cleaned_messages.append(msg)
                                        else:
                                            logger.info(f"STREAM PATCH: Skipping message with no content")
                                    else:
                                        cleaned_messages.append(msg)
                                else:
                                    cleaned_messages.append(msg)
                            kwargs['messages'] = cleaned_messages
                            logger.info(f"STREAM PATCH: Sending {len(cleaned_messages)} messages to model converse_stream")
                        return original_converse_stream(*args, **kwargs)
                    
                    model_client.converse_stream = patched_converse_stream
                    logger.info("Patched model client converse_stream method to filter blank text")
            except Exception as e:
                logger.warning(f"Could not patch model client: {e}")
        
        # Wrap agent.model.invoke to track model API calls
        original_invoke = agent.model.invoke
        model_call_number = [0]  # Use list to allow modification in nested function
        
        if original_invoke is None or not callable(original_invoke):
            logger.warning(f"agent.model.invoke is {type(original_invoke)}, skipping invoke wrapping")
            original_invoke = None
        
        def tracked_invoke(*args, **kwargs):
            model_call_number[0] += 1
            call_num = model_call_number[0]
            start_time = time.time()
            
            # Filter out blank text content items before sending to the model
            def filter_blank_text(messages):
                filtered = []
                for msg in messages:
                    # Get content from message
                    content = None
                    if hasattr(msg, 'content'):
                        content = msg.content
                    elif isinstance(msg, dict):
                        content = msg.get('content')
                    
                    if isinstance(content, list):
                        # Filter out blank text items
                        new_content = []
                        for item in content:
                            # Convert DictAsObject to dict if needed
                            if hasattr(item, '_dict'):
                                item = item._dict
                            
                            if isinstance(item, dict):
                                # Skip items with blank text
                                # Check both {"text": ""} and {"type": "text", "text": ""}
                                text_val = item.get('text')
                                item_type = item.get('type')
                                
                                if text_val is not None or item_type == 'text':
                                    if text_val is None or text_val == '' or (isinstance(text_val, str) and not text_val.strip()):
                                        logger.info(f"Filtering blank text item: {item}")
                                        continue
                            new_content.append(item)
                        
                        # Update message content if we filtered anything
                        if len(new_content) != len(content):
                            if hasattr(msg, 'content'):
                                msg.content = new_content
                            elif isinstance(msg, dict):
                                msg['content'] = new_content
                        
                        # Skip messages with no content left
                        if len(new_content) == 0:
                            logger.info(f"Skipping message with no content after filtering")
                            continue
                    
                    filtered.append(msg)
                return filtered
            
            # Apply filtering to messages
            if args:
                messages = args[0] if isinstance(args[0], list) else kwargs.get('messages', [])
                filtered_messages = filter_blank_text(messages)
                if len(filtered_messages) != len(messages):
                    logger.info(f"Filtered messages: {len(messages)} -> {len(filtered_messages)}")
                    if isinstance(args[0], list):
                        args = (filtered_messages,) + args[1:]
                    else:
                        kwargs['messages'] = filtered_messages
                
                logger.info(f"Model call #{call_num}: {len(filtered_messages)} messages")
                for i, msg in enumerate(filtered_messages):
                    if hasattr(msg, 'role'):
                        role = msg.role
                    elif isinstance(msg, dict):
                        role = msg.get('role', 'unknown')
                    else:
                        role = 'unknown'
                    
                    # Check for tool_use in content
                    content = None
                    if hasattr(msg, 'content'):
                        content = msg.content
                    elif isinstance(msg, dict):
                        content = msg.get('content')
                    
                    tool_use_ids = []
                    tool_result_ids = []
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                if 'toolUse' in item:
                                    tool_use_ids.append(item['toolUse'].get('toolUseId', 'unknown'))
                                elif 'toolResult' in item:
                                    tool_result_ids.append(item['toolResult'].get('toolUseId', 'unknown'))
                    
                    extra = ""
                    if tool_use_ids:
                        extra = f" [tool_use: {tool_use_ids}]"
                    if tool_result_ids:
                        extra = f" [tool_result: {tool_result_ids}]"
                    logger.info(f"  Message {i}: role={role}{extra}")
            
            self.event_queue.put({
                "type": "model_start",
                "call_number": call_num,
                "timestamp": start_time
            })
            
            try:
                if original_invoke is None:
                    logger.error("original_invoke is None, cannot call model.invoke")
                    raise RuntimeError("model.invoke is not available")
                result = original_invoke(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                
                self.event_queue.put({
                    "type": "model_complete",
                    "call_number": call_num,
                    "duration": duration,
                    "timestamp": end_time
                })
                
                return result
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                self.event_queue.put({
                    "type": "model_error",
                    "call_number": call_num,
                    "duration": duration,
                    "error": str(e),
                    "timestamp": end_time
                })
                raise
        
        if original_invoke is not None:
            agent.model.invoke = tracked_invoke
            logger.info("Wrapped agent.model.invoke for model timing")
        else:
            logger.warning("Skipping agent.model.invoke wrapping (invoke is not callable)")
        
        tool_hook = self.create_tool_hook(self.timing_metrics)
        # Add tool hook to agent
        if hasattr(agent, 'tool_hooks'):
            if agent.tool_hooks:
                agent.tool_hooks.append(tool_hook)
            else:
                agent.tool_hooks = [tool_hook]
        elif hasattr(agent, 'add_tool_hook'):
            agent.add_tool_hook(tool_hook)
        
        self.timing_metrics["agent_run_start"] = time.time()
        time_to_agent_run = self.timing_metrics["agent_run_start"] - request_start_time
        logger.info(f"⏱️  METRICS: Time to agent.run() start: {time_to_agent_run:.2f}s")
        
        self.event_queue.put({
            "type": "start",
            "message": "Processing prompt..."
        })
        
        import traceback as _tb
        # Monkey-patch Agno's log_error to include traceback
        try:
            import agno.agent.agent as _agno_agent_mod
            _original_log_error = _agno_agent_mod.log_error
            def _patched_log_error(msg, *args, **kwargs):
                import sys
                logger.error(f"[AGNO] {msg}")
                exc_info = sys.exc_info()
                if exc_info[2]:
                    logger.error(f"[AGNO TRACEBACK]\n{''.join(_tb.format_exception(*exc_info))}")
                _original_log_error(msg, *args, **kwargs)
            _agno_agent_mod.log_error = _patched_log_error
        except Exception as patch_err:
            logger.warning(f"Could not patch agno log_error: {patch_err}")
        
        try:
            # Use streaming mode to get real-time token streaming
            run_iterator = agent.run(request.prompt, stream=True)
            
            # Track accumulated content for final response
            accumulated_content = ""
            run_result = None
            early_session_id_sent = False
            
            # Process streaming events
            event_count = 0
            for event in run_iterator:
                event_count += 1
                # Emit session_id as early as possible (on first iteration, agent has created the session)
                if not early_session_id_sent and not target_session_id:
                    early_sid = getattr(agent.session, 'session_id', None) or getattr(agent.session, 'id', None) if hasattr(agent, 'session') and agent.session else None
                    if early_sid:
                        logger.info(f"📤 Early session_id emission: {str(early_sid)[:8]}...")
                        self.event_queue.put({
                            "type": "session_id",
                            "session_id": str(early_sid)
                        })
                        early_session_id_sent = True

                event_type = type(event).__name__
                has_content = hasattr(event, 'content') and event.content
                has_output = hasattr(event, 'output') and event.output
                if event_count <= 5 or has_content or has_output:
                    logger.info(f"🔄 Stream event #{event_count}: type={event_type}, has_content={has_content}, has_output={has_output}, accumulated={len(accumulated_content)} chars")
                
                if event_type == 'RunErrorEvent':
                    error_msg = getattr(event, 'content', None) or getattr(event, 'error', None) or str(event)
                    logger.error(f"🚨 RunErrorEvent: {error_msg}")
                    if hasattr(event, 'exception') and event.exception:
                        logger.error(f"🚨 RunErrorEvent exception: {''.join(_tb.format_exception(type(event.exception), event.exception, event.exception.__traceback__))}")
                
                # Handle content deltas (token-by-token streaming)
                if has_content:
                    if isinstance(event.content, str):
                        content_delta = event.content
                    else:
                        content_delta = str(event.content)
                    
                    if content_delta and content_delta.strip():
                        accumulated_content += content_delta
                        self.event_queue.put({
                            "type": "content_delta",
                            "delta": content_delta
                        })
                
                # Handle RunOutput / final result
                if has_output or event_type in ('RunOutput', 'RunResponse'):
                    run_result = event
                    if has_output:
                        final_content = str(event.output)
                        # Emit as content_delta if not yet streamed
                        if final_content and final_content.strip() and final_content not in accumulated_content:
                            logger.info(f"📝 Emitting RunOutput content as delta ({len(final_content)} chars, accumulated so far: {len(accumulated_content)} chars)")
                            self.event_queue.put({
                                "type": "content_delta",
                                "delta": final_content
                            })
                            accumulated_content = final_content
                
                # Handle RunOutputEvent for content
                if event_type == 'RunOutputEvent' and hasattr(event, 'content'):
                    if event.content and isinstance(event.content, str):
                        if event.content not in accumulated_content:
                            self.event_queue.put({
                                "type": "content_delta",
                                "delta": event.content
                            })
                            accumulated_content += event.content
            
            logger.info(f"🔄 Stream loop finished after {event_count} events, accumulated {len(accumulated_content)} chars")
            
            self.timing_metrics["agent_run_end"] = time.time()
            
            agent_run_duration = self.timing_metrics["agent_run_end"] - self.timing_metrics["agent_run_start"]
            logger.info(f"⏱️  METRICS: Agent run took: {agent_run_duration:.2f}s")
            
            # Try multiple ways to get session_id after agent.run() completes
            current_session_id = None
            
            # CRITICAL: For new sessions (no target_session_id), ensure the session is saved first
            # The session is created during agent.run(), but we need to save it to get the session_id
            if not target_session_id and hasattr(agent, 'session') and agent.session:
                # For new sessions, save the session first to ensure it has a session_id
                try:
                    if hasattr(agent, 'db') and agent.db:
                        # Save the session to ensure it's persisted and has a session_id
                        saved_session = agent.db.upsert_session(agent.session)
                        if saved_session:
                            # Get session_id from the saved session
                            current_session_id = getattr(saved_session, 'session_id', None) or getattr(saved_session, 'id', None)
                            if current_session_id:
                                logger.info(f"✅ Got session_id from saved new session: {current_session_id[:8]}...")
                                # Update agent.session with the saved session to ensure consistency
                                agent.session = saved_session
                except Exception as e:
                    logger.warning(f"Could not save new session to get session_id: {e}", exc_info=True)
            
            # Method 1: From agent.session (after potential save above)
            if not current_session_id and hasattr(agent, 'session') and agent.session:
                current_session_id = getattr(agent.session, 'session_id', None) or getattr(agent.session, 'id', None)
                logger.info(f"Got session_id from agent.session: {current_session_id[:8] if current_session_id else 'None'}...")
            
            # Method 2: From agent.last_run
            if not current_session_id and hasattr(agent, 'last_run') and agent.last_run:
                current_session_id = getattr(agent.last_run, 'session_id', None)
                logger.info(f"Got session_id from agent.last_run: {current_session_id[:8] if current_session_id else 'None'}...")
            
            # Method 3: From run_result
            if not current_session_id and run_result:
                if hasattr(run_result, 'session_id'):
                    current_session_id = run_result.session_id
                    logger.info(f"Got session_id from run_result: {current_session_id[:8] if current_session_id else 'None'}...")
                elif isinstance(run_result, dict) and 'session_id' in run_result:
                    current_session_id = run_result['session_id']
                    logger.info(f"Got session_id from run_result dict: {current_session_id[:8] if current_session_id else 'None'}...")
            
            # Method 4: Check if agent has a session attribute that was just created
            if not current_session_id and hasattr(agent, 'session') and agent.session:
                # Try accessing session attributes directly
                try:
                    session_obj = agent.session
                    if hasattr(session_obj, '__dict__'):
                        for attr in ['session_id', 'id', '_id']:
                            if hasattr(session_obj, attr):
                                val = getattr(session_obj, attr)
                                if val:
                                    current_session_id = str(val)
                                    logger.info(f"Got session_id from agent.session.{attr}: {current_session_id[:8]}...")
                                    break
                except Exception as e:
                    logger.debug(f"Could not extract session_id from agent.session: {e}")
            
            # Set session summary for new sessions or update if session_name provided
            # If we still don't have session_id, try to get it from the most recent session in DB
            if not current_session_id and hasattr(agent, 'db') and agent.db:
                try:
                    from agno.db.base import SessionType
                    # Get the most recent session for this user
                    sessions_result = agent.db.get_sessions(
                        session_type=SessionType.AGENT,
                        user_id=self.user_id,
                        limit=1,
                        sort_by='updated_at',
                        sort_order='desc',
                        deserialize=False
                    )
                    if sessions_result:
                        # sessions_result is a tuple of (list, count) or just a list
                        if isinstance(sessions_result, tuple):
                            sessions_list = sessions_result[0]
                        else:
                            sessions_list = sessions_result
                        
                        if sessions_list and len(sessions_list) > 0:
                            latest_session = sessions_list[0]
                            if isinstance(latest_session, dict):
                                current_session_id = latest_session.get('session_id') or latest_session.get('id')
                            elif hasattr(latest_session, 'session_id'):
                                current_session_id = latest_session.session_id
                            elif hasattr(latest_session, 'id'):
                                current_session_id = latest_session.id
                            
                            if current_session_id:
                                logger.info(f"Got session_id from most recent session query: {current_session_id[:8]}...")
                except Exception as e:
                    logger.warning(f"Could not get session_id from database query: {e}")
            
            if current_session_id and hasattr(agent, 'db') and agent.db:
                try:
                    from agno.db.base import SessionType
                    reloaded_session = agent.db.get_session(
                        session_id=current_session_id,
                        session_type=SessionType.AGENT,
                        user_id=self.user_id,
                        deserialize=True
                    )
                    
                    if reloaded_session:
                        if not current_session_id:
                            current_session_id = getattr(reloaded_session, 'session_id', None) or getattr(reloaded_session, 'id', None)

                        current_title = (reloaded_session.summary or {}).get("title") if hasattr(reloaded_session, 'summary') and reloaded_session.summary else None
                        provided_session_name = request.session_name.strip() if request.session_name and request.session_name.strip() else None
                        has_real_title = current_title and current_title != "My Session"

                        # If a real title already exists and user didn't provide a new name, skip entirely
                        if has_real_title and not provided_session_name:
                            logger.info(f"Session {current_session_id[:8]} already has title '{current_title}', skipping title/summary generation")
                        else:
                            session_summary_text = None
                            if provided_session_name:
                                session_title = provided_session_name
                            else:
                                logger.info(f"Generating title from first prompt: {request.prompt[:50]}...")
                                session_summary_text = generate_summary_from_prompt(agent, request.prompt)
                                if session_summary_text:
                                    session_title = session_summary_text[:57] + "..." if len(session_summary_text) > 60 else session_summary_text
                                else:
                                    session_title = "My Session"
                                logger.info(f"Generated title: {session_title}")

                            if not hasattr(reloaded_session, 'summary') or not reloaded_session.summary:
                                reloaded_session.summary = {}
                            reloaded_session.summary["title"] = session_title
                            if not provided_session_name and session_summary_text:
                                reloaded_session.summary["summary"] = session_summary_text
                            agent.db.upsert_session(reloaded_session)
                            logger.info(f"✅ Set session title to: {session_title}")
                except Exception as e:
                    logger.warning(f"Could not set session summary: {e}", exc_info=True)
            
            # Save session - try even if current_session_id is None (it might be in agent.session)
            # First, try to get session_id from agent.session if we don't have it
            if not current_session_id and hasattr(agent, 'session') and agent.session:
                current_session_id = getattr(agent.session, 'session_id', None) or getattr(agent.session, 'id', None)
                if current_session_id:
                    logger.info(f"Got session_id from agent.session before save: {current_session_id[:8]}...")
            
            logger.info(f"Session save check: current_session_id={current_session_id[:8] if current_session_id else None}, has_session={hasattr(agent, 'session')}, session={bool(hasattr(agent, 'session') and agent.session)}, has_db={hasattr(agent, 'db')}, db={bool(hasattr(agent, 'db') and agent.db)}, collected_citations={len(self.collected_citations) if self.collected_citations else 0}, collected_collection_metadata={bool(self.collected_collection_metadata)}")
            
            # Try to save citations even if agent.session is not available
            # We can reload the session using current_session_id and agent.db
            if current_session_id and hasattr(agent, 'db') and agent.db and self.collected_citations:
                try:
                    import time as time_module
                    time_module.sleep(0.1)
                    
                    from agno.db.base import SessionType
                    reloaded_session = agent.db.get_session(
                        session_id=current_session_id,
                        session_type=SessionType.AGENT,
                        user_id=self.user_id,
                        deserialize=True
                    )
                    
                    if not reloaded_session:
                        logger.warning(f"Could not reload session {current_session_id[:8]}... to add citations")
                        return
                    
                    # We have a reloaded session, now add citations to the most recent run
                    reloaded_runs = []
                    if hasattr(reloaded_session, 'runs') and reloaded_session.runs:
                        runs_raw = reloaded_session.runs
                        if isinstance(runs_raw, str):
                            try:
                                reloaded_runs = json.loads(runs_raw)
                            except:
                                reloaded_runs = []
                        elif isinstance(runs_raw, list):
                            reloaded_runs = runs_raw
                    
                    # CRITICAL: Preserve summary from reloaded_session before modifying runs
                    # The summary might have been set in a previous upsert_session call
                    preserved_summary = None
                    if hasattr(reloaded_session, 'summary') and reloaded_session.summary:
                        preserved_summary = reloaded_session.summary
                        logger.info(f"Preserving summary before adding citations: {preserved_summary}")
                    
                    # Add citations, collection_metadata, and tool_events to the most recent run (last one in reloaded_runs)
                    if (self.collected_citations or self.collected_collection_metadata or self.collected_tool_events) and reloaded_runs:
                        if len(reloaded_runs) > 0:
                            last_run = reloaded_runs[-1]
                            logger.info(f"Last run type: {type(last_run)}, is dict: {isinstance(last_run, dict)}")
                            # Convert to dict if needed
                            from lib.vastdb_storage import convert_to_dict
                            if not isinstance(last_run, dict):
                                logger.info(f"Converting last_run from {type(last_run)} to dict")
                                last_run = convert_to_dict(last_run)
                                reloaded_runs[-1] = last_run  # Update the list with the converted dict
                                logger.info(f"After conversion, type: {type(last_run)}, is dict: {isinstance(last_run, dict)}")
                            
                            if isinstance(last_run, dict):
                                if self.collected_citations:
                                    unique_citations = list(dict.fromkeys(self.collected_citations))
                                    last_run['citations'] = unique_citations
                                    logger.info(f"📚 Added {len(unique_citations)} citations to last run: {unique_citations[:5]}")
                                
                                if self.collected_collection_metadata:
                                    last_run['collection_metadata'] = self.collected_collection_metadata
                                    logger.info(f"📊 Added collection_metadata to last run: {self.collected_collection_metadata}")
                                
                                if self.collected_tool_events:
                                    # Initialize tool_events list if it doesn't exist
                                    if 'tool_events' not in last_run:
                                        last_run['tool_events'] = []
                                    # Append new tool events
                                    last_run['tool_events'].extend(self.collected_tool_events)
                                    logger.info(f"🔧 Added {len(self.collected_tool_events)} tool events to last run")
                            else:
                                logger.warning(f"Last run is still not a dict after conversion, type: {type(last_run)}")
                        else:
                            logger.warning(f"No runs in reloaded_runs to add citations/collection_metadata to")
                    else:
                        if not self.collected_citations and not self.collected_collection_metadata:
                            logger.warning(f"No collected citations or collection_metadata to add")
                        if not reloaded_runs:
                            logger.warning(f"No reloaded_runs to add citations/collection_metadata to")
                    
                    if reloaded_runs:
                        logger.info(f"Saving {len(reloaded_runs)} runs to session with citations")
                        # Log citations before serialization
                        for idx, run in enumerate(reloaded_runs):
                            if isinstance(run, dict):
                                logger.info(f"Before serialization - Run {idx} citations: {run.get('citations', [])}")
                        reloaded_session.runs = json.dumps(reloaded_runs, default=str)
                        # Verify citations are in JSON
                        try:
                            test_deserialize = json.loads(reloaded_session.runs)
                            if isinstance(test_deserialize, list) and len(test_deserialize) > 0:
                                logger.info(f"After serialization - Run 0 citations in JSON: {test_deserialize[0].get('citations', []) if isinstance(test_deserialize[0], dict) else 'N/A'}")
                        except:
                            pass
                        
                        # CRITICAL: Restore summary if it was preserved
                        if preserved_summary:
                            if not hasattr(reloaded_session, 'summary') or not reloaded_session.summary:
                                reloaded_session.summary = preserved_summary
                                logger.info(f"✅ Restored summary before final upsert: {preserved_summary}")
                            else:
                                logger.info(f"Summary already present, not restoring: {reloaded_session.summary}")
                        
                        agent.db.upsert_session(reloaded_session)
                        # Clear collected citations, collection_metadata, and tool_events after saving
                        self.collected_citations = []
                        self.collected_collection_metadata = None
                        self.collected_tool_events = []
                        # Update agent.session if available
                        if hasattr(agent, 'session'):
                            agent.session = reloaded_session
                    else:
                        logger.warning(f"No reloaded_runs to save, but we have {len(self.collected_citations) if self.collected_citations else 0} collected citations")
                    
                    # Ensure we have session_id from the reloaded session (regardless of whether runs were updated)
                    saved_session_id = getattr(reloaded_session, 'session_id', None) or getattr(reloaded_session, 'id', None)
                    if saved_session_id:
                        current_session_id = saved_session_id
                        logger.info(f"Got session_id from reloaded_session: {current_session_id[:8]}...")
                except Exception as e:
                    logger.warning(f"Could not save session: {e}")
            
            # Final attempt: If we still don't have session_id, try to get it from the database
            # by querying for the most recent session for this user
            if not current_session_id and hasattr(agent, 'db') and agent.db:
                try:
                    from agno.db.base import SessionType
                    # Get the most recent session for this user
                    sessions = agent.db.get_sessions(
                        session_type=SessionType.AGENT,
                        user_id=self.user_id,
                        limit=1,
                        sort_by='updated_at',
                        sort_order='desc',
                        deserialize=False
                    )
                    if sessions and len(sessions) > 0:
                        # sessions is a tuple of (list, count)
                        if isinstance(sessions, tuple):
                            sessions_list = sessions[0]
                        else:
                            sessions_list = sessions
                        
                        if sessions_list and len(sessions_list) > 0:
                            latest_session = sessions_list[0]
                            if isinstance(latest_session, dict):
                                current_session_id = latest_session.get('session_id') or latest_session.get('id')
                            elif hasattr(latest_session, 'session_id'):
                                current_session_id = latest_session.session_id
                            elif hasattr(latest_session, 'id'):
                                current_session_id = latest_session.id
                            
                            if current_session_id:
                                logger.info(f"Got session_id from database query: {current_session_id[:8]}...")
                except Exception as e:
                    logger.warning(f"Could not get session_id from database: {e}")
            
            # Send session_id event after session is saved (if we have it)
            if current_session_id:
                logger.info(f"📤 Sending session_id event: {current_session_id[:8]}...")
                self.event_queue.put({
                    "type": "session_id",
                    "session_id": current_session_id
                })
            else:
                logger.warning("⚠️  No session_id available to send - this is a problem!")
            
            # Use accumulated content from streaming, or extract from run_result
            response_content = accumulated_content
            if not response_content:
                if run_result:
                    if hasattr(run_result, 'content'):
                        response_content = run_result.content
                    elif hasattr(run_result, 'output'):
                        response_content = str(run_result.output) if run_result.output else ""
                    elif isinstance(run_result, dict):
                        response_content = run_result.get("content", "") or run_result.get("output", "")
                    elif isinstance(run_result, str):
                        response_content = run_result
            
            self.timing_metrics["total_time"] = time.time() - request_start_time
            logger.info(f"⏱️  METRICS: Total request time: {self.timing_metrics['total_time']:.2f}s")
            
            return run_result, current_session_id, response_content
        except Exception as e:
            logger.error(f"Agent run failed: {e}", exc_info=True)
            self.event_queue.put({
                "type": "error",
                "error": f"Agent failed to generate response: {str(e)}"
            })
            raise HTTPException(status_code=500, detail=f"Agent failed to generate response: {str(e)}")
    
    async def event_generator(self, request: PromptRequest):
        """Generate SSE events from the event queue in real-time"""
        import json as json_module
        
        # Create a task to run the agent in background
        loop = asyncio.get_event_loop()
        agent_task = None
        agent_completed = False
        agent_error = None
        
        async def run_agent_async():
            """Run agent in executor and handle completion"""
            nonlocal agent_completed, agent_error
            try:
                run_result, session_id, response_content = await loop.run_in_executor(
                    None, self.run_agent, request
                )
                
                # Send complete event
                final_event = {
                    "type": "complete",
                    "response": {"content": response_content},
                    "session_id": session_id
                }
                self.event_queue.put(final_event)
                agent_completed = True
            except Exception as e:
                logger.error(f"Error in event generator: {e}", exc_info=True)
                agent_error = e
                self.event_queue.put({
                    "type": "error",
                    "error": str(e)
                })
                agent_completed = True
        
        # Start agent task
        agent_task = asyncio.create_task(run_agent_async())
        
        # Yield events from queue in real-time while agent is running
        while not agent_completed or not self.event_queue.empty():
            try:
                # Use a short timeout to check queue frequently
                event = self.event_queue.get(timeout=0.1)
                yield f"data: {json_module.dumps(event)}\n\n"
                
                if event.get("type") in ["complete", "error"]:
                    break
            except:
                # Queue is empty, check if agent is still running
                if agent_completed:
                    # Agent finished, wait a bit more for any final events
                    await asyncio.sleep(0.05)
                    if self.event_queue.empty():
                        break
                else:
                    # Agent still running, yield empty line to keep connection alive
                    await asyncio.sleep(0.01)
        
        # Ensure agent task completes
        if agent_task and not agent_task.done():
            await agent_task


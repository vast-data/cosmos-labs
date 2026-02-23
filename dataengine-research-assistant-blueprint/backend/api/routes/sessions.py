"""
Sessions routes
"""
import logging
import json
from typing import Optional
from fastapi import HTTPException, Depends

from models import (
    SessionsResponse, SessionItem, SessionResponse,
    UpdateSessionRequest
)
from services.auth import get_token, decode_jwt
from services.agent import get_or_create_agent

logger = logging.getLogger(__name__)

# Import DictAsObject for handling wrapped objects
try:
    from lib.vastdb_storage import DictAsObject
except ImportError:
    # Fallback if DictAsObject is not available
    DictAsObject = type('DictAsObject', (), {})


class SessionsRouter:
    """Router for sessions endpoints"""
    
    @staticmethod
    async def list_sessions(
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        token: str = Depends(get_token)
    ) -> SessionsResponse:
        """
        List all sessions for the authenticated user.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            token: JWT token from Authorization header
        
        Returns:
            SessionsResponse with list of sessions
        """
        try:
            jwt_payload = decode_jwt(token)
            user_id = str(jwt_payload.get("sub") or jwt_payload.get("user_id") or "default_user")
            
            base_agent = get_or_create_agent(user_id=user_id, token=token)
            if not base_agent or not hasattr(base_agent, 'db') or not base_agent.db:
                raise HTTPException(status_code=500, detail="Failed to access database")
            
            from agno.db.base import SessionType
            sessions_result = base_agent.db.get_sessions(
                user_id=user_id,
                session_type=SessionType.AGENT,
                limit=limit or 50
            )
            
            # Handle different return types from get_sessions
            sessions_list = []
            total_count = 0
            
            if isinstance(sessions_result, tuple):
                # Returns (sessions_list, total_count)
                sessions_list, total_count = sessions_result
            elif hasattr(sessions_result, 'sessions'):
                # Returns object with .sessions attribute
                sessions_list = sessions_result.sessions or []
                total_count = getattr(sessions_result, 'total', len(sessions_list))
            elif isinstance(sessions_result, list):
                # Returns list directly
                sessions_list = sessions_result
                total_count = len(sessions_list)
            else:
                sessions_list = []
                total_count = 0
            
            # Convert to response format and filter out deleted sessions
            session_items = []
            if sessions_list:
                for session in sessions_list:
                    # Handle both dict and object formats
                    if isinstance(session, dict):
                        session_id = session.get("session_id")
                        created_at = session.get("created_at", 0)
                        updated_at = session.get("updated_at", 0)
                        summary = session.get("summary", {})
                        metadata = session.get("metadata", {})
                    else:
                        session_id = getattr(session, "session_id", None)
                        created_at = getattr(session, "created_at", 0)
                        updated_at = getattr(session, "updated_at", 0)
                        summary = getattr(session, "summary", {})
                        metadata = getattr(session, "metadata", {})
                    
                    # Filter out deleted sessions
                    is_deleted = False
                    if metadata:
                        if isinstance(metadata, dict):
                            is_deleted = metadata.get("deleted", False)
                        elif isinstance(metadata, str):
                            try:
                                import json
                                parsed = json.loads(metadata)
                                is_deleted = parsed.get("deleted", False) if isinstance(parsed, dict) else False
                            except (json.JSONDecodeError, TypeError):
                                pass
                    
                    if session_id and not is_deleted:
                        # Extract messages from runs (same logic as get_session)
                        messages_list = []
                        
                        # Get runs - handle both dict and object formats
                        if isinstance(session, dict):
                            runs = session.get("runs", [])
                        else:
                            runs = getattr(session, "runs", None)
                            if runs is None:
                                runs = []
                        
                        # Collect citations and collection_metadata from all runs
                        all_citations = []
                        accumulated_collection_metadata = {
                            "num_chunks": 0,
                            "num_unique_files": 0,
                            "total_doc_size_bytes": 0,
                            "total_doc_size_mb": 0.0
                        }  # Accumulate collection_metadata from all runs
                        
                        if runs:
                            
                            # Handle runs - might be a JSON string or list
                            if isinstance(runs, str):
                                try:
                                    runs = json.loads(runs)
                                except (json.JSONDecodeError, TypeError):
                                    runs = []
                            if not isinstance(runs, list):
                                runs = []
                            
                            for run in runs:
                                # Handle DictAsObject wrapper - check for _dict attribute (duck typing)
                                if hasattr(run, "_dict") and isinstance(run._dict, dict):
                                    run_dict = run._dict
                                elif isinstance(run, dict):
                                    run_dict = run
                                else:
                                    continue
                                
                                # Extract citations from run (if stored)
                                run_citations = run_dict.get("citations", [])
                                if run_citations and isinstance(run_citations, list):
                                    all_citations.extend(run_citations)
                                
                                # Extract collection_metadata from run (if stored)
                                run_collection_metadata = run_dict.get("collection_metadata")
                                if run_collection_metadata and isinstance(run_collection_metadata, dict):
                                    # Accumulate collection_metadata values
                                    accumulated_collection_metadata["num_chunks"] += run_collection_metadata.get("num_chunks", 0)
                                    accumulated_collection_metadata["num_unique_files"] += run_collection_metadata.get("num_unique_files", 0)
                                    accumulated_collection_metadata["total_doc_size_bytes"] += run_collection_metadata.get("total_doc_size_bytes", 0)
                                    accumulated_collection_metadata["total_doc_size_mb"] += run_collection_metadata.get("total_doc_size_mb", 0.0)
                                
                                # Extract messages from run
                                run_messages = run_dict.get("messages", [])
                                
                                # Get run input (contains the user's prompt for this run)
                                run_input = run_dict.get("input", "")
                                if run_input and isinstance(run_input, dict):
                                    run_input = run_input.get("input_content") or run_input.get("input")
                                elif hasattr(run_input, "_dict") and isinstance(run_input._dict, dict):
                                    run_input_dict = run_input._dict
                                    run_input = run_input_dict.get("input_content") or run_input_dict.get("input")
                                
                                if not run_messages:
                                    # If no messages, try to construct from input
                                    if run_input:
                                        messages_list.append({
                                            "role": "user",
                                            "content": str(run_input),
                                            "created_at": run_dict.get("created_at", 0),
                                            "citations": None,
                                            "collection_metadata": None
                                        })
                                else:
                                    # First pass: collect all messages and identify the final assistant message
                                    run_messages_processed = []
                                    last_assistant_idx = -1
                                    
                                    for msg_idx, msg in enumerate(run_messages):
                                        # Handle DictAsObject wrapper for messages - check for _dict attribute
                                        if hasattr(msg, "_dict") and isinstance(msg._dict, dict):
                                            msg_dict = msg._dict
                                        elif isinstance(msg, dict):
                                            msg_dict = msg
                                        else:
                                            continue
                                        
                                        # Extract role and content
                                        role = msg_dict.get("role", "user")
                                        content = msg_dict.get("content", "")
                                        
                                        # Handle content as list or string
                                        if isinstance(content, list):
                                            content_texts = []
                                            for item in content:
                                                if isinstance(item, dict):
                                                    if item.get("type") == "text" or "text" in item:
                                                        content_texts.append(str(item.get("text", "")))
                                                    elif "toolResult" in item:
                                                        # Skip tool results in list view
                                                        continue
                                                    elif "content" in item:
                                                        content_texts.append(str(item.get("content", "")))
                                                elif hasattr(item, "_dict") and isinstance(item._dict, dict):
                                                    item_dict = item._dict
                                                    if item_dict.get("type") == "text" or "text" in item_dict:
                                                        content_texts.append(str(item_dict.get("text", "")))
                                                    elif "content" in item_dict:
                                                        content_texts.append(str(item_dict.get("content", "")))
                                                else:
                                                    content_texts.append(str(item))
                                            content = " ".join(content_texts) if content_texts else ""
                                        
                                        # If content is empty or is a tool result, try to get from run.input
                                        if not content or (isinstance(content, str) and "toolResult" in content):
                                            if run_input and role == "user":
                                                content = str(run_input)
                                        
                                        if content:
                                            # Track the last assistant message with content
                                            if role == "assistant":
                                                last_assistant_idx = len(run_messages_processed)
                                            
                                            run_messages_processed.append({
                                                "role": role,
                                                "content": str(content),
                                                "created_at": msg_dict.get("created_at", run_dict.get("created_at", 0)),
                                                "original_idx": msg_idx
                                            })
                                    
                                    # Second pass: add messages with citations and collection_metadata only on the final assistant message
                                    for msg_idx, msg_data in enumerate(run_messages_processed):
                                        message_citations = None
                                        message_collection_metadata = None
                                        # Only attach citations and collection_metadata to the final assistant message
                                        if msg_data["role"] == "assistant" and msg_idx == last_assistant_idx:
                                            if run_citations and isinstance(run_citations, list):
                                                message_citations = run_citations
                                            if run_collection_metadata:
                                                message_collection_metadata = run_collection_metadata
                                        
                                        messages_list.append({
                                            "role": msg_data["role"],
                                            "content": msg_data["content"],
                                            "created_at": msg_data["created_at"],
                                            "citations": message_citations,
                                            "collection_metadata": message_collection_metadata
                                        })
                        
                        # Remove duplicate citations and preserve order
                        unique_citations = list(dict.fromkeys(all_citations)) if all_citations else None
                        
                        # Return accumulated collection_metadata only if we have data
                        final_collection_metadata = None
                        if accumulated_collection_metadata["num_chunks"] > 0 or accumulated_collection_metadata["num_unique_files"] > 0:
                            final_collection_metadata = accumulated_collection_metadata
                        
                        session_items.append(SessionItem(
                            session_id=str(session_id),
                            created_at=int(created_at) if created_at else 0,
                            updated_at=int(updated_at) if updated_at else 0,
                            summary=summary if summary else None,
                            metadata=metadata if metadata else None,
                            messages=messages_list if messages_list else None,
                            citations=unique_citations if unique_citations else None,
                            collection_metadata=final_collection_metadata
                        ))
            
            return SessionsResponse(
                sessions=session_items,
                total=len(session_items)  # Use filtered count
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing sessions: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")
    
    @staticmethod
    async def get_session(
        session_id: str,
        token: str = Depends(get_token)
    ) -> SessionResponse:
        """
        Get details of a specific session.
        
        Args:
            session_id: The session ID to retrieve
            token: JWT token from Authorization header
        
        Returns:
            SessionResponse with session details including messages
        """
        try:
            jwt_payload = decode_jwt(token)
            user_id = str(jwt_payload.get("sub") or jwt_payload.get("user_id") or "default_user")
            
            base_agent = get_or_create_agent(user_id=user_id, token=token)
            if not base_agent or not hasattr(base_agent, 'db') or not base_agent.db:
                raise HTTPException(status_code=500, detail="Failed to access database")
            
            from agno.db.base import SessionType
            session = base_agent.db.get_session(
                session_id=session_id,
                session_type=SessionType.AGENT,
                user_id=user_id,
                deserialize=True
            )
            
            if not session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # Extract messages from runs
            messages_list = []
            runs = getattr(session, 'runs', None) if hasattr(session, 'runs') else None
            logger.info(f"get_session: Initial runs type: {type(runs)}, value: {runs[:1] if isinstance(runs, list) and runs else 'empty'}")
            if not runs:
                runs = []
            
            # Handle runs - might be a JSON string or list
            if isinstance(runs, str):
                try:
                    runs = json.loads(runs)
                    logger.info(f"get_session: Parsed runs from JSON, count: {len(runs) if isinstance(runs, list) else 0}")
                except (json.JSONDecodeError, TypeError):
                    runs = []
            
            if not isinstance(runs, list):
                runs = []
            
            logger.info(f"get_session: Final runs count: {len(runs)}")
            
            # Collect citations, collection_metadata, and tool_events from all runs
            all_citations = []
            accumulated_collection_metadata = {
                "num_chunks": 0,
                "num_unique_files": 0,
                "total_doc_size_bytes": 0,
                "total_doc_size_mb": 0.0
            }  # Accumulate collection_metadata from all runs
            all_tool_events = []  # Collect all tool_start and tool_ended events from all runs
            
            for run_idx, run in enumerate(runs):
                logger.info(f"get_session: Processing run {run_idx}, type: {type(run)}")
                # Handle DictAsObject wrapper - check for _dict attribute (duck typing)
                if hasattr(run, "_dict") and isinstance(run._dict, dict):
                    run_dict = run._dict
                    logger.info(f"get_session: Run {run_idx} is DictAsObject, converted to dict, keys: {list(run_dict.keys())[:15]}")
                elif isinstance(run, dict):
                    run_dict = run
                    logger.info(f"get_session: Run {run_idx} is already dict, keys: {list(run_dict.keys())[:15]}")
                else:
                    # Try to convert using convert_to_dict
                    try:
                        from lib.vastdb_storage import convert_to_dict
                        run_dict = convert_to_dict(run)
                        logger.info(f"get_session: Run {run_idx} converted using convert_to_dict, keys: {list(run_dict.keys())[:15] if isinstance(run_dict, dict) else 'N/A'}")
                    except Exception as e:
                        logger.warning(f"get_session: Run {run_idx} could not be converted: {e}, skipping")
                        continue
                
                # Extract citations from run (if stored) - try multiple ways
                run_citations = []
                if isinstance(run_dict, dict):
                    run_citations = run_dict.get("citations", [])
                elif hasattr(run, "citations"):
                    run_citations = getattr(run, "citations", [])
                
                logger.info(f"get_session: Run {run_idx} citations: {run_citations}, type: {type(run_citations)}, is_list: {isinstance(run_citations, list)}")
                if run_citations and isinstance(run_citations, list) and len(run_citations) > 0:
                    all_citations.extend(run_citations)
                    logger.info(f"get_session: ✅ Added {len(run_citations)} citations from run {run_idx}, total: {len(all_citations)}")
                else:
                    logger.warning(f"get_session: Run {run_idx} has no citations (value: {run_citations}, type: {type(run_citations)})")
                
                # Extract collection_metadata from run (if stored) - try multiple ways
                run_collection_metadata = None
                if isinstance(run_dict, dict):
                    run_collection_metadata = run_dict.get("collection_metadata")
                elif hasattr(run, "collection_metadata"):
                    run_collection_metadata = getattr(run, "collection_metadata", None)
                
                if run_collection_metadata:
                    # Accumulate collection_metadata values
                    if isinstance(run_collection_metadata, dict):
                        accumulated_collection_metadata["num_chunks"] += run_collection_metadata.get("num_chunks", 0)
                        accumulated_collection_metadata["num_unique_files"] += run_collection_metadata.get("num_unique_files", 0)
                        accumulated_collection_metadata["total_doc_size_bytes"] += run_collection_metadata.get("total_doc_size_bytes", 0)
                        accumulated_collection_metadata["total_doc_size_mb"] += run_collection_metadata.get("total_doc_size_mb", 0.0)
                        logger.info(f"get_session: ✅ Found collection_metadata in run {run_idx}: {run_collection_metadata}, accumulated: {accumulated_collection_metadata}")
                else:
                    logger.debug(f"get_session: Run {run_idx} has no collection_metadata")
                
                # Extract tool_events from run (if stored) - keep them per run for matching with messages
                run_tool_events = []
                if isinstance(run_dict, dict):
                    run_tool_events = run_dict.get("tool_events", [])
                    # Handle case where tool_events might be stored as JSON string
                    if isinstance(run_tool_events, str):
                        try:
                            import json
                            run_tool_events = json.loads(run_tool_events)
                        except:
                            run_tool_events = []
                    # Also check _dict if it's a DictAsObject
                    if (not run_tool_events or not isinstance(run_tool_events, list)) and hasattr(run, "_dict"):
                        run_tool_events = run._dict.get("tool_events", [])
                        if isinstance(run_tool_events, str):
                            try:
                                import json
                                run_tool_events = json.loads(run_tool_events)
                            except:
                                run_tool_events = []
                elif hasattr(run, "tool_events"):
                    run_tool_events = getattr(run, "tool_events", [])
                
                # Ensure it's a list
                if not isinstance(run_tool_events, list):
                    if run_tool_events is None:
                        run_tool_events = []
                    else:
                        logger.warning(f"get_session: Run {run_idx} tool_events is not a list: {type(run_tool_events)}, value: {run_tool_events}")
                        run_tool_events = []
                
                if run_tool_events and len(run_tool_events) > 0:
                    all_tool_events.extend(run_tool_events)
                    logger.info(f"get_session: ✅ Found {len(run_tool_events)} tool events in run {run_idx}, total: {len(all_tool_events)}")
                else:
                    logger.debug(f"get_session: Run {run_idx} has no tool_events (value: {run_tool_events}, type: {type(run_tool_events)})")
                
                # Update run to be the dict for message processing
                run = run_dict
                
                # Extract messages from run
                run_messages = run.get("messages", [])
                
                # Get run input (contains the user's prompt for this run)
                run_input = run.get("input", "")
                if run_input and isinstance(run_input, dict):
                    run_input = run_input.get("input_content") or run_input.get("input")
                
                if not run_messages:
                    # If no messages, try to construct from input
                    if run_input:
                        messages_list.append({
                            "role": "user",
                            "content": str(run_input),
                            "created_at": run.get("created_at", 0),
                            "citations": None,
                            "collection_metadata": None
                        })
                else:
                    # First pass: collect all messages, identify the final assistant message, and match tool_events
                    # Strategy: Match tool_events to messages based on position
                    # ToolResult items appear in user messages after assistant messages that call tools
                    run_messages_processed = []
                    last_assistant_idx = -1
                    tool_events_by_message = {}  # Map message index to list of tool_events
                    tool_event_index = 0  # Track position in run_tool_events
                    
                    # Pre-process: collect all messages first, then match tool_events
                    all_run_messages = []
                    for msg in run_messages:
                        if hasattr(msg, "_dict") and isinstance(msg._dict, dict):
                            all_run_messages.append(msg._dict)
                        elif isinstance(msg, dict):
                            all_run_messages.append(msg)
                    
                    logger.info(f"get_session: Processing {len(all_run_messages)} messages from run, {len(run_tool_events)} tool_events available")
                    
                    for msg_idx, msg_dict in enumerate(all_run_messages):
                        # Extract role and content - check RAW content before any processing
                        role = msg_dict.get("role", "user")
                        raw_content = msg_dict.get("content", "")
                        logger.info(f"get_session: Message {msg_idx}: role={role}, content_type={type(raw_content).__name__}, run_messages_processed_len={len(run_messages_processed)}, tool_event_index={tool_event_index}")
                        
                        # Log raw content structure
                        logger.info(f"get_session: Message {msg_idx} (role={role}) raw_content type: {type(raw_content).__name__}")
                        if isinstance(raw_content, list):
                            logger.info(f"get_session: Message {msg_idx} raw_content is list with {len(raw_content)} items")
                            for item_idx, item in enumerate(raw_content[:5]):
                                if isinstance(item, dict):
                                    logger.info(f"get_session: Message {msg_idx} raw_content item {item_idx} keys: {list(item.keys())}")
                        
                        content = raw_content  # Use raw content for processing
                        
                        # Debug: log raw message structure
                        logger.info(f"get_session: Processing message {msg_idx}, role={role}, content_type={type(content).__name__}")
                        if isinstance(content, list):
                            logger.info(f"get_session: Message {msg_idx} content is list with {len(content)} items")
                            for item_idx, item in enumerate(content[:5]):  # First 5 items
                                if isinstance(item, dict):
                                    logger.info(f"get_session: Message {msg_idx} item {item_idx} keys: {list(item.keys())}")
                                    if "toolResult" in item:
                                        logger.info(f"get_session: ✅ Message {msg_idx} item {item_idx} contains toolResult!")
                        elif isinstance(content, str):
                            logger.info(f"get_session: Message {msg_idx} content is string (length={len(content)})")
                        
                        # Check if this message contains toolResult items or should have tool_events
                        message_tool_events = []
                        has_tool_result = False
                        tool_result_count = 0
                        
                        # Handle content as list or string
                        if isinstance(content, list):
                            content_texts = []
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get("type") == "text" or "text" in item:
                                        content_texts.append(str(item.get("text", "")))
                                    elif "toolResult" in item:
                                        # Found a toolResult - match with tool_events
                                        has_tool_result = True
                                        tool_result_count += 1
                                        logger.info(f"get_session: ✅ Found toolResult in message {msg_idx} (role={role}), tool_result_count={tool_result_count}, tool_event_index={tool_event_index}, total_events={len(run_tool_events)}")
                                        
                                        # Find matching tool_start and tool_ended events
                                        # Match by order: each toolResult should have a tool_start followed by tool_ended
                                        # We match by sequential order since tool_events are stored in execution order
                                        if tool_event_index < len(run_tool_events):
                                            # Look for the next tool_start
                                            start_found = False
                                            while tool_event_index < len(run_tool_events):
                                                event = run_tool_events[tool_event_index]
                                                if event.get("type") == "tool_start":
                                                    message_tool_events.append(event)
                                                    logger.info(f"get_session: ✅ Matched tool_start for toolResult {tool_result_count}: {event.get('tool_name')}")
                                                    tool_event_index += 1
                                                    start_found = True
                                                    break
                                                tool_event_index += 1
                                            
                                            # Look for corresponding tool_ended (should be immediately after tool_start)
                                            if start_found and tool_event_index < len(run_tool_events):
                                                event = run_tool_events[tool_event_index]
                                                if event.get("type") == "tool_ended":
                                                    message_tool_events.append(event)
                                                    logger.info(f"get_session: ✅ Matched tool_ended for toolResult {tool_result_count}: {event.get('tool_name')}, duration={event.get('duration')}")
                                                    tool_event_index += 1
                                            elif start_found:
                                                logger.warning(f"get_session: ⚠️  Found tool_start but no tool_ended at index {tool_event_index}")
                                        else:
                                            logger.warning(f"get_session: ⚠️  tool_event_index ({tool_event_index}) >= total events ({len(run_tool_events)})")
                                    elif "content" in item:
                                        content_texts.append(str(item.get("content", "")))
                                else:
                                    content_texts.append(str(item))
                            content = " ".join(content_texts) if content_texts else ""
                        elif isinstance(content, str) and not content and role == "user":
                            # Message with empty string content and user role might be a toolResult message
                            # Try to match with tool_events based on position
                            # ToolResult messages typically appear as user messages with empty content
                            # Match if we have tool_events available and this looks like a toolResult message
                            if tool_event_index < len(run_tool_events):
                                # Check if the previous message was an assistant message (tool call pattern)
                                if len(run_messages_processed) > 0:
                                    prev_msg = run_messages_processed[-1]
                                    if prev_msg.get("role") == "assistant":
                                        # This might be a toolResult message - try to match tool_events
                                        has_tool_result = True
                                        logger.info(f"get_session: 🤔 Message {msg_idx} (role={role}) has empty content, might be toolResult, tool_event_index={tool_event_index}, total_events={len(run_tool_events)}")
                                        
                                        # Match the next tool_start and tool_ended
                                        if tool_event_index < len(run_tool_events):
                                            event = run_tool_events[tool_event_index]
                                            if event.get("type") == "tool_start":
                                                message_tool_events.append(event)
                                                tool_event_index += 1
                                                logger.info(f"get_session: ✅ Matched tool_start for empty user message: {event.get('tool_name')}")
                                                
                                                if tool_event_index < len(run_tool_events):
                                                    event = run_tool_events[tool_event_index]
                                                    if event.get("type") == "tool_ended":
                                                        message_tool_events.append(event)
                                                        tool_event_index += 1
                                                        logger.info(f"get_session: ✅ Matched tool_ended for empty user message: {event.get('tool_name')}")
                        
                        # If content is empty or is a tool result, try to get from run.input
                        if not content or (isinstance(content, str) and "toolResult" in content):
                            if run_input and role == "user":
                                content = str(run_input)
                        
                        # Match tool_events to messages based on position
                        # Strategy: Match tool_events to assistant messages that likely called tools
                        # Each assistant message that comes after a user message might have called a tool
                        # We match tool_events in order to assistant messages
                        # Allow multiple tool_events per message (assistant can call multiple tools)
                        if role == "assistant" and tool_event_index < len(run_tool_events) and len(run_messages_processed) > 0:
                            prev_msg = run_messages_processed[-1]
                            # If previous message was user, this assistant might have called tools
                            if prev_msg.get("role") == "user":
                                # Match tool_events to this assistant message (can match multiple)
                                has_tool_result = True
                                logger.info(f"get_session: 🤔 Message {msg_idx} (role={role}) after user message, matching tool_events, tool_event_index={tool_event_index}")
                                
                                # Match all available tool_start/tool_ended pairs for this assistant message
                                # Continue matching while we have tool_events and they're tool_start/tool_ended pairs
                                while tool_event_index < len(run_tool_events):
                                    event = run_tool_events[tool_event_index]
                                    if event.get("type") == "tool_start":
                                        message_tool_events.append(event)
                                        tool_event_index += 1
                                        logger.info(f"get_session: ✅ Matched tool_start to assistant message: {event.get('tool_name')}")
                                        
                                        if tool_event_index < len(run_tool_events):
                                            event = run_tool_events[tool_event_index]
                                            if event.get("type") == "tool_ended":
                                                message_tool_events.append(event)
                                                tool_event_index += 1
                                                logger.info(f"get_session: ✅ Matched tool_ended to assistant message: {event.get('tool_name')}")
                                            else:
                                                # Next event is not tool_ended, stop matching for this message
                                                break
                                    else:
                                        # Next event is not tool_start, stop matching for this message
                                        break
                        
                        # Include message if it has content OR if we detected/matched toolResult items
                        if content or has_tool_result:
                            # Track the last assistant message with content
                            if role == "assistant" and content:
                                last_assistant_idx = len(run_messages_processed)
                            
                            processed_idx = len(run_messages_processed)
                            run_messages_processed.append({
                                "role": role,
                                "content": str(content) if content else "",
                                "created_at": msg_dict.get("created_at", run.get("created_at", 0)),
                                "original_idx": msg_idx
                            })
                            
                            # Store tool_events for this message if it has toolResult
                            if message_tool_events:
                                tool_events_by_message[processed_idx] = message_tool_events
                                logger.info(f"get_session: ✅ Message {msg_idx} (role={role}) has {len(message_tool_events)} tool events, tool_result_count={tool_result_count}")
                            elif has_tool_result:
                                logger.warning(f"get_session: ⚠️  Message {msg_idx} (role={role}) has toolResult but no tool_events matched (tool_event_index={tool_event_index}, total_events={len(run_tool_events)})")
                    
                    # Second pass: add messages with citations, collection_metadata, and tool_events
                    for msg_idx, msg_data in enumerate(run_messages_processed):
                        message_citations = None
                        message_collection_metadata = None
                        message_tool_events = tool_events_by_message.get(msg_idx, None)
                        
                        # Only attach citations and collection_metadata to the final assistant message
                        if msg_data["role"] == "assistant" and msg_idx == last_assistant_idx:
                            if run_citations and isinstance(run_citations, list):
                                message_citations = run_citations
                            if run_collection_metadata:
                                message_collection_metadata = run_collection_metadata
                        
                        message_dict = {
                            "role": msg_data["role"],
                            "content": msg_data["content"],
                            "created_at": msg_data["created_at"],
                            "citations": message_citations,
                            "collection_metadata": message_collection_metadata
                        }
                        
                        # Attach tool_events to this message if it has any
                        if message_tool_events:
                            message_dict["tool_events"] = message_tool_events
                            logger.info(f"get_session: ✅ Attached {len(message_tool_events)} tool events to message {msg_idx} (role={msg_data['role']})")
                        
                        messages_list.append(message_dict)
            
            # Remove duplicate citations and preserve order
            unique_citations = list(dict.fromkeys(all_citations)) if all_citations else None
            
            # Return accumulated collection_metadata only if we have data
            final_collection_metadata = None
            if accumulated_collection_metadata["num_chunks"] > 0 or accumulated_collection_metadata["num_unique_files"] > 0:
                final_collection_metadata = accumulated_collection_metadata
            
            return SessionResponse(
                session_id=session.session_id if hasattr(session, 'session_id') else session.id,
                created_at=session.created_at if hasattr(session, 'created_at') else 0,
                updated_at=session.updated_at if hasattr(session, 'updated_at') else 0,
                summary=session.summary if hasattr(session, 'summary') else None,
                metadata=session.metadata if hasattr(session, 'metadata') else None,
                messages=messages_list if messages_list else None,
                citations=unique_citations if unique_citations else None,
                collection_metadata=final_collection_metadata,
                tool_events=all_tool_events if all_tool_events else None
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")
    
    @staticmethod
    async def update_session(
        session_id: str,
        request: UpdateSessionRequest,
        token: str = Depends(get_token)
    ) -> SessionResponse:
        """
        Update session summary and/or metadata.
        
        Args:
            session_id: The session ID to update
            request: UpdateSessionRequest with summary and/or metadata
            token: JWT token from Authorization header
        
        Returns:
            SessionResponse with updated session details
        """
        try:
            jwt_payload = decode_jwt(token)
            user_id = str(jwt_payload.get("sub") or jwt_payload.get("user_id") or "default_user")
            
            base_agent = get_or_create_agent(user_id=user_id, token=token)
            if not base_agent or not hasattr(base_agent, 'db') or not base_agent.db:
                raise HTTPException(status_code=500, detail="Failed to access database")
            
            from agno.db.base import SessionType
            session = base_agent.db.get_session(
                session_id=session_id,
                session_type=SessionType.AGENT,
                user_id=user_id,
                deserialize=True
            )
            
            if not session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # Update summary if provided
            if request.summary is not None:
                session.summary = request.summary
            
            # Update metadata if provided
            if request.metadata is not None:
                if session.metadata is None:
                    session.metadata = {}
                session.metadata.update(request.metadata)
            
            # Save updated session
            base_agent.db.upsert_session(session)
            
            return SessionResponse(
                session_id=session.session_id if hasattr(session, 'session_id') else session.id,
                created_at=session.created_at if hasattr(session, 'created_at') else 0,
                updated_at=session.updated_at if hasattr(session, 'updated_at') else 0,
                summary=session.summary if hasattr(session, 'summary') else None,
                metadata=session.metadata if hasattr(session, 'metadata') else None,
                messages=None  # Don't include messages in update response
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


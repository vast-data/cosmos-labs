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
                            if isinstance(runs, str):
                                try: runs = json.loads(runs)
                                except: runs = []
                            if not isinstance(runs, list): runs = []

                            # Only use the LAST run's messages (each run has full accumulated history)
                            for run in runs:
                                if hasattr(run, "_dict") and isinstance(run._dict, dict): run_dict = run._dict
                                elif isinstance(run, dict): run_dict = run
                                else: continue
                                rc = run_dict.get("citations", [])
                                if rc and isinstance(rc, list): all_citations.extend(rc)
                                rcm = run_dict.get("collection_metadata")
                                if rcm and isinstance(rcm, dict):
                                    accumulated_collection_metadata["num_chunks"] += rcm.get("num_chunks", 0)
                                    accumulated_collection_metadata["num_unique_files"] += rcm.get("num_unique_files", 0)
                                    accumulated_collection_metadata["total_doc_size_bytes"] += rcm.get("total_doc_size_bytes", 0)
                                    accumulated_collection_metadata["total_doc_size_mb"] += rcm.get("total_doc_size_mb", 0.0)

                            if runs:
                                last_run_raw = runs[-1]
                                if hasattr(last_run_raw, "_dict") and isinstance(last_run_raw._dict, dict): last_rd = last_run_raw._dict
                                elif isinstance(last_run_raw, dict): last_rd = last_run_raw
                                else: last_rd = {}
                                run_messages = last_rd.get("messages", [])
                                run_input = last_rd.get("input", "")
                                if run_input and isinstance(run_input, dict):
                                    run_input = run_input.get("input_content") or run_input.get("input")
                                last_run_citations = last_rd.get("citations", [])
                                last_run_cm = last_rd.get("collection_metadata")

                                if not run_messages and run_input:
                                    messages_list.append({"role": "user", "content": str(run_input), "created_at": last_rd.get("created_at", 0), "citations": None, "collection_metadata": None})
                                else:
                                    processed = []
                                    last_asst = -1
                                    for msg in run_messages:
                                        if hasattr(msg, "_dict") and isinstance(msg._dict, dict): md = msg._dict
                                        elif isinstance(msg, dict): md = msg
                                        else: continue
                                        role = md.get("role", "user")
                                        content = md.get("content", "")
                                        if isinstance(content, list):
                                            texts = []
                                            for it in content:
                                                if isinstance(it, dict):
                                                    if it.get("type") == "text" or "text" in it: texts.append(str(it.get("text", "")))
                                                    elif "toolResult" in it: continue
                                                    elif "content" in it: texts.append(str(it.get("content", "")))
                                                else: texts.append(str(it))
                                            content = " ".join(texts) if texts else ""
                                        if not content and run_input and role == "user": content = str(run_input)
                                        if content:
                                            if role == "assistant": last_asst = len(processed)
                                            processed.append({"role": role, "content": str(content), "created_at": md.get("created_at", last_rd.get("created_at", 0))})
                                    for idx, m in enumerate(processed):
                                        mc = last_run_citations if (m["role"] == "assistant" and idx == last_asst and last_run_citations) else None
                                        mcm = last_run_cm if (m["role"] == "assistant" and idx == last_asst and last_run_cm) else None
                                        messages_list.append({"role": m["role"], "content": m["content"], "created_at": m["created_at"], "citations": mc, "collection_metadata": mcm})
                        
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
            
            # ── Collect per-run metadata (citations, collection_metadata, tool_events) ──
            # Each run stores the full accumulated message history, so we only
            # extract *messages* from the LAST run to avoid duplication.
            # But we still walk every run to collect citations and metadata.
            per_run_meta = []  # list of {citations, collection_metadata, tool_events}
            run_dicts = []     # run dicts in order

            for run_idx, run in enumerate(runs):
                if hasattr(run, "_dict") and isinstance(run._dict, dict):
                    rd = run._dict
                elif isinstance(run, dict):
                    rd = run
                else:
                    try:
                        from lib.vastdb_storage import convert_to_dict
                        rd = convert_to_dict(run)
                    except Exception:
                        continue
                run_dicts.append(rd)

                rc = rd.get("citations", []) if isinstance(rd, dict) else []
                rcm = rd.get("collection_metadata") if isinstance(rd, dict) else None
                rte = rd.get("tool_events", []) if isinstance(rd, dict) else []
                if isinstance(rte, str):
                    try: rte = json.loads(rte)
                    except: rte = []
                if not isinstance(rte, list): rte = []
                if not isinstance(rc, list): rc = []
                per_run_meta.append({"citations": rc, "collection_metadata": rcm, "tool_events": rte})

            # ── Build a map: run_id → per_run_meta index ──
            run_id_to_meta = {}
            for idx, rd in enumerate(run_dicts):
                rid = rd.get("id") or rd.get("run_id")
                if rid:
                    run_id_to_meta[str(rid)] = idx

            # ── Only process messages from the LAST run (it has the full history) ──
            accumulated_collection_metadata = {"num_chunks": 0, "num_unique_files": 0, "total_doc_size_bytes": 0, "total_doc_size_mb": 0.0}
            all_citations = []
            all_tool_events = []

            for meta in per_run_meta:
                if meta["citations"]:
                    all_citations.extend(meta["citations"])
                cm = meta["collection_metadata"]
                if cm and isinstance(cm, dict):
                    accumulated_collection_metadata["num_chunks"] += cm.get("num_chunks", 0)
                    accumulated_collection_metadata["num_unique_files"] += cm.get("num_unique_files", 0)
                    accumulated_collection_metadata["total_doc_size_bytes"] += cm.get("total_doc_size_bytes", 0)
                    accumulated_collection_metadata["total_doc_size_mb"] += cm.get("total_doc_size_mb", 0.0)
                if meta["tool_events"]:
                    all_tool_events.extend(meta["tool_events"])

            if run_dicts:
                last_run = run_dicts[-1]
                last_run_meta = per_run_meta[-1] if per_run_meta else {}
                run_messages = last_run.get("messages", [])
                run_input = last_run.get("input", "")
                if run_input and isinstance(run_input, dict):
                    run_input = run_input.get("input_content") or run_input.get("input")

                logger.info(f"get_session: Using last run with {len(run_messages)} messages")

                if not run_messages and run_input:
                    messages_list.append({"role": "user", "content": str(run_input), "created_at": last_run.get("created_at", 0), "citations": None, "collection_metadata": None})
                else:
                    all_run_messages = []
                    for msg in run_messages:
                        if hasattr(msg, "_dict") and isinstance(msg._dict, dict):
                            all_run_messages.append(msg._dict)
                        elif isinstance(msg, dict):
                            all_run_messages.append(msg)

                    last_run_citations = last_run_meta.get("citations", []) if last_run_meta else []
                    last_run_cm = last_run_meta.get("collection_metadata") if last_run_meta else None

                    # Build per-run tool_events queue (one entry per run, in order)
                    run_tool_events_queue = [m.get("tool_events", []) for m in per_run_meta]

                    # Extract only real user prompts and final assistant answers,
                    # deduplicating by content prefix.
                    output_messages = []
                    last_assistant_idx = -1
                    seen_content = set()

                    for msg_dict in all_run_messages:
                        role = msg_dict.get("role", "user")
                        raw_content = msg_dict.get("content", "")

                        text = ""
                        is_tool_message = False
                        if isinstance(raw_content, list):
                            texts = []
                            for item in raw_content:
                                if isinstance(item, dict):
                                    if "toolResult" in item or "toolUse" in item:
                                        is_tool_message = True
                                    elif item.get("type") == "text" or "text" in item:
                                        t = str(item.get("text", ""))
                                        if t.strip():
                                            texts.append(t)
                                    elif "content" in item:
                                        t = str(item.get("content", ""))
                                        if t.strip():
                                            texts.append(t)
                            text = " ".join(texts) if texts else ""
                        elif isinstance(raw_content, str):
                            text = raw_content.strip()

                        if not text:
                            continue
                        if is_tool_message and role == "user":
                            continue

                        content_key = (role, text[:200])
                        if content_key in seen_content:
                            continue
                        seen_content.add(content_key)

                        ts = msg_dict.get("created_at", last_run.get("created_at", 0))
                        if role == "user":
                            output_messages.append({"role": "user", "content": text, "created_at": ts, "citations": None, "collection_metadata": None})
                        elif role == "assistant":
                            last_assistant_idx = len(output_messages)
                            output_messages.append({"role": "assistant", "content": text, "created_at": ts, "citations": None, "collection_metadata": None})

                    # Distribute each run's tool_events to the Nth assistant message
                    assistant_indices = [i for i, m in enumerate(output_messages) if m["role"] == "assistant"]
                    for run_idx, tool_evts in enumerate(run_tool_events_queue):
                        if tool_evts and run_idx < len(assistant_indices):
                            target = output_messages[assistant_indices[run_idx]]
                            target["tool_events"] = tool_evts

                    # Attach citations/collection_metadata to the last assistant message
                    if last_assistant_idx >= 0:
                        output_messages[last_assistant_idx]["citations"] = last_run_citations if last_run_citations else None
                        output_messages[last_assistant_idx]["collection_metadata"] = last_run_cm

                    messages_list = output_messages
                    logger.info(f"get_session: Produced {len(messages_list)} deduplicated messages from {len(all_run_messages)} raw ({len(assistant_indices)} assistant, {len(run_tool_events_queue)} runs with tools)")

            unique_citations = list(dict.fromkeys(all_citations)) if all_citations else None
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


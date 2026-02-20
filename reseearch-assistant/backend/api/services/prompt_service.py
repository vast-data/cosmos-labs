"""
Prompt handling service
"""
import logging
import time
from typing import Optional, Dict, Any

from fastapi import HTTPException

from models import PromptRequest, PromptResponse
from services.auth import decode_jwt
from services.agent import get_or_create_agent
from api.utils.session_utils import generate_summary_from_prompt

logger = logging.getLogger(__name__)


class PromptService:
    """Service for handling prompt requests"""
    
    def __init__(self, user_id: str, token: str):
        self.user_id = user_id
        self.token = token
        self.timing_metrics = {}
    
    def send_prompt(self, request: PromptRequest) -> PromptResponse:
        """
        Send a prompt to the research assistant agent.
        
        Args:
            request: PromptRequest with prompt text and optional conversation_id/session_name
        
        Returns:
            PromptResponse with agent's response and session_id
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
        
        # Handle session management
        target_session_id = None
        loaded_session = None
        
        is_new_session = not (request.conversation_id and request.conversation_id != "unknown")
        
        if not is_new_session:
            target_session_id = request.conversation_id
            base_agent = get_or_create_agent(user_id=self.user_id, token=self.token)
            if not base_agent:
                raise HTTPException(status_code=500, detail="Failed to create agent")
            
            if hasattr(base_agent, 'db') and base_agent.db:
                try:
                    from agno.db.base import SessionType
                    loaded_session = base_agent.db.get_session(
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
        
        # Create or get agent
        self.timing_metrics["agent_creation_start"] = time.time()
        # Get collection name from request (use first collection if list provided)
        collection_name = None
        if request.collections:
            collection_name = request.collections[0] if isinstance(request.collections, list) else request.collections
        
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
        
        agent_creation_time = self.timing_metrics["agent_creation_end"] - self.timing_metrics["agent_creation_start"]
        logger.info(f"⏱️  METRICS: Agent creation took: {agent_creation_time:.2f}s")
        
        # Track first tool timing and collect citations
        first_tool_started = False
        collected_citations = []  # Store citations from tool calls
        
        def extract_citations_from_result(function_name: str, result: Any) -> list:
            """Extract citations from retrieve_chunks tool result (same logic as streaming service)"""
            citations = []
            if function_name == "retrieve_chunks":
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
                    
                    for chunk in chunks:
                        if not isinstance(chunk, dict):
                            continue
                        
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
                            if str(file_name) not in citations:
                                citations.append(str(file_name))
            return citations
        
        def timing_tool_hook(function_name: str, function_call, arguments: Dict[str, Any]):
            nonlocal first_tool_started, collected_citations
            if not first_tool_started:
                first_tool_started = True
                self.timing_metrics["first_tool_start"] = time.time()
                time_to_first_tool = self.timing_metrics["first_tool_start"] - self.timing_metrics.get("agent_run_start", request_start_time)
                logger.info(f"⏱️  METRICS: Time to first tool: {time_to_first_tool:.2f}s")
            
            result = function_call(**arguments)
            
            # Extract citations from retrieve_chunks results
            if function_name == "retrieve_chunks":
                logger.info(f"🔍 Tool hook: retrieve_chunks called, result type: {type(result).__name__}")
                if isinstance(result, dict):
                    logger.info(f"   Result keys: {list(result.keys())[:10]}")
                    # Check for errors first
                    if "error" in result:
                        logger.error(f"   ❌ retrieve_chunks returned error: {result.get('error')}")
                        logger.error(f"   Detail: {result.get('detail', 'no detail')}")
                    # Check for chunks/documents/results
                    for key in ["chunks", "documents", "results", "data"]:
                        if key in result:
                            val = result[key]
                            logger.info(f"   Found '{key}': type={type(val).__name__}, length={len(val) if isinstance(val, (list, dict)) else 'N/A'}")
                            if isinstance(val, list) and len(val) > 0:
                                first_item = val[0]
                                logger.info(f"      First item type: {type(first_item).__name__}, keys: {list(first_item.keys())[:5] if isinstance(first_item, dict) else 'N/A'}")
                citations = extract_citations_from_result(function_name, result)
                if citations:
                    logger.info(f"📚 Extracted {len(citations)} citations from retrieve_chunks: {citations[:5]}")
                    collected_citations.extend(citations)
                else:
                    logger.warning(f"⚠️  No citations extracted from retrieve_chunks result")
            
            if first_tool_started and self.timing_metrics.get("first_tool_complete") is None:
                self.timing_metrics["first_tool_complete"] = time.time()
                time_to_first_tool_complete = self.timing_metrics["first_tool_complete"] - self.timing_metrics.get("first_tool_start", time.time())
                logger.info(f"⏱️  METRICS: First tool completed in: {time_to_first_tool_complete:.2f}s")
            
            return result
        
        # Run agent
        self.timing_metrics["agent_run_start"] = time.time()
        time_to_agent_run = self.timing_metrics["agent_run_start"] - request_start_time
        logger.info(f"⏱️  METRICS: Time to agent.run() start: {time_to_agent_run:.2f}s")
        
        # Add tool hook to agent
        if hasattr(agent, 'tool_hooks'):
            if agent.tool_hooks:
                agent.tool_hooks.append(timing_tool_hook)
            else:
                agent.tool_hooks = [timing_tool_hook]
        elif hasattr(agent, 'add_tool_hook'):
            agent.add_tool_hook(timing_tool_hook)
        
        run_result = agent.run(request.prompt)
        self.timing_metrics["agent_run_end"] = time.time()
        
        agent_run_duration = self.timing_metrics["agent_run_end"] - self.timing_metrics["agent_run_start"]
        logger.info(f"⏱️  METRICS: Agent run took: {agent_run_duration:.2f}s")
        
        # Get session ID - try multiple sources
        current_session_id = None
        
        # First, try to get from agent.session
        if hasattr(agent, 'session') and agent.session:
            current_session_id = getattr(agent.session, 'session_id', None) or getattr(agent.session, 'id', None)
        
        # If not found, try from last_run
        if not current_session_id and hasattr(agent, 'last_run') and agent.last_run:
            current_session_id = getattr(agent.last_run, 'session_id', None)
        
        # If still not found, try from run_result
        if not current_session_id and run_result:
            if hasattr(run_result, 'session_id'):
                current_session_id = run_result.session_id
            elif isinstance(run_result, dict) and 'session_id' in run_result:
                current_session_id = run_result['session_id']
        
        # If we had a target_session_id (for continuing sessions), use it
        if not current_session_id and target_session_id:
            current_session_id = target_session_id
        
        # Log for debugging
        if not current_session_id:
            logger.warning(f"Could not determine session_id. agent.session={hasattr(agent, 'session')}, agent.last_run={hasattr(agent, 'last_run')}, run_result type={type(run_result)}")
        
        # Set session summary for new sessions or update if session_name provided
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
                    # Check if this is the first prompt (only 1 run = the current one we just executed)
                    num_runs = len(reloaded_session.runs) if reloaded_session.runs else 0
                    is_first_prompt = num_runs <= 1
                    
                    # Normalize session_name (treat empty strings as None)
                    provided_session_name = request.session_name.strip() if request.session_name and request.session_name.strip() else None
                    
                    logger.info(f"Setting session summary: session_id={current_session_id[:8]}..., provided_session_name={provided_session_name}, num_runs={num_runs}, is_first_prompt={is_first_prompt}")
                    
                    # Determine the session title and summary
                    if provided_session_name:
                        # User provided a name, always use it as title
                        session_title = provided_session_name
                        logger.info(f"Using provided session name: {session_title}")
                    elif reloaded_session.summary and reloaded_session.summary.get("title"):
                        # Existing title, keep it unless user provided a new one
                        session_title = reloaded_session.summary.get("title")
                        logger.info(f"Keeping existing title: {session_title}")
                    else:
                        # Fallback
                        session_title = "My Session"
                        logger.info(f"Using fallback title: {session_title}")
                    
                    # Generate summary from first prompt if it's the first prompt and no summary exists
                    session_summary_text = None
                    if is_first_prompt and not (reloaded_session.summary and reloaded_session.summary.get("summary")):
                        logger.info(f"Generating summary from first prompt: {request.prompt[:50]}...")
                        session_summary_text = generate_summary_from_prompt(agent, request.prompt)
                        logger.info(f"Generated summary: {session_summary_text[:100]}...")
                    
                    # Update summary dict if needed
                    if not reloaded_session.summary:
                        reloaded_session.summary = {}
                    
                    # Always update title if:
                    # 1. User provided a session_name (always respect user input)
                    # 2. It's the first prompt and no title exists yet
                    # 3. Current title is default "My Session" and we have a better one
                    current_title = reloaded_session.summary.get("title") if reloaded_session.summary else None
                    should_update_title = (
                        provided_session_name or  # User provided a name
                        (is_first_prompt and not current_title) or  # First prompt, no title
                        (is_first_prompt and current_title == "My Session" and session_title != "My Session")  # First prompt, replace default
                    )
                    
                    # Always update summary if we generated one
                    should_update_summary = session_summary_text is not None
                    
                    # If we have a summary but no title (or default title), use summary as title
                    if session_summary_text and (not current_title or current_title == "My Session"):
                        # Use summary as title (truncate if too long)
                        if len(session_summary_text) > 60:
                            session_title = session_summary_text[:57] + "..."
                        else:
                            session_title = session_summary_text
                        should_update_title = True
                        logger.info(f"Using generated summary as title: {session_title}")
                    
                    if should_update_title:
                        reloaded_session.summary["title"] = session_title
                    
                    if should_update_summary:
                        reloaded_session.summary["summary"] = session_summary_text
                    
                    if should_update_title or should_update_summary:
                        agent.db.upsert_session(reloaded_session)
                        logger.info(f"✅ Set session title to: {session_title}")
                        if session_summary_text:
                            logger.info(f"✅ Set session summary: {session_summary_text[:100]}...")
                    else:
                        logger.info(f"⚠️  Not updating: provided_session_name={provided_session_name}, is_first_prompt={is_first_prompt}, current_title={current_title}")
            except Exception as e:
                logger.warning(f"Could not set session summary: {e}", exc_info=True)
        
        # Save session if needed
        if current_session_id and hasattr(agent, 'session') and agent.session and hasattr(agent, 'db') and agent.db:
            try:
                from agno.db.base import SessionType
                reloaded_session = agent.db.get_session(
                    session_id=current_session_id,
                    session_type=SessionType.AGENT,
                    user_id=self.user_id,
                    deserialize=False
                )
                
                if reloaded_session:
                    reloaded_runs = []
                    if hasattr(reloaded_session, 'runs') and reloaded_session.runs:
                        import json
                        runs_raw = reloaded_session.runs
                        if isinstance(runs_raw, str):
                            try:
                                reloaded_runs = json.loads(runs_raw)
                            except:
                                reloaded_runs = []
                        elif isinstance(reloaded_runs, list):
                            reloaded_runs = runs_raw
                    
                    # Check if agent.session has more runs than reloaded
                    agent_runs_count = 0
                    if hasattr(agent.session, 'runs') and agent.session.runs:
                        if isinstance(agent.session.runs, list):
                            agent_runs_count = len(agent.session.runs)
                        elif isinstance(agent.session.runs, str):
                            try:
                                agent_runs_list = json.loads(agent.session.runs)
                                agent_runs_count = len(agent_runs_list)
                            except:
                                pass
                    
                    if agent_runs_count > len(reloaded_runs):
                        # Use agent.session as base
                        if hasattr(agent.session, 'runs') and agent.session.runs:
                            if isinstance(agent.session.runs, list):
                                reloaded_runs = agent.session.runs
                            elif isinstance(agent.session.runs, str):
                                try:
                                    reloaded_runs = json.loads(agent.session.runs)
                                except:
                                    pass
                    
                    # Identify the new run to add
                    run_to_add = None
                    if hasattr(agent, 'last_run') and agent.last_run:
                        run_to_add = agent.last_run
                    elif hasattr(agent.session, 'runs') and agent.session.runs:
                        if isinstance(agent.session.runs, list) and len(agent.session.runs) > 0:
                            run_to_add = agent.session.runs[-1]
                    
                    if run_to_add:
                        from lib.vastdb_storage import convert_to_dict
                        run_dict = convert_to_dict(run_to_add)
                        if run_dict and run_dict not in reloaded_runs:
                            # Add collected citations to the run
                            if collected_citations:
                                unique_citations = list(dict.fromkeys(collected_citations))
                                run_dict['citations'] = unique_citations
                                logger.info(f"📚 Added {len(unique_citations)} citations to run: {unique_citations[:5]}")
                            reloaded_runs.append(run_dict)
                    
                    if reloaded_runs:
                        reloaded_session.runs = json.dumps(reloaded_runs, default=str)
                        agent.db.upsert_session(reloaded_session)
            except Exception as e:
                logger.warning(f"Could not save session: {e}")
        
        # Extract response content
        response_content = ""
        if hasattr(run_result, 'content'):
            response_content = run_result.content
        elif isinstance(run_result, dict):
            response_content = run_result.get("content", "")
        elif isinstance(run_result, str):
            response_content = run_result
        
        self.timing_metrics["total_time"] = time.time() - request_start_time
        logger.info(f"⏱️  METRICS: Total request time: {self.timing_metrics['total_time']:.2f}s")
        
        return PromptResponse(
            response={"content": response_content},
            session_id=str(current_session_id) if current_session_id else "unknown"
        )


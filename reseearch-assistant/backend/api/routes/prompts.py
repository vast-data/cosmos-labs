"""
Prompt routes
"""
import logging
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse

from models import PromptRequest, PromptResponse
from services.auth import get_token, decode_jwt
from api.services.prompt_service import PromptService
from api.services.streaming_service import StreamingService

logger = logging.getLogger(__name__)


class PromptsRouter:
    """Router for prompt endpoints"""
    
    @staticmethod
    async def send_prompt(
        request: PromptRequest,
        token: str = Depends(get_token)
    ) -> PromptResponse:
        """
        Send a prompt to the research assistant agent.
        
        Args:
            request: PromptRequest with prompt text and optional conversation_id/collections
            token: JWT token from Authorization header
        
        Returns:
            PromptResponse with agent's response and conversation_id
        """
        try:
            jwt_payload = decode_jwt(token)
            user_id = str(jwt_payload.get("sub") or jwt_payload.get("user_id") or "default_user")
            
            service = PromptService(user_id=user_id, token=token)
            return service.send_prompt(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending prompt: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to process prompt: {str(e)}")
    
    @staticmethod
    async def send_prompt_stream(
        request: PromptRequest,
        token: str = Depends(get_token)
    ) -> StreamingResponse:
        """
        Send a prompt to the research assistant agent with real-time tool usage streaming.
        Uses Server-Sent Events (SSE) to stream tool execution updates to the client.
        
        Args:
            request: PromptRequest with prompt text and optional conversation_id/collections
            token: JWT token from Authorization header
        
        Returns:
            StreamingResponse with SSE events for tool usage and final response
        """
        try:
            jwt_payload = decode_jwt(token)
            user_id = str(jwt_payload.get("sub") or jwt_payload.get("user_id") or "default_user")
            
            service = StreamingService(user_id=user_id, token=token)
            return StreamingResponse(
                service.event_generator(request),
                media_type="text/event-stream"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error streaming prompt: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to stream prompt: {str(e)}")


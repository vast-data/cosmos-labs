"""
Tools routes
"""
import logging
from fastapi import HTTPException

from models import ToolsResponse, ToolItem
from services.agent import get_available_tools

logger = logging.getLogger(__name__)


class ToolsRouter:
    """Router for tools endpoints"""
    
    @staticmethod
    async def get_tools() -> ToolsResponse:
        """
        List all available tools for the agent.
        
        Returns:
            ToolsResponse with list of available tools
        """
        try:
            tools = get_available_tools()
            tool_items = [ToolItem(**tool) for tool in tools]
            return ToolsResponse(tools=tool_items)
        except Exception as e:
            logger.error(f"Error getting tools: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")


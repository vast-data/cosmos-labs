from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter()

FRONTEND_CONFIG_PATH = Path("/app/frontend-config/search-suggestions.json")

@router.get("/search-suggestions")
async def get_search_suggestions():
    try:
        if not FRONTEND_CONFIG_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail="Search suggestions configuration not found"
            )
        
        with open(FRONTEND_CONFIG_PATH, 'r') as f:
            suggestions = json.load(f)
        
        return suggestions
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in search suggestions config: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading search suggestions: {str(e)}"
        )


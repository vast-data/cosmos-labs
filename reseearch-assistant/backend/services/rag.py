"""
RAG service
Handles interactions with the RAG backend
"""

import logging
import json
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
import httpx

from config import RAG_BASE_URL, RAG_SSL_VERIFY, RAG_TIMEOUT
from services.auth import get_headers

logger = logging.getLogger(__name__)


def list_collections_from_rag(
    token: str,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all available collections for RAG queries.
    
    Args:
        token: JWT token for authentication
        base_url: Base URL of the RAG API
    
    Returns:
        Dictionary containing collections information
    
    Raises:
        HTTPException: If the request fails
    """
    base_url = (base_url or RAG_BASE_URL).rstrip('/')
    client = httpx.Client(
        base_url=base_url,
        verify=RAG_SSL_VERIFY,
        timeout=RAG_TIMEOUT
    )
    
    try:
        response = client.get(
            "/api/v1/collections",
            headers=get_headers(token)
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to get collections: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting collections: {str(e)}"
        )
    finally:
        client.close()


def create_collection(
    collection_name: str,
    token: str,
    is_public: bool = True,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new collection in the RAG backend.
    
    Args:
        collection_name: Name of the collection to create
        token: JWT token for authentication
        is_public: Whether the collection should be public (default: True)
        base_url: Base URL of the RAG API
    
    Returns:
        Dictionary containing the creation result
    
    Raises:
        HTTPException: If the request fails
    """
    base_url = (base_url or RAG_BASE_URL).rstrip('/')
    client = httpx.Client(
        base_url=base_url,
        verify=RAG_SSL_VERIFY,
        timeout=RAG_TIMEOUT
    )
    
    try:
        # The API expects a JSON object with collection_names, is_public, etc.
        payload = {
            "collection_names": [collection_name],
            "is_public": is_public,
        }
        # Only add allowed_groups and allowed_users when collection is public
        if is_public:
            payload["allowed_groups"] = ["*"]
            payload["allowed_users"] = ["*"]
        
        response = client.post(
            "/api/v1/collections",
            json=payload,
            headers=get_headers(token)
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to create collection: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating collection: {str(e)}"
        )
    finally:
        client.close()


def upload_document(
    file_content: bytes,
    filename: str,
    collection_name: str,
    token: str,
    base_url: Optional[str] = None,
    allowed_groups: Optional[List[str]] = None,
    is_public: bool = False
) -> Dict[str, Any]:
    """
    Upload a document to a collection in the RAG backend.
    
    Args:
        file_content: Binary content of the file to upload
        filename: Name of the file (e.g., "document.pdf")
        collection_name: Name of the collection to upload to
        token: JWT token for authentication
        base_url: Base URL of the RAG API
        allowed_groups: List of allowed groups (default: ["public-read"])
        is_public: Whether the document is public (default: False)
    
    Returns:
        Dictionary containing the upload result
    
    Raises:
        HTTPException: If the request fails
    """
    base_url = (base_url or RAG_BASE_URL).rstrip('/')
    client = httpx.Client(
        base_url=base_url,
        verify=RAG_SSL_VERIFY,
        timeout=RAG_TIMEOUT * 2  # Longer timeout for file uploads
    )
    
    if allowed_groups is None:
        allowed_groups = ["public-read"]
    
    try:
        # Prepare multipart form data
        files = {
            'documents': (filename, file_content)
        }
        
        # Prepare metadata as JSON string
        data = {
            "collection_name": collection_name,
            "allowed_groups": allowed_groups,
            "is_public": is_public
        }
        
        # Create form data with file and JSON metadata
        form_data = {
            'data': json.dumps(data)
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
        
        response = client.post(
            "/api/v1/documents",
            files=files,
            data=form_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to upload document: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )
    finally:
        client.close()


def delete_collections(
    collection_names: List[str],
    token: str,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete one or more collections from the RAG backend.
    
    Args:
        collection_names: List of collection names to delete
        token: JWT token for authentication
        base_url: Base URL of the RAG API
    
    Returns:
        Dictionary containing the deletion result
    
    Raises:
        HTTPException: If the request fails
    """
    base_url = (base_url or RAG_BASE_URL).rstrip('/')
    client = httpx.Client(
        base_url=base_url,
        verify=RAG_SSL_VERIFY,
        timeout=RAG_TIMEOUT
    )
    
    try:
        response = client.request(
            method="DELETE",
            url="/api/v1/collections",
            json=collection_names,
            headers=get_headers(token)
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to delete collections: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting collections: {str(e)}"
        )
    finally:
        client.close()


def list_documents(
    collection_name: str,
    token: str,
    is_public: bool = False,
    limit: int = 0,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    List documents in a collection from the RAG backend.
    
    Args:
        collection_name: Name of the collection to list documents from
        token: JWT token for authentication
        is_public: Whether to list only public documents (default: False)
        limit: Maximum number of documents to return (0 means no limit, default: 0)
        base_url: Base URL of the RAG API
    
    Returns:
        Dictionary containing documents information
    
    Raises:
        HTTPException: If the request fails
    """
    base_url = (base_url or RAG_BASE_URL).rstrip('/')
    client = httpx.Client(
        base_url=base_url,
        verify=RAG_SSL_VERIFY,
        timeout=RAG_TIMEOUT
    )
    
    try:
        # Build query parameters
        params = {
            "collection_name": collection_name,
            "is_public": str(is_public).lower()
        }
        
        response = client.get(
            "/api/v1/documents",
            params=params,
            headers=get_headers(token)
        )
        response.raise_for_status()
        result = response.json()
        
        # Apply limit if specified (0 means no limit)
        if limit > 0 and "documents" in result:
            result["documents"] = result["documents"][:limit]
            # Update total_documents to reflect the limited count
            if "total_documents" in result:
                result["total_documents"] = len(result["documents"])
        
        return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to list documents: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )
    finally:
        client.close()


"""
Collections routes
"""
import os
import logging
import urllib.request
from typing import Optional, List
from fastapi import HTTPException, Depends, UploadFile, File, Form

import vastdb

# Try to import ADBC for native VastDB queries
try:
    import adbc_driver_manager
    import adbc_driver_manager.dbapi
    ADBC_AVAILABLE = True
except ImportError:
    ADBC_AVAILABLE = False

from models import (
    CollectionsResponse, CollectionItem,
    CreateCollectionRequest, CreateCollectionResponse,
    DeleteCollectionsRequest, DeleteCollectionsResponse,
    UploadDocumentRequest,
    ListDocumentsResponse, DocumentItem
)
from services.auth import get_token
from services.rag import list_collections_from_rag, create_collection, delete_collections, upload_document, list_documents

logger = logging.getLogger(__name__)

# VastDB ADBC driver path
ADBC_DRIVER_PATH = "/tmp/libadbc_driver_vastdb.so"
ADBC_DRIVER_URL = os.getenv(
    "VASTDB_ADBC_DRIVER_URL",
    "https://artifactory.vastdata.com/files/vastdb-native-client/1955131/libadbc_driver_vastdb.so"
)


def ensure_adbc_driver():
    """Download VastDB ADBC driver if not present"""
    if not os.path.exists(ADBC_DRIVER_PATH):
        logger.info(f"Downloading VastDB ADBC driver from {ADBC_DRIVER_URL}")
        try:
            urllib.request.urlretrieve(ADBC_DRIVER_URL, ADBC_DRIVER_PATH)
            os.chmod(ADBC_DRIVER_PATH, 0o755)
            logger.info(f"VastDB ADBC driver downloaded to {ADBC_DRIVER_PATH}")
        except Exception as e:
            logger.error(f"Failed to download ADBC driver: {e}")
            return False
    return True


class CollectionsRouter:
    """Router for collections endpoints"""
    
    @staticmethod
    async def get_collections(
        limit: Optional[int] = None,
        token: str = Depends(get_token)
    ) -> CollectionsResponse:
        """
        List all available collections for RAG queries.
        
        Args:
            limit: Optional limit on number of collections to return (-1 for unlimited)
            token: JWT token from Authorization header
        
        Returns:
            CollectionsResponse with list of collections
        """
        try:
            collections_data = list_collections_from_rag(token=token)
            
            # Extract collections from response
            if isinstance(collections_data, list):
                collections_list = collections_data
            elif isinstance(collections_data, dict) and "collections" in collections_data:
                collections_list = collections_data["collections"]
            elif isinstance(collections_data, dict) and "items" in collections_data:
                collections_list = collections_data["items"]
            else:
                collections_list = []
            
            # Apply limit if specified (limit=-1 means unlimited)
            if limit is not None and limit != -1 and limit > 0:
                collections_list = collections_list[:limit]
            
            # Convert to CollectionItem models
            collection_items = []
            for item in collections_list:
                if isinstance(item, dict):
                    # Extract collection name/ID from various possible fields
                    coll_id = (
                        item.get("full_collection_name") or 
                        item.get("collection_name") or 
                        item.get("id") or 
                        item.get("collection_id") or 
                        ""
                    )
                    
                    # Build a descriptive string from available metadata
                    desc_parts = []
                    if item.get("description"):
                        desc_parts.append(item.get("description"))
                    if item.get("num_entities") is not None:
                        desc_parts.append(f"{item.get('num_entities')} entities")
                    if item.get("source"):
                        desc_parts.append(f"source: {item.get('source')}")
                    if item.get("allowed_users"):
                        desc_parts.append(f"users: {', '.join(item.get('allowed_users', []))}")
                    
                    coll_desc = " | ".join(desc_parts) if desc_parts else (
                        item.get("name") or 
                        f"Collection: {coll_id}" if coll_id else 
                        "No description"
                    )
                    
                    if coll_id:
                        collection_items.append(CollectionItem(
                            id=coll_id,
                            description=coll_desc
                        ))
            
            return CollectionsResponse(collections=collection_items)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting collections: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to get collections: {str(e)}")
    
    @staticmethod
    async def create_collection_endpoint(
        request: CreateCollectionRequest,
        token: str = Depends(get_token)
    ) -> CreateCollectionResponse:
        """
        Create a new collection in the RAG backend.
        
        Args:
            request: CreateCollectionRequest with collection_name and is_public
            token: JWT token from Authorization header
        
        Returns:
            CreateCollectionResponse with creation result
        """
        try:
            result = create_collection(
                collection_name=request.collection_name,
                token=token,
                is_public=request.is_public
            )
            return CreateCollectionResponse(
                message="Collection created successfully",
                collection_name=request.collection_name,
                result=result
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating collection: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")
    
    @staticmethod
    async def delete_collections_endpoint(
        collection_names: List[str],
        token: str = Depends(get_token)
    ) -> DeleteCollectionsResponse:
        """
        Delete one or more collections from the RAG backend.
        
        Args:
            collection_names: List of collection names to delete (passed as JSON body)
            token: JWT token from Authorization header
        
        Returns:
            DeleteCollectionsResponse with deletion result
        """
        try:
            result = delete_collections(
                collection_names=collection_names,
                token=token
            )
            return DeleteCollectionsResponse(
                message="Collections deleted successfully",
                deleted_collections=collection_names,
                result=result
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting collections: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to delete collections: {str(e)}")
    
    @staticmethod
    async def upload_document_endpoint(
        collection_name: str = Form(...),
        file: UploadFile = File(...),
        token: str = Depends(get_token),
        allowed_groups: Optional[str] = Form(None),
        is_public: bool = Form(False)
    ) -> dict:
        """
        Upload a document to a collection in the RAG backend.
        
        Args:
            collection_name: Name of the collection to upload to
            file: The file to upload
            token: JWT token from Authorization header
            allowed_groups: Optional comma-separated list of allowed groups
            is_public: Whether the document should be public
        
        Returns:
            Dictionary with upload result
        """
        try:
            # Parse allowed_groups if provided
            groups_list = None
            if allowed_groups:
                groups_list = [g.strip() for g in allowed_groups.split(",") if g.strip()]
            
            # Read file content
            file_content = await file.read()
            
            result = upload_document(
                collection_name=collection_name,
                file_content=file_content,
                filename=file.filename,
                token=token,
                allowed_groups=groups_list or ["public-read"],
                is_public=is_public
            )
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading document: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    @staticmethod
    async def get_full_collections(
        collection_name: Optional[str] = None,
        token: str = Depends(get_token)
    ) -> CollectionsResponse:
        """
        Get full collection details with metadata from VastDB.
        
        Returns the same structure as GET /collections (id and description),
        but the description includes metadata: num_chunks, num_unique_files, total_doc_size.
        
        Args:
            collection_name: Optional specific collection to query (defaults to all from RAG)
            token: JWT token from Authorization header
        
        Returns:
            CollectionsResponse with collections containing metadata in description
        """
        try:
            # Get VastDB connection parameters from environment
            endpoint = os.getenv("VASTDB_ENDPOINT")
            access_key = os.getenv("VASTDB_ACCESS_KEY")
            secret_key = os.getenv("VASTDB_SECRET_KEY")
            
            # Derive bucket and schema from RAG_BASE_URL
            from services.agent import _get_collections_bucket_and_schema
            bucket_name, schema_name = _get_collections_bucket_and_schema()
            
            if not all([endpoint, access_key, secret_key, bucket_name]):
                raise HTTPException(
                    status_code=500,
                    detail="VastDB environment variables not configured"
                )
            
            # Get collections from RAG
            if collection_name:
                collections_to_query = [collection_name]
            else:
                collections_data = list_collections_from_rag(token=token)
                if isinstance(collections_data, list):
                    collections_list = collections_data
                elif isinstance(collections_data, dict) and "collections" in collections_data:
                    collections_list = collections_data["collections"]
                elif isinstance(collections_data, dict) and "items" in collections_data:
                    collections_list = collections_data["items"]
                else:
                    collections_list = []
                
                collections_to_query = []
                for item in collections_list:
                    if isinstance(item, dict):
                        coll_name = (
                            item.get("full_collection_name") or 
                            item.get("collection_name") or 
                            item.get("id") or 
                            ""
                        )
                        if coll_name:
                            collections_to_query.append(coll_name)
            
            collection_items: List[CollectionItem] = []
            session = vastdb.connect(
                endpoint=endpoint,
                access=access_key,
                secret=secret_key,
                ssl_verify=False
            )
            
            try:
                with session.transaction() as tx:
                    bucket_obj = tx.bucket(bucket_name)
                    
                    for coll_name in collections_to_query:
                        try:
                            is_syncengine = coll_name.startswith("syncengine.")
                            
                            # Find table
                            lookup_schema = schema_name
                            lookup_table_name = coll_name
                            
                            if not is_syncengine and '__' in coll_name:
                                parts = coll_name.split('__', 1)
                                if len(parts) == 2:
                                    lookup_schema = parts[0]
                                    lookup_table_name = parts[1]
                            
                            try:
                                table = bucket_obj.schema(lookup_schema).table(lookup_table_name)
                            except Exception:
                                table = bucket_obj.schema(schema_name).table(coll_name)
                            
                            if table is None:
                                raise Exception(f"Table not found for collection {coll_name}")
                            
                            # Get chunk count
                            stats = table.stats
                            num_chunks = stats.num_rows if stats else 0
                            
                            # Get file count and sizes from catalog
                            num_unique_files = 0
                            total_doc_size = 0
                            
                            try:
                                from ibis import _ as ibis_col
                                cat = tx.catalog()
                                
                                if is_syncengine:
                                    # For syncengine collections: parent_path format is /syncengine.something/
                                    predicate = ibis_col.parent_path.startswith(f"/{coll_name}/") & (ibis_col.element_type == "FILE")
                                else:
                                    # For regular collections: parent_path format is /{bucket_name}/{collection}/
                                    predicate = ibis_col.parent_path.startswith(f"/{bucket_name}/{coll_name}/") & (ibis_col.element_type == "FILE")
                                
                                reader = cat.select(["name", "size", "parent_path", "element_type"], predicate=predicate)
                                result = reader.read_all()
                                df = result.to_pandas()
                                
                                if len(df) > 0:
                                    num_unique_files = len(df)
                                    total_doc_size = int(df["size"].sum())
                                    
                            except Exception as e:
                                logger.warning(f"Catalog query failed for {coll_name}: {e}")
                            
                            # Format description with metadata in a structured way
                            total_doc_size_mb = round(total_doc_size / (1024 * 1024), 2) if total_doc_size else 0.0
                            description = f"num_chunks={num_chunks}|num_unique_files={num_unique_files}|total_doc_size_bytes={total_doc_size}|total_doc_size_mb={total_doc_size_mb}"
                            
                            collection_items.append(CollectionItem(
                                id=coll_name,
                                description=description
                            ))
                            
                        except Exception as e:
                            logger.warning(f"Could not query collection {coll_name}: {e}")
                            # Return empty metadata for failed collections
                            description = f"num_chunks=0|num_unique_files=0|total_doc_size_bytes=0|total_doc_size_mb=0.0"
                            collection_items.append(CollectionItem(
                                id=coll_name,
                                description=description
                            ))
            finally:
                pass
            
            return CollectionsResponse(collections=collection_items)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting full collections: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to get full collections: {str(e)}")
    
    @staticmethod
    async def list_documents_endpoint(
        collection_name: str,
        token: str = Depends(get_token),
        is_public: bool = False,
        limit: int = 0
    ) -> ListDocumentsResponse:
        """
        List documents in a collection from the RAG backend.
        
        Args:
            collection_name: Name of the collection to list documents from
            token: JWT token from Authorization header
            is_public: Whether to list only public documents (default: False)
            limit: Maximum number of documents to return (0 means no limit, default: 0)
        
        Returns:
            ListDocumentsResponse with list of documents
        """
        try:
            result = list_documents(
                collection_name=collection_name,
                token=token,
                is_public=is_public,
                limit=limit
            )
            
            # Convert to response model
            documents = []
            if "documents" in result:
                for doc in result["documents"]:
                    if isinstance(doc, dict):
                        doc_name = doc.get("document_name", "")
                        if doc_name:
                            documents.append(DocumentItem(document_name=doc_name))
            
            return ListDocumentsResponse(
                message=result.get("message", "Documents retrieved successfully"),
                total_documents=result.get("total_documents", len(documents)),
                documents=documents
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing documents: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


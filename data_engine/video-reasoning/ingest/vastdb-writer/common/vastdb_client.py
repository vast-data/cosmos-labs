import logging
import hashlib
import vastdb
import pyarrow as pa
from typing import Dict, List, Any
from datetime import datetime


class VastDBClient:
    """VastDB client for storing video reasoning vectors"""

    def __init__(self, settings):
        self.settings = settings
        self.table_name = settings.vdbcollection
        self.bucket = settings.vdbbucket
        self.schema_name = settings.vdbschema

        # VastDB schema columns for video reasoning vectors
        self.schema_columns = pa.schema([
            ("pk", pa.utf8()),                                          # Unique ID (hash of source)
            ("source", pa.utf8()),                                      # Original video S3 path
            ("segment_source", pa.utf8()),                              # Segment S3 path
            ("filename", pa.utf8()),                                    # Segment filename
            ("segment_number", pa.uint32()),                            # Segment number (extracted from filename)
            ("reasoning_content", pa.utf8()),                           # AI-generated reasoning text
            ("vector", pa.list_(pa.field(name="item", type=pa.float32(), nullable=False), self.settings.embeddingdimensions)),  # Embedding vector
            ("cosmos_model", pa.utf8()),                                # Cosmos model name
            ("embedding_model", pa.utf8()),                             # Embedding model name
            ("tokens_used", pa.int32()),                                # Cosmos tokens
            ("processing_time", pa.float64()),                          # Cosmos processing time
            ("timestamp", pa.utf8()),                                   # Record creation time
            ("video_url", pa.utf8()),                                   # Cosmos video URL
            
            # NEW: Permission fields for GUI access control
            ("allowed_users", pa.list_(pa.utf8())),                     # List of usernames with access
            ("is_public", pa.bool_()),                                  # Whether video is publicly accessible (default True)
            
            # NEW: Additional metadata fields
            ("upload_timestamp", pa.timestamp('ns')),                   # When video was uploaded
            ("duration", pa.float64()),                                 # Segment duration in seconds
            ("total_segments", pa.uint32()),                            # Total number of segments
            ("original_video", pa.utf8()),                              # Original video filename
            ("tags", pa.list_(pa.utf8())),                              # User-defined tags
            
            ("extra_metadata", pa.string())                             # JSON for extensibility
        ])

        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize VastDB connection"""
        endpoint = self.settings.vdbendpoint
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"http://{endpoint}"

        logging.info(f"[VDB_CLIENT] Connecting to VastDB at {endpoint}")

        self.session = vastdb.connect(
            endpoint=endpoint,
            access=self.settings.vdbaccesskey,
            secret=self.settings.vdbsecretkey,
            ssl_verify=False
        )

        logging.info("[VDB_CLIENT] VastDB connection established")

    def ensure_schema_and_table(self) -> bool:
        """Ensure schema and table exist"""
        try:
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                
                # Create schema if it doesn't exist
                schema = bucket.schema(self.schema_name, fail_if_missing=False)
                if schema is None:
                    schema = bucket.create_schema(self.schema_name, fail_if_exists=False)
                    logging.info(f"[VDB_CLIENT] Schema '{self.schema_name}' created")
                else:
                    logging.info(f"[VDB_CLIENT] Schema '{self.schema_name}' already exists")
                
                # Create table if it doesn't exist
                table = schema.table(self.table_name, fail_if_missing=False)
                if table is None:
                    try:
                        table = schema.create_table(self.table_name, columns=self.schema_columns)
                        logging.info(f"[VDB_CLIENT] Table '{self.table_name}' created")
                    except Exception as e:
                        # Handle race condition - table might have been created by another process
                        if "409" in str(e) or "Conflict" in str(e) or "already exists" in str(e).lower():
                            logging.info(f"[VDB_CLIENT] Table '{self.table_name}' already exists, using existing")
                            table = schema.table(self.table_name, fail_if_missing=False)
                            if table is None:
                                raise RuntimeError(f"Failed to get table after creation conflict")
                        else:
                            raise
                else:
                    logging.info(f"[VDB_CLIENT] Table '{self.table_name}' already exists")
                
                return True
                
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Error ensuring schema and table: {e}")
            return False

    def store_vector(self, embedding_event: Dict[str, Any]) -> bool:
        """
        Store video reasoning with vector in VastDB
        
        This is a pure storage function - receives pre-computed embedding
        """
        try:
            source = embedding_event.get("source", "")
            filename = embedding_event.get("filename", "")
            reasoning_content = embedding_event.get("reasoning_content", "")
            embedding = embedding_event.get("embedding", [])
            embedding_model = embedding_event.get("embedding_model", "")
            embedding_dimensions = embedding_event.get("embedding_dimensions", 0)
            cosmos_model = embedding_event.get("cosmos_model", "")
            tokens_used = embedding_event.get("tokens_used", 0)
            processing_time = embedding_event.get("processing_time", 0.0)
            video_url = embedding_event.get("video_url", "")
            status = embedding_event.get("status", "success")
            
            if not reasoning_content:
                logging.warning("[VDB_CLIENT] No reasoning content to store")
                return True
            
            if not embedding:
                logging.warning("[VDB_CLIENT] No embedding vector to store")
                return False
            
            # Generate unique primary key
            pk = hashlib.md5(source.encode()).hexdigest()
            
            # Generate timestamp
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Extract permission and metadata fields from event (populated from pipeline)
            is_public = embedding_event.get("is_public", True)  # Default to public (CLI uploads)
            allowed_users_str = embedding_event.get("allowed_users", "")  # Empty for CLI uploads
            tags_str = embedding_event.get("tags", "")
            original_video = embedding_event.get("original_video", filename)
            upload_timestamp_str = embedding_event.get("upload_timestamp", "")
            segment_duration_event = embedding_event.get("segment_duration", 5.0)
            segment_number_event = embedding_event.get("segment_number")
            total_segments_event = embedding_event.get("total_segments")
            
            # Parse allowed_users and tags from comma-separated strings
            allowed_users = [u.strip() for u in allowed_users_str.split(",") if u.strip()] if allowed_users_str else []
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            
            # Use segment metadata from event (passed through pipeline from S3)
            # IMPORTANT: Use "is not None" to handle 0 values correctly
            if segment_number_event is not None:
                segment_number = int(segment_number_event) if segment_number_event else 0
            else:
                # Fallback: Extract from filename
                segment_number = 0
                if "_segment_" in filename:
                    try:
                        parts = filename.split("_segment_")[1].split("_of_")
                        segment_number = int(parts[0])
                    except:
                        logging.warning(f"[VDB_CLIENT] Could not extract segment number from filename: {filename}")
            
            if total_segments_event is not None:
                total_segments = int(total_segments_event) if total_segments_event else 1
            else:
                # Fallback: Extract from filename
                total_segments = 1
                if "_segment_" in filename and "_of_" in filename:
                    try:
                        parts = filename.split("_of_")[1].split(".")[0]
                        total_segments = int(parts)
                    except:
                        logging.warning(f"[VDB_CLIENT] Could not extract total segments from filename: {filename}")
            
            segment_duration = float(segment_duration_event) if segment_duration_event else 5.0
            
            logging.info(f"[VDB_CLIENT] [DEBUG] Event metadata: segment_number={segment_number_event}, total_segments={total_segments_event}, allowed_users={allowed_users_str}")
            logging.info(f"[VDB_CLIENT] [DEBUG] Parsed metadata: segment_number={segment_number}, total_segments={total_segments}, allowed_users={allowed_users}")
            
            # Parse upload timestamp
            if upload_timestamp_str:
                try:
                    upload_timestamp = datetime.fromisoformat(upload_timestamp_str.replace('Z', '+00:00'))
                except:
                    upload_timestamp = datetime.utcnow()
            else:
                upload_timestamp = datetime.utcnow()
            
            # Prepare extra metadata as JSON
            extra_metadata = {
                "status": status,
                "embedding_dimensions": embedding_dimensions
            }
            
            record = {
                "pk": pk,
                "source": source,
                "segment_source": source,  # For segments, source and segment_source are the same
                "filename": filename,
                "segment_number": segment_number,
                "reasoning_content": reasoning_content,
                "vector": embedding,
                "cosmos_model": cosmos_model,
                "embedding_model": embedding_model,
                "tokens_used": tokens_used,
                "processing_time": processing_time,
                "timestamp": timestamp,
                "video_url": video_url,
                
                # Permission fields (from pipeline)
                "allowed_users": allowed_users,
                "is_public": is_public,
                
                # Additional metadata fields (from pipeline)
                "upload_timestamp": upload_timestamp,
                "duration": segment_duration,
                "total_segments": total_segments,
                "original_video": original_video,
                "tags": tags,
                
                "extra_metadata": str(extra_metadata)
            }
            
            logging.info(f"[VDB_CLIENT] Storing reasoning vector for {filename}")
            logging.info(f"[VDB_CLIENT] Reasoning content: {reasoning_content[:100]}...")
            logging.info(f"[VDB_CLIENT] Vector dimensions: {len(embedding)}")
            logging.info(f"[VDB_CLIENT] Metadata: is_public={is_public}, allowed_users={allowed_users}, segment={segment_number}/{total_segments}, tags={tags}")
            
            # Ensure schema and table exist before inserting
            if not self.ensure_schema_and_table():
                return False
            
            # Create Arrow table and insert
            arrow_table = pa.Table.from_pylist([record], schema=self.schema_columns)
            
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                schema = bucket.schema(self.schema_name)
                table = schema.table(self.table_name)
                table.insert(arrow_table)
            
            logging.info(f"[VDB_CLIENT] Successfully stored reasoning vector for {filename} in VastDB")
            logging.info(f"[VDB_CLIENT] Table: {self.bucket}.{self.schema_name}.{self.table_name}")
            return True
            
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Error storing reasoning vector: {e}", exc_info=True)
            return False

    def close(self):
        """Close VastDB connection"""
        if hasattr(self, 'session') and hasattr(self.session, 'close'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


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

        self.schema_columns = pa.schema([
            ("pk", pa.utf8()),
            ("source", pa.utf8()),
            ("segment_source", pa.utf8()),
            ("filename", pa.utf8()),
            ("segment_number", pa.uint32()),
            ("reasoning_content", pa.utf8()),
            ("vector", pa.list_(pa.field(name="item", type=pa.float32(), nullable=False), self.settings.embeddingdimensions)),
            ("cosmos_model", pa.utf8()),
            ("embedding_model", pa.utf8()),
            ("tokens_used", pa.int32()),
            ("processing_time", pa.float64()),
            ("timestamp", pa.utf8()),
            ("video_url", pa.utf8()),
            ("allowed_users", pa.list_(pa.utf8())),
            ("is_public", pa.bool_()),
            ("upload_timestamp", pa.timestamp('ns')),
            ("duration", pa.float64()),
            ("total_segments", pa.uint32()),
            ("original_video", pa.utf8()),
            ("tags", pa.list_(pa.utf8())),
            ("camera_id", pa.utf8()),
            ("capture_type", pa.utf8()),
            ("neighborhood", pa.utf8()),
            ("extra_metadata", pa.string())
        ])

        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize VastDB connection"""
        endpoint = self.settings.vdbendpoint
        if not endpoint.startswith(("http://", "https://")):
            endpoint = f"http://{endpoint}"

        self.session = vastdb.connect(
            endpoint=endpoint,
            access=self.settings.vdbaccesskey,
            secret=self.settings.vdbsecretkey,
            ssl_verify=False
        )

    def ensure_schema_and_table(self) -> bool:
        """Ensure schema and table exist, creating them if needed."""
        try:
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                
                schema = bucket.schema(self.schema_name, fail_if_missing=False)
                if schema is None:
                    schema = bucket.create_schema(self.schema_name, fail_if_exists=False)
                
                table = schema.table(self.table_name, fail_if_missing=False)
                if table is None:
                    try:
                        schema.create_table(self.table_name, columns=self.schema_columns)
                    except Exception as e:
                        if "409" in str(e) or "Conflict" in str(e) or "already exists" in str(e).lower():
                            table = schema.table(self.table_name, fail_if_missing=False)
                            if table is None:
                                raise RuntimeError("Failed to get table after creation conflict")
                        else:
                            raise
                
                return True
                
        except Exception as e:
            logging.error(f"Error ensuring schema/table: {e}")
            return False

    def store_vector(self, embedding_event: Dict[str, Any]) -> bool:
        """Store video reasoning with vector in VastDB."""
        try:
            source = embedding_event.get("source", "")
            filename = embedding_event.get("filename", "")
            reasoning_content = embedding_event.get("reasoning_content", "")
            embedding = embedding_event.get("embedding", [])
            
            if not reasoning_content:
                return True
            
            if not embedding:
                logging.warning("No embedding vector to store")
                return False
            
            pk = hashlib.md5(source.encode()).hexdigest()
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            is_public = embedding_event.get("is_public", True)
            allowed_users_str = embedding_event.get("allowed_users", "")
            tags_str = embedding_event.get("tags", "")
            original_video = embedding_event.get("original_video", filename)
            upload_timestamp_str = embedding_event.get("upload_timestamp", "")
            segment_duration_event = embedding_event.get("segment_duration", 5.0)
            segment_number_event = embedding_event.get("segment_number")
            total_segments_event = embedding_event.get("total_segments")
            
            camera_id = embedding_event.get("camera_id", "")
            capture_type = embedding_event.get("capture_type", "")
            neighborhood = embedding_event.get("neighborhood", "")
            
            allowed_users = [u.strip() for u in allowed_users_str.split(",") if u.strip()] if allowed_users_str else []
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
            
            # Parse segment metadata
            if segment_number_event is not None:
                segment_number = int(segment_number_event) if segment_number_event else 0
            else:
                segment_number = 0
                if "_segment_" in filename:
                    try:
                        parts = filename.split("_segment_")[1].split("_of_")
                        segment_number = int(parts[0])
                    except:
                        pass
            
            if total_segments_event is not None:
                total_segments = int(total_segments_event) if total_segments_event else 1
            else:
                total_segments = 1
                if "_segment_" in filename and "_of_" in filename:
                    try:
                        parts = filename.split("_of_")[1].split(".")[0]
                        total_segments = int(parts)
                    except:
                        pass
            
            segment_duration = float(segment_duration_event) if segment_duration_event else 5.0
            
            if upload_timestamp_str:
                try:
                    upload_timestamp = datetime.fromisoformat(upload_timestamp_str.replace('Z', '+00:00'))
                except:
                    upload_timestamp = datetime.utcnow()
            else:
                upload_timestamp = datetime.utcnow()
            
            extra_metadata = {
                "status": embedding_event.get("status", "success"),
                "embedding_dimensions": embedding_event.get("embedding_dimensions", 0)
            }
            
            record = {
                "pk": pk,
                "source": source,
                "segment_source": source,
                "filename": filename,
                "segment_number": segment_number,
                "reasoning_content": reasoning_content,
                "vector": embedding,
                "cosmos_model": embedding_event.get("cosmos_model", ""),
                "embedding_model": embedding_event.get("embedding_model", ""),
                "tokens_used": embedding_event.get("tokens_used", 0),
                "processing_time": embedding_event.get("processing_time", 0.0),
                "timestamp": timestamp,
                "video_url": embedding_event.get("video_url", ""),
                "allowed_users": allowed_users,
                "is_public": is_public,
                "upload_timestamp": upload_timestamp,
                "duration": segment_duration,
                "total_segments": total_segments,
                "original_video": original_video,
                "tags": tags,
                "camera_id": camera_id,
                "capture_type": capture_type,
                "neighborhood": neighborhood,
                "extra_metadata": str(extra_metadata)
            }
            
            if not self.ensure_schema_and_table():
                return False
            
            arrow_table = pa.Table.from_pylist([record], schema=self.schema_columns)
            
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                schema = bucket.schema(self.schema_name)
                table = schema.table(self.table_name)
                table.insert(arrow_table)
            
            return True
            
        except Exception as e:
            logging.error(f"Error storing vector: {e}")
            return False

    def close(self):
        """Close VastDB connection"""
        if hasattr(self, 'session') and hasattr(self.session, 'close'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


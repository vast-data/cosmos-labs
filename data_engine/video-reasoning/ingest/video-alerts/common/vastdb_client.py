import logging
import hashlib
import vastdb
import pyarrow as pa
import os
import urllib.request
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    import adbc_driver_manager
    import adbc_driver_manager.dbapi
    ADBC_AVAILABLE = True
except ImportError:
    ADBC_AVAILABLE = False
    logging.warning("ADBC driver manager not available - install with: pip install adbc-driver-manager")


class VastDBClient:
    """VastDB client for reading video segments and storing safety alerts"""

    def __init__(self, settings):
        self.settings = settings
        self.bucket = settings.vdbbucket
        self.schema_name = settings.vdbschema
        
        # Table names
        self.video_table = settings.vdbcollection
        self.alerts_table = settings.alerts_table

        # Schema for safety_alerts table
        self.alerts_schema = pa.schema([
            ("pk", pa.utf8()),                                          # Unique ID (hash of query+source+timestamp)
            ("alert_query", pa.utf8()),                                 # The alert query that triggered
            ("source", pa.utf8()),                                      # Video segment S3 path
            ("similarity_score", pa.float64()),                         # Similarity score
            ("threshold", pa.float64()),                                # Threshold used
            ("reasoning_content", pa.utf8()),                           # AI reasoning from video segment
            ("original_video", pa.utf8()),                              # Original video filename
            ("segment_number", pa.uint32()),                            # Segment number
            ("sms_sent", pa.bool_()),                                   # Whether SMS was sent successfully
            ("alert_timestamp", pa.timestamp('ns')),                    # When alert was triggered
            ("extra_metadata", pa.string())                             # JSON for extensibility
        ])

        # Initialize ADBC connection attribute
        self._adbc_connection = None
        
        self._initialize_connection()
        self._setup_adbc()

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

    def _setup_adbc(self):
        """Setup ADBC connection for similarity search"""
        if not ADBC_AVAILABLE:
            logging.error("[VDB_CLIENT] ADBC driver manager not available")
            self._adbc_connection = None
            return
        
        try:
            # Download VastDB ADBC driver if not already present
            driver_path = "/tmp/libadbc_driver_vastdb.so"
            if not os.path.exists(driver_path):
                driver_url = "artifactory_adbc_so_file_placeholder"
                logging.info(f"[VDB_CLIENT] Downloading VastDB ADBC driver from {driver_url}")
                urllib.request.urlretrieve(driver_url, driver_path)
                os.chmod(driver_path, 0o755)
                logging.info(f"[VDB_CLIENT] VastDB ADBC driver downloaded to {driver_path}")
            
            # Store connection parameters for ADBC
            self._adbc_connection = {
                "driver_path": driver_path,
                "endpoint": self.settings.vdbendpoint,
                "access_key": self.settings.vdbaccesskey,
                "secret_key": self.settings.vdbsecretkey,
                "bucket": self.bucket,
                "schema": self.schema_name
            }
            logging.info("[VDB_CLIENT] ADBC connection parameters configured")
            logging.info(f"[VDB_CLIENT] ADBC configured: driver={driver_path}, endpoint={self.settings.vdbendpoint}")
            
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Failed to setup ADBC: {e}", exc_info=True)
            self._adbc_connection = None

    def ensure_alerts_table(self) -> bool:
        """Ensure safety_alerts table exists"""
        try:
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                
                schema = bucket.schema(self.schema_name, fail_if_missing=False)
                if schema is None:
                    schema = bucket.create_schema(self.schema_name, fail_if_exists=False)
                    logging.info(f"[VDB_CLIENT] Schema '{self.schema_name}' created")
                else:
                    logging.info(f"[VDB_CLIENT] Schema '{self.schema_name}' already exists")
                
                table = schema.table(self.alerts_table, fail_if_missing=False)
                if table is None:
                    try:
                        table = schema.create_table(self.alerts_table, columns=self.alerts_schema)
                        logging.info(f"[VDB_CLIENT] Table '{self.alerts_table}' created")
                    except Exception as e:
                        if "409" in str(e) or "Conflict" in str(e) or "already exists" in str(e).lower():
                            logging.info(f"[VDB_CLIENT] Table '{self.alerts_table}' already exists, using existing")
                            table = schema.table(self.alerts_table, fail_if_missing=False)
                            if table is None:
                                raise RuntimeError(f"Failed to get table after creation conflict")
                        else:
                            raise
                else:
                    logging.info(f"[VDB_CLIENT] Table '{self.alerts_table}' already exists")
                
                return True
                
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Error ensuring alerts table: {e}")
            return False

    def similarity_search(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform similarity search on video_segments table using ADBC
        
        Only searches videos uploaded within the configured lookback window
        
        Returns list of matching segments with similarity scores above threshold
        """
        try:
            if not self._adbc_connection:
                logging.error(f"[VDB_CLIENT] ADBC connection check failed: _adbc_connection = {self._adbc_connection}")
                logging.error(f"[VDB_CLIENT] Instance id: {id(self)}, has attribute: {hasattr(self, '_adbc_connection')}")
                raise RuntimeError("ADBC not configured - cannot perform vector similarity search")
            
            lookback_minutes = self.settings.alert_lookback_minutes
            logging.info(f"[VDB_CLIENT] Performing similarity search (top_k={top_k}, threshold={threshold}, lookback={lookback_minutes}min)")
            
            # Calculate cutoff timestamp in Python (VastDB doesn't support INTERVAL arithmetic)
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            cutoff_time_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Build SQL query using array_cosine_distance function
            table_path = f'"{self._adbc_connection["bucket"]}/{self._adbc_connection["schema"]}"."{self.video_table}"'
            dimension = len(query_embedding)
            
            sql_query = f"""
                SELECT 
                    source,
                    reasoning_content,
                    segment_number,
                    original_video,
                    upload_timestamp,
                    array_cosine_distance(vector::FLOAT[{dimension}], ARRAY{query_embedding}::FLOAT[{dimension}]) as distance
                FROM {table_path}
                WHERE upload_timestamp >= TIMESTAMP '{cutoff_time_str}'
                ORDER BY distance ASC
                LIMIT {top_k}
            """
            
            logging.info(f"[VDB_CLIENT] Using array_cosine_distance for similarity search (dimension={dimension})")
            logging.info(f"[VDB_CLIENT] Time filter: upload_timestamp >= '{cutoff_time_str}'")
            
            # Execute query using ADBC
            with adbc_driver_manager.dbapi.connect(
                driver=self._adbc_connection["driver_path"],
                db_kwargs={
                    "vast.db.endpoint": self._adbc_connection["endpoint"],
                    "vast.db.access_key": self._adbc_connection["access_key"],
                    "vast.db.secret_key": self._adbc_connection["secret_key"]
                }
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    result_table = cursor.fetch_arrow_table()
            
            # Process results
            matches = []
            for i in range(len(result_table)):
                row = {
                    "source": result_table["source"][i].as_py(),
                    "reasoning_content": result_table["reasoning_content"][i].as_py(),
                    "segment_number": result_table["segment_number"][i].as_py(),
                    "original_video": result_table["original_video"][i].as_py(),
                    "distance": float(result_table["distance"][i].as_py())
                }
                
                # Convert cosine distance to similarity score (1 - distance)
                similarity_score = 1.0 - row["distance"]
                
                if similarity_score >= threshold:
                    matches.append({
                        "source": row["source"],
                        "reasoning_content": row["reasoning_content"],
                        "segment_number": row["segment_number"],
                        "original_video": row["original_video"],
                        "similarity_score": similarity_score
                    })
            
            logging.info(f"[VDB_CLIENT] Found {len(matches)} results above threshold {threshold}")
            return matches
                
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Similarity search failed: {e}", exc_info=True)
            return []

    def get_last_alert_time(self, query_text: str, source: str) -> Optional[datetime]:
        """
        Get the timestamp of the last alert for a given query+source combination
        
        Returns None if no previous alert exists
        """
        try:
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                schema = bucket.schema(self.schema_name)
                
                # Check if alerts table exists first
                table = schema.table(self.alerts_table, fail_if_missing=False)
                if table is None:
                    logging.info(f"[VDB_CLIENT] Alerts table does not exist yet, no cooldown to check")
                    return None
                
                query = f"""
                    SELECT alert_timestamp
                    FROM "{self.alerts_table}"
                    WHERE alert_query = '{query_text}' AND source = '{source}'
                    ORDER BY alert_timestamp DESC
                    LIMIT 1
                """
                
                cursor = table.query(query)
                result = cursor.fetchone()
                
                if result:
                    return result["alert_timestamp"]
                else:
                    return None
                    
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Failed to get last alert time: {e}")
            return None

    def store_alert(self, alert_record: Dict[str, Any]) -> bool:
        """Store safety alert record in VastDB"""
        try:
            query_text = alert_record["alert_query"]
            source = alert_record["source"]
            timestamp = alert_record["timestamp"]
            
            # Generate unique primary key
            pk_string = f"{query_text}_{source}_{timestamp.isoformat()}"
            pk = hashlib.md5(pk_string.encode()).hexdigest()
            
            # Prepare record
            record = {
                "pk": pk,
                "alert_query": query_text,
                "source": source,
                "similarity_score": alert_record["similarity_score"],
                "threshold": alert_record["threshold"],
                "reasoning_content": alert_record["reasoning_content"],
                "original_video": alert_record["original_video"],
                "segment_number": alert_record["segment_number"],
                "sms_sent": alert_record["sms_sent"],
                "alert_timestamp": timestamp,
                "extra_metadata": "{}"
            }
            
            logging.info(f"[VDB_CLIENT] Storing alert record for query: '{query_text}'")
            
            # Ensure table exists before inserting
            if not self.ensure_alerts_table():
                return False
            
            # Create Arrow table and insert
            arrow_table = pa.Table.from_pylist([record], schema=self.alerts_schema)
            
            with self.session.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                schema = bucket.schema(self.schema_name)
                table = schema.table(self.alerts_table)
                table.insert(arrow_table)
            
            logging.info(f"[VDB_CLIENT] Successfully stored alert record in {self.bucket}.{self.schema_name}.{self.alerts_table}")
            return True
            
        except Exception as e:
            logging.error(f"[VDB_CLIENT] Error storing alert record: {e}", exc_info=True)
            return False

    def close(self):
        """Close VastDB connection"""
        if hasattr(self, 'session') and hasattr(self.session, 'close'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


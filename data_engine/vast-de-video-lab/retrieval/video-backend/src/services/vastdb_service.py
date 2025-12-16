"""
VastDB service for vector similarity search with permission filtering
"""
import logging
import vastdb
import vastdb._internal as _internal
import pyarrow as pa
import time
import os
import urllib.request
from datetime import datetime, timedelta
from typing import List, Optional
from src.config import get_settings
from src.models.video import VideoSearchResult
from src.models.user import User

# Import ADBC driver manager
try:
    import adbc_driver_manager
    import adbc_driver_manager.dbapi
    ADBC_AVAILABLE = True
except ImportError:
    ADBC_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================================
# VASTDB MONKEY PATCH TO SUPPORT UNSUPPORTED COLUMN TYPES (vector columns)
# ============================================================================
# This patch filters out unsupported column types (like vector embeddings)
# from the schema before building queries, working around a VastDB SDK limitation.

_original_build_query_data_request = _internal.build_query_data_request

def _patched_build_query_data_request(schema, predicate, field_names):
    """Patched version that filters out unsupported field types from the schema."""
    supported_fields = []
    unsupported_field_names = set()
    
    for field in schema:
        # Check for unsupported types (vector columns)
        if 'fixed_size_list' in str(field.type):
            unsupported_field_names.add(field.name)
        else:
            supported_fields.append(field)
    
    if unsupported_field_names:
        # Use INFO level so it's visible in logs
        logger.info(f"[VastDB Patch] Excluding unsupported columns from query: {', '.join(unsupported_field_names)}")
    
    # Filter the field_names list to exclude unsupported fields
    filtered_field_names = [name for name in field_names if name not in unsupported_field_names]
    
    filtered_schema = pa.schema(supported_fields)
    logger.info(f"[VastDB Patch] Calling original with {len(supported_fields)} fields (was {len(list(schema))})")
    return _original_build_query_data_request(filtered_schema, predicate, filtered_field_names)

# Apply the monkey patch globally
_internal.build_query_data_request = _patched_build_query_data_request
print("[VastDB] Applied monkey patch to support tables with vector columns")  # Use print for import-time logging
# ============================================================================
settings = get_settings()


class VastDBService:
    """Service for VastDB vector operations with permission filtering"""
    
    def __init__(self):
        self.settings = settings
        self.client = None
        self._adbc_connection = None
        self._connect()
        self._setup_adbc()
    
    def _connect(self):
        """Initialize VastDB connection"""
        try:
            self.client = vastdb.connect(
                endpoint=self.settings.vdb_endpoint,
                access=self.settings.vdb_access_key,
                secret=self.settings.vdb_secret_key,
                ssl_verify=False
            )
            logger.info("VastDB connection established")
        except Exception as e:
            logger.error(f"Failed to connect to VastDB: {e}")
            raise
    
    def _setup_adbc(self):
        """Set up ADBC connection for native VastDB vector search"""
        if not ADBC_AVAILABLE:
            logger.error("ADBC driver manager not available")
            return
        
        try:
            logger.info(f"Setting up ADBC connection to VastDB at {self.settings.vdb_endpoint}")
            
            # Download VastDB ADBC driver if not already present
            driver_path = "/tmp/libadbc_driver_vastdb.so"
            if not os.path.exists(driver_path):
                driver_url = "https://artifactory.vastdata.com/files/vastdb-native-client/1955131/libadbc_driver_vastdb.so"
                logger.info(f"Downloading VastDB ADBC driver from {driver_url}")
                urllib.request.urlretrieve(driver_url, driver_path)
                # Make executable
                os.chmod(driver_path, 0o755)
                logger.info(f"VastDB ADBC driver downloaded to {driver_path}")
            
            # Store connection parameters for ADBC
            self._adbc_connection = {
                "driver_path": driver_path,
                "endpoint": self.settings.vdb_endpoint,
                "access_key": self.settings.vdb_access_key,
                "secret_key": self.settings.vdb_secret_key,
                "bucket": self.settings.vdb_bucket,
                "schema": self.settings.vdb_schema
            }
            logger.info("ADBC connection parameters configured")
            
        except Exception as e:
            logger.error(f"Failed to setup ADBC: {e}")
            self._adbc_connection = None
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int,
        user: User,
        tags: List[str] = None,
        include_public: bool = True,
        time_filter: str = "all",
        custom_start_date: Optional[str] = None,
        custom_end_date: Optional[str] = None,
        metadata_filters: dict = None,
        min_similarity: float = 0.4
    ) -> tuple[List[VideoSearchResult], float, int]:
        """
        Perform similarity search with permission filtering, time filtering, and dynamic metadata filtering
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            user: Current authenticated user
            tags: Optional tag filter
            include_public: Whether to include public videos in results
            time_filter: Time range filter ('all', '5m', '15m', '1h', '24h', '7d', 'custom')
            custom_start_date: Custom start date (ISO 8601 string) for 'custom' filter
            custom_end_date: Custom end date (ISO 8601 string) for 'custom' filter
            metadata_filters: Dynamic metadata filters (e.g., {'camera_id': 'CAM-001', 'neighborhood': 'Midtown'})
            min_similarity: Minimum similarity score threshold (0.3-0.8 recommended, default 0.1)
            
        Returns:
            Tuple of (results list, search time in ms, number filtered by permissions)
            
        Raises:
            Exception if search fails
        """
        start_time = time.time()
        permission_filtered_count = 0
        
        try:
            # Build SQL query with vector similarity
            # Fetch more results than needed to account for permission filtering
            fetch_count = min(top_k * 3, 100)  # Fetch 3x to ensure enough after filtering
            
            # Use ADBC for vector similarity search
            if not self._adbc_connection:
                raise RuntimeError("ADBC not configured - cannot perform vector similarity search")
            
            # Build SQL query using array_cosine_distance function (better for normalized embeddings)
            table_path = f'"{self._adbc_connection["bucket"]}/{self._adbc_connection["schema"]}"."{self.settings.vdb_collection}"'
            dimension = len(query_embedding)
            
            sql_query = f"""
                SELECT 
                    filename,
                    source,
                    reasoning_content,
                    video_url,
                    allowed_users,
                    is_public,
                    upload_timestamp,
                    duration,
                    segment_number,
                    total_segments,
                    original_video,
                    tags,
                    cosmos_model,
                    tokens_used,
                    camera_id,
                    capture_type,
                    neighborhood,
                    array_cosine_distance(vector::FLOAT[{dimension}], ARRAY{query_embedding}::FLOAT[{dimension}]) as distance
                FROM {table_path}
            """
            
            # Build WHERE clause conditions
            where_conditions = []
            
            # Add tag filter if provided
            if tags:
                tags_str = ", ".join([f"'{tag}'" for tag in tags])
                where_conditions.append(f"tags && ARRAY[{tags_str}]")
            
            # Add time filter if not 'all'
            if time_filter == "custom":
                # Use custom date range
                logger.info(f"[TIME_FILTER] Custom filter requested - start: {custom_start_date}, end: {custom_end_date}")
                if custom_start_date or custom_end_date:
                    try:
                        if custom_start_date:
                            # Parse datetime string - remove timezone info to treat as LOCAL time
                            # This matches how VastDB stores upload_timestamp (local time)
                            clean_start = custom_start_date.replace('Z', '').replace('+00:00', '')
                            # Remove milliseconds if present
                            if '.' in clean_start:
                                clean_start = clean_start.split('.')[0]
                            start_dt = datetime.fromisoformat(clean_start)
                            # Format for VastDB TIMESTAMP comparison
                            start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
                            where_conditions.append(f"upload_timestamp >= TIMESTAMP '{start_str}'")
                            logger.info(f"[TIME_FILTER] ✓ Custom start (LOCAL): {start_str} (from {custom_start_date})")
                        
                        if custom_end_date:
                            # Parse datetime string - remove timezone info to treat as LOCAL time
                            clean_end = custom_end_date.replace('Z', '').replace('+00:00', '')
                            if '.' in clean_end:
                                clean_end = clean_end.split('.')[0]
                            end_dt = datetime.fromisoformat(clean_end)
                            end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
                            where_conditions.append(f"upload_timestamp <= TIMESTAMP '{end_str}'")
                            logger.info(f"[TIME_FILTER] ✓ Custom end (LOCAL): {end_str} (from {custom_end_date})")
                    except Exception as e:
                        logger.error(f"[TIME_FILTER] ✗ Failed to parse custom dates: {e}", exc_info=True)
                else:
                    logger.warning(f"[TIME_FILTER] Custom filter selected but no dates provided!")
            elif time_filter != "all":
                # Calculate timestamp threshold based on preset time_filter
                time_threshold = self._calculate_time_threshold(time_filter)
                if time_threshold:
                    # Format timestamp for VastDB (ISO 8601 format)
                    time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
                    where_conditions.append(f"upload_timestamp >= TIMESTAMP '{time_threshold_str}'")
                    logger.info(f"[TIME_FILTER] Filtering videos uploaded after: {time_threshold_str}")
            
            # Add dynamic metadata filters
            if metadata_filters:
                logger.info(f"[METADATA_FILTER] Applying {len(metadata_filters)} metadata filters")
                for field_name, field_value in metadata_filters.items():
                    if field_value is not None and field_value != "":
                        # Sanitize field name to prevent SQL injection
                        safe_field_name = field_name.replace("'", "").replace('"', "").replace(";", "")
                        
                        # Build condition based on value type
                        if isinstance(field_value, bool):
                            where_conditions.append(f"{safe_field_name} = {str(field_value).upper()}")
                        elif isinstance(field_value, (int, float)):
                            where_conditions.append(f"{safe_field_name} = {field_value}")
                        else:
                            # String value - escape single quotes
                            safe_value = str(field_value).replace("'", "''")
                            where_conditions.append(f"{safe_field_name} = '{safe_value}'")
                        
                        logger.info(f"[METADATA_FILTER] Added filter: {safe_field_name} = {field_value}")
                logger.info(f"[METADATA_FILTER] Total metadata conditions: {len([c for c in where_conditions if safe_field_name in c])}")
            
            # Add WHERE clause if there are any conditions
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                sql_query += where_clause
                logger.info(f"[SQL] WHERE conditions applied: {where_conditions}")
            else:
                logger.info(f"[SQL] No WHERE conditions (searching all data)")
            
            sql_query += f" ORDER BY distance LIMIT {fetch_count}"
            
            logger.info(f"[SQL] Using array_cosine_distance for semantic similarity search (dimension={dimension})")
            logger.debug(f"[SQL] Executing ADBC similarity search (fetching {fetch_count} for top_k={top_k})")
            # Log query structure (without embedding vector for readability)
            query_log = sql_query.replace(f'ARRAY{query_embedding}', 'ARRAY[...embedding_vector...]')
            logger.debug(f"[SQL] Query: {query_log}")
            
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
                    arrow_table = cursor.fetch_arrow_table()
            
            df = arrow_table.to_pandas()
            
            search_time_ms = (time.time() - start_time) * 1000
            
            if df.empty:
                return [], search_time_ms, 0
            
            logger.info(f"Retrieved {len(df)} results")
            
            # Apply permission filtering and minimum similarity threshold
            filtered_results = []
            similarity_filtered_count = 0
            for _, row in df.iterrows():
                # Calculate similarity score
                similarity_score = 1.0 - row['distance']
                
                # Filter by minimum similarity threshold
                if similarity_score < min_similarity:
                    similarity_filtered_count += 1
                    continue
                    
                # Check if user has access (respecting include_public filter)
                if self._user_has_access(row, user, include_public):
                    # Convert cosine distance to similarity score
                    # Cosine distance: 0.0=identical, 1.0=orthogonal, 2.0=opposite
                    # Similarity: 1.0=identical, 0.0=orthogonal, -1.0=opposite
                    similarity_score = 1.0 - row['distance']
                    
                    result = VideoSearchResult(
                        filename=row['filename'],
                        source=row['source'],
                        reasoning_content=row['reasoning_content'],
                        video_url=row['video_url'],
                        is_public=row['is_public'],
                        upload_timestamp=row['upload_timestamp'],
                        duration=row['duration'],
                        segment_number=row['segment_number'],
                        total_segments=row['total_segments'],
                        original_video=row['original_video'],
                        tags=row['tags'] if row['tags'] else [],
                        similarity_score=similarity_score,
                        cosmos_model=row.get('cosmos_model'),
                        tokens_used=row.get('tokens_used'),
                        camera_id=row.get('camera_id'),
                        capture_type=row.get('capture_type'),
                        neighborhood=row.get('neighborhood')
                    )
                    filtered_results.append(result)
                    
                    # Stop if we have enough results
                    if len(filtered_results) >= top_k:
                        break
                else:
                    permission_filtered_count += 1
            
            logger.info(f"Filtering: {len(filtered_results)} accessible, {permission_filtered_count} permission filtered, {similarity_filtered_count} below similarity threshold ({min_similarity})")
            
            return filtered_results[:top_k], search_time_ms, permission_filtered_count
                
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}")
            raise
    
    def _calculate_time_threshold(self, time_filter: str) -> Optional[datetime]:
        """
        Calculate timestamp threshold based on time filter
        
        Args:
            time_filter: Time filter string ('5m', '15m', '1h', '24h', '7d')
            
        Returns:
            datetime threshold for filtering, or None if invalid filter
        """
        now = datetime.utcnow()
        
        time_map = {
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7)
        }
        
        delta = time_map.get(time_filter)
        if delta:
            threshold = now - delta
            logger.debug(f"[TIME_FILTER] Filter: {time_filter}, Threshold: {threshold}, Now: {now}")
            return threshold
        
        logger.warning(f"[TIME_FILTER] Invalid time filter: {time_filter}")
        return None
    
    def _user_has_access(self, row, user: User, include_public: bool = True) -> bool:
        """
        NEW LOGIC: Check if user has access to a video segment
        
        Security model:
        - is_public=True → everyone can see (regardless of allowed_users)
        - is_public=False → only users in allowed_users can see
        
        Args:
            row: DataFrame row with video data
            user: Current user
            include_public: Whether to include public videos (False = "My Videos" only)
            
        Returns:
            True if user has access, False otherwise
        """
        # If include_public=False ("My Videos" mode), only show videos where user is in allowed_users
        if not include_public:
            allowed_users = row.get('allowed_users', [])
            return user.username in allowed_users if allowed_users else False
        
        # If is_public=True, everyone can see it (no further checks)
        if row['is_public']:
            return True
        
        # If is_public=False, check if user is in allowed_users list
        allowed_users = row.get('allowed_users', [])
        if allowed_users and user.username in allowed_users:
            return True
        
        return False
    
    def get_video_by_source(self, source: str, user: User) -> VideoSearchResult | None:
        """
        Get a specific video by source URL using ADBC
        
        Args:
            source: S3 source URL
            user: Current user
            
        Returns:
            VideoSearchResult if found and accessible, None otherwise
        """
        try:
            # Use ADBC for query (excludes vector column to avoid VastDB client issues)
            if not self._adbc_connection:
                raise RuntimeError("ADBC not configured")
            
            table_path = f'"{self._adbc_connection["bucket"]}/{self._adbc_connection["schema"]}"."{self.settings.vdb_collection}"'
            
            # SELECT all columns EXCEPT vector (to avoid unsupported predicate error)
            sql_query = f"""
                SELECT 
                    filename,
                    source,
                    reasoning_content,
                    video_url,
                    allowed_users,
                    is_public,
                    upload_timestamp,
                    duration,
                    segment_number,
                    total_segments,
                    original_video,
                    tags,
                    cosmos_model,
                    tokens_used,
                    camera_id,
                    capture_type,
                    neighborhood
                FROM {table_path}
                WHERE source = '{source}'
                LIMIT 1
            """
            
            logger.debug(f"Fetching video by source: {source}")
            
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
                    arrow_table = cursor.fetch_arrow_table()
            
            df = arrow_table.to_pandas()
            
            if df.empty:
                logger.info(f"No video found for source: {source}")
                return None
            
            row = df.iloc[0]
            
            # Check permissions
            if not self._user_has_access(row, user):
                logger.warning(f"User {user.username} denied access to {source}")
                return None
            
            return VideoSearchResult(
                filename=row['filename'],
                source=row['source'],
                reasoning_content=row['reasoning_content'],
                video_url=row['video_url'],
                is_public=row['is_public'],
                upload_timestamp=row['upload_timestamp'],
                duration=row['duration'],
                segment_number=row['segment_number'],
                total_segments=row['total_segments'],
                original_video=row['original_video'],
                tags=row['tags'] if row['tags'] else [],
                similarity_score=1.0,  # Not applicable for direct lookup
                cosmos_model=row.get('cosmos_model'),
                tokens_used=row.get('tokens_used'),
                camera_id=row.get('camera_id'),
                capture_type=row.get('capture_type'),
                neighborhood=row.get('neighborhood')
            )
                
        except Exception as e:
            logger.error(f"Error fetching video by source: {str(e)}")
            return None
    
    def get_table_schema(self):
        """
        Get the PyArrow schema of the VastDB table
        
        Returns:
            PyArrow schema with all column definitions
        """
        try:
            with self.client.transaction() as tx:
                bucket = tx.bucket(self.settings.vdb_bucket)
                schema = bucket.schema(self.settings.vdb_schema)
                table = schema.table(self.settings.vdb_collection)
                
                # Get Arrow schema
                arrow_schema = table.columns()
                
                logger.info(f"[SCHEMA] Discovered {len(arrow_schema)} columns from VastDB table")
                return arrow_schema
                
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            raise
    
    def get_distinct_values(self, column_name: str, prefix: str = "", limit: int = 100) -> List[str]:
        """
        Get REAL distinct values for a column from VastDB (for dropdown options)
        
        Uses VastDB Python SDK with PyArrow.
        Excludes vector columns from the query to work around SDK limitations.
        
        Args:
            column_name: Column to get distinct values from
            prefix: Optional prefix filter for autocomplete
            limit: Maximum number of values to return
        
        Returns:
            List of distinct string values from the actual database
        """
        try:
            logger.info(f"[DISTINCT] Getting REAL distinct values for column: {column_name}")
            
            with self.client.transaction() as tx:
                bucket = tx.bucket(self.settings.vdb_bucket)
                db_schema = bucket.schema(self.settings.vdb_schema)
                table = db_schema.table(self.settings.vdb_collection)
                
                # Get full schema
                full_schema = table.columns()
                logger.info(f"[DISTINCT] Full schema has {len(full_schema)} columns")
                
                # Check if column exists
                if column_name not in full_schema.names:
                    logger.warning(f"[DISTINCT] Column {column_name} not found in table")
                    return []
                
                # Build a list of columns EXCLUDING vector types
                # VastDB SDK can't handle fixed_size_list (vector) columns in queries
                columns_to_select = []
                for field in full_schema:
                    field_type_str = str(field.type)
                    # Skip vector columns
                    if 'fixed_size_list' in field_type_str:
                        logger.debug(f"[DISTINCT] Skipping vector column: {field.name}")
                        continue
                    if 'list<' in field_type_str and 'float' in field_type_str:
                        logger.debug(f"[DISTINCT] Skipping float list column: {field.name}")
                        continue
                    columns_to_select.append(field.name)
                
                logger.info(f"[DISTINCT] Will select {len(columns_to_select)} non-vector columns")
                
                # Make sure our target column is queryable
                if column_name not in columns_to_select:
                    logger.warning(f"[DISTINCT] Column {column_name} is a vector type, cannot query")
                    return []
                
                # Select all non-vector columns (SDK validates full schema)
                result = table.select(
                    columns=columns_to_select,
                    internal_row_id=False
                )
                
                # Read data as PyArrow table
                arrow_table = result.read_all()
                logger.info(f"[DISTINCT] Read {arrow_table.num_rows} rows from VastDB")
                
                # Convert to pandas
                df = arrow_table.to_pandas()
                
                if df.empty:
                    logger.info(f"[DISTINCT] No data found in table")
                    return []
                
                # Get distinct values for the specific column
                if column_name not in df.columns:
                    logger.warning(f"[DISTINCT] Column {column_name} not in query result")
                    return []
                
                # Extract unique values, filter nulls/empty
                values = df[column_name].dropna().unique().tolist()
                values = [str(v).strip() for v in values if v is not None and str(v).strip()]
                
                # Apply prefix filter if specified (for autocomplete)
                if prefix:
                    values = [v for v in values if v.lower().startswith(prefix.lower())]
                
                # Sort and limit
                values = sorted(set(values))[:limit]
                
                logger.info(f"[DISTINCT] Found {len(values)} distinct values for {column_name}: {values[:10]}")
                return values
            
        except ValueError as ve:
            error_msg = str(ve)
            if 'unsupported predicate for type=' in error_msg or 'fixed_size_list' in error_msg:
                logger.error(f"[DISTINCT] VastDB SDK limitation with vector columns: {ve}")
            else:
                logger.error(f"[DISTINCT] ValueError for {column_name}: {ve}")
            return []
        except Exception as e:
            logger.error(f"[DISTINCT] Error getting distinct values for {column_name}: {str(e)}")
            import traceback
            logger.error(f"[DISTINCT] Traceback: {traceback.format_exc()}")
            return []


# Global VastDB service instance
_vastdb_service: VastDBService | None = None


def get_vastdb_service() -> VastDBService:
    """Get or create global VastDB service instance"""
    global _vastdb_service
    if _vastdb_service is None:
        _vastdb_service = VastDBService()
    return _vastdb_service


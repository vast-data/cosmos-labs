"""
VastDB service for vector similarity search with permission filtering
"""
import logging
import vastdb
import vastdb._internal as _internal
import pyarrow as pa
import pandas as pd
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
            
            # Check for driver in embedded location (from Docker image), then fallback to /tmp
            driver_paths = [
                "/opt/adbc-driver/libadbc_driver_vastdb.so",  # Embedded in Docker image
                "/tmp/libadbc_driver_vastdb.so"  # Fallback location
            ]
            
            driver_path = None
            for path in driver_paths:
                if os.path.exists(path):
                    driver_path = path
                    logger.info(f"Found VastDB ADBC driver at {driver_path}")
                    break
            
            # If not found, try to download from artifactory (fallback)
            if not driver_path:
                driver_path = "/tmp/libadbc_driver_vastdb.so"
                driver_url = "https://artifactory.vastdata.com/files/vastdb-native-client/1955131/libadbc_driver_vastdb.so"
                logger.warning(f"Driver not found in image, downloading from {driver_url}")
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
        public_only: bool = False,
        time_filter: str = "all",
        custom_start_date: Optional[str] = None,
        custom_end_date: Optional[str] = None,
        metadata_filters: dict = None,
        min_similarity: float = 0.4,
        user_query_text: Optional[str] = None
    ) -> tuple[List[VideoSearchResult], float, int, str]:
        """
        Perform similarity search with permission filtering, time filtering, and dynamic metadata filtering
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            user: Current authenticated user
            tags: Optional tag filter
            include_public: Whether to include public videos in results
            public_only: If True, only return rows where is_public=True (exclude private)
            time_filter: Time range filter ('all', '5m', '15m', '1h', '24h', '7d', 'custom')
            custom_start_date: Custom start date (ISO 8601 string) for 'custom' filter
            custom_end_date: Custom end date (ISO 8601 string) for 'custom' filter
            metadata_filters: Dynamic metadata filters (e.g., {'camera_id': 'CAM-001', 'neighborhood': 'Midtown'})
            min_similarity: Minimum similarity score threshold (0.3-0.8 recommended, default 0.1)
            user_query_text: Original user query text (for SQL query formatting)
            
        Returns:
            Tuple of (results list, search time in ms, number filtered by permissions, formatted SQL query)
            
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
                    array_cosine_distance(vectors::FLOAT[{dimension}], ARRAY{query_embedding}::FLOAT[{dimension}]) as distance
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
            
            # Create user-friendly formatted SQL query for display
            # Replace embedding array with user query text if provided
            formatted_sql = sql_query
            if user_query_text:
                # Escape single quotes in user query for SQL display
                safe_query_text = user_query_text.replace("'", "''")
                embedding_replacement = f"ARRAY[...embedding for query: \"{safe_query_text}\"...]"
            else:
                embedding_replacement = "ARRAY[...embedding_vector...]"
            
            # Replace the actual embedding array with user-friendly text
            formatted_sql = formatted_sql.replace(f'ARRAY{query_embedding}', embedding_replacement)
            
            # Format SQL for readability (basic indentation)
            formatted_sql = self._format_sql_for_display(formatted_sql)
            
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
                return [], search_time_ms, 0, formatted_sql
            
            logger.info(f"Retrieved {len(df)} results")
            
            # Apply permission filtering and minimum similarity threshold
            filtered_results = []
            similarity_filtered_count = 0
            row_index = 0
            for idx, row in df.iterrows():
                row_index += 1
                try:
                    logger.debug(f"[ROW {row_index}] Processing row {idx}")
                    
                    # Calculate similarity score
                    try:
                        distance_value = row['distance']
                        logger.debug(f"[ROW {row_index}] distance type: {type(distance_value)}, value: {distance_value}")
                        similarity_score = 1.0 - distance_value
                    except Exception as e:
                        logger.error(f"[ROW {row_index}] Error accessing distance: {e}, type: {type(row.get('distance'))}")
                        raise
                    
                    # Filter by minimum similarity threshold
                    if similarity_score < min_similarity:
                        similarity_filtered_count += 1
                        logger.debug(f"[ROW {row_index}] Filtered by similarity threshold: {similarity_score} < {min_similarity}")
                        continue
                    
                    # Log field types before access check
                    try:
                        is_public_raw = row.get('is_public')
                        allowed_users_raw = row.get('allowed_users', [])
                        tags_raw = row.get('tags', [])
                        logger.debug(f"[ROW {row_index}] Field types - is_public: {type(is_public_raw)}, allowed_users: {type(allowed_users_raw)}, tags: {type(tags_raw)}")
                        logger.debug(f"[ROW {row_index}] Field values - is_public: {is_public_raw}, allowed_users: {allowed_users_raw}, tags: {tags_raw}")
                    except Exception as e:
                        logger.error(f"[ROW {row_index}] Error inspecting field types: {e}")
                        raise
                    
                    # Check if user has access (respecting include_public and public_only)
                    try:
                        has_access = self._user_has_access(row, user, include_public, public_only)
                        logger.debug(f"[ROW {row_index}] User access check result: {has_access}")
                    except Exception as e:
                        logger.error(f"[ROW {row_index}] Error in _user_has_access: {e}", exc_info=True)
                        raise
                    
                    if has_access:
                        # Convert cosine distance to similarity score
                        # Cosine distance: 0.0=identical, 1.0=orthogonal, 2.0=opposite
                        # Similarity: 1.0=identical, 0.0=orthogonal, -1.0=opposite
                        similarity_score = 1.0 - row['distance']
                        
                        # Safely convert tags from NumPy array to list
                        try:
                            tags_list = self._safe_array_to_list(row['tags'])
                            logger.debug(f"[ROW {row_index}] Tags converted: {tags_list}")
                        except Exception as e:
                            logger.error(f"[ROW {row_index}] Error converting tags: {e}", exc_info=True)
                            tags_list = []
                        
                        # Safely extract is_public as a boolean scalar
                        try:
                            is_public_value = self._safe_scalar_value(row.get('is_public', False), default=False)
                            is_public_bool = bool(is_public_value) if is_public_value is not None and pd.notna(is_public_value) else False
                            logger.debug(f"[ROW {row_index}] is_public extracted: {is_public_bool} (from {is_public_value})")
                        except Exception as e:
                            logger.error(f"[ROW {row_index}] Error extracting is_public: {e}", exc_info=True)
                            is_public_bool = False
                        
                        # Extract other fields safely
                        try:
                            result = VideoSearchResult(
                                filename=str(row['filename']) if pd.notna(row.get('filename')) else '',
                                source=str(row['source']) if pd.notna(row.get('source')) else '',
                                reasoning_content=str(row['reasoning_content']) if pd.notna(row.get('reasoning_content')) else '',
                                video_url=str(row['video_url']) if pd.notna(row.get('video_url')) else '',
                                is_public=is_public_bool,
                                upload_timestamp=row['upload_timestamp'],
                                duration=row.get('duration'),
                                segment_number=int(row['segment_number']) if pd.notna(row.get('segment_number')) else None,
                                total_segments=int(row['total_segments']) if pd.notna(row.get('total_segments')) else None,
                                original_video=str(row['original_video']) if pd.notna(row.get('original_video')) else '',
                                tags=tags_list,
                                similarity_score=similarity_score,
                                cosmos_model=str(row.get('cosmos_model')) if pd.notna(row.get('cosmos_model')) else None,
                                tokens_used=int(row.get('tokens_used')) if pd.notna(row.get('tokens_used')) else None,
                                camera_id=str(row.get('camera_id')) if pd.notna(row.get('camera_id')) else None,
                                capture_type=str(row.get('capture_type')) if pd.notna(row.get('capture_type')) else None,
                                neighborhood=str(row.get('neighborhood')) if pd.notna(row.get('neighborhood')) else None
                            )
                            filtered_results.append(result)
                            logger.debug(f"[ROW {row_index}] Successfully created VideoSearchResult")
                        except Exception as e:
                            logger.error(f"[ROW {row_index}] Error creating VideoSearchResult: {e}", exc_info=True)
                            raise
                        
                        # Stop if we have enough results
                        if len(filtered_results) >= top_k:
                            logger.debug(f"[ROW {row_index}] Reached top_k limit, stopping")
                            break
                    else:
                        permission_filtered_count += 1
                        logger.debug(f"[ROW {row_index}] Permission denied")
                except Exception as e:
                    logger.error(f"[ROW {row_index}] Error processing row {idx}: {e}", exc_info=True)
                    # Continue processing other rows instead of failing completely
                    permission_filtered_count += 1
                    continue
            
            logger.info(f"Filtering: {len(filtered_results)} accessible, {permission_filtered_count} permission filtered, {similarity_filtered_count} below similarity threshold ({min_similarity})")
            
            return filtered_results[:top_k], search_time_ms, permission_filtered_count, formatted_sql
                
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
    
    def _format_sql_for_display(self, sql: str) -> str:
        """
        Format SQL query for user-friendly display with basic indentation
        
        Args:
            sql: Raw SQL query string
            
        Returns:
            Formatted SQL string with improved readability
        """
        # Basic SQL formatting - add indentation for readability
        lines = sql.strip().split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Decrease indent before certain keywords
            if any(stripped.upper().startswith(kw) for kw in ['FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'HAVING']):
                indent_level = max(0, indent_level - 1)
            
            # Add indented line
            formatted_lines.append('  ' * indent_level + stripped)
            
            # Increase indent after certain keywords
            if any(stripped.upper().startswith(kw) for kw in ['SELECT', 'FROM', 'WHERE', 'ORDER BY']):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def _safe_array_to_list(self, value) -> List:
        """
        Safely convert a NumPy array, pandas Series, or other iterable to a Python list.
        Handles None, NaN, and empty values properly to avoid "ambiguous truth value" errors.
        
        Args:
            value: Value that might be a NumPy array, pandas Series, list, or None/NaN
            
        Returns:
            List representation of the value, or empty list if None/NaN/empty
        """
        try:
            logger.debug(f"[SAFE_ARRAY_TO_LIST] Input value type: {type(value)}, value: {value}")
            
            if value is None:
                logger.debug(f"[SAFE_ARRAY_TO_LIST] Value is None, returning []")
                return []
            
            # Check for NaN
            try:
                if pd.isna(value):
                    logger.debug(f"[SAFE_ARRAY_TO_LIST] Value is NaN, returning []")
                    return []
            except (TypeError, ValueError) as e:
                logger.debug(f"[SAFE_ARRAY_TO_LIST] Could not check for NaN (might be array): {e}")
            
            if hasattr(value, '__iter__') and not isinstance(value, str):
                try:
                    result = list(value)
                    logger.debug(f"[SAFE_ARRAY_TO_LIST] Converted to list, length: {len(result)}")
                    # Filter out any NaN values that might be in the list
                    filtered = [item for item in result if item is not None and not pd.isna(item)]
                    logger.debug(f"[SAFE_ARRAY_TO_LIST] Filtered result length: {len(filtered)}")
                    return filtered
                except (TypeError, ValueError) as e:
                    logger.warning(f"[SAFE_ARRAY_TO_LIST] Error converting to list: {e}")
                    return []
            
            logger.debug(f"[SAFE_ARRAY_TO_LIST] Not an iterable (or is string), returning []")
            return []
        except Exception as e:
            logger.error(f"[SAFE_ARRAY_TO_LIST] Unexpected error: {e}", exc_info=True)
            return []
    
    def _safe_scalar_value(self, value, default=None):
        """
        Safely extract a scalar value from a pandas Series, NumPy array, or other type.
        Handles cases where the value might be wrapped in a Series or array.
        
        Args:
            value: Value that might be a scalar, Series, array, or None/NaN
            default: Default value to return if extraction fails
            
        Returns:
            Scalar value, or default if extraction fails
        """
        try:
            logger.debug(f"[SAFE_SCALAR] Input value type: {type(value)}, value: {value}")
            
            if value is None:
                logger.debug(f"[SAFE_SCALAR] Value is None, returning default: {default}")
                return default
            
            # Check for NaN
            try:
                if pd.isna(value):
                    logger.debug(f"[SAFE_SCALAR] Value is NaN, returning default: {default}")
                    return default
            except (TypeError, ValueError) as e:
                logger.debug(f"[SAFE_SCALAR] Could not check for NaN (might be array): {e}")
            
            # If it's a pandas Series, get the first value
            if hasattr(value, 'iloc'):
                try:
                    length = len(value)
                    logger.debug(f"[SAFE_SCALAR] Detected pandas Series with length {length}")
                    result = value.iloc[0] if length > 0 else default
                    logger.debug(f"[SAFE_SCALAR] Extracted from Series: {result}")
                    return result
                except (TypeError, ValueError, IndexError) as e:
                    logger.warning(f"[SAFE_SCALAR] Error extracting from Series: {e}")
                    return default
            
            # If it's an array/iterable (but not a string), get the first element
            if hasattr(value, '__iter__') and not isinstance(value, str):
                try:
                    value_list = list(value)
                    logger.debug(f"[SAFE_SCALAR] Detected iterable (not string) with length {len(value_list)}")
                    if len(value_list) > 0:
                        result = value_list[0]
                        logger.debug(f"[SAFE_SCALAR] Extracted first element: {result}")
                        return result
                    else:
                        logger.debug(f"[SAFE_SCALAR] Iterable is empty, returning default: {default}")
                        return default
                except (TypeError, ValueError, IndexError) as e:
                    logger.warning(f"[SAFE_SCALAR] Error converting iterable to list: {e}")
                    return default
            
            # Otherwise, return as-is (should be a scalar)
            logger.debug(f"[SAFE_SCALAR] Treating as scalar, returning: {value}")
            return value
        except Exception as e:
            logger.error(f"[SAFE_SCALAR] Unexpected error: {e}", exc_info=True)
            return default
    
    def _user_has_access(self, row, user: User, include_public: bool = True, public_only: bool = False) -> bool:
        """
        NEW LOGIC: Check if user has access to a video segment
        
        Security model:
        - is_public=True → everyone can see (regardless of allowed_users)
        - is_public=False → only users in allowed_users can see
        
        Args:
            row: DataFrame row with video data
            user: Current user
            include_public: Whether to include public videos (False = "My Videos" only)
            public_only: If True, only allow access when is_public=True ("Public Only" scope)
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            logger.debug(f"[ACCESS_CHECK] Starting access check for user {user.username}, include_public={include_public}, public_only={public_only}")
            
            # If public_only=True ("Public Only" scope), only allow rows where is_public is True
            if public_only:
                is_public_raw = row.get('is_public', False)
                is_public_value = self._safe_scalar_value(is_public_raw, default=False)
                if is_public_value is None or pd.isna(is_public_value):
                    return False
                if not bool(is_public_value):
                    return False
                return True
            
            # If include_public=False ("My Videos" mode), only show videos where user is in allowed_users
            if not include_public:
                try:
                    allowed_users_raw = row.get('allowed_users', [])
                    logger.debug(f"[ACCESS_CHECK] include_public=False, allowed_users_raw type: {type(allowed_users_raw)}, value: {allowed_users_raw}")
                    allowed_users_list = self._safe_array_to_list(allowed_users_raw)
                    logger.debug(f"[ACCESS_CHECK] allowed_users_list: {allowed_users_list}")
                    result = user.username in allowed_users_list if len(allowed_users_list) > 0 else False
                    logger.debug(f"[ACCESS_CHECK] Result (include_public=False): {result}")
                    return result
                except Exception as e:
                    logger.error(f"[ACCESS_CHECK] Error in include_public=False branch: {e}", exc_info=True)
                    return False
            
            # If is_public=True, everyone can see it (no further checks)
            # Safely extract scalar value and convert to bool (handles NumPy bool_, pandas bool, arrays, etc.)
            try:
                is_public_raw = row.get('is_public', False)
                logger.debug(f"[ACCESS_CHECK] is_public_raw type: {type(is_public_raw)}, value: {is_public_raw}")
                
                # Check if it's an array before trying to extract scalar
                if hasattr(is_public_raw, '__iter__') and not isinstance(is_public_raw, str):
                    logger.warning(f"[ACCESS_CHECK] is_public appears to be an array/iterable: {type(is_public_raw)}, value: {is_public_raw}")
                
                is_public_value = self._safe_scalar_value(is_public_raw, default=False)
                logger.debug(f"[ACCESS_CHECK] is_public_value after extraction: {is_public_value}, type: {type(is_public_value)}")
                
                if is_public_value is not None and pd.notna(is_public_value):
                    # Try to convert to bool - this is where the error might occur
                    try:
                        is_public_bool = bool(is_public_value)
                        logger.debug(f"[ACCESS_CHECK] is_public_bool: {is_public_bool}")
                        if is_public_bool:
                            logger.debug(f"[ACCESS_CHECK] Video is public, granting access")
                            return True
                    except ValueError as ve:
                        logger.error(f"[ACCESS_CHECK] ValueError converting is_public to bool: {ve}, value: {is_public_value}, type: {type(is_public_value)}")
                        # If conversion fails, treat as False
                        is_public_bool = False
                else:
                    logger.debug(f"[ACCESS_CHECK] is_public is None or NaN, treating as False")
                    is_public_bool = False
            except Exception as e:
                logger.error(f"[ACCESS_CHECK] Error checking is_public: {e}", exc_info=True)
                is_public_bool = False
            
            # If is_public=False, check if user is in allowed_users list
            try:
                allowed_users_raw = row.get('allowed_users', [])
                logger.debug(f"[ACCESS_CHECK] Checking allowed_users, raw type: {type(allowed_users_raw)}, value: {allowed_users_raw}")
                allowed_users_list = self._safe_array_to_list(allowed_users_raw)
                logger.debug(f"[ACCESS_CHECK] allowed_users_list: {allowed_users_list}")
                if len(allowed_users_list) > 0:
                    username_in_list = user.username in allowed_users_list
                    logger.debug(f"[ACCESS_CHECK] User {user.username} in allowed_users: {username_in_list}")
                    if username_in_list:
                        logger.debug(f"[ACCESS_CHECK] User found in allowed_users, granting access")
                        return True
            except Exception as e:
                logger.error(f"[ACCESS_CHECK] Error checking allowed_users: {e}", exc_info=True)
            
            logger.debug(f"[ACCESS_CHECK] Access denied")
            return False
        except Exception as e:
            logger.error(f"[ACCESS_CHECK] Unexpected error in _user_has_access: {e}", exc_info=True)
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
            
            # Safely convert tags from NumPy array to list
            tags_list = self._safe_array_to_list(row['tags'])
            
            # Safely extract is_public as a boolean scalar
            is_public_value = self._safe_scalar_value(row.get('is_public', False), default=False)
            is_public_bool = bool(is_public_value) if is_public_value is not None and pd.notna(is_public_value) else False
            
            return VideoSearchResult(
                filename=row['filename'],
                source=row['source'],
                reasoning_content=row['reasoning_content'],
                video_url=row['video_url'],
                is_public=is_public_bool,
                upload_timestamp=row['upload_timestamp'],
                duration=row['duration'],
                segment_number=row['segment_number'],
                total_segments=row['total_segments'],
                original_video=row['original_video'],
                tags=tags_list,
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


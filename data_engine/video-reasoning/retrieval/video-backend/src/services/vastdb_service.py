"""
VastDB service for vector similarity search with permission filtering
"""
import logging
import vastdb
import time
import os
import urllib.request
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
    logger.warning("ADBC driver manager not available - install with: pip install adbc-driver-manager")

logger = logging.getLogger(__name__)
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
                driver_url = "artifactory_adbc_so_file_placeholder"
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
        include_public: bool = True
    ) -> tuple[List[VideoSearchResult], float, int]:
        """
        Perform similarity search with permission filtering
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            user: Current authenticated user
            tags: Optional tag filter
            include_public: Whether to include public videos in results
            
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
                    array_cosine_distance(vector::FLOAT[{dimension}], ARRAY{query_embedding}::FLOAT[{dimension}]) as distance
                FROM {table_path}
            """
            
            # Add tag filter if provided
            if tags:
                tags_str = ", ".join([f"'{tag}'" for tag in tags])
                sql_query += f" WHERE tags && ARRAY[{tags_str}]"
            
            sql_query += f" ORDER BY distance LIMIT {fetch_count}"
            
            logger.info(f"Using array_cosine_distance for semantic similarity search (dimension={dimension})")
            logger.debug(f"Executing ADBC similarity search (fetching {fetch_count} for top_k={top_k})")
            logger.debug(f"SQL Query structure: {sql_query.replace(f'ARRAY{query_embedding}', 'ARRAY[vector_data]')}")
            
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
                logger.info("No results found")
                return [], search_time_ms, 0
            
            # DEBUG: Log distance distribution to verify similarity search
            if not df.empty and 'distance' in df.columns:
                distances = df['distance'].tolist()
                logger.info(f"Top 5 similarity distances: {distances[:5]}")
                logger.info(f"Min distance: {min(distances):.4f}, Max distance: {max(distances):.4f}, Avg distance: {sum(distances)/len(distances):.4f}")
                logger.info(f"Distance range (max-min): {max(distances) - min(distances):.4f}")
                
                # Log some reasoning content to see if it matches the query
                if len(df) > 0:
                    top_result_summary = df.iloc[0]['reasoning_content'][:150]
                    logger.info(f"Top result summary: {top_result_summary}...")
            
            logger.info(f"Retrieved {len(df)} results before permission filtering")
            
            # Apply permission filtering
            filtered_results = []
            for _, row in df.iterrows():
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
                        tokens_used=row.get('tokens_used')
                    )
                    filtered_results.append(result)
                    
                    # Stop if we have enough results
                    if len(filtered_results) >= top_k:
                        break
                else:
                    permission_filtered_count += 1
            
            logger.info(f"Permission filtering: {len(filtered_results)} accessible, {permission_filtered_count} filtered")
            
            return filtered_results[:top_k], search_time_ms, permission_filtered_count
                
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}")
            raise
    
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
                    tokens_used
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
                tokens_used=row.get('tokens_used')
            )
                
        except Exception as e:
            logger.error(f"Error fetching video by source: {str(e)}")
            return None


# Global VastDB service instance
_vastdb_service: VastDBService | None = None


def get_vastdb_service() -> VastDBService:
    """Get or create global VastDB service instance"""
    global _vastdb_service
    if _vastdb_service is None:
        _vastdb_service = VastDBService()
    return _vastdb_service


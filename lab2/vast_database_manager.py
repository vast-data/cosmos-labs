#!/usr/bin/env python3
"""
VAST Database Manager for Lab 2 Metadata Infrastructure
Safely manages database creation, schema setup, and metadata storage
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

try:
    import vastdb
    VASTDB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  vastdb not found. ImportError: {e}")
    print("💡 This is required for Lab 2 database functionality")
    print("🔧 For now, using mock database operations")
    VASTDB_AVAILABLE = False

try:
    import ibis
    IBIS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ibis not found. ImportError: {e}")
    print("💡 This enables efficient predicate pushdown for queries")
    print("🔧 Falling back to Python-side filtering")
    IBIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VASTDatabaseManager:
    """Manages VAST Database operations for metadata catalog"""
    
    def __init__(self, config, show_api_calls: bool = False):
        """Initialize the database manager"""
        self.config = config
        self.show_api_calls = show_api_calls
        # Lab 2 database bucket – use only lab2.vastdb.bucket (not the general datastore/S3 bucket)
        self.bucket_name = config.get('lab2.vastdb.bucket', 'your-tenant-metadata')
        self.schema_name = config.get('lab2.vastdb.schema', 'satellite_observations')
        
        # Database connection parameters for vastdb (using S3 credentials)
        self.db_config = {
            'access': config.get_secret('s3_access_key'),
            'secret': config.get_secret('s3_secret_key'),
            'endpoint': config.get('lab2.vastdb.endpoint', 'http://localhost:8080'),
            'ssl_verify': config.get('lab2.vastdb.ssl_verify', True),
            'timeout': config.get('lab2.vastdb.timeout', 30)
        }
        
        # Debug: log what we're trying to connect with
        logger.info(f"🔧 VAST DB config - access: {'***' if self.db_config['access'] else 'None'}, "
                   f"secret: {'***' if self.db_config['secret'] else 'None'}, "
                   f"endpoint: {self.db_config['endpoint']}")
        
        self.connection = None
        self.database = None
    
    def _log_api_call(self, operation: str, details: str = ""):
        """Log API calls if show_api_calls is enabled"""
        if self.show_api_calls:
            # Obfuscate credentials in the details
            obfuscated_details = details
            if 'access' in obfuscated_details:
                obfuscated_details = obfuscated_details.replace(self.db_config['access'], '***')
            if 'secret' in obfuscated_details:
                obfuscated_details = obfuscated_details.replace(self.db_config['secret'], '***')
            
            print(f"🔌 API CALL: {operation}")
            if details:
                print(f"   Details: {obfuscated_details}")
            print()
    
    def _build_ibis_predicate(self, search_criteria: Dict[str, Any]):
        """Build ibis predicate from search criteria for efficient database filtering"""
        if not IBIS_AVAILABLE:
            return None
            
        try:
            from ibis import _
            predicates = []
            
            for key, criteria in search_criteria.items():
                try:
                    # Get the column reference
                    column = getattr(_, key)
                    
                    if criteria['type'] == 'exact':
                        # Exact match: key = value
                        predicates.append(column == criteria['value'])
                        
                    elif criteria['type'] == 'wildcard':
                        pattern = criteria['pattern']
                        if pattern == '*':
                            # Match all - no predicate needed
                            continue
                        elif pattern.startswith('*') and pattern.endswith('*'):
                            # Contains: *value* -> contains() method
                            search_value = pattern[1:-1]
                            predicates.append(column.contains(search_value))
                        elif pattern.startswith('*'):
                            # Ends with: *value -> endswith() method
                            search_value = pattern[1:]
                            predicates.append(column.endswith(search_value))
                        elif pattern.endswith('*'):
                            # Starts with: value* -> startswith() method
                            search_value = pattern[:-1]
                            predicates.append(column.startswith(search_value))
                        else:
                            # No wildcards - treat as exact match
                            predicates.append(column == pattern)
                            
                    elif criteria['type'] == 'comparison':
                        operator = criteria['operator']
                        value = criteria['value']
                        
                        # Try to convert to appropriate type for comparison
                        try:
                            # Try date comparison first
                            from datetime import datetime
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                            # It's a valid date, keep as string for comparison
                            compare_value = value
                        except (ValueError, TypeError):
                            try:
                                # Try numeric comparison
                                compare_value = float(value)
                            except (ValueError, TypeError):
                                # Fallback to string comparison
                                compare_value = value
                        
                        if operator == '>':
                            predicates.append(column > compare_value)
                        elif operator == '<':
                            predicates.append(column < compare_value)
                        elif operator == '>=':
                            predicates.append(column >= compare_value)
                        elif operator == '<=':
                            predicates.append(column <= compare_value)
                            
                except AttributeError as e:
                    logger.warning(f"⚠️  Column '{key}' not found in ibis schema: {e}")
                    # Skip this predicate if column doesn't exist
                    continue
            
            # Combine all predicates with AND using proper ibis syntax
            if predicates:
                if len(predicates) == 1:
                    return predicates[0]
                else:
                    # Combine with AND operator using & (as shown in documentation)
                    result = predicates[0]
                    for pred in predicates[1:]:
                        result = result & pred
                    return result
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to build ibis predicate: {e}")
            return None
        
    def connect(self) -> bool:
        """Establish connection to VAST Database"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - using mock connection")
            self.connection = "MOCK_CONNECTION"
            return True
            
        try:
            # Log API call
            self._log_api_call(
                "vastdb.connect()",
                f"endpoint={self.db_config['endpoint']}, ssl_verify={self.db_config['ssl_verify']}, timeout={self.db_config['timeout']}"
            )
            
            # Connect to VAST Database using the correct parameters
            self.connection = vastdb.connect(**self.db_config)
            logger.info(f"✅ Connected to VAST Database at {self.db_config['endpoint']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to VAST Database: {e}")
            return False
    
    def database_exists(self) -> bool:
        """Check if the target bucket exists in VAST DB"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock database exists check")
            return False  # Mock: database doesn't exist
            
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            # Check if bucket exists using VAST DB API
            with self.connection.transaction() as tx:
                try:
                    bucket = tx.bucket(self.bucket_name)
                    # Try to list schemas to verify bucket exists
                    schemas = bucket.schemas()
                    logger.info(f"✅ Bucket '{self.bucket_name}' exists with {len(schemas)} schemas")
                    return True
                except Exception:
                    logger.info(f"ℹ️  Bucket '{self.bucket_name}' does not exist")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Error checking bucket existence: {e}")
            return False
    
    def create_schema_and_table(self) -> bool:
        """Create the target schema and table if they don't exist"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            # First, try to create the bucket using S3 operations if it doesn't exist
            if not self._ensure_bucket_exists():
                logger.error(f"❌ Failed to ensure bucket '{self.bucket_name}' exists")
                return False
            
            # Use VAST DB transaction to create schema and table
            with self.connection.transaction() as tx:
                # Get or create bucket
                bucket = tx.bucket(self.bucket_name)
                
                # Create schema
                schema = bucket.create_schema(self.schema_name)
                logger.info(f"✅ Created schema '{self.schema_name}' in bucket '{self.bucket_name}'")
                
                # Create table with complete metadata columns
                import pyarrow as pa
                columns = pa.schema([
                    ('file_path', pa.utf8()),
                    ('file_name', pa.utf8()),
                    ('file_size_bytes', pa.int64()),
                    ('file_format', pa.utf8()),
                    ('dataset_name', pa.utf8()),
                    ('mission_id', pa.utf8()),
                    ('satellite_name', pa.utf8()),
                    ('instrument_type', pa.utf8()),
                    ('observation_timestamp', pa.timestamp('us')),
                    ('target_object', pa.utf8()),
                    ('processing_status', pa.utf8()),
                    ('ingestion_timestamp', pa.timestamp('us')),
                    ('last_modified', pa.timestamp('us')),
                    ('checksum', pa.utf8()),
                    ('metadata_version', pa.utf8()),
                    ('created_at', pa.timestamp('us')),
                    ('updated_at', pa.timestamp('us'))
                ])
                
                # Log API call
                self._log_api_call(
                    "schema.create_table()",
                    f"schema={self.schema_name}, table=swift_metadata, columns={len(columns)}"
                )
                
                table = schema.create_table("swift_metadata", columns)
                logger.info(f"✅ Created table 'swift_metadata' in schema '{self.schema_name}'")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create schema and table: {e}")
            return False
    
    def _ensure_bucket_exists(self) -> bool:
        """Ensure the target bucket exists, create it if needed"""
        try:
            # Import boto3 for S3 operations
            import boto3
            
            # Create S3 client using the same credentials
            s3_client = boto3.client(
                's3',
                endpoint_url=self.db_config['endpoint'],
                aws_access_key_id=self.db_config['access'],
                aws_secret_access_key=self.db_config['secret'],
                region_name='us-east-1',
                use_ssl=False,
                config=boto3.session.Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'path'}
                )
            )
            
            # Check if bucket exists
            try:
                s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ Bucket '{self.bucket_name}' already exists")
                return True
            except Exception:
                # Bucket doesn't exist, create it
                logger.info(f"🔧 Creating bucket '{self.bucket_name}'...")
                s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ Created bucket '{self.bucket_name}' successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure bucket exists: {e}")
            return False
    
    def schema_exists(self) -> bool:
        """Check if the target schema exists"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = %s
            """, (self.schema_name,))
            
            exists = cursor.fetchone() is not None
            cursor.close()
            
            if exists:
                logger.info(f"✅ Schema '{self.schema_name}' exists")
            else:
                logger.info(f"ℹ️  Schema '{self.schema_name}' does not exist")
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ Error checking schema existence: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the target schema if it doesn't exist"""
        try:
            if self.schema_exists():
                logger.info(f"ℹ️  Schema '{self.schema_name}' already exists")
                return True
            
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE SCHEMA {self.schema_name}")
            cursor.close()
            
            logger.info(f"✅ Created schema '{self.schema_name}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create schema: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a specific table exists"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (self.schema_name, table_name))
            
            exists = cursor.fetchone() is not None
            cursor.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ Error checking table existence: {e}")
            return False
    
    def create_metadata_table(self) -> bool:
        """Create the metadata table if it doesn't exist"""
        try:
            table_name = 'swift_metadata'
            
            if self.table_exists(table_name):
                logger.info(f"ℹ️  Table '{table_name}' already exists")
                return True
            
            cursor = self.connection.cursor()
            
            # Create metadata table with comprehensive schema
            create_table_sql = f"""
            CREATE TABLE {self.schema_name}.{table_name} (
                id SERIAL PRIMARY KEY,
                file_path VARCHAR(500) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_size_bytes BIGINT,
                file_format VARCHAR(50),
                dataset_name VARCHAR(100),
                
                -- Swift-specific metadata
                mission_id VARCHAR(100),
                satellite_name VARCHAR(100),
                instrument_type VARCHAR(100),
                observation_timestamp TIMESTAMP,
                target_object VARCHAR(100),
                processing_status VARCHAR(50),
                
                -- File metadata
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP,
                checksum VARCHAR(64),
                metadata_version VARCHAR(20),
                
                -- Search optimization
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_sql)
            
            # Create indexes for better search performance
            cursor.execute(f"""
                CREATE INDEX idx_{table_name}_mission_id ON {self.schema_name}.{table_name} (mission_id)
            """)
            cursor.execute(f"""
                CREATE INDEX idx_{table_name}_target_object ON {self.schema_name}.{table_name} (target_object)
            """)
            cursor.execute(f"""
                CREATE INDEX idx_{table_name}_observation_timestamp ON {self.schema_name}.{table_name} (observation_timestamp)
            """)
            cursor.execute(f"""
                CREATE INDEX idx_{table_name}_file_path ON {self.schema_name}.{table_name} (file_path)
            """)
            
            cursor.close()
            
            logger.info(f"✅ Created metadata table '{table_name}' with indexes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create metadata table: {e}")
            return False
    
    def metadata_exists(self, file_path: str) -> bool:
        """Check if metadata for a file already exists in the database using VAST DB"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock metadata existence check")
            return False
            
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            # Use VAST DB transaction to check if metadata exists
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                
                # Check if schema and table exist
                try:
                    schema = bucket.schema(self.schema_name)
                    table = schema.table("swift_metadata")
                    
                    # Search for the file_path
                    reader = table.select()
                    
                    for batch in reader:
                        for i in range(len(batch)):
                            if batch['file_path'][i].as_py() == file_path:
                                return True
                    
                    return False
                    
                except Exception:
                    # Schema or table doesn't exist yet
                    logger.info(f"ℹ️  Schema '{self.schema_name}' or table 'swift_metadata' doesn't exist yet")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Error checking metadata existence: {e}")
            return False
    
    def insert_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Insert metadata into the database using VAST DB"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock metadata insertion")
            return True
            
        try:
            if not self.connection:
                logger.info("🔧 No database connection, attempting to connect...")
                if not self.connect():
                    logger.error("❌ Failed to connect to database")
                    return False
            
            # Insert metadata (no need to log every file)
            
            # Use VAST DB transaction to insert metadata
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                schema = bucket.schema(self.schema_name)
                table = schema.table("swift_metadata")
                
                # Convert metadata to PyArrow format
                import pyarrow as pa
                import json
                
                # Prepare data for insertion (matching the complete table schema - 17 columns)
                # Convert timestamp strings to datetime objects for PyArrow
                def parse_timestamp(ts_str):
                    if not ts_str:
                        return None
                    if isinstance(ts_str, datetime):
                        return ts_str
                    try:
                        # Try parsing ISO format timestamp
                        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        return None
                
                # PyArrow expects data as column arrays, not row arrays
                data = {
                    'file_path': [metadata.get('file_path', '')],
                    'file_name': [metadata.get('file_name', '')],
                    'file_size_bytes': [metadata.get('file_size_bytes', 0)],
                    'file_format': [metadata.get('file_format', '')],
                    'dataset_name': [metadata.get('dataset_name', '')],
                    'mission_id': [metadata.get('mission_id', '')],
                    'satellite_name': [metadata.get('satellite_name', '')],
                    'instrument_type': [metadata.get('instrument_type', '')],
                    'observation_timestamp': [parse_timestamp(metadata.get('observation_timestamp', datetime.now()))],
                    'target_object': [metadata.get('target_object', '')],
                    'processing_status': [metadata.get('processing_status', '')],
                    'ingestion_timestamp': [parse_timestamp(metadata.get('ingestion_timestamp', datetime.now()))],
                    'last_modified': [parse_timestamp(metadata.get('last_modified'))],
                    'checksum': [metadata.get('checksum', '')],
                    'metadata_version': [metadata.get('metadata_version', '1.0')],
                    'created_at': [datetime.now()],
                    'updated_at': [datetime.now()]
                }
                
                # Validate schema and data match
                schema = table.columns()
                data_columns = len(data)
                schema_columns = len(schema)
                
                # Schema validation (debug level to reduce noise)
                logger.debug(f"🔧 Table schema has {schema_columns} columns: {[col.name for col in schema]}")
                logger.debug(f"🔧 Data dictionary has {data_columns} columns")
                
                if data_columns != schema_columns:
                    error_msg = f"❌ SCHEMA MISMATCH: Data has {data_columns} columns but table schema expects {schema_columns} columns"
                    logger.error(error_msg)
                    logger.error(f"❌ Table columns: {[col.name for col in schema]}")
                    logger.error(f"❌ Data columns: {list(data.keys())}")
                    logger.error("❌ Stopping processing to prevent data corruption. Please fix schema mismatch.")
                    raise ValueError(error_msg)
                
                # Create PyArrow table and insert
                arrow_table = pa.table(data=data, schema=table.columns())
                
                # Log API call
                self._log_api_call(
                    "table.insert()",
                    f"table=swift_metadata, file_name={metadata.get('file_name', 'Unknown')}"
                )
                
                table.insert(arrow_table)
                # Success - no need to log every single insertion
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to insert metadata: {e}")
            return False
    
    def search_metadata(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata based on criteria using VAST DB with wildcard support"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock metadata search")
            return []
            
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # Use VAST DB transaction to search metadata
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                
                # Check if schema and table exist
                try:
                    schema = bucket.schema(self.schema_name)
                    table = schema.table("swift_metadata")
                    
                    # Try to use ibis predicate pushdown for efficient filtering
                    predicate = self._build_ibis_predicate(search_criteria)
                    
                    if predicate and IBIS_AVAILABLE:
                        # Use ibis predicate pushdown (efficient)
                        self._log_api_call(
                            "table.select()",
                            f"table=swift_metadata, ibis_predicate_pushdown=True, conditions={len(search_criteria)}"
                        )
                        reader = table.select(predicate=predicate)
                    else:
                        # Fallback to Python-side filtering (less efficient but works)
                        if not IBIS_AVAILABLE:
                            logger.debug("⚠️  ibis not available, using Python-side filtering")
                        else:
                            logger.debug("⚠️  Could not build ibis predicate, using Python-side filtering")
                            
                        self._log_api_call(
                            "table.select()",
                            f"table=swift_metadata, python_filtering=True, conditions={len(search_criteria)}"
                        )
                        reader = table.select()
                    results = []
                    
                    for batch in reader:
                        for i in range(len(batch)):
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in batch.column_names:
                                value = batch[col_name][i]
                                if value is not None:
                                    record[col_name] = value.as_py()
                                else:
                                    record[col_name] = None
                            
                            # Only apply Python filtering if we didn't use ibis predicate pushdown
                            if predicate and IBIS_AVAILABLE:
                                # Results are already filtered by ibis predicate
                                results.append(record)
                            else:
                                # Apply search criteria with wildcard support (Python filtering)
                                matches = True
                                for key, criteria in search_criteria.items():
                                    if key not in record:
                                        matches = False
                                        break
                                    
                                    record_value = str(record[key]).lower()
                                
                                    if criteria['type'] == 'exact':
                                        # Exact match
                                        if record_value != str(criteria['value']).lower():
                                            matches = False
                                            break
                                    elif criteria['type'] == 'wildcard':
                                        # Wildcard match
                                        pattern = criteria['pattern'].lower()
                                        
                                        if pattern == '*':
                                            # Match everything
                                            continue
                                        elif pattern.startswith('*') and pattern.endswith('*'):
                                            # Contains pattern: *value*
                                            search_value = pattern[1:-1]
                                            if search_value not in record_value:
                                                matches = False
                                                break
                                        elif pattern.startswith('*'):
                                            # Ends with pattern: *value
                                            search_value = pattern[1:]
                                            if not record_value.endswith(search_value):
                                                matches = False
                                                break
                                        elif pattern.endswith('*'):
                                            # Starts with pattern: value*
                                            search_value = pattern[:-1]
                                            if not record_value.startswith(search_value):
                                                matches = False
                                                break
                                        else:
                                            # No wildcards, treat as exact match
                                            if record_value != pattern:
                                                matches = False
                                                break
                                    elif criteria['type'] == 'comparison':
                                        # Comparison match (for dates, numbers, etc.)
                                        operator = criteria['operator']
                                        compare_value = criteria['value']
                                        
                                        # Try to parse as date first
                                        try:
                                            from datetime import datetime
                                            record_date = datetime.fromisoformat(record_value.replace('Z', '+00:00'))
                                            compare_date = datetime.fromisoformat(compare_value.replace('Z', '+00:00'))
                                            
                                            if operator == '>':
                                                if not (record_date > compare_date):
                                                    matches = False
                                                    break
                                            elif operator == '<':
                                                if not (record_date < compare_date):
                                                    matches = False
                                                    break
                                            elif operator == '>=':
                                                if not (record_date >= compare_date):
                                                    matches = False
                                                    break
                                            elif operator == '<=':
                                                if not (record_date <= compare_date):
                                                    matches = False
                                                    break
                                        except (ValueError, TypeError):
                                            # Not a date, try numeric comparison
                                            try:
                                                record_num = float(record_value)
                                                compare_num = float(compare_value)
                                                
                                                if operator == '>':
                                                    if not (record_num > compare_num):
                                                        matches = False
                                                        break
                                                elif operator == '<':
                                                    if not (record_num < compare_num):
                                                        matches = False
                                                        break
                                                elif operator == '>=':
                                                    if not (record_num >= compare_num):
                                                        matches = False
                                                        break
                                                elif operator == '<=':
                                                    if not (record_num <= compare_num):
                                                        matches = False
                                                        break
                                            except (ValueError, TypeError):
                                                # Not numeric either, do string comparison
                                                if operator == '>':
                                                    if not (record_value > compare_value):
                                                        matches = False
                                                        break
                                                elif operator == '<':
                                                    if not (record_value < compare_value):
                                                        matches = False
                                                        break
                                                elif operator == '>=':
                                                    if not (record_value >= compare_value):
                                                        matches = False
                                                        break
                                                elif operator == '<=':
                                                    if not (record_value <= compare_value):
                                                        matches = False
                                                        break
                                
                                if matches:
                                    results.append(record)
                    
                    logger.info(f"🔍 Found {len(results)} metadata records")
                    return results
                    
                except Exception as e:
                    # Check if it's a schema/table issue or something else
                    error_msg = str(e).lower()
                    if 'schema' in error_msg or 'table' in error_msg or 'not found' in error_msg:
                        logger.info(f"ℹ️  Schema '{self.schema_name}' or table 'swift_metadata' doesn't exist yet")
                    else:
                        logger.error(f"❌ Search error: {e}")
                        # If it's an ibis-related error, try fallback to Python filtering
                        if 'ibis' in error_msg.lower() or 'predicate' in error_msg.lower():
                            logger.info("🔄 Retrying with Python-side filtering...")
                            try:
                                # Retry without ibis predicate
                                reader = table.select()
                                results = []
                                
                                for batch in reader:
                                    for i in range(len(batch)):
                                        record = {}
                                        for col_name in batch.column_names:
                                            value = batch[col_name][i]
                                            if value is not None:
                                                record[col_name] = value.as_py()
                                            else:
                                                record[col_name] = None
                                        
                                        # Apply Python filtering
                                        matches = True
                                        for key, criteria in search_criteria.items():
                                            if key not in record:
                                                matches = False
                                                break
                                            
                                            record_value = str(record[key]).lower()
                                            
                                            if criteria['type'] == 'exact':
                                                if record_value != str(criteria['value']).lower():
                                                    matches = False
                                                    break
                                            elif criteria['type'] == 'wildcard':
                                                pattern = criteria['pattern'].lower()
                                                if pattern == '*':
                                                    continue
                                                elif pattern.startswith('*') and pattern.endswith('*'):
                                                    search_value = pattern[1:-1]
                                                    if search_value not in record_value:
                                                        matches = False
                                                        break
                                                elif pattern.startswith('*'):
                                                    search_value = pattern[1:]
                                                    if not record_value.endswith(search_value):
                                                        matches = False
                                                        break
                                                elif pattern.endswith('*'):
                                                    search_value = pattern[:-1]
                                                    if not record_value.startswith(search_value):
                                                        matches = False
                                                        break
                                                else:
                                                    if record_value != pattern:
                                                        matches = False
                                                        break
                                            elif criteria['type'] == 'comparison':
                                                operator = criteria['operator']
                                                compare_value = criteria['value']
                                                
                                                try:
                                                    from datetime import datetime
                                                    record_date = datetime.fromisoformat(record_value.replace('Z', '+00:00'))
                                                    compare_date = datetime.fromisoformat(compare_value.replace('Z', '+00:00'))
                                                    
                                                    if operator == '>':
                                                        if not (record_date > compare_date):
                                                            matches = False
                                                            break
                                                    elif operator == '<':
                                                        if not (record_date < compare_date):
                                                            matches = False
                                                            break
                                                    elif operator == '>=':
                                                        if not (record_date >= compare_date):
                                                            matches = False
                                                            break
                                                    elif operator == '<=':
                                                        if not (record_date <= compare_date):
                                                            matches = False
                                                            break
                                                except (ValueError, TypeError):
                                                    try:
                                                        record_num = float(record_value)
                                                        compare_num = float(compare_value)
                                                        
                                                        if operator == '>':
                                                            if not (record_num > compare_num):
                                                                matches = False
                                                                break
                                                        elif operator == '<':
                                                            if not (record_num < compare_num):
                                                                matches = False
                                                                break
                                                        elif operator == '>=':
                                                            if not (record_num >= compare_num):
                                                                matches = False
                                                                break
                                                        elif operator == '<=':
                                                            if not (record_num <= compare_num):
                                                                matches = False
                                                                break
                                                    except (ValueError, TypeError):
                                                        if operator == '>':
                                                            if not (record_value > compare_value):
                                                                matches = False
                                                                break
                                                        elif operator == '<':
                                                            if not (record_value < compare_value):
                                                                matches = False
                                                                break
                                                        elif operator == '>=':
                                                            if not (record_value >= compare_value):
                                                                matches = False
                                                                break
                                                        elif operator == '<=':
                                                            if not (record_value <= compare_value):
                                                                matches = False
                                                                break
                                        
                                        if matches:
                                            results.append(record)
                                
                                logger.info(f"🔍 Found {len(results)} metadata records (fallback filtering)")
                                return results
                            except Exception as fallback_error:
                                logger.error(f"❌ Fallback filtering also failed: {fallback_error}")
                    return []
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Get all metadata records from the database"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock metadata retrieval")
            return []
            
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # Use VAST DB transaction to get all metadata
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                
                # Check if schema and table exist
                try:
                    schema = bucket.schema(self.schema_name)
                    table = schema.table("swift_metadata")
                    
                    # Get all records
                    reader = table.select()
                    results = []
                    
                    for batch in reader:
                        for i in range(len(batch)):
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in batch.column_names:
                                col_data = batch.column(col_name)
                                if hasattr(col_data, 'to_pylist'):
                                    record[col_name] = col_data.to_pylist()[i]
                                else:
                                    record[col_name] = col_data[i]
                            results.append(record)
                    
                    logger.info(f"📊 Retrieved {len(results)} metadata records")
                    return results
                    
                except Exception as e:
                    logger.error(f"❌ Failed to access metadata table: {e}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to get all metadata: {e}")
            return []
    
    def get_recent_metadata(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent metadata records from the database (limited for performance)"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock recent metadata")
            return []
            
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # Use VAST DB transaction to get recent metadata
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                
                # Check if schema and table exist
                try:
                    schema = bucket.schema(self.schema_name)
                    table = schema.table("swift_metadata")
                    
                    # Get limited number of records
                    reader = table.select().limit(limit)
                    results = []
                    
                    for batch in reader:
                        for i in range(len(batch)):
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in batch.column_names:
                                col_data = batch.column(col_name)
                                if hasattr(col_data, 'to_pylist'):
                                    record[col_name] = col_data.to_pylist()[i]
                                else:
                                    record[col_name] = col_data[i]
                            results.append(record)
                    
                    logger.info(f"📊 Retrieved {len(results)} recent metadata records (limit: {limit})")
                    return results
                    
                except Exception as e:
                    logger.error(f"❌ Failed to access metadata table: {e}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to get recent metadata: {e}")
            return []
    
    def get_latest_files(self, count: int) -> List[Dict[str, Any]]:
        """Get the N latest files by observation timestamp using VAST DB"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock latest files")
            return []
            
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # Use VAST DB transaction to get latest files
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                
                # Check if schema and table exist
                try:
                    schema = bucket.schema(self.schema_name)
                    table = schema.table("swift_metadata")
                    
                    # Get all records and sort by observation_timestamp
                    reader = table.select()
                    all_records = []
                    
                    for batch in reader:
                        for i in range(len(batch)):
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in batch.column_names:
                                value = batch[col_name][i]
                                if value is not None:
                                    record[col_name] = value.as_py()
                                else:
                                    record[col_name] = None
                            
                            all_records.append(record)
                    
                    # Sort by observation_timestamp (descending - latest first)
                    # Handle both datetime objects and string timestamps
                    def get_timestamp(record):
                        obs_time = record.get('observation_timestamp')
                        if obs_time is None:
                            return datetime.min
                        if isinstance(obs_time, str):
                            try:
                                return datetime.fromisoformat(obs_time.replace('Z', '+00:00'))
                            except:
                                return datetime.min
                        return obs_time
                    
                    all_records.sort(key=get_timestamp, reverse=True)
                    
                    # Return the requested number of latest files
                    latest_files = all_records[:count]
                    
                    logger.info(f"🕒 Retrieved {len(latest_files)} latest files")
                    return latest_files
                    
                except Exception:
                    # Schema or table doesn't exist yet
                    logger.info(f"ℹ️  Schema '{self.schema_name}' or table 'swift_metadata' doesn't exist yet")
                    return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest files: {e}")
            return []
    
    def get_metadata_stats(self) -> Dict[str, Any]:
        """Get statistics about the metadata catalog using VAST DB"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock metadata stats")
            return {
                'total_files': 0,
                'mission_counts': {},
                'dataset_counts': {}
            }
            
        try:
            if not self.connection:
                if not self.connect():
                    return {}
            
            # Use VAST DB transaction to get statistics
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                
                # Check if schema and table exist
                try:
                    schema = bucket.schema(self.schema_name)
                    table = schema.table("swift_metadata")
                    
                    # Get total count using select()
                    reader = table.select()
                    total_count = 0
                    mission_counts = {}
                    dataset_counts = {}
                    
                    # Process all records to count them
                    for batch in reader:
                        total_count += len(batch)
                        
                        # Count by mission and dataset
                        for i in range(len(batch)):
                            mission_id = batch['mission_id'][i].as_py() if batch['mission_id'][i] is not None else 'unknown'
                            dataset_name = batch['dataset_name'][i].as_py() if batch['dataset_name'][i] is not None else 'unknown'
                            
                            mission_counts[mission_id] = mission_counts.get(mission_id, 0) + 1
                            dataset_counts[dataset_name] = dataset_counts.get(dataset_name, 0) + 1
                    
                    return {
                        'total_files': total_count,
                        'mission_counts': mission_counts,
                        'dataset_counts': dataset_counts
                    }
                    
                except Exception:
                    # Schema or table doesn't exist yet
                    logger.info(f"ℹ️  Schema '{self.schema_name}' or table 'swift_metadata' doesn't exist yet")
                    return {
                        'total_files': 0,
                        'mission_counts': {},
                        'dataset_counts': {}
                    }
            
        except Exception as e:
            logger.error(f"❌ Failed to get metadata stats: {e}")
            return {}
    
    def clear_all_tables(self) -> bool:
        """Clear all data from metadata tables while preserving structure"""
        try:
            if not VASTDB_AVAILABLE:
                logger.warning("⚠️  vastdb not available - mock table clearing")
                return True
            
            cursor = self.connection.cursor()
            
            # Clear the main metadata table
            cursor.execute(f"DELETE FROM {self.schema_name}.swift_metadata")
            deleted_count = cursor.rowcount
            
            # Reset sequence if it exists
            cursor.execute(f"ALTER SEQUENCE {self.schema_name}.swift_metadata_id_seq RESTART WITH 1")
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Cleared {deleted_count} records from metadata tables")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear tables: {e}")
            if self.connection and VASTDB_AVAILABLE:
                self.connection.rollback()
            return False
    
    def remove_database(self) -> bool:
        """Remove the entire database (DESTRUCTIVE OPERATION)"""
        try:
            if not VASTDB_AVAILABLE:
                logger.warning("⚠️  vastdb not available - mock database removal")
                return True
            
            cursor = self.connection.cursor()
            
            # Drop the database (requires connection to a different database)
            cursor.execute(f"DROP DATABASE IF EXISTS {self.database_name}")
            
            cursor.close()
            logger.info(f"✅ Database '{self.database_name}' removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove database: {e}")
            return False
    
    def delete_vast_schema(self) -> bool:
        """Delete the VAST schema and all its tables (DESTRUCTIVE OPERATION)"""
        try:
            logger.info(f"🗑️  Starting VAST schema deletion for schema: {self.schema_name}")
            
            if not self.connection:
                if not self.connect():
                    return False
            
            # Use VAST DB transaction to delete tables first, then schema
            with self.connection.transaction() as tx:
                try:
                    # Get bucket
                    bucket = tx.bucket(self.bucket_name)
                    
                    # Get schema
                    schema = bucket.schema(self.schema_name, fail_if_missing=False)
                    if not schema:
                        logger.info(f"ℹ️  Schema '{self.schema_name}' does not exist (already deleted)")
                        return True
                    
                    # First, delete all tables in the schema
                    logger.info(f"🔧 Deleting all tables in schema '{self.schema_name}'...")
                    tables_deleted = 0
                    
                    # Get all tables in the schema
                    try:
                        # Try to get the swift_metadata table specifically
                        try:
                            table = schema.table("swift_metadata")
                            
                            # Log API call
                            self._log_api_call(
                                "table.drop()",
                                f"table=swift_metadata (DESTRUCTIVE OPERATION)"
                            )
                            
                            table.drop()
                            tables_deleted += 1
                            logger.info(f"✅ Deleted table 'swift_metadata'")
                        except Exception as e:
                            logger.debug(f"Table 'swift_metadata' may not exist: {e}")
                        
                        # Now try to drop the schema
                        # Log API call
                        self._log_api_call(
                            "schema.drop()",
                            f"schema={self.schema_name} (DESTRUCTIVE OPERATION)"
                        )
                        
                        schema.drop()
                        logger.info(f"✅ Deleted VAST schema '{self.schema_name}' and {tables_deleted} tables")
                        return True
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "TabularSchemaNotEmpty" in error_msg:
                            logger.error(f"❌ Cannot delete schema '{self.schema_name}' - it still contains tables")
                            logger.error(f"❌ Error: {error_msg}")
                            return False
                        else:
                            logger.error(f"❌ Failed to delete schema '{self.schema_name}': {e}")
                            return False
                    
                except Exception as e:
                    logger.error(f"❌ Failed to delete VAST schema: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to delete VAST schema: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and VASTDB_AVAILABLE:
            # VAST DB Sessions don't have a close() method, just set to None
            self.connection = None
            logger.info("🔌 Closed VAST Database connection")
        elif self.connection == "MOCK_CONNECTION":
            logger.info("🔌 Closed mock database connection")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

#!/usr/bin/env python3
"""
VAST Database Manager for Lab 2 Metadata Infrastructure
Safely manages database creation, schema setup, and metadata storage
"""

import logging
import json
import os
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Suppress SSL warnings for internal networks
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

try:
    import vastdb
    VASTDB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  vastdb not found. ImportError: {e}")
    print("💡 This is required for Lab 2 database functionality")
    VASTDB_AVAILABLE = False

# ibis support removed - will be added in future lab

logger = logging.getLogger(__name__)

class VASTDatabaseManager:
    """Manages VAST Database operations for metadata catalog"""
    
    def __init__(self, config, show_api_calls: bool = False):
        """Initialize the database manager"""
        self.config = config
        self.show_api_calls = show_api_calls
        # Lab 2 metadata database – use configured database name
        self.bucket_name = config.get('lab2.database.name', 'lab2-metadata-db')
        self.schema_name = config.get('lab2.database.schema', 'satellite_observations')
        
        # Database connection parameters for vastdb (using S3 credentials)
        self.db_config = {
            'access': config.get_secret('s3_access_key'),
            'secret': config.get_secret('s3_secret_key'),
            'endpoint': config.get('vastdb.endpoint', 'https://your-vms-hostname'),
            'ssl_verify': config.get('vastdb.ssl_verify', True),
            'timeout': config.get('vastdb.timeout', 30)
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
    
        
    def connect(self) -> bool:
        """Establish connection to VAST Database"""
        if not VASTDB_AVAILABLE:
            logger.error("❌ vastdb not available - cannot connect to VAST Database")
            return False
            
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
            logger.error("❌ vastdb not available - cannot check database existence")
            return False
            
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
                
                # Create schema (handle case where it already exists)
                try:
                    schema = bucket.create_schema(self.schema_name)
                    logger.info(f"✅ Created schema '{self.schema_name}' in bucket '{self.bucket_name}'")
                except vastdb.errors.SchemaExists:
                    # Schema already exists, get it
                    schema = bucket.schema(self.schema_name)
                    logger.info(f"✅ Schema '{self.schema_name}' already exists in bucket '{self.bucket_name}'")
                except Exception as e:
                    logger.error(f"❌ Failed to create/get schema '{self.schema_name}': {e}")
                    raise
                
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
                
                # Create table (handle case where it already exists)
                try:
                    table = schema.create_table("swift_metadata", columns)
                    logger.info(f"✅ Created table 'swift_metadata' in schema '{self.schema_name}'")
                except vastdb.errors.TableExists:
                    # Table already exists, get it
                    table = schema.table("swift_metadata")
                    logger.info(f"✅ Table 'swift_metadata' already exists in schema '{self.schema_name}'")
                except Exception as e:
                    logger.error(f"❌ Failed to create/get table 'swift_metadata': {e}")
                    raise
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create schema and table: {e}")
            return False
    
    def _ensure_bucket_exists(self) -> bool:
        """Ensure the underlying view for this 'bucket' exists using vastpy.

        Note: VAST systems expose views, not /api/buckets. We treat the
        view path '/{bucket_name}' as the backing for VAST DB operations.
        """
        try:
            from vastpy import VASTClient
            
            vms_endpoint = self.config.get('vast.address')
            vms_username = self.config.get('vast.user')
            vms_password = self.config.get_secret('vast_password')
            view_path = self.config.get('lab2.database.view_path', f"/{self.bucket_name}")
            
            if not vms_endpoint or not vms_username or not vms_password:
                logger.error("❌ Missing VMS settings in config.yaml/secrets.yaml (vast.address, vast.user, vast_password)")
                return False
            
            # Strip protocol from address (vastpy expects just hostname:port)
            address = vms_endpoint
            if address.startswith('https://'):
                address = address[8:]
            elif address.startswith('http://'):
                address = address[7:]
            
            client = VASTClient(user=vms_username, password=vms_password, address=address)
            
            # Verify view exists; create if missing using default policy
            try:
                views = client.views.get()
                existing = next((v for v in views if v.get('path') == view_path), None)
                if existing:
                    logger.info(f"✅ View '{view_path}' exists (backing for bucket '{self.bucket_name}')")
                    return True
                # Try to create view
                policies = client.viewpolicies.get(name='default')
                if not policies:
                    logger.error("❌ Default view policy not found; cannot create view")
                    return False
                policy_id = policies[0]['id']
                client.views.post(path=view_path, policy_id=policy_id, create_dir=True)
                logger.info(f"✅ Created view '{view_path}' (backing for bucket '{self.bucket_name}')")
                return True
            except Exception as e:
                logger.error(f"❌ Failed ensuring view '{view_path}': {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to ensure view exists via vastpy: {e}")
            return False
    
    def schema_exists(self) -> bool:
        """Check if the target schema exists"""
        try:
            if not self.connection:
                if not self.connect():
                    return False

            # Use vastdb transaction API to check schema existence
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                try:
                    _ = bucket.schema(self.schema_name)
                    logger.info(f"✅ Schema '{self.schema_name}' exists")
                    return True
                except Exception:
                    logger.info(f"ℹ️  Schema '{self.schema_name}' does not exist")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Error checking schema existence: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the target schema if it doesn't exist"""
        try:
            if self.schema_exists():
                logger.info(f"ℹ️  Schema '{self.schema_name}' already exists")
                return True

            # Create schema using vastdb API
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                try:
                    bucket.create_schema(self.schema_name)
                    logger.info(f"✅ Created schema '{self.schema_name}'")
                    return True
                except vastdb.errors.SchemaExists:
                    logger.info(f"✅ Schema '{self.schema_name}' already exists")
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to create schema '{self.schema_name}': {e}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Failed to create schema: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a specific table exists"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                try:
                    schema = bucket.schema(self.schema_name)
                    _ = schema.table(table_name)
                    return True
                except Exception:
                    return False
            
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

            # Create table using vastdb API
            with self.connection.transaction() as tx:
                bucket = tx.bucket(self.bucket_name)
                schema = bucket.schema(self.schema_name)
                
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
                
                try:
                    schema.create_table(table_name, columns)
                    logger.info(f"✅ Created metadata table '{table_name}'")
                    return True
                except vastdb.errors.TableExists:
                    logger.info(f"✅ Table '{table_name}' already exists")
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to create metadata table '{table_name}': {e}")
                    return False
            
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
            logger.error("❌ vastdb not available - cannot search metadata")
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
                    
                    # Use Python-side filtering (ibis support removed)
                    self._log_api_call(
                        "table.select()",
                        f"table=swift_metadata, python_filtering=True, conditions={len(search_criteria)}"
                    )
                    logger.info(f"Search criteria: {search_criteria}")
                    reader = table.select()
                    results = []
                    
                    batch_count = 0
                    total_records_processed = 0
                    for batch in reader:
                        batch_count += 1
                        logger.info(f"Processing batch {batch_count} with {len(batch)} records")
                        for i in range(len(batch)):
                            total_records_processed += 1
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in batch.column_names:
                                value = batch[col_name][i]
                                if value is not None:
                                    record[col_name] = value.as_py()
                                else:
                                    record[col_name] = None
                            
                            # Apply search criteria with wildcard support (Python filtering)
                            matches = True
                            criteria_loop_break = False
                            for key, criteria in search_criteria.items():
                                if total_records_processed <= 3:
                                    logger.info(f"Processing criteria for record {total_records_processed}: {key}")
                                if key not in record:
                                    logger.info(f"Key '{key}' not found in record. Available keys: {list(record.keys())}")
                                    matches = False
                                    criteria_loop_break = True
                                    break
                                
                                record_value = str(record[key]).lower() if record[key] is not None else ""
                                
                                if total_records_processed <= 3:  # Debug first few records
                                    logger.info(f"Record {total_records_processed}: {key}='{record_value}' (criteria: {criteria})")
                                
                                if criteria['type'] == 'exact':
                                    # Exact match
                                    if record_value != str(criteria['value']).lower():
                                        matches = False
                                        criteria_loop_break = True
                                        break
                                elif criteria['type'] == 'wildcard':
                                    # Wildcard match
                                    pattern = criteria['pattern'].lower()
                                    
                                    if pattern == '*':
                                        # Match everything - set matches to True and break out of criteria loop
                                        if total_records_processed <= 3:
                                            logger.info(f"Wildcard '*' match - setting matches=True")
                                        matches = True
                                        criteria_loop_break = True
                                        break
                                    else:
                                        # Other wildcard patterns
                                        if pattern.startswith('*') and pattern.endswith('*'):
                                            # Contains pattern: *value*
                                            search_value = pattern[1:-1]
                                            if search_value not in record_value:
                                                matches = False
                                                criteria_loop_break = True
                                                break
                                        elif pattern.startswith('*'):
                                            # Ends with pattern: *value
                                            search_value = pattern[1:]
                                            if not record_value.endswith(search_value):
                                                matches = False
                                                criteria_loop_break = True
                                                break
                                        elif pattern.endswith('*'):
                                            # Starts with pattern: value*
                                            search_value = pattern[:-1]
                                            if not record_value.startswith(search_value):
                                                matches = False
                                                criteria_loop_break = True
                                                break
                                        else:
                                            # No wildcards, treat as exact match
                                            if record_value != pattern:
                                                matches = False
                                                criteria_loop_break = True
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
                                                criteria_loop_break = True
                                                break
                                        elif operator == '<':
                                            if not (record_date < compare_date):
                                                matches = False
                                                criteria_loop_break = True
                                                break
                                        elif operator == '>=':
                                            if not (record_date >= compare_date):
                                                matches = False
                                                criteria_loop_break = True
                                                break
                                        elif operator == '<=':
                                            if not (record_date <= compare_date):
                                                matches = False
                                                criteria_loop_break = True
                                                break
                                    except (ValueError, TypeError):
                                        # Not a date, try numeric comparison
                                        try:
                                            record_num = float(record_value)
                                            compare_num = float(compare_value)
                                            
                                            if operator == '>':
                                                if not (record_num > compare_num):
                                                    matches = False
                                                    criteria_loop_break = True
                                                    break
                                            elif operator == '<':
                                                if not (record_num < compare_num):
                                                    matches = False
                                                    criteria_loop_break = True
                                                    break
                                            elif operator == '>=':
                                                if not (record_num >= compare_num):
                                                    matches = False
                                                    criteria_loop_break = True
                                                    break
                                            elif operator == '<=':
                                                if not (record_num <= compare_num):
                                                    matches = False
                                                    criteria_loop_break = True
                                                    break
                                        except (ValueError, TypeError):
                                                # Not numeric either, do string comparison
                                                if operator == '>':
                                                    if not (record_value > compare_value):
                                                        matches = False
                                                        criteria_loop_break = True
                                                        break
                                                elif operator == '<':
                                                    if not (record_value < compare_value):
                                                        matches = False
                                                        criteria_loop_break = True
                                                        break
                                                elif operator == '>=':
                                                    if not (record_value >= compare_value):
                                                        matches = False
                                                        criteria_loop_break = True
                                                        break
                                                elif operator == '<=':
                                                    if not (record_value <= compare_value):
                                                        matches = False
                                                        criteria_loop_break = True
                                                        break
                                
                                # Check if we should continue to the next record
                                if criteria_loop_break:
                                    if total_records_processed <= 3:
                                        logger.info(f"Record {total_records_processed}: criteria loop broke, matches={matches}")
                                
                                if total_records_processed <= 3:
                                    logger.info(f"Record {total_records_processed}: matches={matches} (after criteria loop)")
                                
                                if matches:
                                    results.append(record)
                                    if len(results) <= 3:
                                        logger.info(f"Added record {len(results)} to results: {record.get('file_name', 'N/A')}")
                    
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
                    
                    # Use QueryConfig to limit results efficiently
                    from vastdb.config import QueryConfig
                    
                    config = QueryConfig(
                        num_splits=1,                    # Use 1 split
                        num_sub_splits=1,                # 1 subsplit per split
                        limit_rows_per_sub_split=limit,  # Limit to requested count
                    )
                    
                    # Get records with limit applied
                    reader = table.select(config=config)
                    results = []
                    
                    # Process the first batch (which should contain up to 'limit' records)
                    try:
                        first_batch = next(reader)
                        for i in range(len(first_batch)):
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in first_batch.column_names:
                                value = first_batch[col_name][i]
                                if value is not None:
                                    record[col_name] = value.as_py()
                                else:
                                    record[col_name] = None
                            results.append(record)
                    except StopIteration:
                        # No data available
                        pass
                    
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
                    
                    # Use QueryConfig to limit results efficiently
                    from vastdb.config import QueryConfig
                    
                    config = QueryConfig(
                        num_splits=1,                    # Use 1 split
                        num_sub_splits=1,                # 1 subsplit per split
                        limit_rows_per_sub_split=count,  # Limit to requested count
                    )
                    
                    # Get records with limit applied
                    reader = table.select(config=config)
                    records = []
                    
                    # Process the first batch (which should contain up to 'count' records)
                    try:
                        first_batch = next(reader)
                        for i in range(len(first_batch)):
                            record = {}
                            # Convert PyArrow record to Python dict
                            for col_name in first_batch.column_names:
                                value = first_batch[col_name][i]
                                if value is not None:
                                    record[col_name] = value.as_py()
                                else:
                                    record[col_name] = None
                            
                            records.append(record)
                    except StopIteration:
                        # No data available
                        pass
                    
                    # Sort by observation_timestamp (descending - latest first)
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
                    
                    records.sort(key=get_timestamp, reverse=True)
                    
                    # Return the requested number of latest files
                    latest_files = records[:count]
                    
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
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

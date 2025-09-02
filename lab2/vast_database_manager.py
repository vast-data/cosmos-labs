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
    print(f"✅ vastdb imported successfully: {vastdb}")
except ImportError as e:
    print(f"⚠️  vastdb not found. ImportError: {e}")
    print("💡 This is required for Lab 2 database functionality")
    print("🔧 For now, using mock database operations")
    VASTDB_AVAILABLE = False

logger = logging.getLogger(__name__)

class VASTDatabaseManager:
    """Manages VAST Database operations for metadata catalog"""
    
    def __init__(self, config):
        """Initialize the database manager"""
        self.config = config
        # Lab 2 database bucket – use only lab2.vastdb.bucket (not the general datastore/S3 bucket)
        self.bucket_name = config.get('lab2.vastdb.bucket', 'cosmos-lab-metadata')
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
        
    def connect(self) -> bool:
        """Establish connection to VAST Database"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - using mock connection")
            self.connection = "MOCK_CONNECTION"
            return True
            
        try:
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
                
                # Create table with metadata columns (matching the insert_metadata method)
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
                    ('metadata_version', pa.utf8()),
                ])
                
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
            
            logger.info(f"🔧 Attempting to insert metadata for: {metadata.get('file_name', 'Unknown')}")
            
            # Use VAST DB transaction to insert metadata
            with self.connection.transaction() as tx:
                logger.info(f"🔧 Getting bucket: {self.bucket_name}")
                bucket = tx.bucket(self.bucket_name)
                
                logger.info(f"🔧 Getting schema: {self.schema_name}")
                schema = bucket.schema(self.schema_name)
                
                logger.info("🔧 Getting table: swift_metadata")
                table = schema.table("swift_metadata")
                
                # Convert metadata to PyArrow format
                import pyarrow as pa
                import json
                
                # Prepare data for insertion (matching the table schema)
                data = [
                    [
                        metadata.get('file_path', ''),
                        metadata.get('file_name', ''),
                        metadata.get('file_size_bytes', 0),
                        metadata.get('file_format', ''),
                        metadata.get('dataset_name', ''),
                        metadata.get('mission_id', ''),
                        metadata.get('satellite_name', ''),
                        metadata.get('instrument_type', ''),
                        metadata.get('observation_timestamp', datetime.now()),
                        metadata.get('target_object', ''),
                        metadata.get('processing_status', ''),
                        metadata.get('ingestion_timestamp', datetime.now()),
                        metadata.get('last_modified', None),
                        metadata.get('checksum', ''),
                        metadata.get('metadata_version', '1.0'),
                        datetime.now(),  # created_at
                        datetime.now()   # updated_at
                    ]
                ]
                
                # Validate schema and data match
                schema = table.columns()
                data_columns = len(data[0])
                schema_columns = len(schema)
                
                logger.info(f"🔧 Table schema has {schema_columns} columns: {[col.name for col in schema]}")
                logger.info(f"🔧 Data array has {data_columns} elements")
                
                if data_columns != schema_columns:
                    error_msg = f"❌ SCHEMA MISMATCH: Data has {data_columns} elements but table schema expects {schema_columns} columns"
                    logger.error(error_msg)
                    logger.error(f"❌ Table columns: {[col.name for col in schema]}")
                    logger.error(f"❌ Data elements: {data_columns}")
                    logger.error("❌ Stopping processing to prevent data corruption. Please fix schema mismatch.")
                    raise ValueError(error_msg)
                
                # Create PyArrow table and insert
                arrow_table = pa.table(data=data, schema=table.columns())
                table.insert(arrow_table)
                logger.info(f"✅ Inserted metadata for: {metadata.get('file_name')}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to insert metadata: {e}")
            return False
    
    def search_metadata(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata based on criteria using VAST DB"""
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
                    
                    # For now, return all records (VAST DB predicate pushdown can be implemented later)
                    # This is a simplified search that gets all records and filters in Python
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
                            
                            # Apply search criteria
                            matches = True
                            for key, value in search_criteria.items():
                                if key in record and record[key] != value:
                                    matches = False
                                    break
                            
                            if matches:
                                results.append(record)
                    
                    logger.info(f"🔍 Found {len(results)} metadata records")
                    return results
                    
                except Exception:
                    # Schema or table doesn't exist yet
                    logger.info(f"ℹ️  Schema '{self.schema_name}' or table 'swift_metadata' doesn't exist yet")
                    return []
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
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

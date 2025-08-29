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
    # Only import what's actually available in vastdb
    VASTDB_AVAILABLE = True
    print(f"✅ vastdb imported successfully: {vastdb}")
    print(f"Available vastdb attributes: {[attr for attr in dir(vastdb) if not attr.startswith('_')]}")
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
        self.database_name = config.get('lab2.vastdb.database', 'orbital_dynamics_metadata')
        self.schema_name = config.get('lab2.vastdb.schema', 'satellite_observations')
        
        # Database connection parameters
        self.db_config = {
            'host': config.get('lab2.vastdb.host', 'localhost'),
            'port': config.get('lab2.vastdb.port', 5432),
            'database': self.database_name,
            'user': config.get('lab2.vastdb.user', 'vast'),
            'password': config.get_secret('lab2.vastdb_password') or 'vastdata',  # Use default if not set
            'schema': self.schema_name
        }
        
        self.connection = None
        self.database = None
        
    def connect(self) -> bool:
        """Establish connection to VAST Database"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - using mock connection")
            self.connection = "MOCK_CONNECTION"
            return True
            
        try:
            # Test connection without specifying database (to check if server is accessible)
            test_config = self.db_config.copy()
            test_config['database'] = 'postgres'  # Default database
            
            self.connection = vastdb.connect(**test_config)
            logger.info(f"✅ Connected to VAST Database server at {self.db_config['host']}:{self.db_config['port']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to VAST Database: {e}")
            return False
    
    def database_exists(self) -> bool:
        """Check if the target database exists"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - mock database exists check")
            return False  # Mock: database doesn't exist
            
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            # Query to check if database exists
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 1 FROM pg_database 
                WHERE datname = %s
            """, (self.database_name,))
            
            exists = cursor.fetchone() is not None
            cursor.close()
            
            if exists:
                logger.info(f"✅ Database '{self.database_name}' exists")
            else:
                logger.info(f"ℹ️  Database '{self.database_name}' does not exist")
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ Error checking database existence: {e}")
            return False
    
    def create_database(self) -> bool:
        """Create the target database if it doesn't exist"""
        try:
            if self.database_exists():
                logger.info(f"ℹ️  Database '{self.database_name}' already exists")
                return True
            
            # Create database
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE {self.database_name}")
            cursor.close()
            
            logger.info(f"✅ Created database '{self.database_name}'")
            
            # Reconnect to the new database
            self.connection.close()
            self.db_config['database'] = self.database_name
            self.connection = vastdb.connect(**self.db_config)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
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
        """Check if metadata for a file already exists in the database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT 1 FROM {self.schema_name}.swift_metadata 
                WHERE file_path = %s
            """, (file_path,))
            
            exists = cursor.fetchone() is not None
            cursor.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ Error checking metadata existence: {e}")
            return False
    
    def insert_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Insert metadata into the database"""
        try:
            cursor = self.connection.cursor()
            
            # Prepare the insert statement
            columns = [
                'file_path', 'file_name', 'file_size_bytes', 'file_format', 'dataset_name',
                'mission_id', 'satellite_name', 'instrument_type', 'observation_timestamp',
                'target_object', 'processing_status', 'ingestion_timestamp', 'metadata_version'
            ]
            
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            
            insert_sql = f"""
                INSERT INTO {self.schema_name}.swift_metadata 
                ({column_names}) VALUES ({placeholders})
            """
            
            # Prepare values in the correct order
            values = [
                metadata.get('file_path'),
                metadata.get('file_name'),
                metadata.get('file_size_bytes'),
                metadata.get('file_format'),
                metadata.get('dataset_name'),
                metadata.get('mission_id'),
                metadata.get('satellite_name'),
                metadata.get('instrument_type'),
                metadata.get('observation_timestamp'),
                metadata.get('target_object'),
                metadata.get('processing_status'),
                metadata.get('ingestion_timestamp'),
                metadata.get('metadata_version', '1.0')
            ]
            
            cursor.execute(insert_sql, values)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Inserted metadata for: {metadata.get('file_name')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to insert metadata: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def search_metadata(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata based on criteria"""
        try:
            cursor = self.connection.cursor()
            
            # Build dynamic search query
            where_conditions = []
            search_values = []
            
            for key, value in search_criteria.items():
                if value is not None:
                    where_conditions.append(f"{key} = %s")
                    search_values.append(value)
            
            if not where_conditions:
                # No search criteria, return all
                search_sql = f"SELECT * FROM {self.schema_name}.swift_metadata ORDER BY created_at DESC"
                cursor.execute(search_sql)
            else:
                where_clause = " AND ".join(where_conditions)
                search_sql = f"""
                    SELECT * FROM {self.schema_name}.swift_metadata 
                    WHERE {where_clause} 
                    ORDER BY created_at DESC
                """
                cursor.execute(search_sql, search_values)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                results.append(result)
            
            cursor.close()
            
            logger.info(f"🔍 Found {len(results)} metadata records")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_metadata_stats(self) -> Dict[str, Any]:
        """Get statistics about the metadata catalog"""
        try:
            cursor = self.connection.cursor()
            
            # Total count
            cursor.execute(f"SELECT COUNT(*) FROM {self.schema_name}.swift_metadata")
            total_count = cursor.fetchone()[0]
            
            # Count by mission
            cursor.execute(f"""
                SELECT mission_id, COUNT(*) as count 
                FROM {self.schema_name}.swift_metadata 
                GROUP BY mission_id
            """)
            mission_counts = dict(cursor.fetchall())
            
            # Count by dataset
            cursor.execute(f"""
                SELECT dataset_name, COUNT(*) as count 
                FROM {self.schema_name}.swift_metadata 
                GROUP BY dataset_name
            """)
            dataset_counts = dict(cursor.fetchall())
            
            cursor.close()
            
            return {
                'total_files': total_count,
                'mission_counts': mission_counts,
                'dataset_counts': dataset_counts
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
            self.connection.close()
            logger.info("🔌 Closed database connection")
        elif self.connection == "MOCK_CONNECTION":
            logger.info("🔌 Closed mock database connection")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

#!/usr/bin/env python3
"""
Lab 2 Complete Solution: Metadata Infrastructure Project
Integrates VAST Database, Swift metadata extraction, and S3 file handling
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config_loader import ConfigLoader
    from vast_database_manager import VASTDatabaseManager
    from swift_metadata_extractor import SwiftMetadataExtractor
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required modules are available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Lab2CompleteSolution:
    """Complete Lab 2 solution integrating database, metadata extraction, and S3"""
    
    def __init__(self, config_path: str = None, production_mode: bool = False, show_api_calls: bool = False):
        """Initialize the complete Lab 2 solution"""
        self.production_mode = production_mode
        self.show_api_calls = show_api_calls
        
        # Load configuration
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = str(project_root / "config.yaml")
            secrets_path = str(project_root / "secrets.yaml")
        else:
            # If config_path is provided, assume secrets.yaml is in the same directory
            secrets_path = str(Path(config_path).parent / "secrets.yaml")
        
        self.config = ConfigLoader(config_path, secrets_path)
        
        # Initialize components
        self.db_manager = VASTDatabaseManager(self.config, show_api_calls=show_api_calls)
        self.metadata_extractor = SwiftMetadataExtractor(self.config)
        
        # Swift datasets configuration
        self.swift_datasets_dir = Path(__file__).parent.parent / "scripts" / "swift_datasets"
        
        mode_text = "PRODUCTION" if production_mode else "DRY RUN"
        logger.info(f"Lab 2 Complete Solution initialized in {mode_text} mode")
    
    def create_lab2_buckets(self) -> bool:
        """Create both raw data and metadata database buckets using vastpy"""
        try:
            from vastpy import VASTClient
            
            vms_endpoint = self.config.get('vast.address')
            vms_username = self.config.get('vast.user')
            vms_password = self.config.get_secret('vast_password')
            tenant_name = self.config.get('vast.tenant', 'default')
            
            if not vms_endpoint or not vms_username or not vms_password:
                logger.error("❌ Missing VMS settings in config.yaml/secrets.yaml (vast.address, vast.user, vast_password)")
                return False
            
            # Strip protocol from address (vastpy expects just hostname:port)
            address = vms_endpoint
            if address.startswith('https://'):
                address = address[8:]
            elif address.startswith('http://'):
                address = address[7:]
            
            # Create VASTClient (correct API)
            client = VASTClient(
                user=vms_username,
                password=vms_password,
                address=address
            )
            
            # Create raw data view (instead of bucket)
            raw_view_path = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data')
            try:
                # Check if view exists
                views = client.views.get()
                existing_view = next((v for v in views if v.get('path') == raw_view_path), None)
                if existing_view:
                    logger.info(f"✅ Raw data view '{raw_view_path}' already exists")
                else:
                    if self.production_mode:
                        # Get default policy for view creation
                        policies = client.viewpolicies.get(name='default')
                        if policies:
                            policy_id = policies[0]['id']
                            view = client.views.post(path=raw_view_path, policy_id=policy_id, create_dir=True)
                            logger.info(f"✅ Created raw data view '{raw_view_path}'")
                        else:
                            logger.warning("⚠️ No default policy found, skipping view creation")
                    else:
                        logger.info(f"🔍 DRY RUN: Would create raw data view '{raw_view_path}'")
            except Exception as e:
                logger.error(f"❌ Failed to check/create raw data view: {e}")
                return False
            
            # Create metadata database view (enables DATABASE protocol so vastdb can connect)
            metadata_view_path = self.config.get('lab2.metadata_database.view_path', '/lab2-metadata-db')
            metadata_db_name = self.config.get('lab2.metadata_database.database_name', 'lab2-metadata-db')
            bucket_owner = self.config.get('vast.user')
            try:
                # Check if view exists
                views = client.views.get()
                existing_view = next((v for v in views if v.get('path') == metadata_view_path), None)
                if existing_view:
                    logger.info(f"✅ Metadata database view '{metadata_view_path}' already exists")
                else:
                    if self.production_mode:
                        # Get default policy for view creation and enable DATABASE protocol
                        policies = client.viewpolicies.get(name='default')
                        if policies:
                            policy_id = policies[0]['id']
                            view = client.views.post(
                                path=metadata_view_path,
                                policy_id=policy_id,
                                create_dir=True,
                                protocols=['S3', 'DATABASE'],
                                bucket=metadata_db_name,
                                bucket_owner=bucket_owner
                            )
                            logger.info(f"✅ Created metadata database view '{metadata_view_path}'")
                        else:
                            logger.warning("⚠️ No default policy found, skipping view creation")
                    else:
                        logger.info(f"🔍 DRY RUN: Would create metadata database view '{metadata_view_path}'")
            except Exception as e:
                logger.error(f"❌ Failed to check/create metadata database view: {e}")
                return False

            # Ensure database schema exists via vastpy (per docs) so vastdb can transact
            try:
                if self.production_mode:
                    client.schemas.post(name=self.config.get('lab2.metadata_database.schema', 'satellite_observations'),
                                        database_name=metadata_db_name)
                    logger.info(f"✅ Ensured schema '{self.config.get('lab2.metadata_database.schema', 'satellite_observations')}' exists in database '{metadata_db_name}'")
                else:
                    logger.info(f"🔍 DRY RUN: Would create schema '{self.config.get('lab2.metadata_database.schema', 'satellite_observations')}' in database '{metadata_db_name}'")
            except Exception as e:
                logger.error(f"❌ Failed to ensure database schema via vastpy: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Lab 2 buckets: {e}")
            return False

    def setup_database_infrastructure(self) -> bool:
        """Safely set up the database infrastructure"""
        try:
            logger.info("🔧 Setting up VAST Database infrastructure...")
            
            # Step 1: Create both buckets using vastpy
            if not self.create_lab2_buckets():
                logger.error("❌ Failed to create Lab 2 buckets")
                return False
            
            # Step 2: Connect to database server
            if not self.db_manager.connect():
                logger.error("❌ Failed to connect to VAST Database server")
                return False
            
            # Step 3: Check if bucket exists, create schema and table if needed
            if not self.db_manager.database_exists():
                if self.production_mode:
                    if not self.db_manager.create_schema_and_table():
                        logger.error("❌ Failed to create schema and table")
                        return False
                else:
                    logger.info("🔍 DRY RUN: Would create schema and table")
            else:
                # Bucket exists, check if we need to create schema and table
                if self.production_mode:
                    if not self.db_manager.create_schema_and_table():
                        logger.error("❌ Failed to create schema and table")
                        return False
                else:
                    logger.info("🔍 DRY RUN: Would create schema and table")
            
            logger.info("✅ Database infrastructure setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database infrastructure setup failed: {e}")
            return False
    
    def get_available_datasets(self) -> List[Dict[str, Any]]:
        """Get list of available Swift datasets"""
        if not self.swift_datasets_dir.exists():
            logger.warning(f"⚠️  Swift datasets directory not found: {self.swift_datasets_dir}")
            return []
        
        logger.info(f"🔍 Scanning Swift datasets directory: {self.swift_datasets_dir}")
        datasets = []
        
        for dataset_dir in self.swift_datasets_dir.iterdir():
            if dataset_dir.is_dir():
                # Calculate total size
                total_size = sum(f.stat().st_size for f in dataset_dir.rglob('*') if f.is_file())
                total_size_gb = total_size / (1024**3)
                
                # Count files
                file_count = sum(1 for f in dataset_dir.rglob('*') if f.is_file())
                
                datasets.append({
                    'name': dataset_dir.name,
                    'path': str(dataset_dir),
                    'size_gb': round(total_size_gb, 2),
                    'file_count': file_count
                })
        
        return sorted(datasets, key=lambda x: x['size_gb'], reverse=True)
    
    def process_dataset_metadata(self, dataset_path: str) -> Dict[str, Any]:
        """Process metadata for a single dataset"""
        dataset_name = Path(dataset_path).name
        
        logger.info(f"📊 Processing dataset: {dataset_name}")
        logger.info(f"   Path: {dataset_path}")
        
        if self.production_mode:
            logger.info("🚨 PRODUCTION MODE: Processing actual files")
        else:
            logger.info("🔍 DRY RUN MODE: No actual processing")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
        
        # Process files one by one - extract metadata and insert immediately
        logger.info(f"🔧 Starting file-by-file processing for dataset: {dataset_name}")
        
        dataset_path = Path(dataset_path)
        if not dataset_path.exists() or not dataset_path.is_dir():
            logger.error(f"❌ Dataset directory not found: {dataset_path}")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
        
        # Find all files in the dataset
        all_files = [f for f in dataset_path.rglob('*') if f.is_file()]
        total_files = len(all_files)
        
        if total_files == 0:
            logger.warning(f"⚠️  No files found in dataset: {dataset_name}")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
        
        logger.info(f"📊 Found {total_files} files to process")
        
        # Process each file individually
        processed_count = 0
        inserted_count = 0
        skipped_count = 0
        failed_count = 0
        
        for file_path in all_files:
            processed_count += 1
            
            # Progress logging
            if processed_count % 10 == 0 or processed_count == 1:
                logger.info(f"🔧 Processing file {processed_count}/{total_files}: {file_path.name}")
            
            try:
                # Extract metadata from this single file
                metadata = self.metadata_extractor.extract_metadata_from_file(file_path, dataset_name)
                
                if not metadata:
                    failed_count += 1
                    logger.warning(f"⚠️  Failed to extract metadata from: {file_path.name}")
                    continue
                
                # Check if metadata already exists in database
                if self.db_manager.metadata_exists(metadata['file_path']):
                    if processed_count % 100 == 0:  # Log every 100 skipped files
                        logger.info(f"ℹ️  Skipping {processed_count} files (already exist in database)")
                    skipped_count += 1
                    continue
                
                # Insert metadata into database immediately
                if self.db_manager.insert_metadata(metadata):
                    inserted_count += 1
                    # Success - no need to log every single file
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to insert metadata for: {file_path.name}")
                    logger.error(f"❌ STOPPING PROCESSING due to database insertion failure")
                    break  # Stop processing immediately
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error processing {file_path.name}: {e}")
                logger.error(f"❌ STOPPING PROCESSING due to exception")
                break  # Stop processing immediately
        
        logger.info(f"✅ Dataset '{dataset_name}' processing completed:")
        logger.info(f"   📊 Processed: {processed_count}")
        logger.info(f"   ✅ Inserted: {inserted_count}")
        logger.info(f"   ⏭️  Skipped: {skipped_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        
        return {
            'processed': processed_count,
            'inserted': inserted_count,
            'skipped': skipped_count,
            'failed': failed_count
        }
    
    def process_all_datasets(self) -> Dict[str, Any]:
        """Process metadata for all available datasets"""
        logger.info("🚀 Starting metadata processing...")
        
        # Get available datasets
        datasets = self.get_available_datasets()
        
        if not datasets:
            logger.warning("⚠️  No datasets found for processing")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"📊 Found {len(datasets)} datasets ready for processing")
        
        # Process each dataset
        success_count = 0
        failed_count = 0
        total_processed = 0
        total_inserted = 0
        
        for dataset in datasets:
            logger.info(f"\n{'='*60}")
            logger.info(f"📤 Processing: {dataset['name']}")
            logger.info(f"{'='*60}")
            
            # Process dataset
            result = self.process_dataset_metadata(dataset['path'])
            
            if result['failed'] == 0:
                success_count += 1
                logger.info(f"✅ Dataset processed successfully: {dataset['name']}")
            else:
                failed_count += 1
                logger.error(f"❌ Dataset processing failed: {dataset['name']}")
            
            # Update totals
            total_processed += result['processed']
            total_inserted += result['inserted']
            
            # Summary for this dataset
            logger.info(f"📊 Processing Summary for {dataset['name']}:")
            logger.info(f"   📊 Processed: {result['processed']}")
            logger.info(f"   ✅ Inserted: {result['inserted']}")
            logger.info(f"   ⏭️  Skipped: {result['skipped']}")
            logger.info(f"   ❌ Failed: {result['failed']}")
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("📊 OVERALL PROCESSING SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"  ✅ Successful datasets: {success_count}")
        logger.info(f"  ❌ Failed datasets: {failed_count}")
        logger.info(f"  📊 Total datasets: {len(datasets)}")
        logger.info(f"  📁 Total files processed: {total_processed}")
        logger.info(f"✅ Processing complete: {total_inserted} metadata records inserted")
        
        if self.production_mode:
            logger.info("✅ Production mode: All changes were applied")
        else:
            logger.info("⚠️  DRY RUN MODE: No actual changes were made")
            logger.info("💡 Use --pushtoprod to perform actual processing")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(datasets),
            'files_processed': total_processed,
            'metadata_inserted': total_inserted
        }

    def upload_all_datasets_to_s3(self) -> bool:
        """Upload all datasets under swift_datasets to S3 using boto (config-driven)."""
        try:
            import boto3
        except Exception as e:
            logger.error(f"❌ boto3 not available: {e}")
            return False
        # Resolve S3 configuration from centralized config
        endpoint_url = self.config.get('s3.endpoint_url')
        region_name = self.config.get('s3.region', 'us-east-1')
        path_style = self.config.get('s3.compatibility.path_style_addressing', True)
        ssl_verify = self.config.get('verify_ssl', True)
        access_key = self.config.get_secret('s3_access_key')
        secret_key = self.config.get_secret('s3_secret_key')
        # Use the raw data view path for uploads (S3 bucket name derived from view path)
        view_path = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data')
        bucket_name = view_path.lstrip('/')  # Remove leading slash for S3 bucket name
        if not endpoint_url or not access_key or not secret_key:
            logger.error("❌ Missing S3 configuration (endpoint_url/access/secret)")
            return False
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            verify=ssl_verify,
            config=boto3.session.Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path' if path_style else 'virtual'}
            )
        )
        if not self.swift_datasets_dir.exists():
            logger.warning(f"⚠️  Swift datasets directory not found: {self.swift_datasets_dir}")
            return False
        logger.info(f"📤 Uploading datasets from {self.swift_datasets_dir} to s3://{bucket_name}")
        uploaded = 0
        failed = 0
        for dataset_dir in self.swift_datasets_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
            dataset_prefix = dataset_dir.name
            for file_path in dataset_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                key = f"{dataset_prefix}/{file_path.name}"
                try:
                    s3_client.upload_file(str(file_path), bucket_name, key)
                    uploaded += 1
                    if uploaded % 100 == 0:
                        logger.info(f"📤 Uploaded {uploaded} files so far…")
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Failed to upload {file_path} -> s3://{bucket_name}/{key}: {e}")
        logger.info(f"✅ Upload complete. Uploaded={uploaded}, Failed={failed}")
        return failed == 0
    
    def show_database_stats(self) -> bool:
        """Display current database statistics"""
        try:
            logger.info("📊 Retrieving database statistics...")
            
            stats = self.db_manager.get_metadata_stats()
            
            if not stats:
                logger.warning("⚠️  No statistics available")
                return False
            
            logger.info(f"📊 Database Statistics:")
            logger.info(f"   📁 Total files: {stats.get('total_files', 0)}")
            
            if stats.get('mission_counts'):
                logger.info(f"   🚀 Missions:")
                for mission, count in stats['mission_counts'].items():
                    logger.info(f"      {mission}: {count} files")
            
            if stats.get('dataset_counts'):
                logger.info(f"   📂 Datasets:")
                for dataset, count in stats['dataset_counts'].items():
                    logger.info(f"      {dataset}: {count} files")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve database stats: {e}")
            return False
    
    def search_metadata(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata in the database with wildcard support"""
        try:
            logger.info(f"🔍 Searching metadata with criteria: {search_criteria}")
            
            # The database manager now handles both exact and wildcard searches
            results = self.db_manager.search_metadata(search_criteria)
            
            logger.info(f"🔍 Search completed: {len(results)} results found")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_latest_files(self, count: int) -> List[Dict[str, Any]]:
        """Get the N latest files by observation timestamp"""
        try:
            logger.info(f"🕒 Getting latest {count} files")
            
            results = self.db_manager.get_latest_files(count)
            
            logger.info(f"🕒 Retrieved {len(results)} latest files")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest files: {e}")
            return []
    
    def close(self):
        """Clean up resources"""
        if self.db_manager:
            self.db_manager.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Lab 2 Complete Solution: Metadata Infrastructure')
    parser.add_argument('--pushtoprod', action='store_true', help='Enable production mode (actual changes)')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--setup-only', action='store_true', help='Only set up database infrastructure')
    parser.add_argument('--process-only', action='store_true', help='Only process metadata (assumes setup is complete)')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--search', type=str, help='Search metadata (e.g., "mission_id=SWIFT,target_object=GRB*,observation_timestamp<2004-12-25") - supports wildcards: *, value*, *value, *value* and comparisons: >, <, >=, <=')
    parser.add_argument('--latest', type=int, help='Get the N latest files (e.g., --latest 10)')
    parser.add_argument('--demo-extraction', type=str, help='Demo metadata extraction from a file (e.g., --demo-extraction /path/to/file.fits)')
    parser.add_argument('--delete-schema', action='store_true', help='Delete VAST schema and recreate with new structure (DESTRUCTIVE)')
    parser.add_argument('--showapicalls', action='store_true', help='Show API calls being made (credentials obfuscated)')
    
    args = parser.parse_args()
    
    if args.pushtoprod:
        print("🚨 WARNING: PRODUCTION MODE ENABLED")
        print("This will make actual changes to your VAST Database!")
        confirm = input("Type 'YES' to confirm: ")
        
        if confirm != 'YES':
            print("❌ Production mode not confirmed. Exiting.")
            return
        
        print("✅ Production mode confirmed. Proceeding with actual changes...")
        production_mode = True
    else:
        print("⚠️  DRY RUN MODE: No actual changes will be made")
        production_mode = False
    
    try:
        # Create solution instance
        solution = Lab2CompleteSolution(config_path=args.config, production_mode=production_mode, show_api_calls=args.showapicalls)
        
        if args.stats:
            # Show database statistics
            solution.show_database_stats()
            
        elif args.search:
            # Search metadata
            # Parse search criteria (format: key1=value1,key2=value2)
            # Supports wildcards: key1=value* (starts with), key1=*value (ends with), key1=*value* (contains)
            search_criteria = {}
            criteria_pairs = args.search.split(',')
            
            for pair in criteria_pairs:
                # Check for comparison operators
                if '>=' in pair:
                    key, value = pair.split('>=', 1)
                    key = key.strip()
                    value = value.strip()
                    search_criteria[key] = {
                        'type': 'comparison',
                        'operator': '>=',
                        'value': value
                    }
                elif '<=' in pair:
                    key, value = pair.split('<=', 1)
                    key = key.strip()
                    value = value.strip()
                    search_criteria[key] = {
                        'type': 'comparison',
                        'operator': '<=',
                        'value': value
                    }
                elif '>' in pair:
                    key, value = pair.split('>', 1)
                    key = key.strip()
                    value = value.strip()
                    search_criteria[key] = {
                        'type': 'comparison',
                        'operator': '>',
                        'value': value
                    }
                elif '<' in pair:
                    key, value = pair.split('<', 1)
                    key = key.strip()
                    value = value.strip()
                    search_criteria[key] = {
                        'type': 'comparison',
                        'operator': '<',
                        'value': value
                    }
                elif '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Check for wildcard patterns
                    if '*' in value:
                        # Store wildcard pattern for special handling
                        search_criteria[key] = {
                            'type': 'wildcard',
                            'pattern': value
                        }
                    else:
                        # Exact match
                        search_criteria[key] = {
                            'type': 'exact',
                            'value': value
                        }
                else:
                    print(f"⚠️  Invalid search criteria format: {pair}")
                    print("💡 Use format: key1=value1,key2=value2")
                    print("💡 Wildcards supported: key1=value*, key1=*value, key1=*value*")
                    print("💡 Comparisons supported: key1>value1, key1<value1, key1>=value1, key1<=value1")
                    sys.exit(1)
            
            results = solution.search_metadata(search_criteria)
            
            if results:
                print(f"\n🔍 Search Results ({len(results)} found):")
                for i, result in enumerate(results[:10], 1):  # Show first 10
                    file_name = result.get('file_name', 'Unknown')
                    mission_id = result.get('mission_id', 'Unknown')
                    target_object = result.get('target_object', 'Unknown')
                    file_size = result.get('file_size_bytes', 0)
                    observation_time = result.get('observation_timestamp', 'Unknown')
                    
                    print(f"{i}. {file_name}")
                    print(f"   Mission: {mission_id} | Object: {target_object}")
                    print(f"   Observed: {observation_time}")
                    
                    if file_size and file_size > 0:
                        if file_size >= 1024 * 1024:  # >= 1 MB
                            size_mb = file_size / (1024 * 1024)
                            print(f"   Size: {size_mb:.1f} MB")
                        elif file_size >= 1024:  # >= 1 KB
                            size_kb = file_size / 1024
                            print(f"   Size: {size_kb:.1f} KB")
                        else:
                            print(f"   Size: {file_size} bytes")
                    else:
                        print(f"   Size: 0.0 MB (file_size_bytes is {file_size})")
                
                if len(results) > 10:
                    print(f"... and {len(results) - 10} more results")
            else:
                print("🔍 No search results found")
                
        elif args.latest:
            # Get the N latest files
            results = solution.get_latest_files(args.latest)
            
            if results:
                print(f"\n🕒 Latest {len(results)} Files:")
                for i, result in enumerate(results, 1):
                    file_name = result.get('file_name', 'Unknown')
                    mission_id = result.get('mission_id', 'Unknown')
                    target_object = result.get('target_object', 'Unknown')
                    file_size = result.get('file_size_bytes', 0)
                    observation_time = result.get('observation_timestamp', 'Unknown')
                    
                    print(f"{i}. {file_name}")
                    print(f"   Mission: {mission_id} | Object: {target_object}")
                    print(f"   Observed: {observation_time}")
                    
                    if file_size and file_size > 0:
                        if file_size >= 1024 * 1024:  # >= 1 MB
                            size_mb = file_size / (1024 * 1024)
                            print(f"   Size: {size_mb:.1f} MB")
                        elif file_size >= 1024:  # >= 1 KB
                            size_kb = file_size / 1024
                            print(f"   Size: {size_kb:.1f} KB")
                        else:
                            print(f"   Size: {file_size} bytes")
                    else:
                        print(f"   Size: 0.0 MB (file_size_bytes is {file_size})")
            else:
                print("🕒 No files found")
                
        elif args.demo_extraction:
            # Demo metadata extraction from a file
            print(f"\n🔬 Metadata Extraction Demo")
            print(f"📁 File: {args.demo_extraction}")
            print("=" * 60)
            
            try:
                # Check file size first
                import os
                file_size = os.path.getsize(args.demo_extraction)
                
                if file_size == 0:
                    print("⚠️  File is empty (0 bytes) - cannot extract metadata")
                    print("💡 This is common in datasets where some files failed to download or are placeholders")
                    return
                
                # Extract metadata from the specified file
                metadata = solution.metadata_extractor.extract_metadata_from_file(args.demo_extraction)
                
                if metadata:
                    print("✅ Successfully extracted metadata:")
                    print()
                    
                    # Display metadata in a nice format
                    for key, value in metadata.items():
                        if value is not None and value != '':
                            # Format the key nicely
                            display_key = key.replace('_', ' ').title()
                            print(f"📋 {display_key}: {value}")
                    
                    print()
                    print(f"📊 Total metadata fields: {len([k for k, v in metadata.items() if v is not None and v != ''])}")
                else:
                    print("❌ Failed to extract metadata from file")
                    print("💡 This could be due to:")
                    print("   - File format not supported")
                    print("   - Corrupted file")
                    print("   - Missing required libraries (astropy)")
                    
            except Exception as e:
                print(f"❌ Error during metadata extraction: {e}")
                
        elif args.delete_schema:
            # Delete VAST schema and recreate with new structure
            if not args.pushtoprod:
                print("❌ ERROR: --delete-schema requires --pushtoprod flag for safety")
                return 1
            
            print("🗑️  Deleting VAST schema and recreating with new structure...")
            if solution.db_manager.delete_vast_schema():
                print("✅ VAST schema deleted successfully")
                print("🔧 Recreating schema with new structure...")
                if solution.setup_database_infrastructure():
                    print("✅ Database infrastructure recreated successfully")
                else:
                    print("❌ Database infrastructure recreation failed")
                    return 1
            else:
                print("❌ VAST schema deletion failed")
                return 1
                
        elif args.setup_only:
            # Only set up database infrastructure
            if solution.setup_database_infrastructure():
                print("✅ Database infrastructure setup completed successfully")
            else:
                print("❌ Database infrastructure setup failed")
                return 1
                
        elif args.process_only:
            # Only process metadata (assumes setup is complete)
            result = solution.process_all_datasets()
            if result['failed'] == 0:
                print("✅ Metadata processing completed successfully")
            else:
                print(f"⚠️  Metadata processing completed with {result['failed']} failures")
                
        else:
            # Full solution: setup + upload + process
            print("🔧 Setting up database infrastructure...")
            if not solution.setup_database_infrastructure():
                print("❌ Database infrastructure setup failed")
                return 1
            
            print("📤 Uploading datasets to S3...")
            if not solution.upload_all_datasets_to_s3():
                print("❌ Dataset upload failed")
                return 1
            
            print("📊 Processing metadata...")
            result = solution.process_all_datasets()
            
            if result['failed'] == 0:
                print("🎉 Lab 2 solution completed successfully!")
            else:
                print(f"⚠️  Lab 2 solution completed with {result['failed']} failures")
        
    except Exception as e:
        logger.error(f"❌ Lab 2 solution failed: {e}")
        return 1
    finally:
        if 'solution' in locals():
            solution.close()
    
    return 0

if __name__ == "__main__":
    exit(main())

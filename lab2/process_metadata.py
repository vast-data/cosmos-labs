#!/usr/bin/env python3
"""
Lab 2 Metadata Processing
Processes metadata from S3-uploaded datasets and stores in VAST Database
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader
from lab2.vast_database_manager import VASTDatabaseManager
from lab2.swift_metadata_extractor import SwiftMetadataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetadataProcessor:
    """Handles S3-based metadata processing and storage"""
    
    def __init__(self, config_path: str = None, secrets_path: str = None):
        # Default to parent directory for config files
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config.yaml")
        if secrets_path is None:
            secrets_path = str(Path(__file__).parent.parent / "secrets.yaml")
        self.config = ConfigLoader(config_path, secrets_path)
        self.db_manager = VASTDatabaseManager(self.config)
        self.extractor = SwiftMetadataExtractor(self.config)
    
    def process_all_datasets(self) -> Dict[str, Any]:
        """Process metadata for all available datasets from S3"""
        logger.info("🚀 Starting metadata processing from S3...")
        
        # Get available datasets from S3
        datasets = self.get_available_datasets_from_s3()
        
        if not datasets:
            logger.warning("⚠️  No datasets found in S3 for processing")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"📊 Found {len(datasets)} datasets ready for processing from S3")
        
        # Process each dataset
        success_count = 0
        failed_count = 0
        total_processed = 0
        total_inserted = 0
        
        for dataset in datasets:
            logger.info(f"\n{'='*60}")
            logger.info(f"📤 Processing: {dataset['name']}")
            logger.info(f"{'='*60}")
            
            # Process dataset from S3
            result = self.process_dataset_metadata_from_s3(dataset['name'])
            
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
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(datasets),
            'files_processed': total_processed,
            'metadata_inserted': total_inserted
        }
    
    def get_available_datasets_from_s3(self) -> List[Dict[str, Any]]:
        """Get list of available Swift datasets from S3"""
        try:
            import boto3
            
            # Get S3 configuration
            endpoint_url = self.config.get('s3.endpoint_url')
            access_key = self.config.get_secret('s3_access_key')
            secret_key = self.config.get_secret('s3_secret_key')
            region_name = self.config.get('s3.region', 'us-east-1')
            
            if not endpoint_url or not access_key or not secret_key:
                logger.error("❌ Missing S3 configuration for dataset discovery")
                return []
            
            # Get bucket name from view path
            view_path = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data')
            bucket_name = view_path.lstrip('/').replace('/', '-')
            
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name
            )
            
            logger.info(f"🔍 Scanning S3 bucket: s3://{bucket_name}")
            
            # List objects with prefix to get dataset directories
            datasets = {}
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix in page['CommonPrefixes']:
                        dataset_name = prefix['Prefix'].rstrip('/')
                        if dataset_name:  # Skip empty prefixes
                            datasets[dataset_name] = {
                                'name': dataset_name,
                                'path': f"s3://{bucket_name}/{dataset_name}",
                                'file_count': 0,
                                'size_gb': 0
                            }
            
            # Count files and calculate sizes for each dataset
            for dataset_name in datasets:
                file_count = 0
                total_size = 0
                
                for page in paginator.paginate(Bucket=bucket_name, Prefix=f"{dataset_name}/"):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            if not obj['Key'].endswith('/'):  # Skip directory markers
                                file_count += 1
                                total_size += obj['Size']
                
                datasets[dataset_name]['file_count'] = file_count
                datasets[dataset_name]['size_gb'] = round(total_size / (1024**3), 2)
            
            dataset_list = list(datasets.values())
            return sorted(dataset_list, key=lambda x: x['size_gb'], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to scan S3 for datasets: {e}")
            return []
    
    def process_dataset_metadata_from_s3(self, dataset_name: str) -> Dict[str, Any]:
        """Process metadata for a dataset from S3"""
        try:
            import boto3
            
            # Get S3 configuration
            endpoint_url = self.config.get('s3.endpoint_url')
            access_key = self.config.get_secret('s3_access_key')
            secret_key = self.config.get_secret('s3_secret_key')
            region_name = self.config.get('s3.region', 'us-east-1')
            
            if not endpoint_url or not access_key or not secret_key:
                logger.error("❌ Missing S3 configuration for metadata processing")
                return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
            
            # Get bucket name from view path
            view_path = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data')
            bucket_name = view_path.lstrip('/').replace('/', '-')
            
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name
            )
            
            logger.info(f"📊 Processing dataset from S3: {dataset_name}")
            logger.info(f"   S3 Path: s3://{bucket_name}/{dataset_name}")
            
            # List all files in the dataset
            files = []
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name, Prefix=f"{dataset_name}/"):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if not obj['Key'].endswith('/'):  # Skip directory markers
                            files.append({
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'last_modified': obj['LastModified']
                            })
            
            logger.info(f"📊 Found {len(files)} files to process")
            
            if not files:
                logger.warning(f"⚠️  No files found in dataset: {dataset_name}")
                return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
            
            # Process files
            processed = 0
            inserted = 0
            skipped = 0
            failed = 0
            
            for i, file_info in enumerate(files, 1):
                if i % 10 == 0 or i == len(files):
                    logger.info(f"🔧 Processing file {i}/{len(files)}: {file_info['key'].split('/')[-1]}")
                
                try:
                    # Download file temporarily for processing
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.gz')
                    s3_client.download_file(bucket_name, file_info['key'], temp_file.name)
                    
                    # Process the file
                    metadata = self.extract_file_metadata(temp_file.name, file_info['key'])
                    
                    if metadata:
                        # Insert metadata into database
                        if self.db_manager.insert_metadata(metadata):
                            inserted += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1
                    
                    processed += 1
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process {file_info['key']}: {e}")
                    failed += 1
                    processed += 1
            
            return {
                'processed': processed,
                'inserted': inserted,
                'skipped': skipped,
                'failed': failed
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process dataset from S3: {e}")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
    
    def extract_file_metadata(self, file_path: str, s3_key: str) -> Dict[str, Any]:
        """Extract metadata from a file and prepare for database insertion"""
        try:
            # Extract dataset name from S3 key (first part before first slash)
            dataset_name = s3_key.split('/')[0] if '/' in s3_key else 'unknown'
            
            # Extract metadata using the Swift metadata extractor
            metadata = self.extractor.extract_metadata_from_file(file_path, dataset_name)
            
            if not metadata:
                return None
            
            # Add S3-specific information
            metadata['s3_key'] = s3_key
            metadata['s3_bucket'] = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data').lstrip('/').replace('/', '-')
            metadata['file_size'] = os.path.getsize(file_path)
            metadata['extraction_timestamp'] = self.extractor.get_current_timestamp()
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to extract metadata from {file_path}: {e}")
            return None

def main():
    """Main entry point for metadata processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process metadata from S3 datasets')
    parser.add_argument('--config', default=None, help='Config file path (default: ../config.yaml)')
    parser.add_argument('--secrets', default=None, help='Secrets file path (default: ../secrets.yaml)')
    parser.add_argument('--dataset', help='Process specific dataset only')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')
    
    args = parser.parse_args()
    
    processor = MetadataProcessor(args.config, args.secrets)
    
    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE: No actual changes will be made")
        logger.info("🔍 Testing connections and checking available datasets...")
        
        # Test database connection
        try:
            logger.info("🔧 Testing VAST Database connection...")
            if processor.db_manager.connect():
                logger.info("✅ VAST Database connection successful")
                processor.db_manager.close()
            else:
                logger.error("❌ VAST Database connection failed")
                return False
        except Exception as e:
            logger.error(f"❌ VAST Database connection failed: {e}")
            return False
        
        # Test S3 connection and list available datasets
        try:
            logger.info("🔧 Testing S3 connection and scanning for datasets...")
            datasets = processor.get_available_datasets_from_s3()
            logger.info(f"✅ Found {len(datasets)} datasets in S3")
            
            if datasets:
                logger.info("📁 Available datasets:")
                for dataset in datasets:
                    dataset_name = dataset.get('dataset_name', 'Unknown')
                    file_count = dataset.get('file_count', 0)
                    logger.info(f"   - {dataset_name}: {file_count} files")
            else:
                logger.info("ℹ️  No datasets found in S3 (upload datasets first)")
            
        except Exception as e:
            logger.error(f"❌ S3 connection or dataset scanning failed: {e}")
            return False
        
        logger.info("✅ Dry-run validation completed successfully")
        logger.info("💡 All connections working, metadata processing would succeed")
        return True
    
    if args.dataset:
        # Process specific dataset
        result = processor.process_dataset_metadata_from_s3(args.dataset)
        logger.info(f"📊 Dataset processing complete: {result}")
    else:
        # Process all datasets
        result = processor.process_all_datasets()
        if result['failed'] == 0:
            logger.info("✅ All datasets processed successfully")
            sys.exit(0)
        else:
            logger.error(f"❌ {result['failed']} datasets failed to process")
            sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Lab 2 Dataset Upload
Uploads Swift datasets to S3 using boto3
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatasetUploader:
    """Handles uploading Swift datasets to S3"""
    
    def __init__(self, config_path: str = None, secrets_path: str = None):
        # Default to parent directory for config files
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config.yaml")
        if secrets_path is None:
            secrets_path = str(Path(__file__).parent.parent / "secrets.yaml")
        self.config = ConfigLoader(config_path, secrets_path)
        self.swift_datasets_dir = Path(__file__).parent.parent / "scripts" / "swift_datasets"
    
    def upload_all_datasets(self) -> bool:
        """Upload all datasets under swift_datasets to S3 using boto3"""
        try:
            import boto3
            
            # Get S3 configuration
            endpoint_url = self.config.get('s3.endpoint_url')
            region_name = self.config.get('s3.region', 'us-east-1')
            path_style = self.config.get('s3.compatibility.path_style_addressing', True)
            ssl_verify = self.config.get('s3.verify_ssl', True)
            access_key = self.config.get_secret('s3_access_key')
            secret_key = self.config.get_secret('s3_secret_key')
            
            # Use the raw data view path for uploads (S3 bucket name derived from view path)
            view_path = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data')
            # Convert view path to valid S3 bucket name by removing slashes and using last part
            bucket_name = view_path.lstrip('/').replace('/', '-')
            
            if not endpoint_url or not access_key or not secret_key:
                logger.error("❌ Missing S3 configuration (endpoint_url/access/secret)")
                return False
            
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name,
                use_ssl=ssl_verify
            )
            
            if not self.swift_datasets_dir.exists():
                logger.warning(f"⚠️  Swift datasets directory not found: {self.swift_datasets_dir}")
                return False
            
            logger.info(f"📤 Uploading datasets from {self.swift_datasets_dir} to s3://{bucket_name}")
            
            uploaded_count = 0
            failed_count = 0
            
            for dataset_dir in self.swift_datasets_dir.iterdir():
                if dataset_dir.is_dir():
                    logger.info(f"📁 Processing dataset: {dataset_dir.name}")
                    
                    for file_path in dataset_dir.rglob('*'):
                        if file_path.is_file():
                            # Create S3 key preserving directory structure
                            relative_path = file_path.relative_to(self.swift_datasets_dir)
                            key = str(relative_path).replace('\\', '/')  # Ensure forward slashes
                            
                            try:
                                s3_client.upload_file(str(file_path), bucket_name, key)
                                uploaded_count += 1
                                
                                if uploaded_count % 100 == 0:
                                    logger.info(f"📤 Uploaded {uploaded_count} files so far…")
                                    
                            except Exception as e:
                                logger.error(f"❌ Failed to upload {file_path} -> s3://{bucket_name}/{key}: {e}")
                                failed_count += 1
            
            logger.info(f"✅ Upload complete. Uploaded={uploaded_count}, Failed={failed_count}")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    def list_uploaded_datasets(self) -> list:
        """List datasets that have been uploaded to S3"""
        try:
            import boto3
            
            # Get S3 configuration
            endpoint_url = self.config.get('s3.endpoint_url')
            access_key = self.config.get_secret('s3_access_key')
            secret_key = self.config.get_secret('s3_secret_key')
            region_name = self.config.get('s3.region', 'us-east-1')
            
            if not endpoint_url or not access_key or not secret_key:
                logger.error("❌ Missing S3 configuration")
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
            
            # List datasets (top-level prefixes)
            datasets = []
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix in page['CommonPrefixes']:
                        dataset_name = prefix['Prefix'].rstrip('/')
                        if dataset_name:
                            datasets.append(dataset_name)
            
            return sorted(datasets)
            
        except Exception as e:
            logger.error(f"❌ Failed to list datasets: {e}")
            return []

def main():
    """Main entry point for dataset upload"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload Swift datasets to S3')
    parser.add_argument('--config', default=None, help='Config file path (default: ../config.yaml)')
    parser.add_argument('--secrets', default=None, help='Secrets file path (default: ../secrets.yaml)')
    parser.add_argument('--list', action='store_true', help='List uploaded datasets')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')
    
    args = parser.parse_args()
    
    uploader = DatasetUploader(args.config, args.secrets)
    
    if args.list:
        datasets = uploader.list_uploaded_datasets()
        if datasets:
            logger.info(f"📁 Found {len(datasets)} uploaded datasets:")
            for dataset in datasets:
                logger.info(f"  - {dataset}")
        else:
            logger.info("📁 No datasets found in S3")
        return
    
    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE: No actual changes will be made")
        logger.info("💡 Dataset upload would be performed")
        return
    
    if uploader.upload_all_datasets():
        logger.info("✅ Dataset upload completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Dataset upload failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple S3 upload script for VAST Data Platform
Based on VAST Data boto3 documentation
"""

import boto3
import logging
import os
import sys
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError


# Fix for modern boto3 versions - only calculate checksums when required
# This prevents problematic headers that VAST S3 doesn't support
os.environ['AWS_REQUEST_CHECKSUM_CALCULATION'] = 'when_required'

# Add parent directory to path for config imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config_loader import ConfigLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the root directory and have installed dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SwiftUploader:
    """Simple S3 uploader for Swift datasets to VAST Data Platform"""
    
    def __init__(self, config_path: str = None):
        """Initialize the S3 uploader with configuration"""
        
        # Load configuration
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = str(project_root / "config.yaml")
            secrets_path = str(project_root / "secrets.yaml")
        
        self.config = ConfigLoader(config_path, secrets_path)
        
        # Get upload configuration
        # Note: We don't need raw_data_path for S3 uploads - that's for VAST file system
        self.swift_datasets_dir = Path(__file__).parent / "swift_datasets"
        
        # S3 configuration
        self.s3_config = self._get_s3_config()
        
        logger.info(f"✅ Configuration loaded successfully")
        logger.info(f"📁 Swift datasets directory: {self.swift_datasets_dir}")
        logger.info(f"🌐 S3 endpoint: {self.s3_config.get('endpoint_url', 'Default AWS')}")
        logger.info(f"📦 S3 bucket: {self.s3_config.get('bucket', 'Default')}")
        
        # Initialize S3 client
        self.s3_client = self._initialize_s3_client()
    
    def _get_s3_config(self) -> dict:
        """Get S3 configuration from config and secrets"""
        s3_config = {}
        
        # Get S3 settings from config
        if self.config.get('s3'):
            s3_config.update(self.config.get('s3'))
        
        # Add credentials from secrets
        if self.config.get_secret('s3_access_key'):
            s3_config['aws_access_key_id'] = self.config.get_secret('s3_access_key')
        if self.config.get_secret('s3_secret_key'):
            s3_config['aws_secret_access_key'] = self.config.get_secret('s3_secret_key')
        
        # S3 bucket and prefix
        s3_config['bucket'] = self.config.get('s3.bucket', 'cosmos-lab-raw')
        s3_config['prefix'] = "swift"
        
        # Validate that credentials were loaded
        if not s3_config.get('aws_access_key_id'):
            raise ValueError("S3 access key not found in secrets.yaml")
        if not s3_config.get('aws_secret_access_key'):
            raise ValueError("S3 secret key not found in secrets.yaml")
        if not s3_config.get('endpoint_url'):
            raise ValueError("S3 endpoint URL not found in config.yaml")
        
        return s3_config
    
    def _initialize_s3_client(self):
        """Initialize the S3 client with VAST-compatible configuration"""
        try:
            # Validate required S3 configuration
            required_keys = ['endpoint_url', 'aws_access_key_id', 'aws_secret_access_key', 'bucket']
            missing_keys = [key for key in required_keys if not self.s3_config.get(key)]
            
            if missing_keys:
                raise ValueError(f"Missing required S3 configuration: {missing_keys}")
            
            # Create S3 client with VAST-recommended configuration
            s3_client = boto3.client(
                's3',
                use_ssl=False,
                endpoint_url=self.s3_config['endpoint_url'],
                aws_access_key_id=self.s3_config['aws_access_key_id'],
                aws_secret_access_key=self.s3_config['aws_secret_access_key'],
                region_name='us-east-1',
                config=boto3.session.Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'path'}
                )
            )
            
            # Test connection
            s3_client.head_bucket(Bucket=self.s3_config['bucket'])
            logger.info(f"✅ S3 client initialized successfully")
            logger.info(f"📦 Connected to bucket: {self.s3_config['bucket']}")
            
            return s3_client
            
        except NoCredentialsError:
            logger.error("❌ S3 credentials not found")
            logger.error("💡 Check your secrets.yaml file for s3_access_key and s3_secret_key")
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"❌ S3 bucket not found: {self.s3_config['bucket']}")
            elif error_code == '403':
                logger.error(f"❌ Access denied to bucket: {self.s3_config['bucket']}")
            else:
                logger.error(f"❌ S3 connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ S3 client initialization failed: {e}")
            raise
    
    def get_available_datasets(self) -> list:
        """Get list of available Swift datasets for upload"""
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
    
    def upload_file_s3(self, local_file: Path, s3_key: str, dry_run: bool = True) -> bool:
        """Upload a single file to S3 using boto3 (with modern boto3 compatibility fix)"""
        try:
            file_size_mb = local_file.stat().st_size / (1024**2)
            
            if dry_run:
                logger.info(f"📤 [DRY RUN] Would upload: {local_file.name} ({file_size_mb:.2f} MB)")
                return True
            
            logger.info(f"📤 Uploading: {local_file.name} ({file_size_mb:.2f} MB)")
            
            # Upload using boto3 put_object (should work with AWS_REQUEST_CHECKSUM_CALCULATION fix)
            with open(local_file, 'rb') as file_data:
                self.s3_client.put_object(
                    Bucket=self.s3_config['bucket'],
                    Key=s3_key,
                    Body=file_data
                )
            logger.info(f"✅ Successfully uploaded: {local_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_file.name}: {e}")
            return False
    
    def upload_dataset_s3(self, dataset_path: str, dry_run: bool = True) -> dict:
        """Upload a single dataset to S3"""
        dataset_name = Path(dataset_path).name
        s3_prefix = f"{self.s3_config['prefix']}/{dataset_name}"
        
        logger.info(f"📤 Uploading dataset: {dataset_name}")
        logger.info(f"   From: {dataset_path}")
        logger.info(f"   To S3: s3://{self.s3_config['bucket']}/{s3_prefix}/")
        
        # Get all files in the dataset
        dataset_files = list(Path(dataset_path).rglob('*'))
        data_files = [f for f in dataset_files if f.is_file()]
        
        logger.info(f"📊 Dataset contains {len(data_files)} files")
        
        if dry_run:
            logger.info("⚠️  DRY RUN MODE: No actual uploads performed")
            return {'uploaded': 0, 'failed': 0, 'total': len(data_files)}
        
        # PRODUCTION MODE: Actually upload files
        logger.info(f"🚨 PRODUCTION MODE: Starting actual upload of {len(data_files)} files")
        
        uploaded_count = 0
        failed_count = 0
        
        for file_path in data_files:
            try:
                # Create S3 key (path in S3)
                relative_path = file_path.relative_to(dataset_path)
                s3_key = f"{s3_prefix}/{relative_path}"
                
                # Upload file
                if self.upload_file_s3(file_path, s3_key, dry_run=False):
                    uploaded_count += 1
                else:
                    failed_count += 1
                

                
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                failed_count += 1
        
        return {
            'uploaded': uploaded_count,
            'failed': failed_count,
            'total': len(data_files)
        }
    
    def upload_all_datasets(self, dry_run: bool = True) -> dict:
        """Upload all available Swift datasets"""
        logger.info("🚀 Starting Swift datasets upload process")
        
        # Get available datasets
        datasets = self.get_available_datasets()
        
        if not datasets:
            logger.warning("⚠️  No datasets found for upload")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"📊 Found {len(datasets)} datasets ready for upload")
        
        # Upload each dataset
        success_count = 0
        failed_count = 0
        
        for dataset in datasets:
            logger.info(f"\n{'='*60}")
            logger.info(f"📤 Processing: {dataset['name']}")
            logger.info(f"{'='*60}")
            
            # Upload dataset
            result = self.upload_dataset_s3(dataset['path'], dry_run=dry_run)
            
            if result['failed'] == 0:
                success_count += 1
                logger.info(f"✅ Dataset processed successfully: {dataset['name']}")
            else:
                failed_count += 1
                logger.error(f"❌ Dataset processing failed: {dataset['name']}")
            
            # Summary for this dataset
            logger.info(f"📊 Upload Summary for {dataset['name']}:")
            logger.info(f"  ✅ Successfully uploaded: {result['uploaded']}")
            logger.info(f"  ❌ Failed: {result['failed']}")
            logger.info(f"  📊 Total: {result['total']}")
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("📊 OVERALL UPLOAD SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"  ✅ Successful datasets: {success_count}")
        logger.info(f"  ❌ Failed datasets: {failed_count}")
        logger.info(f"  📊 Total datasets: {len(datasets)}")
        
        if dry_run:
            logger.info("⚠️  This was a DRY RUN - no actual uploads were performed")
            logger.info("💡 Use --pushtoprod to perform actual uploads")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(datasets)
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload Swift datasets to VAST Data Platform via S3')
    parser.add_argument('--pushtoprod', action='store_true', help='Enable production mode (actual uploads)')
    parser.add_argument('--config', type=str, help='Path to config file')
    
    args = parser.parse_args()
    
    if args.pushtoprod:
        print("🚨 WARNING: PRODUCTION MODE ENABLED")
        print("This will perform actual S3 uploads to your VAST system!")
        confirm = input("Type 'YES' to confirm: ")
        
        if confirm != 'YES':
            print("❌ Production mode not confirmed. Exiting.")
            return
        
        print("✅ Production mode confirmed. Proceeding with actual S3 uploads...")
        dry_run = False
    else:
        print("⚠️  DRY RUN MODE: No actual uploads will be performed")
        dry_run = True
    
    try:
        # Create uploader and upload all datasets
        uploader = SwiftUploader(config_path=args.config)
        result = uploader.upload_all_datasets(dry_run=dry_run)
        
        if result['failed'] == 0:
            print(f"🎉 Upload process completed successfully!")
        else:
            print(f"⚠️  Upload process completed with {result['failed']} failures")
            
    except Exception as e:
        logger.error(f"❌ S3 upload process failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

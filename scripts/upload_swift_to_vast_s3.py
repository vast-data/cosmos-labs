#!/usr/bin/env python3
"""
Swift Dataset S3 Upload Script for VAST Data Platform
Actually uploads files using S3 multipart uploads
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import time
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add parent directory to path for config imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config_loader import ConfigLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the root directory and have installed dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('swift_s3_upload.log')
    ]
)
logger = logging.getLogger(__name__)

class SwiftS3Uploader:
    """Handles S3-based upload of Swift datasets to VAST Data Platform"""
    
    def __init__(self, config_path: str = None, production_mode: bool = False):
        """Initialize the S3 uploader with configuration"""
        self.production_mode = production_mode
        
        # Load configuration
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = str(project_root / "config.yaml")
            secrets_path = str(project_root / "secrets.yaml")
        
        self.config = ConfigLoader(config_path, secrets_path)
        
        # Get upload configuration
        self.raw_data_path = self.config.get_data_directories()[0]  # First directory is raw data
        self.swift_datasets_dir = Path(__file__).parent / "swift_datasets"
        
        # S3 configuration
        self.s3_config = self._get_s3_config()
        
        logger.info(f"✅ Configuration loaded successfully")
        logger.info(f"📁 Raw data view: {self.raw_data_path}")
        logger.info(f"📁 Swift datasets directory: {self.swift_datasets_dir}")
        logger.info(f"🌐 S3 endpoint: {self.s3_config.get('endpoint_url', 'Default AWS')}")
        
        # Initialize S3 client
        self.s3_client = self._initialize_s3_client()
    
    def _get_s3_config(self) -> dict:
        """Get S3 configuration from config and secrets"""
        s3_config = {}
        
        # Try to get S3 settings from config
        if self.config.get('s3'):
            s3_config.update(self.config.get('s3'))
        
        # Add credentials from secrets
        if self.config.get_secret('s3_access_key'):
            s3_config['aws_access_key_id'] = self.config.get_secret('s3_access_key')
        if self.config.get_secret('s3_secret_key'):
            s3_config['aws_secret_access_key'] = self.config.get_secret('s3_secret_key')
        
        # Use environment variables as fallback
        if not s3_config.get('aws_access_key_id'):
            s3_config['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
        if not s3_config.get('aws_secret_access_key'):
            s3_config['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # S3 bucket and prefix
        s3_config['bucket'] = self.config.get('s3.bucket', 'cosmos-lab-raw')
        s3_config['prefix'] = f"swift"
        
        # Use explicitly configured S3 endpoint if provided
        if self.config.get('s3.endpoint_url'):
            s3_config['endpoint_url'] = self.config.get('s3.endpoint_url')
            logger.info(f"🔧 Using configured S3 endpoint: {s3_config['endpoint_url']}")
        else:
            # Fallback: use default endpoint (avoid recursion)
            s3_config['endpoint_url'] = "http://localhost:9000"
            logger.info(f"🔧 Using fallback S3 endpoint: {s3_config['endpoint_url']}")
        
        return s3_config
    
    def _initialize_s3_client(self):
        """Initialize the S3 client"""
        try:
            logger.info(f"🔧 Creating S3 client...")
            logger.info(f"   Endpoint: {self.s3_config.get('endpoint_url', 'Default AWS')}")
            logger.info(f"   Bucket: {self.s3_config['bucket']}")
            logger.info(f"   Access Key: {self.s3_config['aws_access_key_id'][:8]}...")
            
            # Test basic network connectivity first
            if self.s3_config.get('endpoint_url'):
                endpoint = self.s3_config['endpoint_url']
                logger.info(f"🔧 Testing network connectivity to: {endpoint}")
                
                try:
                    import socket
                    from urllib.parse import urlparse
                    
                    parsed = urlparse(endpoint)
                    host = parsed.hostname
                    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                    
                    # Test DNS resolution first
                    logger.info(f"🔧 Testing DNS resolution for: {host}")
                    try:
                        # Try to resolve hostname
                        resolved_ip = socket.gethostbyname(host)
                        logger.info(f"✅ DNS resolution successful: {host} -> {resolved_ip}")
                    except socket.gaierror as dns_error:
                        logger.warning(f"⚠️  DNS resolution failed for {host}: {dns_error}")
                        logger.warning(f"💡 This might be a DNS configuration issue")
                        
                        # Try alternative DNS resolution if configured
                        if self.s3_config.get('dns', {}).get('servers'):
                            logger.info(f"🔧 Trying custom DNS servers...")
                            for dns_server in self.s3_config['dns']['servers']:
                                try:
                                    # This is a simplified approach - in practice you'd need a custom resolver
                                    logger.info(f"   Trying DNS server: {dns_server}")
                                except Exception as alt_dns_error:
                                    logger.warning(f"   Failed with {dns_server}: {alt_dns_error}")
                    
                    logger.info(f"🔧 Testing connection to {host}:{port}")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)  # 5 second timeout
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        logger.info(f"✅ Network connectivity test passed")
                    else:
                        logger.warning(f"⚠️  Network connectivity test failed (error code: {result})")
                        logger.warning(f"💡 This might indicate network issues")
                        
                except Exception as net_error:
                    logger.warning(f"⚠️  Could not test network connectivity: {net_error}")
            
            # Create S3 client with custom endpoint if specified
            if self.s3_config.get('endpoint_url'):
                logger.info(f"🔧 Using custom S3 endpoint: {self.s3_config['endpoint_url']}")
                # Create custom session with DNS configuration
                session = boto3.Session()
                
                # Create S3 client with custom endpoint and DNS settings
                s3_client = session.client(
                    's3',
                    endpoint_url=self.s3_config['endpoint_url'],
                    aws_access_key_id=self.s3_config['aws_access_key_id'],
                    aws_secret_access_key=self.s3_config['aws_secret_access_key'],
                    verify=self.s3_config.get('verify_ssl', False),  # SSL verification (for HTTPS)
                    use_ssl=self.s3_config.get('use_ssl', False),   # Use SSL/TLS encryption
                    config=boto3.session.Config(
                        connect_timeout=self.s3_config.get('connect_timeout', 10),  # Use config setting
                        read_timeout=self.s3_config.get('read_timeout', 30),       # Use config setting
                        retries={'max_attempts': self.s3_config.get('max_attempts', 1)},  # Use config setting
                        # Custom DNS configuration
                        user_agent_extra='CustomDNS',
                        # You can also set custom DNS through environment variables
                        # AWS_DNS_SERVER or custom DNS resolution
                    )
                )
            else:
                # Use default AWS S3
                logger.info(f"🔧 Using default AWS S3 endpoint")
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.s3_config['aws_access_key_id'],
                    aws_secret_access_key=self.s3_config['aws_secret_access_key']
                )
            
            logger.info(f"🔧 S3 client created, testing connection...")
            logger.info(f"🔧 Testing bucket access: {self.s3_config['bucket']}")
            
            # Test connection with timeout
            try:
                s3_client.head_bucket(Bucket=self.s3_config['bucket'])
                logger.info(f"✅ S3 client initialized successfully")
                logger.info(f"📦 Connected to bucket: {self.s3_config['bucket']}")
            except Exception as bucket_error:
                logger.error(f"❌ Failed to access bucket {self.s3_config['bucket']}: {bucket_error}")
                logger.error(f"💡 This could mean:")
                logger.error(f"   - The bucket doesn't exist")
                logger.error(f"   - The endpoint is not responding")
                logger.error(f"   - Network connectivity issues")
                logger.error(f"   - Invalid credentials")
                raise
            
            return s3_client
            
        except NoCredentialsError:
            logger.error("❌ S3 credentials not found")
            logger.error("💡 Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            raise
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"❌ S3 bucket not found: {self.s3_config['bucket']}")
            else:
                logger.error(f"❌ S3 connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during S3 client initialization: {e}")
            logger.error(f"💡 Check your network connection and S3 endpoint configuration")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
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
                logger.info(f"📁 Found dataset directory: {dataset_dir.name}")
                
                # Get all files in the dataset
                all_files = list(dataset_dir.rglob('*'))
                data_files = [f for f in all_files if f.is_file()]
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in data_files)
                total_size_gb = total_size / (1024**3)
                
                # Show file breakdown by type
                file_extensions = {}
                for file_path in data_files:
                    ext = file_path.suffix.lower()
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
                logger.info(f"   📊 Dataset: {dataset_dir.name}")
                logger.info(f"   📁 Total files: {len(data_files)}")
                logger.info(f"   💾 Total size: {total_size_gb:.2f} GB")
                
                # Show file type breakdown
                if file_extensions:
                    logger.info(f"   📋 File types:")
                    for ext, count in sorted(file_extensions.items()):
                        ext_display = ext if ext else "no extension"
                        logger.info(f"      {ext_display}: {count} files")
                
                # Show sample files (first 5)
                if data_files:
                    logger.info(f"   📄 Sample files:")
                    for file_path in data_files[:5]:
                        file_size_mb = file_path.stat().st_size / (1024**2)
                        relative_path = file_path.relative_to(dataset_dir)
                        logger.info(f"      {relative_path} ({file_size_mb:.2f} MB)")
                    
                    if len(data_files) > 5:
                        logger.info(f"      ... and {len(data_files) - 5} more files")
                
                datasets.append({
                    'name': dataset_dir.name,
                    'path': str(dataset_dir),
                    'size_gb': round(total_size_gb, 2),
                    'file_count': len(data_files),
                    'file_extensions': file_extensions
                })
                
                logger.info(f"   ✅ Dataset {dataset_dir.name} ready for upload")
                logger.info("")  # Empty line for readability
        
        logger.info(f"🎯 Found {len(datasets)} datasets ready for upload")
        return sorted(datasets, key=lambda x: x['size_gb'], reverse=True)
    
    def upload_file_s3(self, local_file: Path, s3_key: str, dry_run: bool = True) -> bool:
        """Upload a single file to S3"""
        try:
            file_size_mb = local_file.stat().st_size / (1024**2)
            
            if dry_run:
                logger.info(f"📤 [DRY RUN] Would upload: {local_file.name} ({file_size_mb:.2f} MB)")
                logger.info(f"   To S3 key: {s3_key}")
                return True
            
            logger.info(f"📤 Uploading: {local_file.name} ({file_size_mb:.2f} MB)")
            
            # Upload file to S3
            self.s3_client.upload_file(
                str(local_file),
                self.s3_config['bucket'],
                s3_key
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
            logger.info("📋 Would upload the following files:")
            
            # Show detailed file list in dry run mode
            for i, file_path in enumerate(data_files, 1):
                relative_path = file_path.relative_to(dataset_path)
                file_size_mb = file_path.stat().st_size / (1024**2)
                s3_key = f"{s3_prefix}/{relative_path}"
                
                logger.info(f"   {i:3d}. {relative_path}")
                logger.info(f"       Size: {file_size_mb:.2f} MB")
                logger.info(f"       S3 Key: {s3_key}")
            
            logger.info(f"📊 Total: {len(data_files)} files would be uploaded")
            return {'uploaded': 0, 'failed': 0, 'total': len(data_files)}
        
        # PRODUCTION MODE: Actually upload files
        logger.info(f"🚨 PRODUCTION MODE: Starting actual upload of {len(data_files)} files")
        logger.info(f"⏱️  Estimated time: {len(data_files) * 0.1:.1f} seconds (with 0.1s delay between files)")
        
        uploaded_count = 0
        failed_count = 0
        
        # Show progress header
        logger.info(f"\n📤 UPLOAD PROGRESS:")
        logger.info(f"{'='*80}")
        
        for i, file_path in enumerate(data_files, 1):
            try:
                # Create S3 key (path in S3)
                relative_path = file_path.relative_to(dataset_path)
                s3_key = f"{s3_prefix}/{relative_path}"
                file_size_mb = file_path.stat().st_size / (1024**2)
                
                # Show progress
                logger.info(f"[{i:3d}/{len(data_files)}] 📤 Uploading: {relative_path}")
                logger.info(f"       Size: {file_size_mb:.2f} MB | S3 Key: {s3_key}")
                
                # Upload file
                if self.upload_file_s3(file_path, s3_key, dry_run=False):
                    uploaded_count += 1
                    logger.info(f"       ✅ SUCCESS")
                else:
                    failed_count += 1
                    logger.info(f"       ❌ FAILED")
                
                # Small delay between uploads
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"       ❌ ERROR: {e}")
                failed_count += 1
        
        logger.info(f"{'='*80}")
        
        return {
            'uploaded': uploaded_count,
            'failed': failed_count,
            'total': len(data_files)
        }
    
    def upload_all_datasets(self, dry_run: bool = True) -> dict:
        """Upload all available Swift datasets via S3"""
        logger.info("🚀 Starting Swift dataset S3 upload process...")
        
        # Get available datasets
        datasets = self.get_available_datasets()
        if not datasets:
            logger.warning("⚠️  No datasets found for upload")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"📊 Found {len(datasets)} datasets for upload:")
        for dataset in datasets:
            logger.info(f"  📁 {dataset['name']}: {dataset['file_count']} files, {dataset['size_gb']} GB")
        
        # Upload each dataset
        success_count = 0
        failed_count = 0
        total_files = 0
        total_size_gb = 0
        
        for dataset in datasets:
            logger.info(f"\n{'='*80}")
            logger.info(f"📤 PROCESSING DATASET: {dataset['name']}")
            logger.info(f"{'='*80}")
            
            # Upload dataset
            result = self.upload_dataset_s3(dataset['path'], dry_run=dry_run)
            
            if result['failed'] == 0:
                success_count += 1
                logger.info(f"✅ Dataset processed successfully: {dataset['name']}")
            else:
                failed_count += 1
                logger.error(f"❌ Dataset processing failed: {dataset['name']}")
            
            # Summary for this dataset
            logger.info(f"\n📊 DATASET SUMMARY: {dataset['name']}")
            logger.info(f"  ✅ Successfully processed: {result['uploaded']}")
            logger.info(f"  ❌ Failed: {result['failed']}")
            logger.info(f"  📊 Total files: {result['total']}")
            logger.info(f"  💾 Dataset size: {dataset['size_gb']} GB")
            
            # Accumulate totals
            total_files += result['total']
            total_size_gb += dataset['size_gb']
        
        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info("🎯 OVERALL UPLOAD SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"  📁 Datasets:")
        logger.info(f"    ✅ Successful: {success_count}")
        logger.info(f"    ❌ Failed: {failed_count}")
        logger.info(f"    📊 Total: {len(datasets)}")
        logger.info(f"  📄 Files:")
        logger.info(f"    📊 Total files: {total_files}")
        logger.info(f"    💾 Total size: {total_size_gb:.2f} GB")
        logger.info(f"  🌐 S3 Details:")
        logger.info(f"    📦 Bucket: {self.s3_config['bucket']}")
        logger.info(f"    🔗 Endpoint: {self.s3_config['endpoint_url']}")
        logger.info(f"    📁 Prefix: {self.s3_config['prefix']}")
        
        if dry_run:
            logger.info(f"\n⚠️  This was a DRY RUN - no actual uploads were performed")
            logger.info(f"💡 Use --pushtoprod to perform actual uploads")
            logger.info(f"💡 Files would be uploaded to: s3://{self.s3_config['bucket']}/{self.s3_config['prefix']}/")
        else:
            logger.info(f"\n🎉 Upload process completed!")
            if failed_count == 0:
                logger.info(f"✅ All {len(datasets)} datasets uploaded successfully!")
            else:
                logger.info(f"⚠️  {failed_count} datasets had issues")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(datasets)
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Upload Swift datasets to VAST Data Platform via S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (safe, no actual uploads)
  python3 upload_swift_to_vast_s3.py
  
  # Production mode (actual uploads)
  python3 upload_swift_to_vast_s3.py --pushtoprod
  
  # Custom config file
  python3 upload_swift_to_vast_s3.py --config my_config.yaml
        """
    )
    
    parser.add_argument('--pushtoprod', action='store_true',
                       help='Enable production mode (actual uploads will be performed)')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run in dry-run mode (default: True)')
    
    args = parser.parse_args()
    
    # Determine production mode
    production_mode = args.pushtoprod
    dry_run = not production_mode
    
    if production_mode:
        print("🚨 WARNING: PRODUCTION MODE ENABLED")
        print("This will perform actual S3 uploads to your VAST system!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("Production mode cancelled. Exiting.")
            return
        print("✅ Production mode confirmed. Proceeding with actual S3 uploads...")
    else:
        print("⚠️  DRY RUN MODE: No actual uploads will be performed")
        print("💡 Use --pushtoprod to enable production mode")
    
    try:
        # Initialize S3 uploader
        uploader = SwiftS3Uploader(args.config, production_mode)
        
        # Perform uploads
        results = uploader.upload_all_datasets(dry_run=dry_run)
        
        if results['failed'] == 0:
            print(f"\n🎉 S3 upload process completed successfully!")
            print(f"   Processed: {results['total']} datasets")
        else:
            print(f"\n⚠️  S3 upload process completed with {results['failed']} failures")
            print(f"   Successful: {results['success']}")
            print(f"   Failed: {results['failed']}")
            print(f"   Total: {results['total']}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Upload process interrupted by user")
    except Exception as e:
        logger.error(f"❌ S3 upload process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

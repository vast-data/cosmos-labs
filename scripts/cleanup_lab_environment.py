#!/usr/bin/env python3
"""
Lab Environment Cleanup Script

This script provides comprehensive cleanup capabilities for the lab environment:
- S3 bucket cleanup (delete all objects)
- Database cleanup (clear tables, optionally remove database)
- Local file cleanup (optional)

Usage:
    python cleanup_lab_environment.py --help
    python cleanup_lab_environment.py --s3-only
    python cleanup_lab_environment.py --db-only
    python cleanup_lab_environment.py --db-remove
    python cleanup_lab_environment.py --all
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
# Add lab2 directory to path for vast_database_manager import
sys.path.append(str(Path(__file__).parent.parent / "lab2"))

try:
    from config_loader import ConfigLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure config_loader.py is available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LabEnvironmentCleaner:
    """Comprehensive cleanup for lab environment"""
    
    def __init__(self, config_path: str = None, production_mode: bool = False):
        """Initialize the cleanup utility"""
        self.production_mode = production_mode
        
        # Load configuration
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = str(project_root / "config.yaml")
            secrets_path = str(project_root / "secrets.yaml")
        
        self.config = ConfigLoader(config_path, secrets_path)
        
        # Initialize S3 client if needed
        self.s3_client = None
        if self._should_cleanup_s3():
            self._initialize_s3_client()
        
        # Initialize database manager if needed
        self.db_manager = None
        if self._should_cleanup_db():
            self._initialize_db_manager()
        
        mode_text = "PRODUCTION" if production_mode else "DRY RUN"
        logger.info(f"Lab Environment Cleaner initialized in {mode_text} mode")
    
    def _should_cleanup_s3(self) -> bool:
        """Check if S3 cleanup is configured"""
        return bool(self.config.get('s3.endpoint_url') and 
                   self.config.get('s3.bucket'))
    
    def _should_cleanup_db(self) -> bool:
        """Check if database cleanup is configured"""
        return bool(self.config.get('lab2.vastdb.host'))
    
    def _initialize_s3_client(self):
        """Initialize S3 client for cleanup operations"""
        try:
            import boto3
            
            # Fix for modern boto3 versions
            os.environ['AWS_REQUEST_CHECKSUM_CALCULATION'] = 'when_required'
            
            s3_config = self._get_s3_config()
            
            self.s3_client = boto3.client(
                's3',
                endpoint_url=s3_config['endpoint_url'],
                aws_access_key_id=s3_config['aws_access_key_id'],
                aws_secret_access_key=s3_config['aws_secret_access_key'],
                region_name='us-east-1',
                use_ssl=False,
                config=boto3.session.Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'path'}
                )
            )
            
            logger.info("✅ S3 client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _initialize_db_manager(self):
        """Initialize database manager for cleanup operations"""
        try:
            from vast_database_manager import VASTDatabaseManager
            self.db_manager = VASTDatabaseManager(self.config)
            logger.info("✅ Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database manager: {e}")
            self.db_manager = None
    
    def _get_s3_config(self) -> Dict[str, Any]:
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
        
        # Validate required fields
        required_fields = ['endpoint_url', 'aws_access_key_id', 'aws_secret_access_key', 'bucket']
        for field in required_fields:
            if not s3_config.get(field):
                raise ValueError(f"S3 {field} not found in configuration")
        
        return s3_config
    
    def cleanup_s3_bucket(self) -> bool:
        """Clean up S3 bucket - delete all objects"""
        if not self.s3_client:
            logger.warning("⚠️  S3 client not available, skipping S3 cleanup")
            return False
        
        try:
            bucket_name = self.config.get('s3.bucket')
            logger.info(f"🧹 Starting S3 bucket cleanup: {bucket_name}")
            
            if not self.production_mode:
                logger.info("🔍 DRY RUN: Would delete all objects from S3 bucket")
                return True
            
            # List all objects in bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            objects_to_delete = []
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects_to_delete.extend([{'Key': obj['Key']} for obj in page['Contents']])
            
            if not objects_to_delete:
                logger.info("ℹ️  S3 bucket is already empty")
                return True
            
            logger.info(f"🗑️  Deleting {len(objects_to_delete)} objects from S3 bucket")
            
            # Delete objects in batches of 1000 (S3 limit)
            batch_size = 1000
            for i in range(0, len(objects_to_delete), batch_size):
                batch = objects_to_delete[i:i + batch_size]
                response = self.s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': batch}
                )
                
                deleted_count = len(response.get('Deleted', []))
                logger.info(f"✅ Deleted batch {i//batch_size + 1}: {deleted_count} objects")
            
            logger.info(f"✅ S3 bucket cleanup completed: {len(objects_to_delete)} objects deleted")
            return True
            
        except Exception as e:
            logger.error(f"❌ S3 bucket cleanup failed: {e}")
            return False
    
    def cleanup_database(self, remove_database: bool = False) -> bool:
        """Clean up database - clear tables or remove entire database"""
        if not self.db_manager:
            logger.warning("⚠️  Database manager not available, skipping database cleanup")
            return False
        
        try:
            if remove_database:
                logger.info("🗑️  Starting complete database removal")
                
                if not self.production_mode:
                    logger.info("🔍 DRY RUN: Would remove entire database")
                    return True
                
                # Connect and remove database
                if self.db_manager.connect():
                    if self.db_manager.database_exists():
                        if self.db_manager.remove_database():
                            logger.info("✅ Database removed successfully")
                            return True
                        else:
                            logger.error("❌ Failed to remove database")
                            return False
                    else:
                        logger.info("ℹ️  Database does not exist")
                        return True
                else:
                    logger.error("❌ Failed to connect to database")
                    return False
            
            else:
                logger.info("🧹 Starting database cleanup (preserving structure)")
                
                if not self.production_mode:
                    logger.info("🔍 DRY RUN: Would clear all tables")
                    return True
                
                # Connect and clear tables
                if self.db_manager.connect():
                    if self.db_manager.clear_all_tables():
                        logger.info("✅ Database tables cleared successfully")
                        return True
                    else:
                        logger.error("❌ Failed to clear database tables")
                        return False
                else:
                    logger.error("❌ Failed to connect to database")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
            return False
    
    def cleanup_local_files(self) -> bool:
        """Clean up local Swift dataset files"""
        try:
            swift_datasets_dir = Path(__file__).parent / "swift_datasets"
            
            if not swift_datasets_dir.exists():
                logger.info("ℹ️  Local Swift datasets directory does not exist")
                return True
            
            logger.info(f"🧹 Starting local file cleanup: {swift_datasets_dir}")
            
            if not self.production_mode:
                logger.info("🔍 DRY RUN: Would remove local Swift datasets")
                return True
            
            # Calculate size before deletion
            total_size = sum(f.stat().st_size for f in swift_datasets_dir.rglob('*') if f.is_file())
            total_size_gb = total_size / (1024**3)
            
            # Remove directory
            import shutil
            shutil.rmtree(swift_datasets_dir)
            
            logger.info(f"✅ Local files cleaned up: {total_size_gb:.2f} GB removed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Local file cleanup failed: {e}")
            return False
    
    def cleanup_all(self, remove_database: bool = False) -> bool:
        """Perform comprehensive cleanup of all components"""
        logger.info("🚀 Starting comprehensive lab environment cleanup")
        
        success = True
        
        # Clean up S3
        if self._should_cleanup_s3():
            if not self.cleanup_s3_bucket():
                success = False
        
        # Clean up database
        if self._should_cleanup_db():
            if not self.cleanup_database(remove_database):
                success = False
        
        # Clean up local files
        if not self.cleanup_local_files():
            success = False
        
        if success:
            logger.info("✅ Comprehensive cleanup completed successfully")
        else:
            logger.warning("⚠️  Some cleanup operations failed")
        
        return success
    
    def show_status(self):
        """Show current status of lab environment"""
        logger.info("📊 Lab Environment Status")
        logger.info("=" * 50)
        
        # S3 Status
        if self._should_cleanup_s3():
            try:
                bucket_name = self.config.get('s3.bucket')
                if self.s3_client:
                    response = self.s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                    object_count = response.get('KeyCount', 0)
                    if 'Contents' in response:
                        logger.info(f"📦 S3 Bucket '{bucket_name}': {object_count}+ objects")
                    else:
                        logger.info(f"📦 S3 Bucket '{bucket_name}': Empty")
                else:
                    logger.info(f"📦 S3 Bucket '{bucket_name}': Client not available")
            except Exception as e:
                logger.info(f"📦 S3 Bucket: Error checking status - {e}")
        else:
            logger.info("📦 S3: Not configured")
        
        # Database Status
        if self._should_cleanup_db():
            try:
                if self.db_manager and self.db_manager.connect():
                    if self.db_manager.database_exists():
                        logger.info("🗄️  Database: Connected and exists")
                    else:
                        logger.info("🗄️  Database: Connected but database doesn't exist")
                else:
                    logger.info("🗄️  Database: Connection failed")
            except Exception as e:
                logger.info(f"🗄️  Database: Error checking status - {e}")
        else:
            logger.info("🗄️  Database: Not configured")
        
        # Local Files Status
        swift_datasets_dir = Path(__file__).parent / "swift_datasets"
        if swift_datasets_dir.exists():
            total_size = sum(f.stat().st_size for f in swift_datasets_dir.rglob('*') if f.is_file())
            total_size_gb = total_size / (1024**3)
            file_count = sum(1 for f in swift_datasets_dir.rglob('*') if f.is_file())
            logger.info(f"📁 Local Files: {file_count} files, {total_size_gb:.2f} GB")
        else:
            logger.info("📁 Local Files: No datasets directory found")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Lab Environment Cleanup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current status
  python cleanup_lab_environment.py --status
  
  # Clean S3 only (dry run)
  python cleanup_lab_environment.py --s3-only
  
  # Clean database only (production)
  python cleanup_lab_environment.py --db-only --pushtoprod
  
  # Remove entire database (production)
  python cleanup_lab_environment.py --db-remove --pushtoprod
  
  # Clean everything (production)
  python cleanup_lab_environment.py --all --pushtoprod
        """
    )
    
    parser.add_argument(
        '--pushtoprod', 
        action='store_true',
        help='Enable production mode (actual changes)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file'
    )
    
    parser.add_argument(
        '--s3-only',
        action='store_true',
        help='Clean up S3 bucket only'
    )
    
    parser.add_argument(
        '--db-only',
        action='store_true',
        help='Clean up database tables only'
    )
    
    parser.add_argument(
        '--db-remove',
        action='store_true',
        help='Remove entire database'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Clean up everything (S3, database, local files)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status only'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if sum([args.s3_only, args.db_only, args.db_remove, args.all, args.status]) != 1:
        parser.error("Please specify exactly one cleanup operation")
    
    # Initialize cleaner
    cleaner = LabEnvironmentCleaner(
        config_path=args.config,
        production_mode=args.pushtoprod
    )
    
    # Show status if requested
    if args.status:
        cleaner.show_status()
        return
    
    # Perform cleanup operations
    if args.s3_only:
        cleaner.cleanup_s3_bucket()
    elif args.db_only:
        cleaner.cleanup_database(remove_database=False)
    elif args.db_remove:
        cleaner.cleanup_database(remove_database=True)
    elif args.all:
        cleaner.cleanup_all(remove_database=args.db_remove)

if __name__ == "__main__":
    main()

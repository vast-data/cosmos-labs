#!/usr/bin/env python3
"""
Lab 2 Infrastructure Setup
Creates VAST views and database schema for metadata infrastructure
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader
from lab2.vast_database_manager import VASTDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InfrastructureSetup:
    """Handles VAST view creation and database setup"""
    
    def __init__(self, config_path: str = None, secrets_path: str = None):
        # Default to parent directory for config files
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config.yaml")
        if secrets_path is None:
            secrets_path = str(Path(__file__).parent.parent / "secrets.yaml")
        self.config = ConfigLoader(config_path, secrets_path)
        self.db_manager = VASTDatabaseManager(self.config)
        
    def setup_all_infrastructure(self) -> bool:
        """Set up all Lab 2 infrastructure components"""
        logger.info("🔧 Setting up VAST Database infrastructure...")
        
        try:
            # Create views using vastpy
            if not self.create_lab2_views():
                logger.error("❌ Failed to create Lab 2 views")
                return False
            
            # Set up database schema and tables
            # Note: Views are already created above, so we just need to create schema/table
            logger.info("🔧 Creating database schema and table...")
            if not self.db_manager.create_schema_and_table():
                logger.error("❌ Failed to create schema and table")
                return False
            
            logger.info("✅ Database infrastructure setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Infrastructure setup failed: {e}")
            return False
        finally:
            self.db_manager.close()
    
    def create_lab2_views(self) -> bool:
        """Create both raw data and metadata database views using vastpy"""
        try:
            from vastpy import VASTClient
            
            vms_endpoint = self.config.get('vast.address')
            vms_username = self.config.get('vast.user')
            vms_password = self.config.get_secret('vast_password')
            
            if not vms_endpoint or not vms_username or not vms_password:
                logger.error("❌ Missing VMS settings in config.yaml/secrets.yaml")
                return False
            
            # Strip protocol from address (vastpy expects just hostname:port)
            address = vms_endpoint
            if address.startswith('https://'):
                address = address[8:]
            elif address.startswith('http://'):
                address = address[7:]
            
            logger.info(f"🔧 Connecting to VAST with user='{vms_username}', address='{address}'")
            
            # Connect to VAST Management System
            client = VASTClient(address=address, user=vms_username, password=vms_password)
            
            try:
                users = client.users.get()
                logger.info(f"✅ Successfully connected to VAST, found {len(users)} users")
            except Exception as e:
                logger.error(f"❌ Failed to connect to VAST: {e}")
                return False
            
            # Create raw data view (S3 protocol)
            if not self.create_raw_data_view(client, vms_username):
                return False
            
            # Create metadata database view (S3 + DATABASE protocols)
            if not self.create_metadata_database_view(client, vms_username):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Lab 2 views: {e}")
            return False
    
    def create_raw_data_view(self, client, vms_username: str) -> bool:
        """Create raw data view with S3 protocol"""
        raw_view_path = self.config.get('lab2.raw_data.view_path', '/lab2-raw-data')
        raw_bucket_owner = self.config.get('lab2.raw_data.bucket_owner', vms_username)
        logger.info(f"🔧 Using bucket owner '{raw_bucket_owner}' for raw data view")
        
        try:
            # Check if view exists
            views = client.views.get()
            existing_view = next((v for v in views if v.get('path') == raw_view_path), None)
            if existing_view:
                logger.info(f"✅ Raw data view '{raw_view_path}' already exists")
                return True
            
            # Get S3 policy for raw data view creation
            policy_name = self.config.get('lab2.raw_data.policy_name', 's3_default_policy')
            policies = client.viewpolicies.get(name=policy_name)
            if policies:
                policy_id = policies[0]['id']
                logger.info(f"🔧 Using policy '{policy_name}' (ID: {policy_id}) for raw data view")
                
                # Derive bucket name from view path for S3
                raw_bucket_name = raw_view_path.lstrip('/').replace('/', '-')
                
                # Create view with S3 protocol for raw data uploads
                view = client.views.post(
                    path=raw_view_path, 
                    policy_id=policy_id, 
                    create_dir=True,
                    protocols=['S3'],
                    bucket=raw_bucket_name,
                    bucket_owner=raw_bucket_owner
                )
                logger.info(f"✅ Created raw data view '{raw_view_path}' with S3 protocol")
                return True
            else:
                logger.error(f"❌ Policy '{policy_name}' not found for raw data view creation")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to check/create raw data view: {e}")
            return False
    
    def create_metadata_database_view(self, client, vms_username: str) -> bool:
        """Create metadata database view with S3 and DATABASE protocols"""
        metadata_view_path = self.config.get('lab2.metadata_database.view_path', '/lab2-metadata-db')
        metadata_db_name = self.config.get('lab2.metadata_database.database_name', 'lab2-metadata-db')
        bucket_owner = self.config.get('lab2.metadata_database.bucket_owner', vms_username)
        logger.info(f"🔧 Using bucket owner '{bucket_owner}' from config")
        
        try:
            # Check if view exists
            views = client.views.get()
            existing_view = next((v for v in views if v.get('path') == metadata_view_path), None)
            if existing_view:
                logger.info(f"✅ Metadata database view '{metadata_view_path}' already exists")
                return True
            
            # Get policy name from config for DATABASE protocol view
            policy_name = self.config.get('lab2.metadata_database.policy_name', 's3_default_policy')
            policies = client.viewpolicies.get(name=policy_name)
            if policies:
                policy_id = policies[0]['id']
                logger.info(f"🔧 Using policy '{policy_name}' (ID: {policy_id}) for DATABASE protocol view")
            else:
                logger.error(f"❌ Policy '{policy_name}' not found for view creation")
                return False
            
            # Create view with S3 and DATABASE protocols
            view = client.views.post(
                path=metadata_view_path,
                policy_id=policy_id,
                create_dir=True,
                protocols=['S3', 'DATABASE'],
                bucket=metadata_db_name,
                bucket_owner=bucket_owner
            )
            logger.info(f"✅ Created metadata database view '{metadata_view_path}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to check/create metadata database view: {e}")
            return False

def main():
    """Main entry point for infrastructure setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up Lab 2 infrastructure')
    parser.add_argument('--config', default=None, help='Config file path (default: ../config.yaml)')
    parser.add_argument('--secrets', default=None, help='Secrets file path (default: ../secrets.yaml)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')
    
    args = parser.parse_args()
    
    setup = InfrastructureSetup(args.config, args.secrets)
    
    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE: No actual changes will be made")
        logger.info("🔍 Testing connections and checking existing infrastructure...")
        
        # Test VAST connection
        try:
            from vastpy import VASTClient
            vms_address = setup.config.get('vast.address')
            vms_username = setup.config.get('vast.user')
            vms_password = setup.config.get_secret('vast_password')
            
            # Strip protocol if present and clean up address
            if vms_address.startswith(('http://', 'https://')):
                vms_address = vms_address.split('://', 1)[1]
            # Remove trailing slash
            vms_address = vms_address.rstrip('/')
            
            logger.info(f"🔧 Testing VAST connection to {vms_address}...")
            client = VASTClient(address=vms_address, user=vms_username, password=vms_password)
            users = client.users.get()
            logger.info(f"✅ VAST connection successful, found {len(users)} users")
            
        except Exception as e:
            logger.error(f"❌ VAST connection failed: {e}")
            return False
        
        # Test database connection
        try:
            logger.info("🔧 Testing VAST Database connection...")
            if setup.db_manager.connect():
                logger.info("✅ VAST Database connection successful")
                setup.db_manager.close()
            else:
                logger.error("❌ VAST Database connection failed")
                return False
        except Exception as e:
            logger.error(f"❌ VAST Database connection failed: {e}")
            return False
        
        # Check existing views
        try:
            raw_view_path = setup.config.get('lab2.raw_data.view_path')
            metadata_view_path = setup.config.get('lab2.metadata_database.view_path')
            
            logger.info(f"🔍 Checking raw data view '{raw_view_path}'...")
            try:
                raw_view = client.views.get(path=raw_view_path)
                logger.info(f"✅ Raw data view '{raw_view_path}' exists")
            except Exception:
                logger.info(f"ℹ️  Raw data view '{raw_view_path}' does not exist (would be created)")
            
            logger.info(f"🔍 Checking metadata database view '{metadata_view_path}'...")
            try:
                metadata_view = client.views.get(path=metadata_view_path)
                logger.info(f"✅ Metadata database view '{metadata_view_path}' exists")
            except Exception:
                logger.info(f"ℹ️  Metadata database view '{metadata_view_path}' does not exist (would be created)")
            
        except Exception as e:
            logger.error(f"❌ Error checking views: {e}")
            return False
        
        logger.info("✅ Dry-run validation completed successfully")
        logger.info("💡 All connections working, infrastructure setup would succeed")
        return True
    
    if setup.setup_all_infrastructure():
        logger.info("✅ Infrastructure setup completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Infrastructure setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

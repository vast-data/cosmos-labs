# multi_observatory_storage_manager.py
import time
import logging
import sys
import os
from datetime import datetime, timedelta
from vastpy import VASTClient
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path for centralized config
sys.path.append(str(Path(__file__).parent.parent))
from lab3.lab3_config import Lab3ConfigLoader
from lab1.safety_checker import SafetyChecker, SafetyCheckFailed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiObservatoryStorageManager:
    """Manages storage for both SWIFT and Chandra observatories using vastpy"""
    
    def __init__(self, config: Lab3ConfigLoader, production_mode: bool = False, show_api_calls: bool = False):
        """
        Initialize the multi-observatory storage manager
        
        Args:
            config: Lab3ConfigLoader instance with loaded configuration
            production_mode: If True, allows actual changes. If False, dry-run only.
            show_api_calls: If True, show API calls being made (credentials obfuscated).
        """
        self.production_mode = production_mode
        self.show_api_calls = show_api_calls
        self.config = config
        
        # Load VAST configuration
        vast_config = config.get_vast_config()
        
        # Build VAST client parameters dynamically based on what's available
        address = vast_config['address']
        if address.startswith('https://'):
            address = address[8:]  # Remove 'https://' prefix
        elif address.startswith('http://'):
            address = address[7:]   # Remove 'http://' prefix
        
        client_params = {
            'user': vast_config['user'],
            'password': vast_config['password'],
            'address': address
        }
        
        # Add optional parameters only if they exist and are supported
        if vast_config.get('token'):
            client_params['token'] = vast_config['token']
        if vast_config.get('version'):
            client_params['version'] = vast_config['version']
        
        try:
            self.client = VASTClient(**client_params)
            logger.info("✅ VAST client initialized successfully")
        except TypeError as e:
            # Handle unsupported parameters gracefully
            if "tenant_name" in str(e):
                logger.warning("⚠️  tenant_name parameter not supported in this vastpy version, retrying without it")
                if 'tenant_name' in client_params:
                    del client_params['tenant_name']
                self.client = VASTClient(**client_params)
                logger.info("✅ VAST client initialized successfully (without tenant_name)")
            else:
                raise
        
        # Initialize safety checker
        self.safety_checker = SafetyChecker(config, self.client)
        
        # Observatory-specific configuration
        self.swift_config = config.get_swift_config()
        self.chandra_config = config.get_chandra_config()
        self.storage_config = config.get_storage_config()
        
        # Storage paths
        self.swift_data_path = config.get_swift_data_path()
        self.chandra_data_path = config.get_chandra_data_path()
        
        # Storage quotas
        self.swift_quota_tb = config.get_swift_storage_quota()
        self.chandra_quota_tb = config.get_chandra_storage_quota()
    
    def _log_api_call(self, operation: str, details: str = ""):
        """Log API calls if show_api_calls is enabled"""
        if self.show_api_calls:
            print(f"\n🔧 API CALL: {operation}")
            if details:
                print(f"   Details: {details}")
            print()
    
    def setup_observatory_storage_views(self) -> bool:
        """Set up storage views for both SWIFT and Chandra observatories"""
        logger.info("🏗️  Setting up multi-observatory storage views...")
        
        try:
            # Set up SWIFT storage views
            swift_success = self._setup_swift_storage_views()
            
            # Set up Chandra storage views
            chandra_success = self._setup_chandra_storage_views()
            
            if swift_success and chandra_success:
                logger.info("✅ Multi-observatory storage views setup completed successfully")
                return True
            else:
                logger.error("❌ Failed to setup some observatory storage views")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting up observatory storage views: {e}")
            return False
    
    def _setup_swift_storage_views(self) -> bool:
        """Set up SWIFT-specific storage views"""
        logger.info(f"📡 Setting up SWIFT storage views at {self.swift_data_path}")
        
        try:
            # Check if SWIFT views already exist
            existing_views = self.client.views.get(path=self.swift_data_path)
            if existing_views:
                logger.info(f"✅ SWIFT storage view already exists at {self.swift_data_path}")
                return True
            
            # Create SWIFT storage view
            if self.production_mode:
                self._log_api_call(
                    "vastpy.views.create()",
                    f"path={self.swift_data_path}, quota={self.swift_quota_tb}TB"
                )
                
                view_data = {
                    'path': self.swift_data_path,
                    'quota': self.swift_quota_tb * 1024 * 1024 * 1024 * 1024,  # Convert TB to bytes
                    'description': 'SWIFT Observatory Data - Real-time burst detection'
                }
                
                self.client.views.create(**view_data)
                logger.info(f"✅ Created SWIFT storage view: {self.swift_data_path}")
            else:
                logger.info(f"🔍 DRY RUN: Would create SWIFT storage view: {self.swift_data_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up SWIFT storage views: {e}")
            return False
    
    def _setup_chandra_storage_views(self) -> bool:
        """Set up Chandra-specific storage views"""
        logger.info(f"🔭 Setting up Chandra storage views at {self.chandra_data_path}")
        
        try:
            # Check if Chandra views already exist
            existing_views = self.client.views.get(path=self.chandra_data_path)
            if existing_views:
                logger.info(f"✅ Chandra storage view already exists at {self.chandra_data_path}")
                return True
            
            # Create Chandra storage view
            if self.production_mode:
                self._log_api_call(
                    "vastpy.views.create()",
                    f"path={self.chandra_data_path}, quota={self.chandra_quota_tb}TB"
                )
                
                view_data = {
                    'path': self.chandra_data_path,
                    'quota': self.chandra_quota_tb * 1024 * 1024 * 1024 * 1024,  # Convert TB to bytes
                    'description': 'Chandra Observatory Data - High-resolution X-ray analysis'
                }
                
                self.client.views.create(**view_data)
                logger.info(f"✅ Created Chandra storage view: {self.chandra_data_path}")
            else:
                logger.info(f"🔍 DRY RUN: Would create Chandra storage view: {self.chandra_data_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up Chandra storage views: {e}")
            return False
    
    def get_observatory_storage_status(self) -> Dict[str, Dict]:
        """Get storage status for both observatories"""
        logger.info("📊 Getting multi-observatory storage status...")
        
        status = {}
        
        try:
            # Get SWIFT storage status
            swift_status = self._get_observatory_storage_status('SWIFT', self.swift_data_path)
            status['swift'] = swift_status
            
            # Get Chandra storage status
            chandra_status = self._get_observatory_storage_status('Chandra', self.chandra_data_path)
            status['chandra'] = chandra_status
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting observatory storage status: {e}")
            return {}
    
    def _get_observatory_storage_status(self, observatory_name: str, data_path: str) -> Dict:
        """Get storage status for a specific observatory"""
        try:
            views = self.client.views.get(path=data_path)
            if not views:
                return {
                    'observatory': observatory_name,
                    'path': data_path,
                    'status': 'NOT_FOUND',
                    'quota_gb': 0,
                    'used_gb': 0,
                    'utilization_percent': 0,
                    'available_gb': 0
                }
            
            view = views[0]
            quota_bytes = view.get('quota', 0)
            used_bytes = view.get('logical_size', 0)
            
            quota_gb = quota_bytes / (1024**3)
            used_gb = used_bytes / (1024**3)
            utilization_percent = (used_bytes / quota_bytes * 100) if quota_bytes > 0 else 0
            available_gb = quota_gb - used_gb
            
            # Determine status
            if utilization_percent >= 90:
                status = 'CRITICAL'
            elif utilization_percent >= 75:
                status = 'WARNING'
            else:
                status = 'NORMAL'
            
            return {
                'observatory': observatory_name,
                'path': data_path,
                'status': status,
                'quota_gb': quota_gb,
                'used_gb': used_gb,
                'utilization_percent': utilization_percent,
                'available_gb': available_gb
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting {observatory_name} storage status: {e}")
            return {
                'observatory': observatory_name,
                'path': data_path,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def monitor_observatory_storage(self) -> bool:
        """Monitor storage for both observatories and take action if needed"""
        logger.info("🔍 Monitoring multi-observatory storage...")
        
        try:
            status = self.get_observatory_storage_status()
            
            # Check each observatory
            for observatory, obs_status in status.items():
                if obs_status['status'] == 'CRITICAL':
                    logger.warning(f"🚨 {observatory} storage is CRITICAL ({obs_status['utilization_percent']:.1f}% used)")
                    # Could implement auto-expansion here
                elif obs_status['status'] == 'WARNING':
                    logger.warning(f"⚠️  {observatory} storage is WARNING ({obs_status['utilization_percent']:.1f}% used)")
                else:
                    logger.info(f"✅ {observatory} storage is NORMAL ({obs_status['utilization_percent']:.1f}% used)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error monitoring observatory storage: {e}")
            return False
    
    def show_observatory_storage_summary(self):
        """Display a summary of storage status for both observatories"""
        print("\n" + "="*80)
        print("🌌 MULTI-OBSERVATORY STORAGE SUMMARY")
        print("="*80)
        
        status = self.get_observatory_storage_status()
        
        for observatory, obs_status in status.items():
            print(f"\n📡 {obs_status['observatory'].upper()} OBSERVATORY")
            print(f"   Path: {obs_status['path']}")
            print(f"   Status: {obs_status['status']}")
            print(f"   Quota: {obs_status['quota_gb']:.1f} GB")
            print(f"   Used: {obs_status['used_gb']:.1f} GB")
            print(f"   Available: {obs_status['available_gb']:.1f} GB")
            print(f"   Utilization: {obs_status['utilization_percent']:.1f}%")
        
        print("\n" + "="*80)

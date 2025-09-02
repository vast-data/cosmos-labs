# lab1_solution.py
import time
import logging
import sys
import argparse
from datetime import datetime, timedelta
from vastpy import VASTClient
from typing import Dict, List, Optional
from lab1_config import Lab1ConfigLoader
from safety_checker import SafetyChecker, SafetyCheckFailed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrbitalDynamicsStorageManager:
    def __init__(self, config: Lab1ConfigLoader, production_mode: bool = False, show_api_calls: bool = False):
        """
        Initialize the storage manager for Orbital Dynamics
        
        Args:
            config: Lab1ConfigLoader instance with loaded configuration
            production_mode: If True, allows actual changes. If False, dry-run only.
            show_api_calls: If True, show API calls being made (credentials obfuscated).
        """
        self.production_mode = production_mode
        self.show_api_calls = show_api_calls
        # Load VAST configuration
        vast_config = config.get_vast_config()
        
        # Build VAST client parameters dynamically based on what's available
        # vastpy constructs URLs as https://{address}/... so we need to strip protocol
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
        
        # Note: tenant_name is not supported in vastpy 0.3.17
        # It will be ignored if not supported by the version
        
        try:
            self.client = VASTClient(**client_params)
            logger.info("✅ VAST client initialized successfully")
        except TypeError as e:
            # Handle unsupported parameters gracefully
            if "tenant_name" in str(e):
                logger.warning("⚠️  tenant_name parameter not supported in this vastpy version, retrying without it")
                # Remove tenant_name and retry
                if 'tenant_name' in client_params:
                    del client_params['tenant_name']
                self.client = VASTClient(**client_params)
                logger.info("✅ VAST client initialized successfully (without tenant_name)")
            else:
                # Re-raise other TypeError exceptions
                raise
        
        # Load configuration values
        self.config = config
        
        # Storage configuration - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        data_dirs = config.get('data.directories', [])
        if len(data_dirs) < 2:
            raise ValueError("data.directories must contain at least 2 directories")
        
        self.raw_data_path = data_dirs[0]  # First directory from data.directories
        self.processed_data_path = data_dirs[1]  # Second directory from data.directories
        self.temp_data_path = data_dirs[2] if len(data_dirs) > 2 else None
        
        # Quota thresholds - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        self.warning_threshold = config.get('lab1.monitoring.alert_threshold')
        self.critical_threshold = config.get('lab1.monitoring.critical_threshold')
        self.auto_expand_size = config.get('lab1.storage.expansion_factor')
        self.max_expansion_gb = config.get('lab1.storage.max_expansion_gb')
        
        # Monitoring settings - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        self.monitoring_interval = config.get('monitoring.interval_seconds')
        
        # Initialize safety checker
        self.safety_checker = SafetyChecker(config, self.client)
        
        # Log mode information
        mode_str = "PRODUCTION" if self.production_mode else "DRY RUN"
        logger.info(f"Orbital Dynamics Storage Manager initialized in {mode_str} mode")
        if not self.production_mode:
            logger.info("⚠️  DRY RUN MODE: No actual changes will be made")
        else:
            logger.warning("🚨 PRODUCTION MODE: Actual changes will be made to your VAST system")
    
    def _log_api_call(self, operation: str, details: str = ""):
        """Log API calls if show_api_calls is enabled"""
        if self.show_api_calls:
            # Obfuscate credentials in the details
            obfuscated_details = details
            vast_config = self.config.get_vast_config()
            if vast_config.get('user') and vast_config['user'] in obfuscated_details:
                obfuscated_details = obfuscated_details.replace(vast_config['user'], '***')
            if vast_config.get('password') and vast_config['password'] in obfuscated_details:
                obfuscated_details = obfuscated_details.replace(vast_config['password'], '***')
            if vast_config.get('token') and vast_config['token'] in obfuscated_details:
                obfuscated_details = obfuscated_details.replace(vast_config['token'], '***')
            
            print(f"🔌 API CALL: {operation}")
            if details:
                print(f"   Details: {obfuscated_details}")
            print()
    
    def show_current_view_status(self):
        """Display current status of all target views"""
        logger.info("\n" + "="*60)
        logger.info("🔍 CURRENT VIEW STATUS")
        logger.info("="*60)
        
        view_paths = [path for path in [self.raw_data_path, self.processed_data_path, self.temp_data_path] if path]
        
        if not view_paths:
            logger.warning("⚠️  No view paths configured")
            return
        
        for view_path in view_paths:
            try:
                existing = self.client.views.get(path=view_path)
                if existing and len(existing) > 0:
                    view = existing[0]
                    view_id = view['id']
                    
                    # Get quota information
                    try:
                        quotas = self.client.quotas.get(path=view_path)
                        if quotas:
                            quota_info = quotas[0]
                            used_capacity = quota_info.get('used_capacity', 0)
                            hard_limit = quota_info.get('hard_limit', 0)
                            soft_limit = quota_info.get('soft_limit', 0)
                            
                            # Convert to GB for display
                            size_gb = used_capacity / (1024**3) if used_capacity else 0
                            hard_limit_gb = hard_limit / (1024**3) if hard_limit else 0
                            soft_limit_gb = soft_limit / (1024**3) if soft_limit else 0
                            
                            # Use hard limit for utilization calculation
                            quota_for_calc = hard_limit if hard_limit > 0 else soft_limit
                            if quota_for_calc > 0:
                                utilization = (used_capacity / quota_for_calc) * 100
                                status_icon = "🟢" if utilization < self.warning_threshold else "🟡" if utilization < self.critical_threshold else "🔴"
                                logger.info(f"{status_icon} {view_path}")
                                logger.info(f"    📊 Size: {size_gb:.2f} GB")
                                if soft_limit_gb > 0:
                                    logger.info(f"    ⚠️  Soft Limit: {soft_limit_gb:.2f} GB")
                                if hard_limit_gb > 0:
                                    logger.info(f"    🚫 Hard Limit: {hard_limit_gb:.2f} GB")
                                logger.info(f"    📈 Utilization: {utilization:.1f}%")
                            else:
                                logger.info(f"📁 {view_path}")
                                logger.info(f"    📊 Size: {size_gb:.2f} GB (no quota set)")
                        else:
                            logger.info(f"📁 {view_path}")
                            logger.info(f"    📊 Size: 0.00 GB (no quota set)")
                        
                        logger.info(f"    🆔 View ID: {view_id}")
                        
                    except Exception as e:
                        logger.info(f"📁 {view_path}")
                        logger.info(f"    ⚠️  Could not get quota info: {e}")
                        logger.info(f"    🆔 View ID: {view_id}")
                else:
                    logger.info(f"❌ {view_path} - NOT FOUND")
            except Exception as e:
                logger.warning(f"⚠️  {view_path} - Could not check status: {e}")
        
        logger.info("="*60)
    
    def create_initial_views(self):
        """Create the initial storage views for different data types"""
        try:
            # Get default policy for views
            policies = self.client.viewpolicies.get(name='default')
            if not policies:
                logger.error("No default view policy found - please create one in VAST")
                return False
            
            default_policy = policies[0]
            logger.info(f"📋 Using view policy: {default_policy.get('name', 'default')} (ID: {default_policy['id']})")
            
            # Filter out None paths and show what we're working with
            view_paths = [path for path in [self.raw_data_path, self.processed_data_path, self.temp_data_path] if path]
            logger.info(f"🎯 Target view paths: {len(view_paths)} directories")
            
            # Check existing views first
            existing_views = []
            missing_views = []
            
            for view_path in view_paths:
                try:
                    # Log API call
                    self._log_api_call(
                        "client.views.get()",
                        f"path={view_path}"
                    )
                    
                    existing = self.client.views.get(path=view_path)
                    if existing:
                        existing_views.append(view_path)
                        logger.info(f"✅ View already exists: {view_path}")
                    else:
                        missing_views.append(view_path)
                        logger.info(f"📁 View does not exist: {view_path}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not check view {view_path}: {e}")
                    missing_views.append(view_path)
            
            # Summary of current state
            logger.info(f"\n📊 VIEW STATUS SUMMARY:")
            logger.info(f"  ✅ Existing views: {len(existing_views)}")
            logger.info(f"  📁 Missing views: {len(missing_views)}")
            
            if existing_views:
                logger.info(f"  📋 Existing: {', '.join(existing_views)}")
            if missing_views:
                logger.info(f"  🔨 To create: {', '.join(missing_views)}")
            
            if not missing_views:
                logger.info("🎉 All required views already exist!")
                return True
            
            if self.production_mode:
                # Actually create the missing views
                logger.info(f"\n🚨 PRODUCTION MODE: Creating {len(missing_views)} missing views...")
                
                created_count = 0
                failed_count = 0
                
                for view_path in missing_views:
                    try:
                        logger.info(f"🔨 Creating view: {view_path}")
                        # Log API call
                        self._log_api_call(
                            "client.views.post()",
                            f"path={view_path}, policy_id={default_policy['id']}"
                        )
                        
                        view = self.client.views.post(
                            path=view_path,
                            policy_id=default_policy['id'],
                            create_dir=True,
                            protocols=['NFS', 'SMB']
                        )
                        logger.info(f"✅ Successfully created view: {view_path}")
                        created_count += 1
                    except Exception as e:
                        error_msg = str(e)
                        if "already exists" in error_msg.lower():
                            logger.info(f"ℹ️  View was created by another process: {view_path}")
                            created_count += 1
                        else:
                            logger.error(f"❌ Failed to create view {view_path}: {error_msg}")
                            failed_count += 1
                
                # Final summary
                logger.info(f"\n📊 VIEW CREATION SUMMARY:")
                logger.info(f"  ✅ Successfully created: {created_count}")
                logger.info(f"  ❌ Failed to create: {failed_count}")
                
                if failed_count == 0:
                    logger.info("🎉 All missing views created successfully!")
                    return True
                else:
                    logger.error(f"⚠️  {failed_count} views failed to create")
                    return False
                    
            else:
                # Dry run - show what would happen
                logger.info(f"\n⚠️  DRY RUN MODE: Would create the following views:")
                for view_path in missing_views:
                    logger.info(f"  📁 {view_path}")
                logger.info(f"  (No actual views were created - {len(missing_views)} views would be created)")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup initial views: {e}")
            return False
    
    def get_view_utilization(self, view_path: str) -> Optional[float]:
        """Get current utilization percentage for a view"""
        try:
            # Get quota information from quotas endpoint
            quotas = self.client.quotas.get(path=view_path)
            if not quotas:
                logger.warning(f"No quota found for path: {view_path}")
                return None
            
            quota_info = quotas[0]
            used_capacity = quota_info.get('used_capacity', 0)
            hard_limit = quota_info.get('hard_limit', 0)
            soft_limit = quota_info.get('soft_limit', 0)
            
            # Use hard limit for utilization calculation (actual storage capacity)
            quota_for_calc = hard_limit if hard_limit > 0 else soft_limit
            
            if quota_for_calc > 0:
                utilization = (used_capacity / quota_for_calc) * 100
                return utilization
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get utilization for {view_path}: {e}")
            return None
    
    def expand_view_quota(self, view_path: str, additional_size_tb: int):
        """Expand the quota for a view by the specified amount with comprehensive safety checks"""
        try:
            logger.info(f"Requesting quota expansion: {view_path} (+{additional_size_tb}TB)")
            
            # Convert TB to GB for safety checks
            additional_size_gb = additional_size_tb * 1024
            
            # ALWAYS run safety checks (regardless of mode)
            if not self.safety_checker.validate_storage_expansion(view_path, additional_size_gb):
                raise SafetyCheckFailed("Quota expansion safety checks failed")
            
            views = self.client.views.get(path=view_path)
            if not views:
                logger.error(f"No view found for path: {view_path}")
                return False
            
            view = views[0]
            view_id = view['id']
            
            # Get current quota from quotas endpoint
            quotas = self.client.quotas.get(path=view_path)
            if not quotas:
                logger.error(f"No quota found for path: {view_path}")
                return False
            
            quota_info = quotas[0]
            current_hard_limit = quota_info.get('hard_limit', 0)
            new_hard_limit = current_hard_limit + (additional_size_tb * 1024 * 1024 * 1024)  # Convert TB to bytes
            
            if self.production_mode:
                # Actually perform the expansion
                logger.info("🚨 PRODUCTION MODE: Expanding quota...")
                
                # Update the quota with new hard limit
                quota_id = quota_info['id']
                updated_quota = self.client.quotas[quota_id].patch(hard_limit=new_hard_limit)
                
                logger.info(f"✅ Successfully expanded quota for {view_path}: {current_hard_limit} → {new_hard_limit} bytes")
                return True
            else:
                # Dry run - show what would happen
                logger.info("⚠️  DRY RUN MODE: Would expand quota:")
                logger.info(f"  📊 View: {view_path}")
                logger.info(f"  📊 Current hard limit: {current_hard_limit} bytes")
                logger.info(f"  📊 Additional size: +{additional_size_tb}TB")
                logger.info(f"  📊 New hard limit: {new_hard_limit} bytes")
                logger.info("  (No actual quota changes were made)")
                return True
            
        except SafetyCheckFailed as e:
            logger.error(f"Safety check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to expand quota for {view_path}: {e}")
            return False
    
    def monitor_all_views(self) -> Dict[str, Dict]:
        """Monitor utilization for all views and return status"""
        views_to_monitor = [
            self.raw_data_path,
            self.processed_data_path,
            self.temp_data_path
        ]
        # Filter out None values
        views_to_monitor = [path for path in views_to_monitor if path is not None]
        
        status = {}
        
        for view_path in views_to_monitor:
            utilization = self.get_view_utilization(view_path)
            
            status[view_path] = {
                'utilization': utilization,
                'status': self._get_status_level(utilization),
                'needs_expansion': utilization and utilization > self.critical_threshold,
                'timestamp': datetime.now().isoformat()
            }
            
            utilization_str = f"{utilization:.1f}%" if utilization is not None else "Unknown"
            logger.info(f"{view_path}: {utilization_str} utilization - {status[view_path]['status']}")
        
        return status
    
    def _get_status_level(self, utilization: Optional[float]) -> str:
        """Determine status level based on utilization"""
        if utilization is None:
            return 'UNKNOWN'
        elif utilization >= self.critical_threshold:
            return 'NEEDS_EXPANSION'
        elif utilization >= self.warning_threshold:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def auto_expand_if_needed(self, status: Dict[str, Dict]) -> List[str]:
        """Automatically expand quotas for views that need it"""
        expanded_views = []
        
        for view_path, view_status in status.items():
            if view_status['status'] == 'NEEDS_EXPANSION':
                logger.info(f"Auto-expanding quota for {view_path} (utilization: {view_status['utilization']:.1f}%)")
                
                # Use a simple 1TB expansion
                expansion_size_tb = 1
                if self.expand_view_quota(view_path, expansion_size_tb):
                    expanded_views.append(view_path)
                    logger.info(f"✅ Successfully expanded {view_path} by {expansion_size_tb}TB")
                else:
                    logger.error(f"❌ Failed to expand {view_path}")
        
        return expanded_views
    
    def send_alert(self, message: str, level: str = 'INFO'):
        """Send alert notification"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"🔔 ALERT [{level}]: {message}")
        
        # In production, this would integrate with email, Slack, etc.
        # For learning purposes, we just log to console
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        # Get current status of all views
        status = self.monitor_all_views()
        
        # Check for views that need expansion and send alerts
        for view_path, view_status in status.items():
            if view_status['status'] == 'NEEDS_EXPANSION':
                self.send_alert(
                    f"Storage expansion needed: {view_path} at {view_status['utilization']:.1f}% utilization",
                    'INFO'
                )
        
        # Auto-expand if needed
        expanded_views = self.auto_expand_if_needed(status)
        
        if expanded_views:
            self.send_alert(
                f"Auto-expanded quotas for: {', '.join(expanded_views)}",
                'INFO'
            )
        
        return status

def main():
    """Main function to run the storage automation"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Orbital Dynamics Storage Automation')
    parser.add_argument('--pushtoprod', action='store_true', 
                       help='Enable production mode (actual changes will be made)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry-run mode (default, no changes made)')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only set up initial views, then exit')
    parser.add_argument('--monitor-only', action='store_true',
                       help='Only run monitoring, skip setup')
    parser.add_argument('--showapicalls', action='store_true',
                       help='Show API calls being made (credentials obfuscated)')
    
    args = parser.parse_args()
    
    # Determine production mode
    production_mode = args.pushtoprod
    
    if production_mode:
        # Require explicit confirmation for production mode
        print("🚨 WARNING: PRODUCTION MODE ENABLED")
        print("This will make actual changes to your VAST system!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("Production mode cancelled. Exiting.")
            return
        print("✅ Production mode confirmed. Proceeding with actual changes...")
    else:
        print("⚠️  DRY RUN MODE: No actual changes will be made")
        print("💡 Use --pushtoprod to enable production mode")
    
    try:
        # Load configuration
        config = Lab1ConfigLoader()
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Initialize storage manager with production mode
        storage_manager = OrbitalDynamicsStorageManager(config, production_mode=production_mode, show_api_calls=args.showapicalls)
        
        # Handle different operation modes
        if args.setup_only:
            # Only set up initial views
            logger.info("Setting up initial storage views...")
            if not storage_manager.create_initial_views():
                logger.error("Failed to create initial views")
                return
            logger.info("✅ Setup complete. Exiting.")
            return
        
        elif args.monitor_only:
            # Skip setup, go straight to monitoring
            logger.info("Skipping setup, starting monitoring...")
        else:
            # Normal mode: setup + monitoring
            logger.info("Setting up initial storage views...")
            if not storage_manager.create_initial_views():
                logger.error("Failed to create initial views")
                return
        
        # Show current view status after setup
        storage_manager.show_current_view_status()
        
        # Run continuous monitoring
        logger.info("Starting continuous monitoring...")
        while True:
            status = storage_manager.run_monitoring_cycle()
            
            # Log summary
            needs_expansion_count = sum(1 for s in status.values() if s['status'] == 'NEEDS_EXPANSION')
            
            logger.info(f"Monitoring cycle complete - Views needing expansion: {needs_expansion_count}")
            
            # Wait before next cycle
            time.sleep(storage_manager.monitoring_interval)
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")

if __name__ == "__main__":
    main() 
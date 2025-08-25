# lab1_solution.py
import time
import logging
from datetime import datetime, timedelta
from vastpy import VASTClient
from typing import Dict, List, Optional
from config_loader import Lab1ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrbitalDynamicsStorageManager:
    def __init__(self, config: ConfigLoader):
        """
        Initialize the storage manager for Orbital Dynamics
        
        Args:
            config: ConfigLoader instance with loaded configuration
        """
        # Load VAST configuration
        vast_config = config.get_vast_config()
        
        self.client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=vast_config['address'],
            token=vast_config.get('token'),  # Optional for Vast 5.3+
            tenant_name=vast_config.get('tenant_name'),  # Optional for Vast 5.3+
            version=vast_config.get('version', 'v1')  # API version
        )
        
        # Load configuration values
        self.config = config
        
        # Storage configuration - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        self.raw_data_path = config.get('data.directories')[0]  # First directory from data.directories
        self.processed_data_path = config.get('data.directories')[1]  # Second directory from data.directories
        self.temp_data_path = config.get('data.directories')[2] if len(config.get('data.directories')) > 2 else None
        
        # Quota thresholds - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        self.warning_threshold = config.get('lab1.monitoring.alert_threshold')
        self.critical_threshold = config.get('lab1.monitoring.critical_threshold')
        self.auto_expand_size = config.get('lab1.storage.expansion_factor')
        self.max_expansion_gb = config.get('lab1.storage.max_expansion_gb')
        
        # Monitoring settings - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        self.monitoring_interval = config.get('monitoring.interval_seconds')
        
        logger.info("Orbital Dynamics Storage Manager initialized")
    
    def create_initial_views(self):
        """Create the initial storage views for different data types"""
        try:
            # Get default policy for views
            policies = self.client.viewpolicies.get(name='default')
            default_policy = policies[0] if policies else None
            
            if not default_policy:
                logger.error("No default view policy found")
                return False
            
            # Create raw data view for incoming telescope data
            raw_view = self.client.views.post(
                path=self.raw_data_path,
                policy_id=default_policy['id'],
                create_dir=True,
                protocols=['NFS', 'SMB']  # Support both protocols
            )
            logger.info(f"Created raw data view: {raw_view['id']}")
            
            # Create processed data view for Jordan's pipeline output
            processed_view = self.client.views.post(
                path=self.processed_data_path,
                policy_id=default_policy['id'],
                create_dir=True,
                protocols=['NFS', 'SMB']
            )
            logger.info(f"Created processed data view: {processed_view['id']}")
            
            # Create temporary data view for intermediate processing
            temp_view = self.client.views.post(
                path=self.temp_data_path,
                policy_id=default_policy['id'],
                create_dir=True,
                protocols=['NFS', 'SMB']
            )
            logger.info(f"Created temp data view: {temp_view['id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create initial views: {e}")
            return False
    
    def get_view_utilization(self, view_path: str) -> Optional[float]:
        """Get current utilization percentage for a view"""
        try:
            views = self.client.views.get(path=view_path)
            if not views:
                logger.warning(f"No view found for path: {view_path}")
                return None
            
            view = views[0]
            view_id = view['id']
            
            # Get detailed view information including usage
            view_details = self.client.views[view_id].get()
            
            # Calculate utilization percentage
            if 'size' in view_details and 'quota' in view_details:
                used_size = view_details['size']
                quota_size = view_details['quota']
                
                if quota_size > 0:
                    utilization = (used_size / quota_size) * 100
                    return utilization
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get utilization for {view_path}: {e}")
            return None
    
    def expand_view_quota(self, view_path: str, additional_size_tb: int):
        """Expand the quota for a view by the specified amount"""
        try:
            views = self.client.views.get(path=view_path)
            if not views:
                logger.error(f"No view found for path: {view_path}")
                return False
            
            view = views[0]
            view_id = view['id']
            
            # Get current quota
            current_quota = view.get('quota', 0)
            new_quota = current_quota + (additional_size_tb * 1024 * 1024 * 1024)  # Convert TB to bytes
            
            # Update the view with new quota
            updated_view = self.client.views[view_id].patch(quota=new_quota)
            
            logger.info(f"Expanded quota for {view_path}: {current_quota} -> {new_quota} bytes")
            return True
            
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
        
        status = {}
        
        for view_path in views_to_monitor:
            utilization = self.get_view_utilization(view_path)
            
            status[view_path] = {
                'utilization': utilization,
                'status': self._get_status_level(utilization),
                'needs_expansion': utilization and utilization > self.critical_threshold,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"{view_path}: {utilization:.1f}% utilization - {status[view_path]['status']}")
        
        return status
    
    def _get_status_level(self, utilization: Optional[float]) -> str:
        """Determine status level based on utilization"""
        if utilization is None:
            return 'UNKNOWN'
        elif utilization >= self.critical_threshold:
            return 'CRITICAL'
        elif utilization >= self.warning_threshold:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def auto_expand_if_needed(self, status: Dict[str, Dict]) -> List[str]:
        """Automatically expand quotas for views that need it"""
        expanded_views = []
        
        for view_path, view_status in status.items():
            if view_status['needs_expansion']:
                logger.warning(f"Auto-expanding quota for {view_path} (utilization: {view_status['utilization']:.1f}%)")
                
                if self.expand_view_quota(view_path, self.auto_expand_size):
                    expanded_views.append(view_path)
                    logger.info(f"Successfully expanded {view_path}")
                else:
                    logger.error(f"Failed to expand {view_path}")
        
        return expanded_views
    
    def send_alert(self, message: str, level: str = 'INFO'):
        """Send alert notification (placeholder for integration with alerting system)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alert_msg = f"[{timestamp}] [{level}] {message}"
        
        # In a real implementation, this would integrate with:
        # - Email notifications
        # - Slack/Teams webhooks
        # - PagerDuty alerts
        # - SMS notifications
        
        logger.info(f"ALERT: {alert_msg}")
        
        # For demo purposes, we'll just log the alert
        # TODO: Integrate with actual alerting system
        pass
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        # Get current status of all views
        status = self.monitor_all_views()
        
        # Check for critical conditions and send alerts
        for view_path, view_status in status.items():
            if view_status['status'] == 'CRITICAL':
                self.send_alert(
                    f"CRITICAL: {view_path} at {view_status['utilization']:.1f}% utilization",
                    'CRITICAL'
                )
            elif view_status['status'] == 'WARNING':
                self.send_alert(
                    f"WARNING: {view_path} at {view_status['utilization']:.1f}% utilization",
                    'WARNING'
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
    
    try:
        # Load configuration
        config = Lab1ConfigLoader()
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Initialize storage manager
        storage_manager = OrbitalDynamicsStorageManager(config)
        
        # Create initial views if they don't exist
        logger.info("Setting up initial storage views...")
        if not storage_manager.create_initial_views():
            logger.error("Failed to create initial views")
            return
        
        # Run continuous monitoring
        logger.info("Starting continuous monitoring...")
        while True:
            status = storage_manager.run_monitoring_cycle()
            
            # Log summary
            critical_count = sum(1 for s in status.values() if s['status'] == 'CRITICAL')
            warning_count = sum(1 for s in status.values() if s['status'] == 'WARNING')
            
            logger.info(f"Monitoring cycle complete - Critical: {critical_count}, Warnings: {warning_count}")
            
            # Wait before next cycle
            time.sleep(storage_manager.monitoring_interval)
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")

if __name__ == "__main__":
    main() 
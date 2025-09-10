# lab3_config.py
import sys
import os
from pathlib import Path

# Add parent directory to path to import centralized config_loader
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader

# Create a lab-specific config loader that inherits from the centralized one
class Lab3ConfigLoader(ConfigLoader):
    """Lab 3 specific configuration loader for multi-observatory storage and analytics"""
    
    def __init__(self):
        # Use centralized config files from parent directory
        project_root = Path(__file__).parent.parent
        super().__init__(
            config_path=str(project_root / "config.yaml"),
            secrets_path=str(project_root / "secrets.yaml")
        )
    
    def get_swift_config(self):
        """Get SWIFT observatory specific configuration"""
        return self.get('lab3.swift', {})
    
    def get_chandra_config(self):
        """Get Chandra observatory specific configuration"""
        return self.get('lab3.chandra', {})
    
    def get_analytics_config(self):
        """Get cross-observatory analytics configuration"""
        return self.get('lab3.analytics', {})
    
    def get_storage_config(self):
        """Get multi-observatory storage configuration"""
        return self.get('lab3.storage', {})
    
    def get_swift_storage_quota(self):
        """Get SWIFT storage quota in TB"""
        return self.get('lab3.swift.storage_quota_tb', 100)
    
    def get_chandra_storage_quota(self):
        """Get Chandra storage quota in TB"""
        return self.get('lab3.chandra.storage_quota_tb', 200)
    
    def get_swift_data_path(self):
        """Get SWIFT data storage path"""
        return self.get('lab3.swift.data_path', '/swift/observations')
    
    def get_chandra_data_path(self):
        """Get Chandra data storage path"""
        return self.get('lab3.chandra.data_path', '/chandra/observations')
    
    def get_analytics_batch_size(self):
        """Get batch size for analytics queries"""
        return self.get('lab3.analytics.batch_size', 1000)
    
    def get_query_timeout(self):
        """Get query timeout in seconds"""
        return self.get('lab3.analytics.query_timeout_seconds', 300)
    
    def get_burst_followup_window_days(self):
        """Get time window for SWIFT burst to Chandra follow-up in days"""
        return self.get('lab3.analytics.burst_followup_window_days', 7)
    
    def get_coordinated_campaign_window_days(self):
        """Get time window for coordinated observation campaigns in days"""
        return self.get('lab3.analytics.coordinated_campaign_window_days', 30)
    
    def get_burst_detection_threshold(self):
        """Get threshold for burst detection queries"""
        return self.get('lab3.analytics.burst_detection_threshold', 0.9)
    
    
    def validate_config(self) -> bool:
        """Validate that required Lab3 configuration is present"""
        errors = []
        
        # Check required lab3 configuration sections
        if not self.get('lab3.swift.storage_quota_tb'):
            errors.append("lab3.swift.storage_quota_tb is required")
        
        if not self.get('lab3.chandra.storage_quota_tb'):
            errors.append("lab3.chandra.storage_quota_tb is required")
        
        if not self.get('lab3.swift.data_path'):
            errors.append("lab3.swift.data_path is required")
        
        if not self.get('lab3.chandra.data_path'):
            errors.append("lab3.chandra.data_path is required")
        
        # Check VAST configuration
        vast_config = self.get_vast_config()
        if not vast_config.get('user'):
            errors.append("vast.user is required")
        if not vast_config.get('address'):
            errors.append("vast.address is required")
        if not vast_config.get('password') and not vast_config.get('token'):
            errors.append("Either vast.password or vast.token is required")
        
        # Check VAST Database configuration
        vastdb_config = self.get('lab2.vastdb', {})
        if not vastdb_config.get('bucket'):
            errors.append("lab2.vastdb.bucket is required for analytics")
        if not vastdb_config.get('endpoint'):
            errors.append("lab2.vastdb.endpoint is required for analytics")
        
        if errors:
            print("❌ Lab3 Configuration Validation FAILED:")
            for error in errors:
                print(f"  ERROR: {error}")
            return False
        
        print("✅ Lab3 configuration validation passed")
        return True

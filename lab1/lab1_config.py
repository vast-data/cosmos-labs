# config_loader.py
import sys
import os
from pathlib import Path

# Add parent directory to path to import centralized config_loader
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader

# Create a lab-specific config loader that inherits from the centralized one
class Lab1ConfigLoader(ConfigLoader):
    """Lab 1 specific configuration loader"""
    
    def __init__(self):
        # Use centralized config files from parent directory
        project_root = Path(__file__).parent.parent
        super().__init__(
            config_path=str(project_root / "config.yaml"),
            secrets_path=str(project_root / "secrets.yaml")
        )
    
    def get_storage_config(self):
        """Get Lab 1 specific storage configuration"""
        return self.get('lab1.storage', {})
    
    def get_monitoring_config(self):
        """Get Lab 1 specific monitoring configuration"""
        return self.get('lab1.monitoring', {})
    
    def get_auto_provision_threshold(self):
        """Get auto-provision threshold for storage"""
        return self.get('lab1.storage.auto_provision_threshold', 75)
    
    def get_expansion_factor(self):
        """Get storage expansion factor"""
        return self.get('lab1.storage.expansion_factor', 1.5)
    
    def get_max_expansion_gb(self):
        """Get maximum storage expansion in GB"""
        return self.get('lab1.storage.max_expansion_gb', 10000)
    
    def get_alert_threshold(self):
        """Get alert threshold percentage"""
        return self.get('lab1.monitoring.alert_threshold', 80)
    
    def get_critical_threshold(self):
        """Get critical threshold percentage"""
        return self.get('lab1.monitoring.critical_threshold', 90) 
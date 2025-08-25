# config_loader.py
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from config_validator import ConfigValidator

class ConfigLoader:
    """Centralized configuration loader for all Orbital Dynamics labs"""
    
    def __init__(self, config_path: str = "config.yaml", secrets_path: str = "secrets.yaml"):
        self.config_path = Path(config_path)
        self.secrets_path = Path(secrets_path)
        self.config = {}
        self.secrets = {}
        
        self._load_config()
        self._load_secrets()
        self._merge_environment_variables()
    
    def _load_config(self):
        """Load main configuration file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
    
    def _load_secrets(self):
        """Load secrets file if it exists"""
        if self.secrets_path.exists():
            with open(self.secrets_path, 'r') as f:
                self.secrets = yaml.safe_load(f)
        else:
            print(f"Warning: Secrets file not found: {self.secrets_path}")
            self.secrets = {}
    
    def _merge_environment_variables(self):
        """Merge environment variables into secrets (overriding file values)"""
        # VAST authentication secrets
        if os.getenv('VAST_PASSWORD'):
            self.secrets['vast_password'] = os.getenv('VAST_PASSWORD')
        if os.getenv('VAST_TOKEN'):
            self.secrets['vast_token'] = os.getenv('VAST_TOKEN')
        if os.getenv('VAST_TENANT_NAME'):
            self.secrets['vast_tenant_name'] = os.getenv('VAST_TENANT_NAME')
        if os.getenv('VAST_API_VERSION'):
            self.secrets['vast_api_version'] = os.getenv('VAST_API_VERSION')
        
        # VAST connection settings
        if os.getenv('VAST_ADDRESS'):
            self.config['vast']['address'] = os.getenv('VAST_ADDRESS')
        if os.getenv('VAST_USER'):
            self.config['vast']['user'] = os.getenv('VAST_USER')
        
        # Catalog settings
        if os.getenv('VAST_CATALOG_PORT'):
            self.config['catalog']['port'] = int(os.getenv('VAST_CATALOG_PORT'))
        
        # External service secrets
        if os.getenv('SLACK_WEBHOOK_URL'):
            self.secrets['slack_webhook_url'] = os.getenv('SLACK_WEBHOOK_URL')
        if os.getenv('PAGERDUTY_API_KEY'):
            self.secrets['pagerduty_api_key'] = os.getenv('PAGERDUTY_API_KEY')
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'vast.user', 'lab1.storage.auto_provision_threshold')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret value using dot notation (e.g., 'vast_password', 'lab3.pipeline_db_password')"""
        keys = key.split('.')
        value = self.secrets
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_vast_config(self) -> Dict:
        """Get VAST configuration dictionary for vastpy client initialization"""
        # Start with non-sensitive config
        vast_config = self.config.get('vast', {}).copy()
        
        # Add sensitive secrets
        if self.secrets.get('vast_password'):
            vast_config['password'] = self.secrets['vast_password']
        if self.secrets.get('vast_token'):
            vast_config['token'] = self.secrets['vast_token']
        
        # Note: tenant_name and version are not supported in older vastpy versions
        # These are commented out to avoid compatibility issues
        # if self.secrets.get('vast_tenant_name'):
        #     vast_config['tenant_name'] = self.secrets['vast_tenant_name']
        # if self.secrets.get('vast_api_version'):
        #     vast_config['version'] = self.secrets['vast_api_version']
        
        # Remove empty values to avoid passing None to vastpy
        return {k: v for k, v in vast_config.items() if v}
    
    def get_lab_config(self, lab_name: str) -> Dict:
        """Get configuration specific to a particular lab"""
        return self.config.get(lab_name, {})
    
    def get_lab_secrets(self, lab_name: str) -> Dict:
        """Get secrets specific to a particular lab"""
        return self.secrets.get(lab_name, {})
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present using strict validation"""
        validator = ConfigValidator()
        
        # Validate the entire configuration structure
        if not validator.validate_config(self.config):
            print("Configuration validation failed:")
            validator.print_validation_report()
            return False
        
        # Additional validation for secrets
        has_password = self.secrets.get('vast_password')
        has_token = self.secrets.get('vast_token')
        
        if not has_password and not has_token:
            print("ERROR: Either vast_password or vast_token is required for authentication")
            return False
        
        # Print warnings if any
        if validator.get_warnings():
            print("Configuration warnings:")
            validator.print_validation_report()
        
        return True
    
    def get_monitoring_config(self) -> Dict:
        """Get monitoring configuration for VAST metrics"""
        return self.config.get('monitoring', {})
    
    def get_views_config(self) -> Dict:
        """Get VAST views configuration"""
        return self.config.get('views', {})
    
    def get_data_directories(self) -> list:
        """Get list of data directories"""
        return self.config.get('data', {}).get('directories', [])
    
    def get_metadata_config(self) -> Dict:
        """Get metadata extraction configuration"""
        return self.config.get('metadata', {})
    
    def get_logging_config(self) -> Dict:
        """Get logging configuration"""
        return self.config.get('logging', {})
    
    def get_performance_config(self) -> Dict:
        """Get performance configuration"""
        return self.config.get('performance', {})

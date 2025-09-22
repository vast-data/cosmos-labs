# config_validator.py
import yaml
from typing import Dict, Any, List
from pathlib import Path

class ConfigValidator:
    """Strict configuration validator to prevent dangerous default values"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the entire configuration structure"""
        self.errors = []
        self.warnings = []
        
        # Validate root-level required sections
        required_sections = ['vast', 's3', 'vastdb']
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing required section: {section}")
        
        if self.errors:
            return False
        
        # Validate each section
        self._validate_vast_section(config.get('vast', {}))
        self._validate_vastdb_section(config.get('vastdb', {}))
        
        # Validate lab-specific sections
        self._validate_lab_sections(config)
        
        return len(self.errors) == 0
    
    def _validate_vast_section(self, vast_config: Dict[str, Any]):
        """Validate VAST connection configuration"""
        required_fields = ['user', 'address']
        for field in required_fields:
            if not vast_config.get(field):
                self.errors.append(f"vast.{field} is required")
        
        # Validate address format
        address = vast_config.get('address')
        if address and not isinstance(address, str):
            self.errors.append("vast.address must be a string")
    
    def _validate_vastdb_section(self, vastdb_config: Dict[str, Any]):
        """Validate VAST Database configuration"""
        required_fields = ['endpoint']
        for field in required_fields:
            if not vastdb_config.get(field):
                self.errors.append(f"vastdb.{field} is required")
        
        # Validate endpoint format
        endpoint = vastdb_config.get('endpoint')
        if endpoint and not isinstance(endpoint, str):
            self.errors.append("vastdb.endpoint must be a string")
        
        # Validate ssl_verify is boolean
        ssl_verify = vastdb_config.get('ssl_verify')
        if ssl_verify is not None and not isinstance(ssl_verify, bool):
            self.errors.append("vastdb.ssl_verify must be a boolean")
    
    def _validate_lab_sections(self, config: Dict[str, Any]):
        """Validate lab-specific configuration sections"""
        lab_sections = ['lab1', 'lab2', 'lab3', 'lab4', 'lab5']
        
        for lab in lab_sections:
            if lab in config:
                lab_config = config[lab]
                if not isinstance(lab_config, dict):
                    self.errors.append(f"{lab} configuration must be a dictionary")
                else:
                    self._validate_lab_specific_config(lab, lab_config)
    
    def _validate_lab_specific_config(self, lab_name: str, lab_config: Dict[str, Any]):
        """Validate configuration for a specific lab"""
        if lab_name == 'lab1':
            self._validate_lab1_config(lab_config)
        elif lab_name == 'lab2':
            self._validate_lab2_config(lab_config)
        elif lab_name == 'lab3':
            self._validate_lab3_config(lab_config)
        # Add validation for other labs as needed
    
    def _validate_lab1_config(self, lab_config: Dict[str, Any]):
        """Validate Lab 1 specific configuration"""
        if 'storage' not in lab_config:
            self.errors.append("lab1.storage is required")
        else:
            storage_config = lab_config['storage']
            required_storage_fields = ['auto_provision_threshold', 'expansion_factor', 'max_expansion_gb']
            for field in required_storage_fields:
                if field not in storage_config:
                    self.errors.append(f"lab1.storage.{field} is required")
            
            # Validate thresholds
            if 'auto_provision_threshold' in storage_config:
                threshold = storage_config['auto_provision_threshold']
                if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
                    self.errors.append("lab1.storage.auto_provision_threshold must be a number between 0 and 100")
        
        if 'monitoring' not in lab_config:
            self.errors.append("lab1.monitoring is required")
        else:
            monitoring_config = lab_config['monitoring']
            required_monitoring_fields = ['alert_threshold', 'critical_threshold', 'refresh_interval_seconds', 'interval_seconds']
            for field in required_monitoring_fields:
                if field not in monitoring_config:
                    self.errors.append(f"lab1.monitoring.{field} is required")
            
            # Validate interval values
            if 'interval_seconds' in monitoring_config:
                interval = monitoring_config['interval_seconds']
                if not isinstance(interval, int) or interval < 1:
                    self.errors.append("lab1.monitoring.interval_seconds must be an integer >= 1")
            
            if 'refresh_interval_seconds' in monitoring_config:
                refresh_interval = monitoring_config['refresh_interval_seconds']
                if not isinstance(refresh_interval, int) or refresh_interval < 1:
                    self.errors.append("lab1.monitoring.refresh_interval_seconds must be an integer >= 1")
        
        # Validate views configuration
        if 'views' not in lab_config:
            self.errors.append("lab1.views is required")
        elif not isinstance(lab_config['views'], dict):
            self.errors.append("lab1.views must be a dictionary")
        else:
            views_config = lab_config['views']
            required_views = ['raw_data', 'processed_data']
            
            for view_name in required_views:
                if view_name not in views_config:
                    self.errors.append(f"lab1.views.{view_name} is required")
                else:
                    view_config = views_config[view_name]
                    if not isinstance(view_config, dict):
                        self.errors.append(f"lab1.views.{view_name} must be a dictionary")
                    else:
                        # Check required fields for each view
                        required_fields = ['path', 'bucket_name', 'quota_gb', 'policy_name', 'bucket_owner']
                        for field in required_fields:
                            if field not in view_config:
                                self.errors.append(f"lab1.views.{view_name}.{field} is required")
                            elif field == 'quota_gb' and not isinstance(view_config[field], (int, float)):
                                self.errors.append(f"lab1.views.{view_name}.quota_gb must be a number")
                            elif field == 'path' and not isinstance(view_config[field], str):
                                self.errors.append(f"lab1.views.{view_name}.path must be a string")
                            elif field == 'path' and not view_config[field].startswith('/'):
                                self.warnings.append(f"lab1.views.{view_name}.path should be an absolute path: {view_config[field]}")
    
    def _validate_lab2_config(self, lab_config: Dict[str, Any]):
        """Validate Lab 2 specific configuration"""
        # Validate raw_data section
        if 'raw_data' not in lab_config:
            self.errors.append("lab2.raw_data is required")
        else:
            raw_data_config = lab_config['raw_data']
            required_raw_data_fields = ['view_path', 'policy_name', 'bucket_owner']
            for field in required_raw_data_fields:
                if field not in raw_data_config:
                    self.errors.append(f"lab2.raw_data.{field} is required")
        
        # Validate database section
        if 'database' not in lab_config:
            self.errors.append("lab2.database is required")
        else:
            database_config = lab_config['database']
            required_database_fields = ['name', 'schema', 'view_path', 'policy_name', 'bucket_owner']
            for field in required_database_fields:
                if field not in database_config:
                    self.errors.append(f"lab2.database.{field} is required")
    
    def _validate_lab3_config(self, lab_config: Dict[str, Any]):
        """Validate Lab 3 specific configuration"""
        # Validate database section
        if 'database' not in lab_config:
            self.errors.append("lab3.database is required")
        else:
            database_config = lab_config['database']
            required_database_fields = ['name', 'schema', 'view_path', 'policy_name', 'bucket_owner']
            for field in required_database_fields:
                if field not in database_config:
                    self.errors.append(f"lab3.database.{field} is required")
        
        # Validate weather section (optional)
        if 'weather' in lab_config:
            weather_config = lab_config['weather']
            if 'presets' in weather_config and not isinstance(weather_config['presets'], dict):
                self.errors.append("lab3.weather.presets must be a dictionary")
    
    def get_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Get list of validation warnings"""
        return self.warnings
    
    def print_validation_report(self):
        """Print a formatted validation report"""
        if self.errors:
            print("❌ Configuration Validation FAILED:")
            for error in self.errors:
                print(f"  ERROR: {error}")
            print()
        
        if self.warnings:
            print("⚠️  Configuration Warnings:")
            for warning in self.warnings:
                print(f"  WARNING: {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ Configuration validation passed!")
        elif not self.errors:
            print("✅ Configuration validation passed with warnings!")
        else:
            print("❌ Configuration validation failed!")

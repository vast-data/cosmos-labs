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
        required_sections = ['vast', 'catalog', 'data', 'metadata', 'views', 'monitoring']
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing required section: {section}")
        
        if self.errors:
            return False
        
        # Validate each section
        self._validate_vast_section(config.get('vast', {}))
        self._validate_catalog_section(config.get('catalog', {}))
        self._validate_lab1_views(config.get('lab1', {}))
        self._validate_metadata_section(config.get('metadata', {}))
        self._validate_views_section(config.get('views', {}))
        self._validate_monitoring_section(config.get('monitoring', {}))
        
        # Validate lab-specific sections
        self._validate_lab_sections(config)
        
        # Validate logging and performance sections
        self._validate_logging_section(config.get('logging', {}))
        self._validate_performance_section(config.get('performance', {}))
        
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
    
    def _validate_catalog_section(self, catalog_config: Dict[str, Any]):
        """Validate catalog configuration"""
        required_fields = ['name', 'port', 'batch_size', 'timeout_seconds', 'max_retries']
        for field in required_fields:
            if field not in catalog_config:
                self.errors.append(f"catalog.{field} is required")
        
        # Validate numeric fields
        if 'port' in catalog_config and not isinstance(catalog_config['port'], int):
            self.errors.append("catalog.port must be an integer")
        if 'batch_size' in catalog_config and not isinstance(catalog_config['batch_size'], int):
            self.errors.append("catalog.batch_size must be an integer")
        if 'timeout_seconds' in catalog_config and not isinstance(catalog_config['timeout_seconds'], int):
            self.errors.append("catalog.timeout_seconds must be an integer")
        if 'max_retries' in catalog_config and not isinstance(catalog_config['max_retries'], int):
            self.errors.append("catalog.max_retries must be an integer")
    
    def _validate_lab1_views(self, lab1_config: Dict[str, Any]):
        """Validate lab1 views configuration"""
        if 'views' not in lab1_config:
            self.errors.append("lab1.views is required")
        elif not isinstance(lab1_config['views'], dict):
            self.errors.append("lab1.views must be a dictionary")
        else:
            views_config = lab1_config['views']
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
    
    def _validate_metadata_section(self, metadata_config: Dict[str, Any]):
        """Validate metadata configuration"""
        if 'supported_formats' not in metadata_config:
            self.errors.append("metadata.supported_formats is required")
        elif not isinstance(metadata_config['supported_formats'], list):
            self.errors.append("metadata.supported_formats must be a list")
        elif len(metadata_config['supported_formats']) == 0:
            self.errors.append("metadata.supported_formats cannot be empty")
        
        if 'quality_threshold' not in metadata_config:
            self.errors.append("metadata.quality_threshold is required")
        elif not isinstance(metadata_config['quality_threshold'], (int, float)):
            self.errors.append("metadata.quality_threshold must be a number")
        elif not 0 <= metadata_config['quality_threshold'] <= 1:
            self.errors.append("metadata.quality_threshold must be between 0 and 1")
    
    def _validate_views_section(self, views_config: Dict[str, Any]):
        """Validate views configuration"""
        required_fields = ['default_policy', 'create_directories', 'protocols']
        for field in required_fields:
            if field not in views_config:
                self.errors.append(f"views.{field} is required")
        
        if 'protocols' in views_config and not isinstance(views_config['protocols'], list):
            self.errors.append("views.protocols must be a list")
        if 'create_directories' in views_config and not isinstance(views_config['create_directories'], bool):
            self.errors.append("views.create_directories must be a boolean")
    
    def _validate_monitoring_section(self, monitoring_config: Dict[str, Any]):
        """Validate monitoring configuration"""
        if 'enabled' not in monitoring_config:
            self.errors.append("monitoring.enabled is required")
        elif not isinstance(monitoring_config['enabled'], bool):
            self.errors.append("monitoring.enabled must be a boolean")
        
        if 'interval_seconds' not in monitoring_config:
            self.errors.append("monitoring.interval_seconds is required")
        elif not isinstance(monitoring_config['interval_seconds'], int):
            self.errors.append("monitoring.interval_seconds must be an integer")
        elif monitoring_config['interval_seconds'] < 1:
            self.errors.append("monitoring.interval_seconds must be at least 1 second")
        
        if 'metrics' not in monitoring_config:
            self.errors.append("monitoring.metrics is required")
        elif not isinstance(monitoring_config['metrics'], list):
            self.errors.append("monitoring.metrics must be a list")
    
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
            required_monitoring_fields = ['alert_threshold', 'critical_threshold']
            for field in required_monitoring_fields:
                if field not in monitoring_config:
                    self.errors.append(f"lab1.monitoring.{field} is required")
    
    def _validate_lab2_config(self, lab_config: Dict[str, Any]):
        """Validate Lab 2 specific configuration"""
        if 'catalog' not in lab_config:
            self.errors.append("lab2.catalog is required")
        else:
            catalog_config = lab_config['catalog']
            required_catalog_fields = ['batch_size', 'max_concurrent_extractions', 'extraction_timeout_seconds']
            for field in required_catalog_fields:
                if field not in catalog_config:
                    self.errors.append(f"lab2.catalog.{field} is required")
        
        if 'search' not in lab_config:
            self.errors.append("lab2.search is required")
        else:
            search_config = lab_config['search']
            required_search_fields = ['default_limit', 'max_limit', 'enable_fuzzy_search']
            for field in required_search_fields:
                if field not in search_config:
                    self.errors.append(f"lab2.search.{field} is required")
    
    def _validate_logging_section(self, logging_config: Dict[str, Any]):
        """Validate logging configuration"""
        required_fields = ['level', 'format', 'file', 'max_size_mb', 'backup_count']
        for field in required_fields:
            if field not in logging_config:
                self.errors.append(f"logging.{field} is required")
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if 'level' in logging_config and logging_config['level'] not in valid_levels:
            self.errors.append(f"logging.level must be one of: {', '.join(valid_levels)}")
    
    def _validate_performance_section(self, performance_config: Dict[str, Any]):
        """Validate performance configuration"""
        required_fields = ['max_concurrent_operations', 'operation_timeout_seconds', 'cache_size_mb', 'enable_compression']
        for field in required_fields:
            if field not in performance_config:
                self.errors.append(f"performance.{field} is required")
        
        # Validate numeric fields
        if 'max_concurrent_operations' in performance_config and not isinstance(performance_config['max_concurrent_operations'], int):
            self.errors.append("performance.max_concurrent_operations must be an integer")
        if 'operation_timeout_seconds' in performance_config and not isinstance(performance_config['operation_timeout_seconds'], int):
            self.errors.append("performance.operation_timeout_seconds must be an integer")
        if 'cache_size_mb' in performance_config and not isinstance(performance_config['cache_size_mb'], int):
            self.errors.append("performance.cache_size_mb must be an integer")
        if 'enable_compression' in performance_config and not isinstance(performance_config['enable_compression'], bool):
            self.errors.append("performance.enable_compression must be a boolean")
    
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

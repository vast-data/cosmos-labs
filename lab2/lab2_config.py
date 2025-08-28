# config_loader.py
import sys
import os
from pathlib import Path

# Add parent directory to path to import centralized config_loader
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader

# Create a lab-specific config loader that inherits from the centralized one
class Lab2ConfigLoader(ConfigLoader):
    """Lab 2 specific configuration loader"""
    
    def __init__(self):
        # Use centralized config files from parent directory
        project_root = Path(__file__).parent.parent
        super().__init__(
            config_path=str(project_root / "config.yaml"),
            secrets_path=str(project_root / "secrets.yaml")
        )
    
    def get_catalog_config(self):
        """Get Lab 2 specific catalog configuration"""
        return self.get('lab2.catalog', {})
    
    def get_search_config(self):
        """Get Lab 2 specific search configuration"""
        return self.get('lab2.search', {})
    
    def get_batch_size(self):
        """Get batch size for metadata processing"""
        return self.get('lab2.catalog.batch_size', 1000)
    
    def get_max_concurrent_extractions(self):
        """Get maximum concurrent metadata extractions"""
        return self.get('lab2.catalog.max_concurrent_extractions', 10)
    
    def get_extraction_timeout(self):
        """Get timeout for metadata extraction operations"""
        return self.get('lab2.catalog.extraction_timeout_seconds', 60)
    
    def get_default_search_limit(self):
        """Get default limit for search results"""
        return self.get('lab2.search.default_limit', 100)
    
    def get_max_search_limit(self):
        """Get maximum limit for search results"""
        return self.get('lab2.search.max_limit', 1000)
    
    def get_fuzzy_search_enabled(self):
        """Get whether fuzzy search is enabled"""
        return self.get('lab2.search.enable_fuzzy_search', True) 
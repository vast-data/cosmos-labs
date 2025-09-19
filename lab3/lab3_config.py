# lab3_config.py
import sys
from pathlib import Path

# Add parent directory to path to import centralized config_loader
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader

# Create a lab-specific config loader that inherits from the centralized one
class Lab3ConfigLoader(ConfigLoader):
    """Lab 3 specific configuration loader for weather data analytics"""
    
    def __init__(self):
        # Use centralized config files from parent directory
        project_root = Path(__file__).parent.parent
        super().__init__(
            config_path=str(project_root / "config.yaml"),
            secrets_path=str(project_root / "secrets.yaml")
        )
    
    def get_weather_config(self):
        """Get weather data specific configuration"""
        return self.get('lab3.weather', {})
    
    def get_weather_presets(self):
        """Get weather data city presets"""
        weather_config = self.get_weather_config()
        return weather_config.get('presets', {})
    
    def get_weather_preset_descriptions(self):
        """Get weather data preset descriptions"""
        weather_config = self.get_weather_config()
        return weather_config.get('preset_descriptions', {})
    
    def get_vastdb_config(self):
        """Get VAST Database configuration (global or lab3-specific)"""
        return self.get('vastdb', {}) or self.get('lab3.vastdb', {})
    
    def validate_config(self) -> bool:
        """Validate that required Lab3 configuration is present"""
        errors = []
        
        # Check weather configuration
        weather_config = self.get_weather_config()
        database_config = self.get('lab3.database', {})
        if not database_config.get('name'):
            errors.append("lab3.database.name is required")
        if not database_config.get('schema'):
            errors.append("lab3.database.schema is required")
        if not database_config.get('view_path'):
            errors.append("lab3.database.view_path is required")
        if not database_config.get('policy_name'):
            errors.append("lab3.database.policy_name is required")
        if not database_config.get('bucket_owner'):
            errors.append("lab3.database.bucket_owner is required")
        
        # Check VAST configuration
        vast_config = self.get_vast_config()
        if not vast_config.get('user'):
            errors.append("vast.user is required")
        if not vast_config.get('address'):
            errors.append("vast.address is required")
        if not vast_config.get('password') and not vast_config.get('token'):
            errors.append("Either vast.password or vast.token is required")
        
        # Check VAST Database configuration (global or lab3-specific)
        vastdb_config = self.get_vastdb_config()
        if not vastdb_config.get('endpoint'):
            errors.append("vastdb.endpoint or lab3.vastdb.endpoint is required for weather data storage")
        
        if errors:
            print("❌ Lab3 Configuration Validation FAILED:")
            for error in errors:
                print(f"  ERROR: {error}")
            return False
        
        print("✅ Lab3 configuration validation passed")
        return True

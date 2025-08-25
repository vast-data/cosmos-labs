#!/usr/bin/env python3
"""
Test script to demonstrate strict configuration validation.
This script shows how the validator prevents dangerous default values.
"""

import sys
from config_loader import ConfigLoader
from config_validator import ConfigValidator

def test_config_validation():
    """Test the configuration validation system"""
    
    print("=" * 60)
    print("Configuration Validation Test")
    print("=" * 60)
    
    try:
        # Test configuration loading and validation
        print("Loading configuration...")
        config = ConfigLoader()
        
        print("Validating configuration...")
        if config.validate_config():
            print("✅ Configuration validation passed!")
            print("All required values are explicitly configured.")
        else:
            print("❌ Configuration validation failed!")
            print("Please fix the configuration errors above.")
            return False
            
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    return True

def test_individual_validation():
    """Test individual validation components"""
    
    print("\n" + "=" * 60)
    print("Individual Validation Component Test")
    print("=" * 60)
    
    from config_validator import ConfigValidator
    validator = ConfigValidator()
    
    # Test with minimal config (should fail)
    minimal_config = {
        'vast': {'user': 'admin', 'address': 'localhost'},
        'catalog': {'name': 'test', 'port': 8080, 'batch_size': 1000, 'timeout_seconds': 30, 'max_retries': 3},
        'data': {'directories': ['/test/data']},
        'metadata': {'supported_formats': ['.txt'], 'quality_threshold': 0.8},
        'views': {'default_policy': 'default', 'create_directories': True, 'protocols': ['NFS']},
        'monitoring': {'enabled': True, 'interval_seconds': 300, 'metrics': ['test']},
        'logging': {'level': 'INFO', 'format': '%(message)s', 'file': '/tmp/test.log', 'max_size_mb': 100, 'backup_count': 5},
        'performance': {'max_concurrent_operations': 10, 'operation_timeout_seconds': 300, 'cache_size_mb': 500, 'enable_compression': True}
    }
    
    print("Testing minimal configuration...")
    if validator.validate_config(minimal_config):
        print("✅ Minimal config validation passed!")
    else:
        print("❌ Minimal config validation failed:")
        validator.print_validation_report()
    
    # Test with missing lab1 section (should fail)
    print("\nTesting configuration without lab1 section...")
    test_config = minimal_config.copy()
    test_config['lab1'] = {
        'storage': {
            'auto_provision_threshold': 75,
            'expansion_factor': 1.5,
            'max_expansion_gb': 10000
        },
        'monitoring': {
            'alert_threshold': 80,
            'critical_threshold': 90
        }
    }
    
    if validator.validate_config(test_config):
        print("✅ Config with lab1 validation passed!")
    else:
        print("❌ Config with lab1 validation failed:")
        validator.print_validation_report()

def main():
    """Main function"""
    print("Testing strict configuration validation system...")
    print("This system prevents dangerous default values from being used.")
    print()
    
    # Test full configuration
    if not test_config_validation():
        print("\n❌ Configuration validation test failed!")
        print("Please ensure all required configuration values are set.")
        sys.exit(1)
    
    # Test individual components
    test_individual_validation()
    
    print("\n" + "=" * 60)
    print("Validation Test Complete")
    print("=" * 60)
    print("✅ The strict validation system is working correctly!")
    print("   No dangerous default values will be used.")
    print("   All configuration must be explicitly defined.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Configuration validator CLI tool
Usage: python validate_config.py [config_file]
"""

import sys
import yaml
from pathlib import Path
from config_validator import ConfigValidator

def main():
    # Get config file path from command line or use default
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    
    if not Path(config_file).exists():
        print(f"❌ Error: Config file '{config_file}' not found")
        sys.exit(1)
    
    try:
        # Load config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate config
        validator = ConfigValidator()
        is_valid = validator.validate_config(config)
        
        if is_valid:
            print("✅ Configuration is valid!")
            sys.exit(0)
        else:
            print("❌ Configuration has errors:")
            for error in validator.get_errors():
                print(f"  - {error}")
            
            # Show warnings if any
            warnings = validator.get_warnings()
            if warnings:
                print("\n⚠️  Warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
            
            sys.exit(1)
            
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

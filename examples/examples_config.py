#!/usr/bin/env python3
"""
Simple config loader for examples
Points to the parent directory for config files
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import the main config loader
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config_loader import ConfigLoader

class ExamplesConfigLoader(ConfigLoader):
    """Config loader for examples that looks in the parent directory"""
    
    def __init__(self):
        # Point to config files in parent directory
        config_path = parent_dir / "config.yaml"
        secrets_path = parent_dir / "secrets.yaml"
        
        super().__init__(
            config_path=str(config_path),
            secrets_path=str(secrets_path)
        )

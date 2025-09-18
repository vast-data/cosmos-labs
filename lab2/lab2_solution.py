#!/usr/bin/env python3
"""
Lab 2 Complete Solution - Main Entry Point
This is now a lightweight wrapper around the focused Lab 2 scripts
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import and run the orchestrator
from lab2_orchestrator import main

if __name__ == "__main__":
    main()

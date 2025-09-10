#!/usr/bin/env python3
"""
Dependency Installation Script for Lab 3
========================================

This script helps install the required dependencies for Lab 3:
Multi-Observatory Data Storage and Analytics.

Installs:
- Python packages (astroquery, astropy, etc.)
- Provides instructions for CIAO installation
- Validates the installation

Author: Lab 3 Development Team
Date: 2025-01-10
"""

import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Run a command and return success status."""
    try:
        logger.info(f"📦 {description}...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"❌ Command not found: {cmd[0]}")
        return False

def install_python_packages():
    """Install required Python packages."""
    packages = [
        "astroquery>=0.4.7",
        "astropy>=5.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "pyyaml>=6.0"
    ]
    
    logger.info("🐍 Installing Python packages...")
    
    for package in packages:
        if not run_command([sys.executable, "-m", "pip", "install", package], 
                          f"Installing {package}"):
            return False
    
    return True

def check_ciao_installation():
    """Check if CIAO is installed."""
    try:
        result = subprocess.run(['download_chandra_obsid', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ CIAO is installed and available")
            return True
        else:
            logger.warning("⚠️ CIAO command found but not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("⚠️ CIAO not found")
        return False

def validate_installation():
    """Validate that all dependencies are working."""
    logger.info("🔍 Validating installation...")
    
    # Test astroquery
    try:
        from astroquery.heasarc import Heasarc
        from astroquery.cda import CDA
        logger.info("✅ astroquery imports successfully")
    except ImportError as e:
        logger.error(f"❌ astroquery import failed: {e}")
        return False
    
    # Test astropy
    try:
        from astropy.coordinates import SkyCoord
        import astropy.units as u
        logger.info("✅ astropy imports successfully")
    except ImportError as e:
        logger.error(f"❌ astropy import failed: {e}")
        return False
    
    # Test CIAO
    ciao_available = check_ciao_installation()
    
    return True

def show_ciao_instructions():
    """Show instructions for installing CIAO."""
    print("\n" + "="*60)
    print("📋 CIAO Installation Instructions")
    print("="*60)
    print()
    print("CIAO (Chandra Interactive Analysis of Observations) is required")
    print("for downloading Chandra data. Please install it manually:")
    print()
    print("1. Visit: https://cxc.cfa.harvard.edu/ciao/download/")
    print("2. Download CIAO for your operating system")
    print("3. Follow the installation instructions")
    print("4. Add CIAO to your PATH environment variable")
    print()
    print("After installation, verify with:")
    print("   download_chandra_obsid --help")
    print()
    print("Note: CIAO is not a Python package, so it must be installed")
    print("separately from the Python dependencies.")
    print()

def main():
    """Main installation function."""
    logger.info("🚀 Starting Lab 3 dependency installation...")
    
    # Install Python packages
    if not install_python_packages():
        logger.error("❌ Failed to install Python packages")
        return 1
    
    # Check CIAO installation
    ciao_available = check_ciao_installation()
    
    # Validate installation
    if not validate_installation():
        logger.error("❌ Installation validation failed")
        return 1
    
    # Show results
    print("\n" + "="*60)
    print("📊 Installation Summary")
    print("="*60)
    print("✅ Python packages: Installed")
    print(f"{'✅' if ciao_available else '❌'} CIAO: {'Available' if ciao_available else 'Not found'}")
    
    if not ciao_available:
        show_ciao_instructions()
        print("⚠️ You can still use Lab 3, but Chandra data downloads will use placeholders")
    else:
        print("\n🎉 All dependencies installed successfully!")
        print("You can now run the automated data downloader:")
        print("   python automated_data_downloader.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

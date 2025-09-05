#!/usr/bin/env python3
"""
Dependency Installation Helper for Orbital Dynamics Labs
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    """Print installation header"""
    print("=" * 60)
    print("🚀 ORBITAL DYNAMICS LABS - DEPENDENCY INSTALLER")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print("✅ pip is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip is not available")
        return False

def install_requirements(requirements_file, description):
    """Install requirements from a specific file"""
    if not os.path.exists(requirements_file):
        print(f"⚠️  {requirements_file} not found, skipping...")
        return False
    
    print(f"\n📦 Installing {description}...")
    print(f"   File: {requirements_file}")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} installed successfully")
            return True
        else:
            print(f"❌ Failed to install {description}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing {description}: {e}")
        return False

def main():
    """Main installation function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_pip():
        return False
    
    print("\n🔧 Installation Options:")
    print("1. Full development environment (recommended)")
    print("2. Lab 1 only (Storage Infrastructure)")
    print("3. Lab 2 only (Metadata Infrastructure)")
    print("4. Lab 6 only (Pipeline Storage Integration)")
    print("5. Examples only (Directory Explorer, Orphaned Data Discovery)")
    
    print("\n💡 Recommendation: Start with option 1 for full functionality")
    
    # Install root requirements (full environment)
    print("\n" + "="*40)
    print("🏗️  INSTALLING FULL DEVELOPMENT ENVIRONMENT")
    print("="*40)
    
    if install_requirements("requirements.txt", "full development environment"):
        print("\n✅ Full environment installed successfully!")
        print("   You can now run any lab with full functionality")
    else:
        print("\n⚠️  Full environment installation had issues")
        print("   Trying individual lab installations...")
        
        # Try individual lab installations
        print("\n" + "="*40)
        print("🔬 INSTALLING INDIVIDUAL LAB DEPENDENCIES")
        print("="*40)
        
        install_requirements("lab1/requirements.txt", "Lab 1 dependencies")
        install_requirements("lab2/requirements.txt", "Lab 2 dependencies")
        install_requirements("lab6/requirements.txt", "Lab 6 dependencies")
        
        # Install examples dependencies (pandas, pyarrow for catalog explorer)
        print("\n📚 Installing examples dependencies...")
        examples_deps = ["pandas>=1.5.0", "pyarrow>=10.0.0"]
        for dep in examples_deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                              capture_output=True, check=True)
                print(f"✅ {dep} installed")
            except subprocess.CalledProcessError:
                print(f"⚠️  {dep} installation failed (may already be installed)")
    
    print("\n" + "="*60)
    print("🎯 INSTALLATION COMPLETE!")
    print("="*60)
    print("\n📚 Next Steps:")
    print("1. Configure your config.yaml and secrets.yaml")
    print("2. Set up VAST Data Platform access")
    print("3. Run: python3 lab1/test_basic_imports.py")
    print("4. Start with Lab 1: cd lab1 && python3 lab1_solution.py --help")
    print("5. Try examples: cd examples && python3 08_directory_catalog_explorer.py")
    print("\n💡 For help: Check the README.md files in each lab directory")
    
    return True

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify basic imports and configuration loading
"""

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import argparse
        print("✅ argparse imported successfully")
    except ImportError as e:
        print(f"❌ argparse import failed: {e}")
        return False
    
    try:
        import time
        import logging
        import sys
        from datetime import datetime, timedelta
        from typing import Dict, List, Optional
        print("✅ Standard library imports successful")
    except ImportError as e:
        print(f"❌ Standard library import failed: {e}")
        return False
    
    try:
        from lab1_config import Lab1ConfigLoader
        print("✅ Lab1ConfigLoader imported successfully")
    except ImportError as e:
        print(f"❌ Lab1ConfigLoader import failed: {e}")
        return False
    
    try:
        from safety_checker import SafetyChecker, SafetyCheckFailed
        print("✅ SafetyChecker imports successful")
    except ImportError as e:
        print(f"❌ SafetyChecker imports failed: {e}")
        return False
    
    return True

def test_config_loading():
    """Test configuration loading (without vastpy)"""
    try:
        from lab1_config import Lab1ConfigLoader
        
        # This will fail without config files, but we can test the import
        print("✅ Lab1ConfigLoader class definition accessible")
        
        # Test that the class has the expected methods
        expected_methods = [
            'get_storage_config',
            'get_monitoring_config', 
            'get_auto_provision_threshold',
            'get_expansion_factor',
            'get_max_expansion_gb',
            'get_alert_threshold',
            'get_critical_threshold'
        ]
        
        for method in expected_methods:
            if hasattr(Lab1ConfigLoader, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Lab 1 Basic Imports and Configuration")
    print("=" * 50)
    
    # Test imports
    print("\n📦 Testing imports...")
    if not test_imports():
        print("❌ Import tests failed")
        return False
    
    # Test configuration
    print("\n⚙️  Testing configuration...")
    if not test_config_loading():
        print("❌ Configuration tests failed")
        return False
    
    print("\n✅ All basic tests passed!")
    print("\n💡 Note: This test doesn't verify VAST connectivity")
    print("   To test with VAST, you'll need:")
    print("   - vastpy installed")
    print("   - config.yaml and secrets.yaml configured")
    print("   - VAST system accessible")
    
    return True

if __name__ == "__main__":
    main()

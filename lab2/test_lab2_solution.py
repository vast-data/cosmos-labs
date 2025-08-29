#!/usr/bin/env python3
"""
Test script for Lab 2 Complete Solution
Verifies that all components can be imported and initialized
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    try:
        logger.info("🔍 Testing imports...")
        
        # Test config loader
        from config_loader import ConfigLoader
        logger.info("✅ ConfigLoader imported successfully")
        
        # Test VAST database manager
        from vast_database_manager import VASTDatabaseManager
        logger.info("✅ VASTDatabaseManager imported successfully")
        
        # Test Swift metadata extractor
        from swift_metadata_extractor import SwiftMetadataExtractor
        logger.info("✅ SwiftMetadataExtractor imported successfully")
        
        # Test complete solution
        from lab2_complete_solution import Lab2CompleteSolution
        logger.info("✅ Lab2CompleteSolution imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_config_loading():
    """Test that configuration can be loaded"""
    try:
        logger.info("🔍 Testing configuration loading...")
        
        from config_loader import ConfigLoader
        
        # Load configuration from parent directory
        project_root = Path(__file__).parent.parent
        config_path = str(project_root / "config.yaml")
        secrets_path = str(project_root / "secrets.yaml")
        
        config = ConfigLoader(config_path, secrets_path)
        logger.info("✅ Configuration loaded successfully")
        
        # Check VAST Database settings
        vastdb_config = config.get('lab2.vastdb')
        if vastdb_config:
            logger.info(f"✅ VAST Database config found: {vastdb_config}")
        else:
            logger.warning("⚠️  VAST Database config not found")
        
        # Check Lab 2 settings
        lab2_config = config.get('lab2')
        if lab2_config:
            logger.info(f"✅ Lab 2 config found: {lab2_config}")
        else:
            logger.warning("⚠️  Lab 2 config not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {e}")
        return False

def test_component_initialization():
    """Test that components can be initialized"""
    try:
        logger.info("🔍 Testing component initialization...")
        
        from config_loader import ConfigLoader
        from vast_database_manager import VASTDatabaseManager
        from swift_metadata_extractor import SwiftMetadataExtractor
        
        # Load configuration from parent directory
        project_root = Path(__file__).parent.parent
        config_path = str(project_root / "config.yaml")
        secrets_path = str(project_root / "secrets.yaml")
        
        config = ConfigLoader(config_path, secrets_path)
        
        # Initialize VAST Database Manager
        db_manager = VASTDatabaseManager(config)
        logger.info("✅ VAST Database Manager initialized")
        
        # Initialize Swift Metadata Extractor
        metadata_extractor = SwiftMetadataExtractor(config)
        logger.info("✅ Swift Metadata Extractor initialized")
        
        # Clean up
        db_manager.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Component initialization failed: {e}")
        return False

def test_swift_datasets():
    """Test Swift datasets availability"""
    try:
        logger.info("🔍 Testing Swift datasets availability...")
        
        swift_datasets_dir = Path(__file__).parent / "swift_datasets"
        
        if not swift_datasets_dir.exists():
            logger.warning(f"⚠️  Swift datasets directory not found: {swift_datasets_dir}")
            logger.info("💡 This is expected if datasets haven't been downloaded yet")
            return True
        
        # Count datasets
        datasets = [d for d in swift_datasets_dir.iterdir() if d.is_dir()]
        logger.info(f"✅ Found {len(datasets)} Swift datasets:")
        
        for dataset in datasets:
            file_count = sum(1 for f in dataset.rglob('*') if f.is_file())
            total_size = sum(f.stat().st_size for f in dataset.rglob('*') if f.is_file())
            size_gb = total_size / (1024**3)
            logger.info(f"   📂 {dataset.name}: {file_count} files, {size_gb:.2f} GB")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Swift datasets test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Starting Lab 2 Solution Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config_loading),
        ("Component Initialization Test", test_component_initialization),
        ("Swift Datasets Test", test_swift_datasets)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {total - passed}")
    logger.info(f"📊 Total: {total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Lab 2 solution is ready.")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())

# test_lab3_solution.py
import sys
import os
from pathlib import Path

# Add parent directory to path for centralized config
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing Lab 3 imports...")
    
    try:
        from lab3.lab3_config import Lab3ConfigLoader
        print("✅ Lab3ConfigLoader imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Lab3ConfigLoader: {e}")
        return False
    
    try:
        from lab3.multi_observatory_storage_manager import MultiObservatoryStorageManager
        print("✅ MultiObservatoryStorageManager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import MultiObservatoryStorageManager: {e}")
        return False
    
    try:
        from lab3.cross_observatory_analytics import CrossObservatoryAnalytics
        print("✅ CrossObservatoryAnalytics imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import CrossObservatoryAnalytics: {e}")
        return False
    
    try:
        from lab3.lab3_solution import Lab3CompleteSolution
        print("✅ Lab3CompleteSolution imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Lab3CompleteSolution: {e}")
        return False
    
    return True

def test_config_loading():
    """Test configuration loading"""
    print("\n🧪 Testing configuration loading...")
    
    try:
        from lab3.lab3_config import Lab3ConfigLoader
        config = Lab3ConfigLoader()
        print("✅ Configuration loaded successfully")
        
        # Test specific configuration methods
        swift_config = config.get_swift_config()
        chandra_config = config.get_chandra_config()
        analytics_config = config.get_analytics_config()
        
        print(f"✅ SWIFT config: {len(swift_config)} items")
        print(f"✅ Chandra config: {len(chandra_config)} items")
        print(f"✅ Analytics config: {len(analytics_config)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_storage_manager():
    """Test storage manager initialization"""
    print("\n🧪 Testing storage manager initialization...")
    
    try:
        from lab3.lab3_config import Lab3ConfigLoader
        from lab3.multi_observatory_storage_manager import MultiObservatoryStorageManager
        
        config = Lab3ConfigLoader()
        storage_manager = MultiObservatoryStorageManager(config, production_mode=False, show_api_calls=False)
        print("✅ Storage manager initialized successfully")
        
        # Test configuration access
        swift_quota = storage_manager.swift_quota_tb
        chandra_quota = storage_manager.chandra_quota_tb
        
        print(f"✅ SWIFT quota: {swift_quota} TB")
        print(f"✅ Chandra quota: {chandra_quota} TB")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage manager initialization failed: {e}")
        return False

def test_analytics_manager():
    """Test analytics manager initialization"""
    print("\n🧪 Testing analytics manager initialization...")
    
    try:
        from lab3.lab3_config import Lab3ConfigLoader
        from lab3.cross_observatory_analytics import CrossObservatoryAnalytics
        
        config = Lab3ConfigLoader()
        analytics_manager = CrossObservatoryAnalytics(config, show_api_calls=False)
        print("✅ Analytics manager initialized successfully")
        
        # Test configuration access
        batch_size = analytics_manager.batch_size
        query_timeout = analytics_manager.query_timeout
        
        print(f"✅ Batch size: {batch_size}")
        print(f"✅ Query timeout: {query_timeout}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics manager initialization failed: {e}")
        return False

def test_solution_integration():
    """Test complete solution integration"""
    print("\n🧪 Testing solution integration...")
    
    try:
        from lab3.lab3_config import Lab3ConfigLoader
        from lab3.lab3_solution import Lab3CompleteSolution
        
        config = Lab3ConfigLoader()
        solution = Lab3CompleteSolution(config, production_mode=False, show_api_calls=False)
        print("✅ Complete solution initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Solution integration failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Lab 3 Solution Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_loading,
        test_storage_manager,
        test_analytics_manager,
        test_solution_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Lab 3 solution is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

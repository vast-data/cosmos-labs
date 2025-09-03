#!/usr/bin/env python3
"""
Example 1: Connect to VAST Management System
Simple connection test to verify VAST access
"""

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient

def main():
    print("🚀 Example 1: Connect to VAST Management System")
    print("=" * 50)
    
    try:
        # Load configuration
        config = ExamplesConfigLoader()
        vast_config = config.get_vast_config()
        
        # Build client parameters
        address = vast_config['address']
        if address.startswith('https://'):
            address = address[8:]
        elif address.startswith('http://'):
            address = address[7:]
        
        print(f"📡 Connecting to: {address}")
        print(f"👤 User: {vast_config['user']}")
        
        # Create VAST client
        client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=address
        )
        
        # Test connection by getting system info
        print("🔍 Testing connection...")
        system_info = client.system.get()
        
        print("✅ Connection successful!")
        print(f"📊 VAST Version: {system_info.get('version', 'Unknown')}")
        print(f"🏢 Cluster Name: {system_info.get('cluster_name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

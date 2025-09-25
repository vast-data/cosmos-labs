#!/usr/bin/env python3
"""
Example 2: List Storage Views
Show all available storage views and their status
"""

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient

def main():
    print("📁 Example 2: List Storage Views")
    print("=" * 50)
    
    try:
        # Load configuration and connect
        config = ExamplesConfigLoader()
        vast_config = config.get_vast_config()
        
        address = vast_config['address']
        if address.startswith('https://'):
            address = address[8:]
        elif address.startswith('http://'):
            address = address[7:]
        
        client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=address
        )
        
        print("🔍 Fetching storage views...")
        views = client.views.get()
        
        if not views:
            print("📭 No storage views found")
            return True
        
        print(f"📊 Found {len(views)} storage views:")
        print()
        
        for i, view in enumerate(views, 1):
            path = view.get('path', 'Unknown')
            logical_capacity = view.get('logical_capacity', 0)
            physical_capacity = view.get('physical_capacity', 0)
            
            # Convert to GB
            logical_gb = logical_capacity / (1024**3) if logical_capacity else 0
            physical_gb = physical_capacity / (1024**3) if physical_capacity else 0
            
            print(f"{i:2d}. {path}")
            print(f"    📏 Logical Size: {logical_gb:.1f} GB")
            print(f"    📏 Physical Size: {physical_gb:.1f} GB")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

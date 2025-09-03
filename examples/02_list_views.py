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
            size_gb = view.get('logical_size', 0) / (1024**3)  # Convert to GB
            utilization = view.get('utilization_percent', 0)
            
            # Status emoji based on utilization
            if utilization > 90:
                status_emoji = "🔴"
            elif utilization > 70:
                status_emoji = "🟡"
            else:
                status_emoji = "🟢"
            
            print(f"{i:2d}. {status_emoji} {path}")
            print(f"    📏 Size: {size_gb:.1f} GB")
            print(f"    📈 Utilization: {utilization:.1f}%")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

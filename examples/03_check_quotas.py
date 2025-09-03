#!/usr/bin/env python3
"""
Example 3: Check Quota Status
Show quota information for storage views
"""

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient

def format_size(bytes_size):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def main():
    print("📊 Example 3: Check Quota Status")
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
        
        print("🔍 Fetching quota information...")
        quotas = client.quotas.get()
        
        if not quotas:
            print("📭 No quotas found")
            return True
        
        print(f"📊 Found {len(quotas)} quota configurations:")
        print()
        
        for i, quota in enumerate(quotas, 1):
            view_path = quota.get('view_path', 'Unknown')
            soft_limit = quota.get('soft_limit', 0)
            hard_limit = quota.get('hard_limit', 0)
            current_usage = quota.get('current_usage', 0)
            
            # Calculate utilization percentage
            if hard_limit > 0:
                utilization = (current_usage / hard_limit) * 100
            else:
                utilization = 0
            
            # Status emoji based on utilization
            if utilization > 90:
                status_emoji = "🔴 CRITICAL"
            elif utilization > 70:
                status_emoji = "🟡 WARNING"
            else:
                status_emoji = "🟢 OK"
            
            print(f"{i:2d}. {status_emoji} {view_path}")
            print(f"    📏 Current Usage: {format_size(current_usage)}")
            print(f"    ⚠️  Soft Limit: {format_size(soft_limit)}")
            print(f"    🚫 Hard Limit: {format_size(hard_limit)}")
            print(f"    📈 Utilization: {utilization:.1f}%")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

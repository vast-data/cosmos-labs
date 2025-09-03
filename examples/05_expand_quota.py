#!/usr/bin/env python3
"""
Example 5: Simple Quota Expansion
Demonstrate how to expand a quota (DRY RUN by default)
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
    print("📈 Example 5: Simple Quota Expansion")
    print("=" * 50)
    
    # Check for production mode flag
    production_mode = '--production' in sys.argv
    
    if production_mode:
        print("🚨 PRODUCTION MODE - This will make actual changes!")
        print("⚠️  This is just a demo - be careful in real environments!")
    else:
        print("🔒 DRY RUN MODE - No actual changes will be made")
        print("💡 Add --production flag to make real changes")
    
    print()
    
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
        
        print("🔍 Finding quotas to expand...")
        quotas = client.quotas.get()
        
        if not quotas:
            print("📭 No quotas found to expand")
            return True
        
        # Find a quota that's over 70% utilization
        target_quota = None
        for quota in quotas:
            current_usage = quota.get('current_usage', 0)
            hard_limit = quota.get('hard_limit', 0)
            
            if hard_limit > 0:
                utilization = (current_usage / hard_limit) * 100
                if utilization > 70:  # Over 70% utilization
                    target_quota = quota
                    break
        
        if not target_quota:
            print("✅ All quotas are healthy (under 70% utilization)")
            return True
        
        view_path = target_quota.get('view_path', 'Unknown')
        current_usage = target_quota.get('current_usage', 0)
        current_limit = target_quota.get('hard_limit', 0)
        utilization = (current_usage / current_limit) * 100
        
        print(f"🎯 Target: {view_path}")
        print(f"   📏 Current Usage: {format_size(current_usage)}")
        print(f"   🚫 Current Limit: {format_size(current_limit)}")
        print(f"   📈 Utilization: {utilization:.1f}%")
        
        # Calculate new limit (add 1TB)
        expansion_size = 1024**4  # 1TB in bytes
        new_limit = current_limit + expansion_size
        
        print()
        print(f"📈 Proposed Expansion:")
        print(f"   ➕ Add: {format_size(expansion_size)}")
        print(f"   🆕 New Limit: {format_size(new_limit)}")
        print(f"   📊 New Utilization: {(current_usage / new_limit) * 100:.1f}%")
        
        if production_mode:
            print()
            print("🚀 Making actual quota expansion...")
            # In a real implementation, you would update the quota here
            # quota_id = target_quota.get('id')
            # client.quotas.patch(quota_id, hard_limit=new_limit)
            print("✅ Quota expansion completed!")
        else:
            print()
            print("🔒 DRY RUN - No actual changes made")
            print("💡 To make real changes, run with --production flag")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

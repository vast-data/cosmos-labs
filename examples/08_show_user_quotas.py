#!/usr/bin/env python3
"""
Example 8: Show User Quotas
Display detailed user quota information in a nice formatted output
"""

import sys
import json
from typing import Dict, Optional

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient

# Constants
BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
TABLE_WIDTH = 60
HEADER_WIDTH = 80
QUOTA_TABLE_HEADERS = ['User', 'Used', 'Soft Limit', 'Hard Limit', 'Usage']
QUOTA_TABLE_WIDTHS = [25, 15, 15, 15, 10]


def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human readable format"""
    if bytes_value is None:
        return "N/A"
    
    for unit in BYTE_UNITS:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} EB"


def format_percentage(used: int, total: int) -> str:
    """Calculate and format percentage"""
    if total is None or total == 0:
        return "N/A"
    
    percentage = (used / total) * 100
    return f"{percentage:.2f}%"


def get_quota_info(client: VASTClient, quota_id: int) -> Optional[Dict]:
    """Get quota information for a specific quota ID"""
    try:
        # Get the specific quota by ID using direct API call
        # This returns the detailed quota information with user_quotas
        quota_data = client.quotas[quota_id].get()
        return quota_data
        
    except Exception as e:
        print(f"❌ Error fetching quota {quota_id}: {e}")
        return None


def display_quota_table(quotas: list, title: str, entity_type: str):
    """Display a table of quotas (users or groups)"""
    if not quotas:
        return
    
    print(f"👥 {title.upper()}:")
    print("-" * TABLE_WIDTH)
    
    # Create header row
    header_row = "".join(f"{header:<{width}}" for header, width in zip(QUOTA_TABLE_HEADERS, QUOTA_TABLE_WIDTHS))
    print(header_row)
    print("-" * TABLE_WIDTH)
    
    for quota in quotas:
        entity = quota.get('entity', {})
        entity_name = entity.get('name', 'Unknown')
        used = quota.get('used_capacity', 0)
        soft = quota.get('soft_limit')
        hard = quota.get('hard_limit')
        
        # Calculate usage percentage
        if hard and hard > 0:
            usage_pct = format_percentage(used, hard)
        else:
            usage_pct = "N/A"
        
        # Create data row
        row_data = [
            entity_name,
            format_bytes(used),
            format_bytes(soft),
            format_bytes(hard),
            usage_pct
        ]
        
        row = "".join(f"{data:<{width}}" for data, width in zip(row_data, QUOTA_TABLE_WIDTHS))
        print(row)
    
    print("-" * TABLE_WIDTH)
    print()


def display_all_quotas_summary(client: VASTClient):
    """Display a summary list of all quotas"""
    try:
        print("🔍 Fetching all quotas...")
        all_quotas = client.quotas.get()
        
        if not all_quotas:
            print("📭 No quotas found")
            return True
        
        print(f"📊 Found {len(all_quotas)} quota configurations:")
        print()
        
        # Create a summary table
        print(f"{'ID':<6} {'Name':<20} {'Path':<25} {'Used':<15} {'Hard Limit':<15} {'Usage':<10} {'Status':<10}")
        print("-" * 95)
        
        for quota in all_quotas:
            quota_id = quota.get('id', 'N/A')
            name = quota.get('name', 'Unknown')[:19]  # Truncate long names
            path = quota.get('path', 'N/A')[:24]      # Truncate long paths
            used = quota.get('used_capacity', 0)
            hard_limit = quota.get('hard_limit')
            state = quota.get('pretty_state', 'Unknown')
            
            # Calculate usage percentage
            if hard_limit and hard_limit > 0:
                usage_pct = format_percentage(used, hard_limit)
            else:
                usage_pct = "N/A"
            
            # Status emoji based on usage
            if hard_limit and hard_limit > 0:
                usage_float = (used / hard_limit) * 100
                if usage_float > 90:
                    status_emoji = "🔴"
                elif usage_float > 70:
                    status_emoji = "🟡"
                else:
                    status_emoji = "🟢"
            else:
                status_emoji = "⚪"
            
            print(f"{quota_id:<6} {name:<20} {path:<25} {format_bytes(used):<15} {format_bytes(hard_limit):<15} {usage_pct:<10} {status_emoji} {state:<10}")
        
        print("-" * 95)
        print()
        print("💡 To see detailed information for a specific quota, run:")
        print("   python 08_show_user_quotas.py <quota_id>")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error fetching quotas: {e}")
        return False


def display_quota_summary(quota_data: Dict):
    """Display a nice summary of the quota information"""
    print("=" * HEADER_WIDTH)
    print(f"📊 QUOTA SUMMARY: {quota_data.get('name', 'Unknown')}")
    print("=" * HEADER_WIDTH)
    
    # Basic quota info
    print(f"🆔 Quota ID: {quota_data.get('id', 'N/A')}")
    print(f"📁 Path: {quota_data.get('path', 'N/A')}")
    print(f"🏷️  Title: {quota_data.get('title', 'N/A')}")
    print(f"📊 State: {quota_data.get('pretty_state', 'N/A')}")
    print(f"🏢 Cluster: {quota_data.get('cluster', 'N/A')}")
    print(f"🏢 Tenant: {quota_data.get('tenant_name', 'N/A')}")
    print()
    
    # Capacity information
    used_capacity = quota_data.get('used_capacity', 0)
    hard_limit = quota_data.get('hard_limit')
    soft_limit = quota_data.get('soft_limit')
    
    print("💾 CAPACITY USAGE:")
    print(f"   Used: {format_bytes(used_capacity)}")
    if hard_limit:
        print(f"   Hard Limit: {format_bytes(hard_limit)}")
        print(f"   Usage: {format_percentage(used_capacity, hard_limit)}")
    else:
        print("   Hard Limit: No limit set")
    
    if soft_limit:
        print(f"   Soft Limit: {format_bytes(soft_limit)}")
    else:
        print("   Soft Limit: No limit set")
    print()
    
    # Inode information
    used_inodes = quota_data.get('used_inodes', 0)
    hard_limit_inodes = quota_data.get('hard_limit_inodes')
    soft_limit_inodes = quota_data.get('soft_limit_inodes')
    
    print("📄 INODE USAGE:")
    print(f"   Used: {used_inodes:,}")
    if hard_limit_inodes:
        print(f"   Hard Limit: {hard_limit_inodes:,}")
        print(f"   Usage: {format_percentage(used_inodes, hard_limit_inodes)}")
    else:
        print("   Hard Limit: No limit set")
    
    if soft_limit_inodes:
        print(f"   Soft Limit: {soft_limit_inodes:,}")
    else:
        print("   Soft Limit: No limit set")
    print()
    
    # Display user and group quotas using the helper function
    user_quotas = quota_data.get('user_quotas', [])
    group_quotas = quota_data.get('group_quotas', [])
    
    display_quota_table(user_quotas, "USER QUOTAS", "user")
    display_quota_table(group_quotas, "GROUP QUOTAS", "group")
    
    # Status information
    print("📈 STATUS:")
    print(f"   Exceeded Users: {quota_data.get('num_exceeded_users', 0)}")
    print(f"   Blocked Users: {quota_data.get('num_blocked_users', 0)}")
    print(f"   Alarms Enabled: {'Yes' if quota_data.get('enable_alarms') else 'No'}")
    print(f"   Last Update: {quota_data.get('last_user_quotas_update', 'N/A')}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Display detailed user quota information')
    parser.add_argument('quota_id', type=int, nargs='?', help='Quota ID to display (e.g., 114)')
    parser.add_argument('--all', action='store_true', help='Show summary of all quotas')
    parser.add_argument('--json', action='store_true', help='Output raw JSON instead of formatted display')
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and args.quota_id is None:
        parser.error("Either provide a quota_id or use --all to show all quotas")
    
    print("🚀 Example 8: Show User Quotas")
    print("=" * 50)
    
    try:
        # Load configuration using examples config loader
        config = ExamplesConfigLoader()
        vast_config = config.get_vast_config()
        
        # Build VAST client parameters
        address = vast_config['address']
        if address.startswith('https://'):
            address = address[8:]  # Remove 'https://' prefix
        elif address.startswith('http://'):
            address = address[7:]   # Remove 'http://' prefix
        
        print(f"📡 Connecting to: {address}")
        print(f"👤 User: {vast_config['user']}")
        print()
        
        # Create VAST client
        client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=address
        )
        
        if args.all:
            # Show all quotas summary
            return display_all_quotas_summary(client)
        else:
            # Show specific quota details
            quota_id = args.quota_id
            print(f"🔍 Fetching quota information for ID: {quota_id}")
            print()
            
            quota_data = get_quota_info(client, quota_id)
            
            if quota_data is None:
                print(f"❌ Failed to retrieve quota information for ID {quota_id}")
                print("💡 Try using a different quota ID or use --all to see available quotas")
                return False
            
            if args.json:
                # Output raw JSON
                print(json.dumps(quota_data, indent=2))
            else:
                # Display formatted output
                display_quota_summary(quota_data)
            return True
            
    except FileNotFoundError as e:
        print(f"❌ Configuration file not found: {e}")
        return False
    except KeyError as e:
        print(f"❌ Missing configuration key: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Example 7: Simple Chargeback Report
===================================

Shows storage costs for root views with enabled quotas.
Uses a default rate of $42 per TB/month.

Usage:
    python 07_chargeback_report.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples_config import ExamplesConfigLoader

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_root_view(path):
    """Extract root view from path (e.g., /jonas/cosmos-lab/raw -> /jonas)"""
    if not path or path == '/':
        return '/'
    
    # Remove leading slash and split
    parts = path.lstrip('/').split('/')
    if parts and parts[0]:
        return f"/{parts[0]}"
    return '/'

def main():
    """Generate chargeback report for root views with quotas"""
    print("💰 VAST Storage Chargeback Report")
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
        
        print("🔧 Connecting to VAST Management System...")
        client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=address
        )
        print(f"✅ Connected to VAST at {vast_config['address']}")
        
        # Get all views
        print(f"📊 Fetching storage views...")
        views = client.views.get()
        
        # Get all quotas
        print(f"📊 Fetching quota information...")
        quotas = client.quotas.get()
        
        # Create a mapping of view paths to quotas
        quota_map = {}
        for quota in quotas:
            if quota.get('path'):
                quota_map[quota['path']] = quota
        
        # Process views and calculate costs
        root_view_costs = {}
        default_rate_per_tb_month = 42.0  # $42 per TB per month
        
        print(f"💰 Calculating costs at ${default_rate_per_tb_month}/TB/month...")
        
        for view in views:
            view_path = view.get('path', '')
            if not view_path:
                continue
                
            # Check if this view has a quota enabled
            has_quota = view_path in quota_map
            
            if has_quota:
                root_view = get_root_view(view_path)
                
                # Get storage size (use logical_size if available, otherwise physical_size)
                size_bytes = view.get('logical_size', 0) or view.get('physical_size', 0)
                
                if size_bytes > 0:
                    # Convert to TB and calculate monthly cost
                    size_tb = size_bytes / (1024**4)  # Convert bytes to TB
                    monthly_cost = size_tb * default_rate_per_tb_month
                    
                    if root_view not in root_view_costs:
                        root_view_costs[root_view] = {
                            'total_size_bytes': 0,
                            'view_count': 0,
                            'monthly_cost': 0.0
                        }
                    
                    root_view_costs[root_view]['total_size_bytes'] += size_bytes
                    root_view_costs[root_view]['view_count'] += 1
                    root_view_costs[root_view]['monthly_cost'] += monthly_cost
        
        # Sort by monthly cost (descending)
        sorted_costs = sorted(
            root_view_costs.items(), 
            key=lambda x: x[1]['monthly_cost'], 
            reverse=True
        )
        
        # Display results
        print(f"\n📊 Top 5 Most Expensive Root Views (with quotas enabled)")
        print(f"💵 Rate: ${default_rate_per_tb_month}/TB/month")
        print(f"📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        if not sorted_costs:
            print("❌ No views found with enabled quotas")
            return
        
        # Show top 5
        for i, (root_view, data) in enumerate(sorted_costs[:5], 1):
            total_size = format_bytes(data['total_size_bytes'])
            monthly_cost = data['monthly_cost']
            view_count = data['view_count']
            
            print(f"{i}. {root_view}")
            print(f"   📁 Views: {view_count}")
            print(f"   📏 Total Storage: {total_size}")
            print(f"   💵 Monthly Cost: ${monthly_cost:.2f}")
            print()
        
        # Summary
        total_monthly_cost = sum(data['monthly_cost'] for _, data in sorted_costs)
        total_views = sum(data['view_count'] for _, data in sorted_costs)
        
        print(f"📊 Summary:")
        print(f"   🏠 Root Views with Quotas: {len(sorted_costs)}")
        print(f"   📁 Total Views: {total_views}")
        print(f"   💵 Total Monthly Cost: ${total_monthly_cost:.2f}")
        print(f"   💰 Average Cost per Root View: ${total_monthly_cost/len(sorted_costs):.2f}")
        
    except Exception as e:
        print(f"❌ Error generating chargeback report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

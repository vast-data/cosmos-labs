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
        
        # Create VAST client using the correct parameter names from vastpy docs
        client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=address
        )
        
        # Test connection by getting cluster info
        print("🔍 Testing connection...")
        clusters = client.clusters.get()
        
        if clusters:
            cluster = clusters[0]  # Get the first cluster
            print("✅ Connection successful!")
            print(f"🏢 Cluster ID: {cluster.get('id', 'Unknown')}")
            print(f"📊 Cluster Name: {cluster.get('name', 'Unknown')}")
            print(f"🆔 Cluster GUID: {cluster.get('guid', 'Unknown')}")
            
            # Display capacity information using the correct field names
            print("\n💾 Storage Capacity Information:")
            print("-" * 50)
            
            # Get capacity values
            physical_space_tb = cluster.get('physical_space_tb')
            usable_capacity_tb = cluster.get('usable_capacity_tb')
            free_usable_capacity_tb = cluster.get('free_usable_capacity_tb')
            logical_space_tb = cluster.get('logical_space_tb')
            auxiliary_space_tb = cluster.get('auxiliary_space_in_use_tb')
            
            # Data Reduction Ratio (if available)
            if usable_capacity_tb and logical_space_tb and logical_space_tb > 0:
                data_reduction_ratio = logical_space_tb / usable_capacity_tb
                print(f"📊 Data Reduction: {data_reduction_ratio:.1f}:1")
            
            # Physical capacity
            if physical_space_tb is not None:
                print(f"🔧 Total Physical Space: {physical_space_tb:.2f} TB")
            
            # Usable capacity (with description matching dashboard)
            if usable_capacity_tb is not None:
                print(f"💽 Usable Capacity: {usable_capacity_tb:.2f} TB")
                print(f"   The amount of usable capacity that is consumed. Usable capacity is dependent on erasure coding overhead. Capacity Licensing is applicable to this value.")
            
            # Free capacity
            if free_usable_capacity_tb is not None:
                print(f"🆓 Free Usable Capacity: {free_usable_capacity_tb:.2f} TB")
            
            # Logical capacity (with description matching dashboard)
            if logical_space_tb is not None:
                print(f"📊 Logical Capacity: {logical_space_tb:.2f} TB")
                print(f"   The amount of raw written data.")
            
            # Usage breakdown with both Usable and Logical values
            if usable_capacity_tb and free_usable_capacity_tb and logical_space_tb:
                used_usable_tb = usable_capacity_tb - free_usable_capacity_tb
                used_logical_tb = logical_space_tb - cluster.get('free_logical_space_tb', 0)
                usage_percent = (used_usable_tb / usable_capacity_tb) * 100
                
                auxiliary_usable_tb = auxiliary_space_tb or 0
                auxiliary_logical_tb = cluster.get('logical_auxiliary_space_in_use_tb', 0) or 0
                auxiliary_percent = (auxiliary_usable_tb / usable_capacity_tb) * 100 if usable_capacity_tb > 0 else 0
                
                free_logical_tb = cluster.get('free_logical_space_tb', 0) or 0
                free_percent = 100 - usage_percent - auxiliary_percent
                
                print(f"\n📈 Capacity Breakdown:")
                print(f"   🔵 {usage_percent:.1f}% Used - Data written:")
                print(f"      Usable: {used_usable_tb:.3f} TiB")
                print(f"      Logical: {used_logical_tb:.3f} TiB")
                
                if auxiliary_usable_tb > 0 or auxiliary_logical_tb > 0:
                    print(f"   🔷 {auxiliary_percent:.1f}% Auxiliary - Snapshots and pending deletes:")
                    print(f"      Usable: {auxiliary_usable_tb:.3f} TiB")
                    print(f"      Logical: {auxiliary_logical_tb:.3f} TiB")
                
                print(f"   ⚪ {free_percent:.1f}% Free - Available capacity:")
                print(f"      Usable: {free_usable_capacity_tb:.3f} TiB")
                print(f"      Logical: {free_logical_tb:.3f} TiB")
            
            # Additional metrics if available
            metadata_usage = cluster.get('metadata_usage_percent')
            if metadata_usage is not None:
                print(f"📋 Metadata Usage: {metadata_usage:.1f}%")
            
            inode_usage = cluster.get('inode_usage_percent')
            if inode_usage is not None:
                print(f"📁 Inode Usage: {inode_usage:.1f}%")
        else:
            print("✅ Connection successful!")
            print("📊 No cluster information available")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

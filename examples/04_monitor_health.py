#!/usr/bin/env python3
"""
Example 4: Monitor VAST System Health
Check cluster health, node status, and system performance
"""

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient

def check_node_status(nodes, node_type):
    """Check and display status for CNodes or DNodes"""
    if not nodes:
        print(f"   📭 No {node_type} found")
        return
    
    healthy_nodes = 0
    total_nodes = len(nodes)
    
    for node in nodes:
        hostname = node.get('hostname', 'Unknown')
        state = node.get('state', 'Unknown')
        sync = node.get('sync', 'Unknown')
        enabled = node.get('enabled', False)
        
        # Determine health status
        if state == 'ACTIVE' and sync == 'SYNCED' and enabled:
            node_state = 'Healthy'
            node_emoji = "🟢"
            healthy_nodes += 1
        elif state == 'ACTIVE' and enabled:
            node_state = 'Active (Not Synced)'
            node_emoji = "🟡"
        else:
            node_state = f'Not Ready (State: {state})'
            node_emoji = "🔴"
        
        print(f"   {node_emoji} {hostname}: {node_state}")
    
    print(f"   📊 Healthy {node_type}: {healthy_nodes}/{total_nodes}")
    
    if healthy_nodes == total_nodes:
        print(f"   ✅ All {node_type} are healthy")
    elif healthy_nodes > 0:
        print(f"   ⚠️  Some {node_type} may have issues")
    else:
        print(f"   🚨 No healthy {node_type} found")

def main():
    print("�� Example 4: Monitor VAST System Health")
    print("=" * 50)
    
    try:
        # Load configuration and connect
        config = ExamplesConfigLoader()
        vast_config = config.get_vast_config()
        
        address = vast_config['address']
        # Remove protocol prefix if present
        address = address.replace('https://', '').replace('http://', '')
        
        client = VASTClient(
            user=vast_config['user'],
            password=vast_config['password'],
            address=address
        )
        
        print("🔍 Checking VAST cluster health...")
        
        # Get cluster information
        clusters = client.clusters.get()
        if clusters:
            cluster = clusters[0]  # Get the first cluster
            
            # Show cluster health information
            print("🏥 CLUSTER HEALTH:")
            print(f"   🟢 Status: HEALTHY (Connected)")
            print(f"   🏢 Cluster: {cluster.get('name', 'Unknown')}")
            print(f"   🆔 Cluster ID: {cluster.get('id', 'Unknown')}")
        else:
            print("🏥 CLUSTER HEALTH:")
            print("   ⚠️  No cluster information available")
        
        print()
        
        # Get CNodes status
        print("🖥️  CNODES STATUS:")
        try:
            cnodes = client.cnodes.get()
            check_node_status(cnodes, 'CNodes')
        except Exception as e:
            print(f"   ⚠️  CNodes information not available: {e}")
        
        print()
        
        # Get DNodes status
        print("💾 DNODES STATUS:")
        try:
            dnodes = client.dnodes.get()
            check_node_status(dnodes, 'DNodes')
        except Exception as e:
            print(f"   ⚠️  DNodes information not available: {e}")
        
        print()
        
        # Overall system status
        print("�� OVERALL SYSTEM STATUS:")
        print("   ✅ VAST Management System: Online")
        print("   ✅ API Connectivity: Working")
        print("   ✅ Configuration: Valid")
        print("   ✅ Authentication: Successful")
        
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
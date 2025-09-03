#!/usr/bin/env python3
"""
Example 4: Monitor VAST System Health
Check cluster health, node status, and system performance
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
    print("🏥 Example 4: Monitor VAST System Health")
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
        
        print("🔍 Checking VAST cluster health...")
        
        # Get system information
        system_info = client.system.get()
        print(f"🏢 Cluster: {system_info.get('cluster_name', 'Unknown')}")
        print(f"📦 Version: {system_info.get('version', 'Unknown')}")
        print(f"🆔 Cluster ID: {system_info.get('cluster_id', 'Unknown')}")
        print()
        
        # Get cluster health information
        print("🏥 CLUSTER HEALTH:")
        try:
            # Try to get cluster health metrics
            health_info = client.cluster.get()
            
            # Check cluster status
            cluster_state = health_info.get('state', 'Unknown')
            if cluster_state.lower() == 'healthy':
                status_emoji = "🟢"
                status_text = "HEALTHY"
            elif cluster_state.lower() == 'degraded':
                status_emoji = "🟡"
                status_text = "DEGRADED"
            else:
                status_emoji = "🔴"
                status_text = "UNHEALTHY"
            
            print(f"   {status_emoji} Status: {status_text}")
            print(f"   📊 State: {cluster_state}")
            
            # Show cluster capacity
            total_capacity = health_info.get('total_capacity', 0)
            used_capacity = health_info.get('used_capacity', 0)
            
            if total_capacity > 0:
                utilization = (used_capacity / total_capacity) * 100
                print(f"   📏 Total Capacity: {format_size(total_capacity)}")
                print(f"   📈 Used Capacity: {format_size(used_capacity)}")
                print(f"   📊 Utilization: {utilization:.1f}%")
            
        except Exception as e:
            print(f"   ⚠️  Cluster health info not available: {e}")
        
        print()
        
        # Get node information
        print("🖥️  NODE STATUS:")
        try:
            nodes = client.nodes.get()
            
            if nodes:
                healthy_nodes = 0
                total_nodes = len(nodes)
                
                for node in nodes:
                    node_name = node.get('name', 'Unknown')
                    node_state = node.get('state', 'Unknown')
                    node_role = node.get('role', 'Unknown')
                    
                    if node_state.lower() == 'healthy':
                        node_emoji = "🟢"
                        healthy_nodes += 1
                    elif node_state.lower() == 'degraded':
                        node_emoji = "🟡"
                    else:
                        node_emoji = "🔴"
                    
                    print(f"   {node_emoji} {node_name} ({node_role}): {node_state}")
                
                print(f"   📊 Healthy Nodes: {healthy_nodes}/{total_nodes}")
                
                if healthy_nodes == total_nodes:
                    print("   ✅ All nodes are healthy")
                elif healthy_nodes > 0:
                    print("   ⚠️  Some nodes may have issues")
                else:
                    print("   🚨 No healthy nodes found")
            else:
                print("   📭 No node information available")
                
        except Exception as e:
            print(f"   ⚠️  Node information not available: {e}")
        
        print()
        
        # Get performance metrics
        print("⚡ PERFORMANCE METRICS:")
        try:
            # Try to get performance data
            performance = client.performance.get()
            
            if performance:
                # Show key performance indicators
                iops = performance.get('iops', 0)
                throughput = performance.get('throughput', 0)
                latency = performance.get('latency', 0)
                
                print(f"   🔄 IOPS: {iops:,}")
                print(f"   📊 Throughput: {format_size(throughput)}/s")
                print(f"   ⏱️  Latency: {latency:.2f}ms")
            else:
                print("   📭 Performance metrics not available")
                
        except Exception as e:
            print(f"   ⚠️  Performance metrics not available: {e}")
        
        print()
        
        # Overall system status
        print("🚨 OVERALL SYSTEM STATUS:")
        print("   ✅ VAST Management System: Online")
        print("   ✅ API Connectivity: Working")
        print("   ✅ Configuration: Valid")
        print("   ✅ Authentication: Successful")
        
        # Check for any alerts
        try:
            alerts = client.alerts.get()
            if alerts:
                active_alerts = [a for a in alerts if a.get('state', '').lower() == 'active']
                if active_alerts:
                    print(f"   ⚠️  Active Alerts: {len(active_alerts)}")
                    for alert in active_alerts[:3]:  # Show first 3 alerts
                        print(f"      - {alert.get('message', 'Unknown alert')}")
                else:
                    print("   ✅ No Active Alerts")
            else:
                print("   ✅ No Alerts Found")
        except Exception as e:
            print(f"   ⚠️  Alert information not available: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

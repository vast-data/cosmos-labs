#!/usr/bin/env python3
"""
Example 6: Show Latest and Oldest Snapshots
Demonstrate snapshot management and display snapshot information
"""

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient
from datetime import datetime

def format_size(bytes_size):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def format_timestamp(timestamp):
    """Format timestamp to human readable format"""
    if isinstance(timestamp, str):
        try:
            # Try to parse ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return timestamp
    elif isinstance(timestamp, (int, float)):
        # Unix timestamp
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(timestamp)

def main():
    print("📸 Example 6: Show Latest and Oldest Snapshots")
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
        
        print("🔍 Fetching snapshot information...")
        
        # Get all snapshots
        snapshots = client.snapshots.get()
        
        if not snapshots:
            print("📭 No snapshots found")
            print("💡 Snapshots are created when you take point-in-time backups of your data")
            return True
        
        print(f"📊 Found {len(snapshots)} snapshots:")
        print()
        
        # Sort snapshots by creation time
        sorted_snapshots = sorted(snapshots, key=lambda x: x.get('creation_time', 0))
        
        # Show oldest snapshot
        if sorted_snapshots:
            oldest = sorted_snapshots[0]
            print("🕰️  OLDEST SNAPSHOT:")
            print(f"   📸 Name: {oldest.get('name', 'Unknown')}")
            print(f"   📅 Created: {format_timestamp(oldest.get('creation_time'))}")
            print(f"   📏 Size: {format_size(oldest.get('logical_size', 0))}")
            print(f"   📁 View: {oldest.get('view_path', 'Unknown')}")
            print(f"   🆔 ID: {oldest.get('id', 'Unknown')}")
            print()
        
        # Show latest snapshot
        if len(sorted_snapshots) > 1:
            latest = sorted_snapshots[-1]
            print("🆕 LATEST SNAPSHOT:")
            print(f"   📸 Name: {latest.get('name', 'Unknown')}")
            print(f"   📅 Created: {format_timestamp(latest.get('creation_time'))}")
            print(f"   📏 Size: {format_size(latest.get('logical_size', 0))}")
            print(f"   📁 View: {latest.get('view_path', 'Unknown')}")
            print(f"   🆔 ID: {latest.get('id', 'Unknown')}")
            print()
        
        # Show summary statistics
        total_size = sum(s.get('logical_size', 0) for s in snapshots)
        avg_size = total_size / len(snapshots) if snapshots else 0
        
        print("📈 SNAPSHOT SUMMARY:")
        print(f"   📊 Total Snapshots: {len(snapshots)}")
        print(f"   📏 Total Size: {format_size(total_size)}")
        print(f"   📊 Average Size: {format_size(avg_size)}")
        
        # Show age range
        if len(sorted_snapshots) > 1:
            oldest_time = sorted_snapshots[0].get('creation_time', 0)
            latest_time = sorted_snapshots[-1].get('creation_time', 0)
            
            if oldest_time and latest_time:
                try:
                    if isinstance(oldest_time, str):
                        oldest_dt = datetime.fromisoformat(oldest_time.replace('Z', '+00:00'))
                    else:
                        oldest_dt = datetime.fromtimestamp(oldest_time)
                    
                    if isinstance(latest_time, str):
                        latest_dt = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                    else:
                        latest_dt = datetime.fromtimestamp(latest_time)
                    
                    age_days = (latest_dt - oldest_dt).days
                    print(f"   ⏰ Age Range: {age_days} days")
                except:
                    print(f"   ⏰ Age Range: Unknown")
        
        print()
        
        # Show all snapshots in a table format
        if len(snapshots) <= 10:  # Only show table if not too many snapshots
            print("📋 ALL SNAPSHOTS:")
            print("-" * 80)
            print(f"{'Name':<20} {'Created':<20} {'Size':<12} {'View':<20}")
            print("-" * 80)
            
            for snapshot in sorted_snapshots:
                name = snapshot.get('name', 'Unknown')[:18]
                created = format_timestamp(snapshot.get('creation_time'))[:18]
                size = format_size(snapshot.get('logical_size', 0))[:10]
                view = snapshot.get('view_path', 'Unknown')[:18]
                
                print(f"{name:<20} {created:<20} {size:<12} {view:<20}")
        else:
            print(f"📋 Showing {len(snapshots)} snapshots (too many for table display)")
            print("💡 Use VAST Management UI for detailed snapshot management")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
VAST System Inventory
Shows a comprehensive overview of your VAST system including views, protocols, and buckets
"""

import sys
import signal
from pathlib import Path

# Add parent directory to path for imports to avoid circular import
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Handle Ctrl-C gracefully
def signal_handler(sig, frame):
    print("\n\n⚠️  Interrupted by user. Exiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    from config_loader import ConfigLoader
    from vastpy import VASTClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    """Show comprehensive VAST system inventory including views, protocols, and buckets"""
    
    # Load configuration from parent directory
    config_path = str(parent_dir / "config.yaml")
    secrets_path = str(parent_dir / "secrets.yaml")
    config = ConfigLoader(config_path, secrets_path)
    
    # Get VAST configuration
    vast_address = config.get('vast.address')
    vast_username = config.get('vast.user')
    vast_password = config.get_secret('vast_password')
    
    # Strip protocol from address as vastpy adds it automatically
    if vast_address.startswith('https://'):
        vast_address = vast_address[8:]
    elif vast_address.startswith('http://'):
        vast_address = vast_address[7:]
    
    print(f"🔧 VAST Configuration:")
    print(f"   Address: {vast_address}")
    print(f"   Username: {vast_username}")
    print(f"   Password: {'***' if vast_password else 'None'}")
    print()
    
    try:
        # Connect to VAST Management System
        print("🔌 Connecting to VAST Management System...")
        client = VASTClient(
            address=vast_address,
            user=vast_username,
            password=vast_password
        )
        
        # List all views and categorize by protocol
        print("📁 Available VAST Views:")
        views = client.views.get()
        
        if views:
            # Categorize views by protocol
            protocol_counts = {}
            s3_views = []
            nfs_views = []
            smb_views = []
            block_views = []
            database_views = []
            
            for view in views:
                view_id = view.get('id', 'Unknown')
                view_path = view.get('path', 'Unknown')
                view_name = view.get('name', 'Unnamed')
                protocols = view.get('protocols', [])
                
                # Get bucket name from the view object
                bucket_name = view.get('bucket', 'N/A')
                
                # Count protocols
                for protocol in protocols:
                    protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
                
                # Categorize views
                if 'S3' in protocols:
                    s3_views.append((view_path, view_id, view_name, bucket_name, protocols))
                if 'NFS' in protocols:
                    nfs_views.append((view_path, view_id, view_name, bucket_name, protocols))
                if 'SMB' in protocols:
                    smb_views.append((view_path, view_id, view_name, bucket_name, protocols))
                if 'BLOCK' in protocols:
                    block_views.append((view_path, view_id, view_name, bucket_name, protocols))
                if 'DATABASE' in protocols:
                    database_views.append((view_path, view_id, view_name, bucket_name, protocols))
            
            # Show S3 views with their bucket names
            if s3_views:
                print(f"\n🪣 S3 Views ({len(s3_views)} total):")
                for view_path, view_id, view_name, bucket_name, protocols in s3_views:
                    print(f"   • {view_path} → Bucket: {bucket_name}")
            
            # Show NFS views
            if nfs_views:
                print(f"\n📁 NFS Views ({len(nfs_views)} total):")
                for view_path, view_id, view_name, bucket_name, protocols in nfs_views:
                    print(f"   • {view_path}")
            
            # Show SMB views
            if smb_views:
                print(f"\n💼 SMB Views ({len(smb_views)} total):")
                for view_path, view_id, view_name, bucket_name, protocols in smb_views:
                    print(f"   • {view_path}")
            
            # Show Block views
            if block_views:
                print(f"\n💾 Block Views ({len(block_views)} total):")
                for view_path, view_id, view_name, bucket_name, protocols in block_views:
                    print(f"   • {view_path}")
        else:
            print("   No views found")
        
        # Show database views
        if database_views:
            print(f"\n🗄️  Database Views ({len(database_views)} total):")
            for view_path, view_id, view_name, bucket_name, protocols in database_views:
                if bucket_name != 'N/A' and bucket_name:
                    print(f"   • {view_path} → Bucket: {bucket_name}")
                else:
                    print(f"   • {view_path} → No bucket name")
        else:
            print("\n🗄️  Database Views:")
            print("   ℹ️  No database-enabled views found")
        
        # Show summary statistics at the end
        if views:
            print(f"\n📊 Summary: {len(views)} total views")
            for protocol, count in sorted(protocol_counts.items()):
                print(f"   • {protocol}: {count} views")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
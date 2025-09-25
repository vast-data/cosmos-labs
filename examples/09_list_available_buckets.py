#!/usr/bin/env python3
"""
VAST Storage and Database Inventory
Analyzes your VAST system to show views by protocol and database statistics
"""

import sys
from pathlib import Path

# Add parent directory to path for imports to avoid circular import
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from config_loader import ConfigLoader
    from vastpy import VASTClient
    import vastdb
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    """Analyze VAST system to show storage inventory and database statistics"""
    
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
                bucket_name = view.get('bucket_name', 'N/A')
                
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
            
            # Show summary statistics
            print(f"   📊 Summary: {len(views)} total views")
            for protocol, count in sorted(protocol_counts.items()):
                print(f"      • {protocol}: {count} views")
            print()
        else:
            print("   No views found")
        
        # Analyze database views and show statistics
        if database_views:
            print("🗄️  VAST Database Analysis:")
            print(f"   📊 Found {len(database_views)} database-enabled views")
            
            db_endpoint = config.get('vastdb.endpoint')
            s3_access_key = config.get_secret('s3_access_key')
            s3_secret_key = config.get_secret('s3_secret_key')
            s3_verify_ssl = config.get('s3.verify_ssl', True)
            
            if db_endpoint and s3_access_key and s3_secret_key:
                try:
                    # Connect to VAST Database using S3 credentials
                    db_client = vastdb.connect(
                        endpoint=db_endpoint,
                        access=s3_access_key,
                        secret=s3_secret_key,
                        ssl_verify=s3_verify_ssl
                    )
                    
                    print(f"   ✅ Connected to VAST Database at {db_endpoint}")
                    
                    # Analyze each database view
                    total_rows = 0
                    total_tables = 0
                    
                    with db_client.transaction() as tx:
                        # First, let's see what buckets are actually available
                        try:
                            available_buckets = tx.buckets()
                            print(f"   📊 Available buckets: {[b.name for b in available_buckets]}")
                        except Exception as e:
                            print(f"   ⚠️  Could not list buckets: {e}")
                        
                        for view_path, view_id, view_name, bucket_name, protocols in database_views:
                            print(f"   🔍 Analyzing database view: {view_path}")
                            
                            try:
                                # Try different bucket naming approaches
                                bucket_names_to_try = [
                                    view_path.lstrip('/').replace('/', '_'),  # Convert path to bucket name
                                    view_name,  # Use view name
                                    bucket_name if bucket_name != 'N/A' else None,  # Use actual bucket name
                                    f"view-{view_id}"  # Use view-{id} format
                                ]
                                
                                bucket = None
                                bucket_name_to_use = None
                                
                                for test_name in bucket_names_to_try:
                                    if test_name:
                                        try:
                                            bucket = tx.bucket(test_name)
                                            bucket_name_to_use = test_name
                                            break
                                        except:
                                            continue
                                
                                if not bucket:
                                    print(f"      ⚠️  Could not access bucket for view {view_path}")
                                    continue
                                
                                # List schemas in this bucket
                                schemas = bucket.schemas()
                                print(f"      📊 Bucket '{bucket_name_to_use}': {len(schemas)} schemas")
                                
                                for schema in schemas:
                                    try:
                                        # Get tables in this schema
                                        tables = schema.tables()
                                        print(f"         📋 Schema '{schema.name}': {len(tables)} tables")
                                        total_tables += len(tables)
                                        
                                        # Count rows in each table
                                        for table in tables:
                                            try:
                                                # Get table info to count rows
                                                table_info = table.info()
                                                if hasattr(table_info, 'num_rows'):
                                                    row_count = table_info.num_rows
                                                    total_rows += row_count
                                                    print(f"            📄 Table '{table.name}': {row_count:,} rows")
                                                else:
                                                    print(f"            📄 Table '{table.name}': row count unavailable")
                                            except Exception as e:
                                                print(f"            ⚠️  Table '{table.name}': {str(e)[:50]}...")
                                                
                                    except Exception as e:
                                        print(f"         ⚠️  Schema '{schema.name}': {str(e)[:50]}...")
                                        
                            except Exception as e:
                                print(f"      ⚠️  Bucket '{bucket_name_to_use}': {str(e)[:50]}...")
                    
                    print(f"   📈 Total Database Statistics:")
                    print(f"      • Total tables: {total_tables}")
                    print(f"      • Total rows: {total_rows:,}")
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"   ❌ Database connection failed: {error_msg}")
                    
                    # Provide helpful guidance for common VAST Database connection issues
                    if "is not a VAST DB server endpoint" in error_msg:
                        print()
                        print("   💡 VAST Database Connection Help:")
                        print("   • You're connecting to the VAST Management System endpoint")
                        print("   • VAST Database requires a different VIP pool endpoint")
                        print("   • Check your config.yaml 'vastdb.endpoint' setting")
                        print("   • It should point to the VAST Database VIP pool, not VMS")
                        print("   • Example: 'https://vastdb-vip.your-domain.com' or similar")
                        print("   • Contact your VAST administrator for the correct endpoint")
                    elif "SSL" in error_msg or "certificate" in error_msg:
                        print()
                        print("   💡 SSL Certificate Help:")
                        print("   • Try setting 's3.verify_ssl: false' in your config.yaml")
                        print("   • Or set 'vastdb.ssl_verify: false' for database connections")
                    elif "access" in error_msg.lower() or "secret" in error_msg.lower():
                        print()
                        print("   💡 Authentication Help:")
                        print("   • Check your secrets.yaml has correct S3 credentials")
                        print("   • Verify 's3_access_key' and 's3_secret_key' are set")
                        print("   • These same credentials are used for VAST Database")
            else:
                print("   ⚠️  Database credentials not configured")
        else:
            print("🗄️  VAST Database Analysis:")
            print("   ℹ️  No database-enabled views found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
List Available VAST Views and Test Database Support
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
    """List available VAST views and test database support"""
    
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
        
        # List all views
        print("📁 Available VAST Views:")
        views = client.views.get()
        
        if views:
            for view in views:
                view_id = view.get('id', 'Unknown')
                view_path = view.get('path', 'Unknown')
                view_name = view.get('name', 'Unnamed')
                protocols = view.get('protocols', [])
                bucket_name = view.get('bucket_name', 'N/A')
                
                print(f"   • {view_path}")
                print(f"     ID: {view_id}")
                print(f"     Name: {view_name}")
                print(f"     Bucket: {bucket_name}")
                print(f"     Protocols: {', '.join(protocols) if protocols else 'None'}")
                print()
        else:
            print("   No views found")
        
        # Test database connection
        print("🗄️  Testing VAST Database Connection:")
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
                
                # List databases
                databases = db_client.list_databases()
                print(f"   ✅ Connected to VAST Database at {db_endpoint}")
                print(f"   📊 Available databases: {len(databases)}")
                for db in databases:
                    print(f"      • {db}")
                    
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
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
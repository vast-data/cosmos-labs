#!/usr/bin/env python3
"""
List Available S3 Buckets and Test Database Support
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config_loader import ConfigLoader
    import boto3
    import vastdb
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    """List available buckets and test database support"""
    
    # Load configuration from parent directory
    config_path = str(Path(__file__).parent.parent / "config.yaml")
    secrets_path = str(Path(__file__).parent.parent / "secrets.yaml")
    config = ConfigLoader(config_path, secrets_path)
    
    # Get S3 credentials
    access_key = config.get_secret('s3_access_key')
    secret_key = config.get_secret('s3_secret_key')
    endpoint = config.get('s3.endpoint_url')
    
    print(f"🔧 S3 Configuration:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Access Key: {'***' if access_key else 'None'}")
    print(f"   Secret Key: {'***' if secret_key else 'None'}")
    print()
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='us-east-1',
        use_ssl=False,
        config=boto3.session.Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        )
    )
    
    try:
        # List all buckets
        print("📦 Available S3 Buckets:")
        response = s3_client.list_buckets()
        
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            creation_date = bucket['CreationDate']
            print(f"   • {bucket_name} (created: {creation_date})")
            
            # Test if bucket supports database operations
            try:
                # Try to connect to VAST DB and access this bucket
                db_config = {
                    'access': access_key,
                    'secret': secret_key,
                    'endpoint': config.get('lab2.vastdb.endpoint'),
                    'ssl_verify': False,
                    'timeout': 30
                }
                
                connection = vastdb.connect(**db_config)
                
                with connection.transaction() as tx:
                    try:
                        bucket_obj = tx.bucket(bucket_name)
                        schemas = bucket_obj.schemas()
                        print(f"     ✅ Supports database operations ({len(schemas)} schemas)")
                    except Exception as e:
                        print(f"     ❌ Database operations not supported: {type(e).__name__}")
                        
            except Exception as e:
                print(f"     ❌ Failed to test database support: {type(e).__name__}")
        
        print()
        print("💡 Recommendation: Use a bucket that supports database operations")
        
    except Exception as e:
        print(f"❌ Failed to list buckets: {e}")

if __name__ == "__main__":
    main()

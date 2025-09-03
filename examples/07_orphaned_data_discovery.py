#!/usr/bin/env python3
"""
Example 7: Orphaned Data Discovery

This script identifies deleted views from audit logs and checks if their
associated directories still exist on the VAST system.
"""

import sys
import time
from examples_config import ExamplesConfigLoader
from vastpy import VASTClient

def main():
    print("🔍 Example 7: Orphaned Data Discovery")
    print("=" * 60)
    
    # Load configuration
    config = ExamplesConfigLoader()
    vast_config = config.get_vast_config()
    
    # Connect to VAST
    print("📋 Step 1: Connecting to VAST...")
    try:
        # Clean the address (remove https:// prefix if present)
        address = vast_config['address']
        if address.startswith('https://'):
            address = address[8:]
        elif address.startswith('http://'):
            address = address[7:]
        
        client = VASTClient(
            address=address,
            user=vast_config['user'],
            password=vast_config['password']
        )
        print("✅ Connected to VAST successfully")
    except Exception as e:
        print(f"❌ Failed to connect to VAST: {e}")
        return False
    
    # Query events endpoint for view deletions
    print("\n📋 Step 2: Querying VAST events for view deletions...")
    return query_events_for_deletions(client, config, vast_config)

def query_events_for_deletions(client, config, vast_config):
    """Query events endpoint for view deletion events"""
    print("🔍 Querying events endpoint for view deletions...")
    
    try:
        events = client.events.get()
        print(f"✅ Retrieved {len(events)} event log entries")
        
        # Filter for view deletion events
        view_deletions = []
        for event in events:
            if (event.get('object_type') == 'View' and 
                event.get('event_type') == 'OBJECT_DELETED'):
                view_deletions.append(event)
        
        print(f"🔍 Found {len(view_deletions)} view deletion events in event logs")
        
        if view_deletions:
            print("\n📊 View deletion summary:")
            for i, deletion in enumerate(view_deletions[:10], 1):
                print(f"{i}. Path: {deletion.get('object_name', 'Unknown')}")
                print(f"   Deleted at: {deletion.get('timestamp', 'Unknown')}")
                print(f"   Event: {deletion.get('event_message', 'Unknown')}")
                print()
            
            if len(view_deletions) > 10:
                print(f"... and {len(view_deletions) - 10} more")
            
            # Check if directories still exist
            print("\n📋 Step 3: Checking if directories still exist...")
            return check_directory_existence(client, view_deletions, config, vast_config)
        
        return True
        
    except Exception as e:
        print(f"❌ Events endpoint failed: {e}")
        return False

def check_directory_existence(client, view_deletions, config, vast_config):
    """Check if directories from deleted views still exist"""
    print("🔍 Checking directory existence for deleted views...")
    
    orphaned_directories = []
    existing_directories = []
    
    for i, deletion in enumerate(view_deletions, 1):  # Check all deleted views
        view_path = deletion.get('object_name', '')
        if not view_path:
            continue
            
        print(f"   {i}. Checking: {view_path}")
        
        try:
            # Try to check if the directory/path still exists and get ownership info
            path_exists = False
            path_ownership = None
            
            # Method 1: Try stat_path API for detailed information
            try:
                import requests
                import json
                
                # Get the base URL and credentials
                vast_address = vast_config['address']
                print(f"      Debug - VAST address from config: {vast_address}")
                
                if not vast_address:
                    print(f"      ⚠️  VAST address not properly configured in config.yaml")
                    print(f"      💡 Please set 'vast.address' in config.yaml")
                    raise Exception("VAST address not configured")
                
                if not vast_address.startswith('http'):
                    vast_address = f"https://{vast_address}"
                vast_address = vast_address.rstrip('/')
                
                auth = (config.config.get('vast.user', 'admin'), config.get_secret('vast_password', ''))
                
                stat_url = f"{vast_address}/api/folders/stat_path/"
                # Try without tenant_id first - let VAST determine the correct tenant
                stat_data = {
                    "path": view_path
                }
                print(f"      Debug - Trying without tenant_id first...")
                
                response = requests.post(stat_url, auth=auth, json=stat_data, verify=False)
                
                if response.status_code == 200:
                    path_ownership = response.json()
                    path_exists = True
                    owner = path_ownership.get('owner', 'Unknown')
                    group = path_ownership.get('group', 'Unknown')
                    print(f"      ❌ Path exists with ownership: {owner}:{group}")
                elif response.status_code == 404:
                    print(f"      ✅ Path not found (404)")
                elif response.status_code == 400:
                    # 400 "Tenant matching query does not exist" - try with tenant_id from event
                    print(f"      ⚠️  Request failed without tenant_id (400), trying with tenant from event...")
                    tenant_id = deletion.get('metadata', {}).get('tenant_id', 1)
                    stat_data['tenant_id'] = tenant_id
                    response = requests.post(stat_url, auth=auth, json=stat_data, verify=False)
                    if response.status_code == 200:
                        path_ownership = response.json()
                        path_exists = True
                        owner = path_ownership.get('owner', 'Unknown')
                        group = path_ownership.get('group', 'Unknown')
                        print(f"      ❌ Path exists with ownership: {owner}:{group} (using tenant {tenant_id})")
                    elif response.status_code == 404:
                        print(f"      ✅ Path not found with tenant {tenant_id} (404)")
                    elif response.status_code == 503:
                        print(f"      ✅ Path not found with tenant {tenant_id} (503)")
                    else:
                        print(f"      ❌ Still failed with tenant {tenant_id}: {response.status_code}")
                elif response.status_code == 503:
                    # 503 "Template directory path wasn't found" - path doesn't exist
                    print(f"      ✅ Path not found (503 - Template directory path wasn't found)")
                elif response.status_code == 429:
                    # Rate limiting - wait and retry
                    print(f"      ⚠️  Rate limited (429), waiting 2 seconds...")
                    time.sleep(2)
                    # Retry once
                    response = requests.post(stat_url, auth=auth, json=stat_data, verify=False)
                    if response.status_code == 200:
                        path_ownership = response.json()
                        path_exists = True
                        owner = path_ownership.get('owner', 'Unknown')
                        group = path_ownership.get('group', 'Unknown')
                        print(f"      ❌ Path exists with ownership: {owner}:{group} (after retry)")
                    else:
                        print(f"      ✅ Path not found after retry: {response.status_code}")
                else:
                    print(f"      ⚠️  Stat path failed: {response.status_code} - {response.text}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                    
            except Exception as stat_error:
                print(f"      ⚠️  Stat path API failed: {stat_error}")
                
                # Fallback: Try files API
                try:
                    files = client.files.get(path=view_path)
                    if files and len(files) > 0:
                        path_exists = True
                        print(f"      ❌ Path exists (found {len(files)} files)")
                except Exception as files_error:
                    # Method 2: Try directories API
                    try:
                        dirs = client.directories.get(path=view_path)
                        if dirs and len(dirs) > 0:
                            path_exists = True
                            print(f"      ❌ Path exists (found {len(dirs)} directories)")
                    except Exception as dirs_error:
                        # Method 3: Try to get files with a wildcard pattern
                        try:
                            files = client.files.get(path=f"{view_path}/*")
                            if files and len(files) > 0:
                                path_exists = True
                                print(f"      ❌ Path exists (found {len(files)} items)")
                        except Exception:
                            pass
            
            if path_exists:
                # Path still exists - this is ORPHANED DATA (BAD)
                orphaned_directories.append({
                    'path': view_path,
                    'deleted_at': deletion.get('timestamp', 'Unknown'),
                    'event': deletion.get('event_message', 'Unknown'),
                    'ownership': path_ownership
                })
                print(f"      🚨 ORPHANED: Directory still exists - NEEDS CLEANUP!")
            else:
                # Path doesn't exist - clean deletion (GOOD)
                existing_directories.append({
                    'path': view_path,
                    'deleted_at': deletion.get('timestamp', 'Unknown'),
                    'event': deletion.get('event_message', 'Unknown')
                })
                print(f"      ✅ CLEAN: Directory properly deleted - No action needed")
                
        except Exception as e:
            print(f"      ⚠️  Error checking directory: {e}")
            continue
    
    # Report results
    print(f"\n📊 Directory Existence Report:")
    print(f"   Total deleted views checked: {len(view_deletions)}")
    print(f"   🚨 ORPHANED directories (still exist): {len(orphaned_directories)}")
    print(f"   ✅ CLEAN deletions (properly removed): {len(existing_directories)}")
    
    if orphaned_directories:
        print(f"\n🚨 ORPHANED Directories (still exist but view deleted - NEEDS CLEANUP):")
        for i, dir_info in enumerate(orphaned_directories[:10], 1):
            print(f"   {i}. {dir_info['path']}")
            print(f"      Deleted at: {dir_info['deleted_at']}")
            print(f"      Event: {dir_info['event']}")
            
            # Show ownership information if available
            if dir_info.get('ownership'):
                ownership = dir_info['ownership']
                owner = ownership.get('owner', 'Unknown')
                group = ownership.get('group', 'Unknown')
                print(f"      Ownership: {owner}:{group}")
                
                # Show additional metadata if available
                if 'permissions' in ownership:
                    print(f"      Permissions: {ownership['permissions']}")
                if 'size' in ownership:
                    print(f"      Size: {ownership['size']}")
            print()
        
        if len(orphaned_directories) > 10:
            print(f"   ... and {len(orphaned_directories) - 10} more orphaned directories")
    
    if existing_directories:
        print(f"\n✅ CLEAN Deletions (directories properly removed - No action needed):")
        for i, dir_info in enumerate(existing_directories[:5], 1):
            print(f"   {i}. {dir_info['path']}")
        
        if len(existing_directories) > 5:
            print(f"   ... and {len(existing_directories) - 5} more clean deletions")

    # Generate full report file
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"orphaned_data_report_{timestamp}.txt"
    
    print(f"\n📄 Generating full report: {report_filename}")
    
    try:
        with open(report_filename, 'w') as report_file:
            report_file.write("VAST Orphaned Data Discovery Report\n")
            report_file.write("=" * 50 + "\n")
            report_file.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write(f"Total deleted views checked: {len(view_deletions)}\n")
            report_file.write(f"🚨 ORPHANED directories (still exist): {len(orphaned_directories)}\n")
            report_file.write(f"✅ CLEAN deletions (properly removed): {len(existing_directories)}\n\n")
            
            if orphaned_directories:
                report_file.write("🚨 ORPHANED DIRECTORIES (still exist but view deleted - NEEDS CLEANUP):\n")
                report_file.write("-" * 50 + "\n")
                for i, dir_info in enumerate(orphaned_directories, 1):
                    report_file.write(f"{i}. {dir_info['path']}\n")
                    report_file.write(f"   Deleted at: {dir_info['deleted_at']}\n")
                    report_file.write(f"   Event: {dir_info['event']}\n")
                    
                    # Show ownership information if available
                    if dir_info.get('ownership'):
                        ownership = dir_info['ownership']
                        owner = ownership.get('owner', 'Unknown')
                        group = ownership.get('group', 'Unknown')
                        report_file.write(f"   Ownership: {owner}:{group}\n")
                        
                        # Show additional metadata if available
                        if 'permissions' in ownership:
                            report_file.write(f"   Permissions: {ownership['permissions']}\n")
                        if 'size' in ownership:
                            report_file.write(f"   Size: {ownership['size']}\n")
                    report_file.write("\n")
            
            if existing_directories:
                report_file.write("✅ CLEAN DELETIONS (directories properly removed - No action needed):\n")
                report_file.write("-" * 50 + "\n")
                for i, dir_info in enumerate(existing_directories, 1):
                    report_file.write(f"{i}. {dir_info['path']}\n")
                    report_file.write(f"   Deleted at: {dir_info['deleted_at']}\n")
                    report_file.write(f"   Event: {dir_info['event']}\n\n")
        
        print(f"✅ Full report saved to: {report_filename}")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not save report file: {e}")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Orphaned data discovery completed successfully")
    else:
        print("\n❌ Orphaned data discovery failed")
        sys.exit(1)

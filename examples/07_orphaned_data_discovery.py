#!/usr/bin/env python3
"""
Example 7: Orphaned Data Discovery

This script identifies deleted views from event logs and checks if their
associated directories still exist on the VAST system using the stat_path API.

The script:
1. Queries VAST event logs for view deletion events
2. Deduplicates events to get unique view deletions
3. Checks if views have been recreated (skips if so)
4. Uses the stat_path API to check if directories still exist
5. Categorizes results as orphaned (need cleanup) or clean (properly deleted)
6. Generates a comprehensive report with ownership and metadata
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
    recreated_views = []
    error_views = []
    no_path_views = 0
    
    # Get current views once to avoid repeated API calls
    print("🔍 Getting current active views for comparison...")
    try:
        current_views = client.views.get()
        current_view_paths = {view.get('path') for view in current_views if view.get('path')}
        print(f"✅ Found {len(current_view_paths)} active views")
    except Exception as e:
        print(f"⚠️  Could not get current views: {e}")
        current_view_paths = set()
    
    # Deduplicate view deletions - keep only the most recent deletion for each path
    print("🔍 Deduplicating view deletions...")
    unique_deletions = {}
    for deletion in view_deletions:
        view_path = deletion.get('object_name', '')
        if view_path:  # Only process views with valid paths
            # Keep the most recent deletion for each path
            if view_path not in unique_deletions or deletion.get('timestamp', '') > unique_deletions[view_path].get('timestamp', ''):
                unique_deletions[view_path] = deletion
    
    print(f"✅ Deduplicated: {len(view_deletions)} → {len(unique_deletions)} unique view deletions")
    
    # Debug: Show some of the unique deletions
    print(f"🔍 Sample unique deletions:")
    for i, (path, deletion) in enumerate(list(unique_deletions.items())[:5], 1):
        print(f"   {i}. {path} (deleted: {deletion.get('timestamp', 'Unknown')})")
    if len(unique_deletions) > 5:
        print(f"   ... and {len(unique_deletions) - 5} more")
    
    # Process only unique view deletions
    for i, (view_path, deletion) in enumerate(unique_deletions.items(), 1):
        print(f"   {i}. Checking: {view_path}")
        
        # First, verify the view is actually deleted (not recreated)
        print(f"      🔍 Verifying view is still deleted...")
        
        if view_path in current_view_paths:
            recreated_views.append({
                'path': view_path,
                'deleted_at': deletion.get('timestamp', 'Unknown'),
                'event': deletion.get('event_message', 'Unknown')
            })
            print(f"      ⚠️  View has been recreated - skipping (not orphaned)")
            continue
        else:
            print(f"      ✅ View confirmed deleted - proceeding with directory check")
        
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
                    is_directory = path_ownership.get('is_directory', False)
                    owner = path_ownership.get('owning_user', 'Unknown')
                    group = path_ownership.get('owning_group', 'Unknown')
                    
                    if is_directory:
                        path_exists = True
                        print(f"      ❌ Directory exists with ownership: {owner}:{group}")
                    else:
                        print(f"      ⚠️  Path exists but is not a directory (file?): {owner}:{group}")
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
                        is_directory = path_ownership.get('is_directory', False)
                        owner = path_ownership.get('owning_user', 'Unknown')
                        group = path_ownership.get('owning_group', 'Unknown')
                        
                        if is_directory:
                            path_exists = True
                            print(f"      ❌ Directory exists with ownership: {owner}:{group} (using tenant {tenant_id})")
                        else:
                            print(f"      ⚠️  Path exists but is not a directory (file?): {owner}:{group} (using tenant {tenant_id})")
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
                        is_directory = path_ownership.get('is_directory', False)
                        owner = path_ownership.get('owning_user', 'Unknown')
                        group = path_ownership.get('owning_group', 'Unknown')
                        
                        if is_directory:
                            path_exists = True
                            print(f"      ❌ Directory exists with ownership: {owner}:{group} (after retry)")
                        else:
                            print(f"      ⚠️  Path exists but is not a directory (file?): {owner}:{group} (after retry)")
                    else:
                        print(f"      ✅ Path not found after retry: {response.status_code}")
                else:
                    print(f"      ⚠️  Stat path failed: {response.status_code} - {response.text}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                    
            except Exception as stat_error:
                print(f"      ⚠️  Stat path API failed: {stat_error}")
                print(f"      ❌ Cannot determine if path exists - API unavailable")
            
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
            error_views.append({
                'path': view_path,
                'deleted_at': deletion.get('timestamp', 'Unknown'),
                'event': deletion.get('event_message', 'Unknown'),
                'error': f"Directory check failed: {str(e)}"
            })
            continue
    
    # Report results
    print(f"\n📊 Directory Existence Report:")
    print(f"   Total view deletion events: {len(view_deletions)}")
    print(f"   📝 Views with no path (skipped): {no_path_views}")
    print(f"   🔄 Views recreated (skipped): {len(recreated_views)}")
    print(f"   🚨 ORPHANED directories (still exist): {len(orphaned_directories)}")
    print(f"   ✅ CLEAN deletions (properly removed): {len(existing_directories)}")
    print(f"   ⚠️  Errors during processing: {len(error_views)}")
    
    # Verify math
    total_processed = len(recreated_views) + len(orphaned_directories) + len(existing_directories) + len(error_views)
    print(f"   📊 Math check: {total_processed}/{len(unique_deletions)} unique views processed")
    
    if orphaned_directories:
        print(f"\n🚨 ORPHANED Directories (still exist but view deleted - NEEDS CLEANUP):")
        for i, dir_info in enumerate(orphaned_directories[:10], 1):
            print(f"   {i}. {dir_info['path']}")
            print(f"      Deleted at: {dir_info['deleted_at']}")
            print(f"      Event: {dir_info['event']}")
            
            # Show ownership information if available
            if dir_info.get('ownership'):
                ownership = dir_info['ownership']
                owner = ownership.get('owning_user', 'Unknown')
                group = ownership.get('owning_group', 'Unknown')
                is_directory = ownership.get('is_directory', False)
                print(f"      Ownership: {owner}:{group}")
                print(f"      Type: {'Directory' if is_directory else 'File'}")
                
                # Show additional metadata if available
                if 'permissions' in ownership:
                    print(f"      Permissions: {ownership['permissions']}")
                if 'size' in ownership:
                    print(f"      Size: {ownership['size']}")
            print()
        
        if len(orphaned_directories) > 10:
            print(f"   ... and {len(orphaned_directories) - 10} more orphaned directories")
    
    if recreated_views:
        print(f"\n🔄 Views Recreated (skipped - not orphaned):")
        for i, view_info in enumerate(recreated_views[:5], 1):
            print(f"   {i}. {view_info['path']}")
            print(f"      Originally deleted: {view_info['deleted_at']}")
        
        if len(recreated_views) > 5:
            print(f"   ... and {len(recreated_views) - 5} more recreated views")
    
    if error_views:
        print(f"\n⚠️  Processing Errors (could not complete check):")
        for i, error_info in enumerate(error_views[:5], 1):
            print(f"   {i}. {error_info['path']}")
            print(f"      Error: {error_info['error']}")
        
        if len(error_views) > 5:
            print(f"   ... and {len(error_views) - 5} more errors")
    
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
            report_file.write(f"Total view deletion events: {len(view_deletions)}\n")
            report_file.write(f"📝 Views with no path (skipped): {no_path_views}\n")
            report_file.write(f"🔄 Views recreated (skipped): {len(recreated_views)}\n")
            report_file.write(f"🚨 ORPHANED directories (still exist): {len(orphaned_directories)}\n")
            report_file.write(f"✅ CLEAN deletions (properly removed): {len(existing_directories)}\n")
            report_file.write(f"⚠️  Processing errors: {len(error_views)}\n\n")
            
            # Math verification
            total_processed = len(recreated_views) + len(orphaned_directories) + len(existing_directories) + len(error_views)
            report_file.write(f"Math verification: {total_processed}/{len(unique_deletions)} unique views processed\n\n")
            
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
                        owner = ownership.get('owning_user', 'Unknown')
                        group = ownership.get('owning_group', 'Unknown')
                        is_directory = ownership.get('is_directory', False)
                        report_file.write(f"   Ownership: {owner}:{group}\n")
                        report_file.write(f"   Type: {'Directory' if is_directory else 'File'}\n")
                        
                        # Show additional metadata if available
                        if 'permissions' in ownership:
                            report_file.write(f"   Permissions: {ownership['permissions']}\n")
                        if 'size' in ownership:
                            report_file.write(f"   Size: {ownership['size']}\n")
                    report_file.write("\n")
            
            if recreated_views:
                report_file.write("🔄 VIEWS RECREATED (skipped - not orphaned):\n")
                report_file.write("-" * 50 + "\n")
                for i, view_info in enumerate(recreated_views, 1):
                    report_file.write(f"{i}. {view_info['path']}\n")
                    report_file.write(f"   Originally deleted: {view_info['deleted_at']}\n")
                    report_file.write(f"   Event: {view_info['event']}\n\n")
            
            if error_views:
                report_file.write("⚠️  PROCESSING ERRORS (could not complete check):\n")
                report_file.write("-" * 50 + "\n")
                for i, error_info in enumerate(error_views, 1):
                    report_file.write(f"{i}. {error_info['path']}\n")
                    report_file.write(f"   Deleted at: {error_info['deleted_at']}\n")
                    report_file.write(f"   Event: {error_info['event']}\n")
                    report_file.write(f"   Error: {error_info['error']}\n\n")
            
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

#!/usr/bin/env python3
"""
Example 7: Orphaned Data Discovery

This script efficiently finds orphaned data by:
1. Getting all actual directory paths from VAST using vastdb catalog
2. Getting all current view paths from VAST
3. Finding directories that exist but have no corresponding views
"""

import sys
from collections import defaultdict
from examples_config import ExamplesConfigLoader
from vastpy import VASTClient
import vastdb
from ibis import _

def get_all_directory_paths():
    """Get all actual directory paths from VAST using vastdb catalog"""
    print("🔍 Step 1: Getting all directory paths from VAST catalog...")
    
    try:
        # Load configuration
        config_loader = ExamplesConfigLoader()
        
        # Get S3 configuration for vastdb (same pattern as example 8)
        s3_config = config_loader.config.get('s3', {})
        
        s3_endpoint = s3_config.get('endpoint_url')
        s3_access_key = config_loader.secrets.get('s3_access_key')
        s3_secret_key = config_loader.secrets.get('s3_secret_key')
        
        # Get SSL verification setting (check vastdb first, then vast, default to True)
        ssl_verify = config_loader.config.get('vastdb.ssl_verify', 
                                               config_loader.config.get('vast.ssl_verify', True))
        
        if not all([s3_endpoint, s3_access_key, s3_secret_key]):
            print("❌ Missing S3 credentials for vastdb connection")
            return set()
        
        # Connect to vastdb
        session = vastdb.connect(
            endpoint=s3_endpoint,
            access=s3_access_key,
            secret=s3_secret_key,
            ssl_verify=ssl_verify
        )
        
        all_directories = set()
        
        with session.transaction() as tx:
            # Use the exact pattern from the official VAST DB documentation
            table = tx.catalog().select(['parent_path', 'name', 'element_type']).read_all()
            df = table.to_pandas()
            
            # Filter for directories only
            dirs_df = df[df['element_type'] == 'DIR']
            print(f"      ✅ Found {len(dirs_df)} directories in catalog")
            
            # Build full paths with progress indicator
            total_rows = len(dirs_df)
            skipped_count = 0
            
            for idx, (_, row) in enumerate(dirs_df.iterrows()):
                if idx % 100000 == 0:  # Show progress every 100k rows
                    print(f"      ⏳ Processing directories: {idx:,}/{total_rows:,} ({idx/total_rows*100:.1f}%)")
                
                parent_path = row['parent_path']
                name = row['name']
                
                # Construct full path
                full_path = f"{parent_path.rstrip('/')}/{name}"
                
                # Skip VAST internal directories
                if full_path.startswith('/.vast_audit_dir') or full_path.startswith('/.vast_removed_protected_paths'):
                    skipped_count += 1
                    continue
                
                all_directories.add(full_path)
            
            if skipped_count > 0:
                print(f"      ⏭️  Skipped {skipped_count:,} VAST internal directories")
        
        print(f"✅ Retrieved {len(all_directories)} unique directory paths")
        return all_directories
        
    except Exception as e:
        print(f"❌ Failed to get directory paths: {e}")
        return set()

def get_current_view_paths():
    """Get all current view paths from VAST"""
    print("\n🔍 Step 2: Getting current view paths...")
    
    try:
        # Load configuration
        config = ExamplesConfigLoader()
        vast_config = config.get_vast_config()
        
        # Connect to VAST
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
        
        # Get current views
        views = client.views.get()
        print(f"      ✅ Retrieved {len(views)} current views")
        
        # Extract view paths
        current_views = {}
        
        for view in views:
            view_path = view.get('path')  # Required field, no need to check for empty
            
            current_views[view_path] = {
                'view_id': view.get('id', 'Unknown'),
                'tenant_id': view.get('tenant_id', 'Unknown')
            }
        
        print(f"✅ Found {len(current_views)} current view paths")
        return current_views
        
    except Exception as e:
        print(f"❌ Failed to get current view paths: {e}")
        return {}

def find_orphaned_directories(all_directories, current_views):
    """Find directories that exist but have no corresponding views"""
    print("\n🔍 Step 3: Finding directories without corresponding views...")
    
    # Collect all view paths and create a more efficient lookup structure
    view_paths = set(current_views.keys())
    print(f"      📊 Total view paths: {len(view_paths)}")
    
    # Create a set of all possible parent paths for faster lookup
    # This avoids the O(n*m) nested loop
    parent_view_paths = set()
    for view_path in view_paths:
        if view_path != '/':
            # Add the view path itself
            parent_view_paths.add(view_path)
            # Add all parent directories of the view path
            parts = view_path.strip('/').split('/')
            for i in range(1, len(parts) + 1):
                parent_path = '/' + '/'.join(parts[:i])
                parent_view_paths.add(parent_path)
    
    print(f"      📊 Total parent view paths (including hierarchy): {len(parent_view_paths)}")
    
    # Find directories that exist but have no views
    orphaned = []
    covered_directories = set()
    
    # Process in batches to show progress
    total_dirs = len(all_directories)
    batch_size = 100000  # Process 100k directories at a time
    processed = 0
    
    for i in range(0, total_dirs, batch_size):
        batch = list(all_directories)[i:i + batch_size]
        
        for directory in batch:
            is_covered = False
            
            # Check if directory is directly covered by a view path
            if directory in view_paths:
                is_covered = True
            
            # Check if directory is covered by any parent view (much faster lookup)
            if not is_covered:
                # Check if any parent path of this directory is in our parent_view_paths
                parts = directory.strip('/').split('/')
                for i in range(1, len(parts) + 1):
                    parent_path = '/' + '/'.join(parts[:i])
                    if parent_path in parent_view_paths:
                        is_covered = True
                        break
            
            if is_covered:
                covered_directories.add(directory)
            else:
                orphaned.append({'directory_path': directory})
        
        processed += len(batch)
        print(f"      ⏳ Processed {processed:,}/{total_dirs:,} directories ({processed/total_dirs*100:.1f}%)")
    
    print(f"      📊 Directories covered by views: {len(covered_directories)}")
    print(f"✅ Found {len(orphaned)} directories without corresponding views")
    return orphaned

def main():
    """Main function"""
    print("🔍 Example 7: Orphaned Data Discovery")
    print("=" * 60)
    
    # Step 1: Get all directory paths
    all_directories = get_all_directory_paths()
    if not all_directories:
        print("❌ No directories found, cannot proceed")
        return False
    
    # Step 2: Get current view paths
    current_views = get_current_view_paths()
    if not current_views:
        print("❌ No current views found, cannot proceed")
        return False
    
    # Step 3: Find orphaned directories
    orphaned = find_orphaned_directories(all_directories, current_views)
    
    # Display results
    print(f"\n📊 Orphaned Data Analysis Results:")
    print(f"   Total directories: {len(all_directories)}")
    print(f"   Current views: {len(current_views)}")
    print(f"   Orphaned directories: {len(orphaned)}")
    
    if orphaned:
        print(f"\n🚨 ORPHANED DIRECTORIES (exist but have no views):")
        print("=" * 60)
        
        # Group orphaned directories by their top-level parent folder
        folder_groups = defaultdict(list)
        
        for item in orphaned:
            directory = item['directory_path']
            # Get the top-level folder (e.g., /1/CL3_HT1_FRONTEND/Dir1//bucket0 -> /1)
            parts = directory.strip('/').split('/')
            top_folder = f"/{parts[0]}" if parts else "/"
            folder_groups[top_folder].append(item)
        
        # Sort folders for consistent output
        sorted_folders = sorted(folder_groups.keys())
        
        print(f"📊 Summary by top-level folders:")
        for folder in sorted_folders:
            count = len(folder_groups[folder])
            print(f"   📁 {folder} - {count:,} orphaned directories")
        
        print(f"\n📋 Detailed breakdown by subdirectories:")
        for folder in sorted_folders:
            items = folder_groups[folder]
            print(f"\n📁 {folder}/ - {len(items):,} total orphaned directories")
            
            # Group by subdirectories within this folder
            subdir_groups = defaultdict(list)
            for item in items:
                directory = item['directory_path']
                # Get the path relative to the top folder
                relative_path = directory[len(folder):].lstrip('/')
                if relative_path:
                    subdir = relative_path.split('/')[0]
                    subdir_groups[subdir].append(item)
                else:
                    subdir_groups['root'].append(item)
            
            # Show counts for each subdirectory
            for subdir in sorted(subdir_groups.keys()):
                subdir_items = subdir_groups[subdir]
                if subdir == 'root':
                    print(f"   📂 Root level: {len(subdir_items):,} directories")
                else:
                    print(f"   📂 {subdir}/: {len(subdir_items):,} directories")
        
        print(f"\n📊 Total: {len(orphaned):,} orphaned directories across {len(sorted_folders)} top-level folders")
    else:
        print("\n✅ No orphaned directories found!")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Orphaned data matching completed successfully")
    else:
        print("\n❌ Orphaned data matching failed")
        sys.exit(1)

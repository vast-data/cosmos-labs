#!/usr/bin/env python3
"""
Example 7b: Orphaned Data Discovery (via API call to capacity/list_dir)

This variant discovers orphaned data by:
1) Enumerating existing directories using VAST VMS endpoint
   GET /api/latest/capacity/list_dir?path=<dir>
2) Getting current view paths from VAST
3) Finding directories that exist but have no corresponding views

Compared to Example 7 (catalog-based), this version queries the VMS directly
and does not require VAST DB credentials.
"""

import sys
import json
from collections import deque, defaultdict
from typing import Dict, Set

import requests
from urllib3.exceptions import InsecureRequestWarning
import argparse

from examples_config import ExamplesConfigLoader
from vastpy import VASTClient


def _normalize_base_url(vast_address: str) -> str:
    if vast_address.endswith('/'):
        return vast_address[:-1]
    return vast_address


def _call_list_dir(base_url: str, path: str, user: str, password: str, verify_ssl: bool, timeout: int = 30):
    url = f"{base_url}/api/latest/capacity/list_dir"
    params = {"path": path}
    response = requests.get(
        url,
        params=params,
        auth=(user, password) if user and password else None,
        timeout=timeout,
        verify=verify_ssl,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return json.loads(response.text)


def get_all_directory_paths_via_capacity(
    root_path: str = "/",
    max_depth: int = 0,
    timeout: int = 30,
) -> Set[str]:
    """Enumerate directories using capacity/list_dir with BFS traversal.

    - root_path: starting path (default: '/')
    - max_depth: safety limit to avoid overly deep scans
    """
    
    print("🔍 Step 1: Getting directory paths from VMS capacity endpoint...")

    try:
        config = ExamplesConfigLoader()
        vast_cfg = config.get_vast_config()

        base_url = _normalize_base_url(vast_cfg["address"])
        user = vast_cfg.get("user")
        password = vast_cfg.get("password")
        verify_ssl = config.get("vast.ssl_verify", True)
        if not verify_ssl:
            # Suppress noisy warnings when user explicitly disables verification
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        visited: Set[str] = set()
        found_dirs: Set[str] = set()

        # BFS over directory hierarchy up to max_depth
        queue = deque([(root_path, 0)])

        while queue:
            current_path, depth = queue.popleft()
            if current_path in visited:
                continue
            visited.add(current_path)

            try:
                entries = _call_list_dir(base_url, current_path, user, password, verify_ssl, timeout)
            except requests.HTTPError as http_err:
                print(f"   ⚠️  HTTP error for {current_path}: {http_err}")
                continue
            except Exception as e:
                print(f"   ⚠️  Failed to list {current_path}: {e}")
                continue

            # The endpoint returns a list of names under current_path
            if isinstance(entries, list):
                # Filter out VAST internal directories at this level
                filtered = [name for name in entries if not name.startswith('.vast_')]
                if depth == 0:
                    print(f"      ✅ Listed {len(filtered)} entries under {current_path}")
                for name in filtered:
                    # Build full path
                    child_path = current_path.rstrip('/') + '/' + name if current_path != '/' else '/' + name
                    found_dirs.add(child_path)

                    # Only continue traversal if depth limit not reached
                    if depth < max_depth:
                        queue.append((child_path, depth + 1))

            # Optional periodic progress (kept minimal)
            if len(found_dirs) % 10000 == 0 and len(found_dirs) > 0:
                print(f"      ⏳ Discovered {len(found_dirs):,} directories so far (depth≤{max_depth})")

        print(f"✅ Retrieved {len(found_dirs):,} directory paths via capacity endpoint (depth≤{max_depth})")
        return found_dirs

    except Exception as e:
        print(f"❌ Failed to get directory paths via capacity endpoint: {e}")
        return set()


def get_current_view_paths() -> Dict[str, Dict[str, str]]:
    """Get current view paths from VAST."""
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

        current_views: Dict[str, Dict[str, str]] = {}
        for view in views:
            view_path = view.get('path')
            current_views[view_path] = {
                'view_id': view.get('id', 'Unknown'),
                'tenant_id': view.get('tenant_id', 'Unknown')
            }

        print(f"✅ Found {len(current_views)} unique view paths")
        return current_views

    except Exception as e:
        print(f"❌ Failed to get current view paths: {e}")
        return {}


def find_orphaned_directories(all_directories: Set[str], current_views: Dict[str, Dict[str, str]]):
    """Find directories that exist but have no corresponding views."""
    print("\n🔍 Step 3: Finding directories without corresponding views...")

    view_paths = set(current_views.keys())
    print(f"      📊 Total view paths: {len(view_paths)}")

    parent_view_paths = set()
    for view_path in view_paths:
        if view_path != '/':
            parent_view_paths.add(view_path)
            parts = view_path.strip('/').split('/')
            for i in range(1, len(parts) + 1):
                parent_path = '/' + '/'.join(parts[:i])
                parent_view_paths.add(parent_path)

    print(f"      📊 Total parent view paths (including hierarchy): {len(parent_view_paths)}")

    orphaned = []
    covered_directories = set()

    total_dirs = len(all_directories)
    batch_size = 100000
    processed = 0

    for i in range(0, total_dirs, batch_size):
        batch = list(all_directories)[i:i + batch_size]
        for directory in batch:
            is_covered = False
            if directory in view_paths:
                is_covered = True
            if not is_covered:
                parts = directory.strip('/').split('/')
                for j in range(1, len(parts) + 1):
                    parent_path = '/' + '/'.join(parts[:j])
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
    print("🔍 Example 7b: Orphaned Data Discovery (capacity endpoint)")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="Orphaned Data Discovery using capacity list_dir")
    parser.add_argument("--path", default="/", help="Path to start enumeration (default: /)")
    parser.add_argument("--max-depth", type=int, default=0, help="Traversal depth (0=list only root contents)")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds (default: 30)")
    args = parser.parse_args()

    if args.max_depth > 0:
        print(f"⚠️  Traversing depth {args.max_depth} from {args.path}. This may take time on large trees.")

    # Step 1: Enumerate directories using capacity endpoint
    all_directories = get_all_directory_paths_via_capacity(
        root_path=args.path,
        max_depth=args.max_depth,
        timeout=args.timeout,
    )
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
    print(f"   Total directories (depth≤{args.max_depth}): {len(all_directories)}")
    print(f"   Unique view paths: {len(current_views)}")
    print(f"   Orphaned directories: {len(orphaned)}")

    if orphaned:
        print(f"\n🚨 ORPHANED DIRECTORIES (exist but have no views):")
        print("=" * 60)

        folder_groups = defaultdict(list)
        for item in orphaned:
            directory = item['directory_path']
            parts = directory.strip('/').split('/')
            top_folder = f"/{parts[0]}" if parts else "/"
            folder_groups[top_folder].append(item)

        sorted_folders = sorted(folder_groups.keys())
        print(f"📊 Summary by top-level folders:")
        for folder in sorted_folders:
            count = len(folder_groups[folder])
            print(f"   📁 {folder} - {count:,} orphaned directories")

        # Keep output succinct: no further breakdown

        print(f"\n📊 Total: {len(orphaned):,} orphaned directories across {len(sorted_folders)} top-level folders")
    else:
        print("\n✅ No orphaned directories found!")

    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Orphaned data matching (capacity) completed successfully")
    else:
        print("\n❌ Orphaned data matching (capacity) failed")
        sys.exit(1)



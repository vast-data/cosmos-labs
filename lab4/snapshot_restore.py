#!/usr/bin/env python3
"""
VAST Snapshot Restore Manager

This module provides functionality to restore snapshots using VAST's protected path
restore API with the two-step process: restore -> commit.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Lab 4 configuration
from lab4_config import Lab4Config
from vastpy import VASTClient


class SnapshotRestoreManager:
    """
    Manager for VAST snapshot restoration using protected path restore API.
    
    Provides methods to restore snapshots using the proper VAST API:
    1. POST /protectedpaths/{id}/restore - Create clone from snapshot
    2. PATCH /protectedpaths/{id}/commit - Commit the restored path
    """
    
    def __init__(self, config: Optional[Lab4Config] = None):
        """
        Initialize the snapshot restore manager.
        
        Args:
            config: Lab 4 configuration instance
        """
        self.config = config or Lab4Config()
        self.vast_config = self.config.get_vast_config()
        
        # Strip protocol from address (like other labs do)
        address = self.vast_config['address']
        if address.startswith('https://'):
            address = address[8:]
        elif address.startswith('http://'):
            address = address[7:]
        
        # Initialize VAST client
        self.logger = logging.getLogger(__name__)
        try:
            self.vast_client = VASTClient(
                address=address,
                user=self.vast_config.get('user'),
                password=self.vast_config.get('password')
            )
            self.logger.info(f"✅ VAST client initialized for snapshot restoration")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize VAST client: {e}")
            self.vast_client = None
    
    def get_protected_path_id(self, protected_path_name: str) -> Optional[int]:
        """
        Get the protected path ID for a given protected path name.
        
        Args:
            protected_path_name: The protected path name to find the ID for
            
        Returns:
            Protected path ID if found, None otherwise
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Looking up protected path ID for name: {protected_path_name}")
        
        try:
            protected_paths = self.vast_client.protectedpaths.get()
            
            # Find protected path by name (exact match first)
            for path in protected_paths:
                if path.get('name') == protected_path_name:
                    path_id = path.get('id')
                    source_dir = path.get('source_dir', 'Unknown')
                    self.logger.info(f"✅ Found protected path: {protected_path_name} (ID: {path_id}) -> {source_dir}")
                    return path_id
            
            # If no exact match, try partial match
            for path in protected_paths:
                if protected_path_name in path.get('name', ''):
                    path_id = path.get('id')
                    path_name = path.get('name', 'Unknown')
                    source_dir = path.get('source_dir', 'Unknown')
                    self.logger.info(f"✅ Found partial match: {path_name} (ID: {path_id}) -> {source_dir}")
                    return path_id
            
            self.logger.warning(f"⚠️  No protected path found with name: {protected_path_name}")
            self.logger.info("💡 Available protected paths:")
            for i, path in enumerate(protected_paths[:10], 1):
                path_name = path.get('name', 'Unknown')
                source_dir = path.get('source_dir', 'Unknown')
                self.logger.info(f"  {i}. {path_name} -> {source_dir}")
            if len(protected_paths) > 10:
                self.logger.info(f"  ... and {len(protected_paths) - 10} more protected paths")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to lookup protected path for name {protected_path_name}: {e}")
            raise
    
    def get_snapshot_id(self, snapshot_name: str, view_path: Optional[str] = None) -> Optional[int]:
        """
        Get the snapshot ID for a given snapshot name.
        
        Args:
            snapshot_name: Name of the snapshot to find
            view_path: Optional view path to filter snapshots
            
        Returns:
            Snapshot ID if found, None otherwise
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Looking up snapshot ID for name: {snapshot_name}")
        if view_path:
            self.logger.info(f"View filter: {view_path}")
        
        try:
            # Build query parameters
            params = {}
            if view_path:
                # Try to resolve the view path, but if it fails, use the provided path as-is
                try:
                    resolved_path = self._resolve_view_path(view_path)
                    params['path'] = resolved_path
                    self.logger.info(f"Resolved view path: {view_path} -> {resolved_path}")
                except Exception as e:
                    self.logger.warning(f"Could not resolve view path '{view_path}': {e}")
                    self.logger.info(f"Using provided path as-is: {view_path}")
                    params['path'] = view_path
            
            snapshots = self.vast_client.snapshots.get(**params)
            
            # Log available snapshots for debugging
            self.logger.info(f"Found {len(snapshots)} snapshots to search through:")
            for i, snapshot in enumerate(snapshots[:10], 1):  # Show first 10
                snapshot_name_found = snapshot.get('name', 'Unknown')
                snapshot_path_found = snapshot.get('path', 'Unknown')
                self.logger.info(f"  {i}. {snapshot_name_found} -> {snapshot_path_found}")
            if len(snapshots) > 10:
                self.logger.info(f"  ... and {len(snapshots) - 10} more snapshots")
            
            # Find snapshot by name (exact match)
            for snapshot in snapshots:
                if snapshot.get('name') == snapshot_name:
                    snapshot_id = snapshot.get('id')
                    self.logger.info(f"✅ Found exact match: {snapshot_name} (ID: {snapshot_id})")
                    return snapshot_id
            
            # If no exact match, try partial match (snapshot name contains search term)
            for snapshot in snapshots:
                snapshot_full_name = snapshot.get('name', '')
                if snapshot_name in snapshot_full_name:
                    snapshot_id = snapshot.get('id')
                    self.logger.info(f"✅ Found partial match: {snapshot_full_name} (ID: {snapshot_id})")
                    return snapshot_id
            
            # If still no match, try reverse partial match (search term contains snapshot name)
            for snapshot in snapshots:
                snapshot_full_name = snapshot.get('name', '')
                if snapshot_full_name in snapshot_name:
                    snapshot_id = snapshot.get('id')
                    self.logger.info(f"✅ Found reverse partial match: {snapshot_full_name} (ID: {snapshot_id})")
                    return snapshot_id
            
            self.logger.warning(f"⚠️  No snapshot found with name: {snapshot_name}")
            self.logger.info("💡 Try using --list-available-snapshots to see available snapshots")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to lookup snapshot {snapshot_name}: {e}")
            raise
    
    def restore_from_snapshot(self, 
                            snapshot_name: str, 
                            protected_path_name: str,
                            dry_run: bool = True) -> Dict[str, Any]:
        """
        Restore a protected path from a snapshot using VAST's protected path restore API.
        
        Args:
            snapshot_name: Name of the snapshot to restore from
            protected_path_name: Name of the protected path to restore
            dry_run: If True, only show what would be done
            
        Returns:
            Dict containing restoration result information
        """
        self.logger.info(f"Starting snapshot restoration process")
        self.logger.info(f"Snapshot: {snapshot_name}")
        self.logger.info(f"Protected path: {protected_path_name}")
        self.logger.info(f"Dry run: {dry_run}")
        
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        try:
            # Step 1: Get protected path ID
            protected_path_id = self.get_protected_path_id(protected_path_name)
            if not protected_path_id:
                raise Exception(f"No protected path found with name: {protected_path_name}")
            
            # Step 2: Get snapshot ID (no view path filtering needed)
            snapshot_id = self.get_snapshot_id(snapshot_name)
            if not snapshot_id:
                raise Exception(f"No snapshot found with name: {snapshot_name}")
            
            if dry_run:
                self.logger.info(f"Would restore protected path '{protected_path_name}' from snapshot '{snapshot_name}'")
                self.logger.info(f"Protected path ID: {protected_path_id}")
                self.logger.info(f"Snapshot ID: {snapshot_id}")
                return {
                    'snapshot_name': snapshot_name,
                    'snapshot_id': snapshot_id,
                    'protected_path_name': protected_path_name,
                    'protected_path_id': protected_path_id,
                    'dry_run': True,
                    'status': 'preview'
                }
            
            # Step 3: Create clone from snapshot (POST /protectedpaths/{id}/restore)
            self.logger.info(f"Step 1: Creating clone from snapshot...")
            restore_payload = {
                "name": f"restore-{snapshot_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "loanee_snapshot_id": snapshot_id
            }
            
            self.logger.debug(f"Restore payload: {json.dumps(restore_payload, indent=2)}")
            
            restore_result = self.vast_client.protectedpaths[protected_path_id].restore.post(**restore_payload)
            self.logger.info(f"✅ Step 1 completed: Clone created from snapshot")
            
            # Step 4: Commit the restored path (PATCH /protectedpaths/{id}/commit)
            self.logger.info(f"Step 2: Committing restored path...")
            commit_result = self.vast_client.protectedpaths[protected_path_id].commit.patch()
            self.logger.info(f"✅ Step 2 completed: Restored path committed")
            
            return {
                'snapshot_name': snapshot_name,
                'snapshot_id': snapshot_id,
                'protected_path_name': protected_path_name,
                'protected_path_id': protected_path_id,
                'dry_run': False,
                'status': 'completed',
                'restore_result': restore_result,
                'commit_result': commit_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restore snapshot: {e}")
            return {
                'snapshot_name': snapshot_name,
                'protected_path_name': protected_path_name,
                'dry_run': dry_run,
                'status': 'failed',
                'error': str(e)
            }
    
    def list_available_snapshots(self, protected_path_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available snapshots for restoration.
        
        Args:
            protected_path_name: Optional protected path name to filter snapshots
            
        Returns:
            List of available snapshots
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Listing available snapshots")
        if protected_path_name:
            self.logger.info(f"Protected path filter: {protected_path_name}")
        
        try:
            # Get all snapshots (no filtering by path for now)
            snapshots = self.vast_client.snapshots.get()
            
            self.logger.info(f"Found {len(snapshots)} available snapshots")
            
            if not snapshots:
                self.logger.info("📭 No snapshots found")
                self.logger.info("💡 Create a snapshot first with: --create-snapshot 'name' --protected-path 'view' --pushtoprod")
                return []
            
            # Display snapshots with better formatting
            self.logger.info(f"\n📸 Available Snapshots:")
            for i, snapshot in enumerate(snapshots, 1):
                snapshot_name = snapshot.get('name', 'Unknown')
                snapshot_path = snapshot.get('path', 'Unknown')
                created = snapshot.get('created', 'Unknown')
                state = snapshot.get('state', 'Unknown')
                size = snapshot.get('size', 0)
                
                # Format size
                if size > 0:
                    size_mb = size / (1024 * 1024)
                    size_str = f"{size_mb:.1f} MB"
                else:
                    size_str = "Unknown"
                
                self.logger.info(f"  {i}. {snapshot_name}")
                self.logger.info(f"     📁 Path: {snapshot_path}")
                self.logger.info(f"     📅 Created: {created}")
                self.logger.info(f"     📊 State: {state}, Size: {size_str}")
                self.logger.info("")
            
            self.logger.info(f"💡 To browse a snapshot: --browse-snapshot 'snapshot-name' --protected-path 'view'")
            self.logger.info(f"💡 To restore a snapshot: --restore-snapshot 'snapshot-name' --protected-path 'view'")
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list snapshots: {e}")
            raise
    
    def _resolve_view_path(self, path_input: str) -> str:
        """
        Resolve protected path names to actual view paths.
        
        Args:
            path_input: Protected path name (e.g., 'raw', 'processed') or full view path
            
        Returns:
            Actual view path
        """
        # If it's already a full path, return as-is
        if path_input.startswith('/'):
            return path_input
        
        # Map protected path names to view paths from config
        lab_config = self.config.get_lab_config()
        views_config = lab_config.get('views', {})
        if path_input in views_config:
            return views_config[path_input]['path']
        
        # If not found, raise an error with available options
        available_paths = list(views_config.keys())
        raise ValueError(f"Unknown protected path '{path_input}'. Available paths: {available_paths}")
    
    def list_snapshot_files(self, 
                           snapshot_name: str, 
                           protected_path_name: Optional[str] = None,
                           path_prefix: str = "",
                           max_depth: int = 3) -> Dict[str, Any]:
        """
        List files and directories in a snapshot using S3.
        
        Args:
            snapshot_name: Name of the snapshot to browse
            protected_path_name: Optional protected path name to get the S3 path
            path_prefix: Optional path prefix to filter files (e.g., "data/")
            max_depth: Maximum directory depth to show
            
        Returns:
            Dict containing file listing information
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Listing files in snapshot: {snapshot_name}")
        if protected_path_name:
            self.logger.info(f"Protected path filter: {protected_path_name}")
        if path_prefix:
            self.logger.info(f"Path prefix: {path_prefix}")
        
        try:
            # Get snapshot ID
            snapshot_id = self.get_snapshot_id(snapshot_name)
            if not snapshot_id:
                raise Exception(f"No snapshot found with name: {snapshot_name}")
            
            # Get snapshot details to find the path
            snapshot = self.vast_client.snapshots.get(id=snapshot_id)
            if not isinstance(snapshot, dict):
                raise Exception(f"Failed to get snapshot details for: {snapshot_name}")
            
            snapshot_path = snapshot.get('path', '')
            snapshot_created = snapshot.get('created', 'Unknown')
            
            self.logger.info(f"Snapshot path: {snapshot_path}")
            self.logger.info(f"Snapshot created: {snapshot_created}")
            
            # Construct snapshot directory path
            snapshot_dir = f"{snapshot_path}/.snapshot/{snapshot_name}"
            
            # Use S3 to list files in snapshot directory
            files_info = self._list_s3_directory_contents(
                snapshot_dir, 
                path_prefix=path_prefix,
                max_depth=max_depth
            )
            
            return {
                'snapshot_name': snapshot_name,
                'snapshot_id': snapshot_id,
                'snapshot_path': snapshot_path,
                'snapshot_dir': snapshot_dir,
                'snapshot_created': snapshot_created,
                'path_prefix': path_prefix,
                'max_depth': max_depth,
                'files': files_info['files'],
                'directories': files_info['directories'],
                'total_files': files_info['total_files'],
                'total_directories': files_info['total_directories'],
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list snapshot files: {e}")
            return {
                'snapshot_name': snapshot_name,
                'protected_path_name': protected_path_name,
                'path_prefix': path_prefix,
                'status': 'failed',
                'error': str(e)
            }
    
    def _list_s3_directory_contents(self, 
                                  s3_path: str,
                                  path_prefix: str = "",
                                  max_depth: int = 3,
                                  current_depth: int = 0) -> Dict[str, Any]:
        """
        List S3 directory contents using boto3.
        
        Args:
            s3_path: S3 path to list contents of
            path_prefix: Path prefix to filter by
            max_depth: Maximum depth to recurse
            current_depth: Current recursion depth
            
        Returns:
            Dict containing files and directories
        """
        files = []
        directories = []
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get S3 configuration (following Lab 2 pattern)
            endpoint_url = self.config.config.get('s3.endpoint_url')
            region_name = self.config.config.get('s3.region', 'us-east-1')
            path_style = self.config.config.get('s3.compatibility.path_style_addressing', True)
            ssl_verify = self.config.config.get('s3.ssl_verify', self.config.config.get('s3.verify_ssl', True))
            access_key = self.config.get_secret('s3_access_key')
            secret_key = self.config.get_secret('s3_secret_key')
            
            if not endpoint_url or not access_key or not secret_key:
                self.logger.error("❌ Missing S3 configuration")
                return {
                    'files': [],
                    'directories': [],
                    'total_files': 0,
                    'total_directories': 0
                }
            
            # Disable SSL warnings if SSL verification is disabled
            if not ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name,
                verify=ssl_verify,
                config=boto3.session.Config(
                    s3={'addressing_style': 'path' if path_style else 'auto'}
                )
            )
            
            # Parse S3 path
            if s3_path.startswith('/'):
                s3_path = s3_path[1:]  # Remove leading slash
            
            # Extract bucket and prefix
            path_parts = s3_path.split('/', 1)
            bucket_name = path_parts[0]
            prefix = path_parts[1] if len(path_parts) > 1 else ""
            
            if prefix and not prefix.endswith('/'):
                prefix += '/'
            
            self.logger.info(f"Listing S3 contents: s3://{bucket_name}/{prefix}")
            
            # List objects in S3
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            for page in page_iterator:
                # Process files
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['Key'] == prefix:  # Skip the directory itself
                            continue
                            
                        relative_path = obj['Key'][len(prefix):] if prefix else obj['Key']
                        
                        # Apply path prefix filter
                        if path_prefix and not relative_path.startswith(path_prefix):
                            continue
                        
                        # Skip if too deep
                        if current_depth >= max_depth:
                            continue
                        
                        file_info = {
                            'name': relative_path,
                            'path': obj['Key'],
                            'size': obj['Size'],
                            'modified': obj['LastModified'].isoformat(),
                            'type': 'file'
                        }
                        files.append(file_info)
                
                # Process directories
                if 'CommonPrefixes' in page:
                    for prefix_info in page['CommonPrefixes']:
                        relative_path = prefix_info['Prefix'][len(prefix):] if prefix else prefix_info['Prefix']
                        relative_path = relative_path.rstrip('/')
                        
                        # Apply path prefix filter
                        if path_prefix and not relative_path.startswith(path_prefix):
                            continue
                        
                        # Skip if too deep
                        if current_depth >= max_depth:
                            continue
                        
                        dir_info = {
                            'name': relative_path,
                            'path': prefix_info['Prefix'],
                            'modified': 'Unknown',
                            'type': 'directory'
                        }
                        directories.append(dir_info)
                        
                        # Recursively list subdirectories
                        if current_depth < max_depth - 1:
                            sub_contents = self._list_s3_directory_contents(
                                f"{bucket_name}/{prefix_info['Prefix']}",
                                path_prefix,
                                max_depth,
                                current_depth + 1
                            )
                            files.extend(sub_contents['files'])
                            directories.extend(sub_contents['directories'])
            
            return {
                'files': files,
                'directories': directories,
                'total_files': len(files),
                'total_directories': len(directories)
            }
            
        except ImportError:
            self.logger.error("❌ boto3 not available - cannot list S3 contents")
            return {
                'files': [],
                'directories': [],
                'total_files': 0,
                'total_directories': 0
            }
        except ClientError as e:
            self.logger.error(f"❌ S3 error listing {s3_path}: {e}")
            return {
                'files': [],
                'directories': [],
                'total_files': 0,
                'total_directories': 0
            }
        except Exception as e:
            self.logger.warning(f"Could not list S3 directory {s3_path}: {e}")
            return {
                'files': [],
                'directories': [],
                'total_files': 0,
                'total_directories': 0
            }
    
    def browse_snapshot(self, 
                       snapshot_name: str, 
                       protected_path_name: Optional[str] = None,
                       interactive: bool = False) -> Dict[str, Any]:
        """
        Browse a snapshot interactively or show summary.
        
        Args:
            snapshot_name: Name of the snapshot to browse
            protected_path_name: Optional protected path name
            interactive: Whether to show interactive browsing
            
        Returns:
            Dict containing browsing results
        """
        self.logger.info(f"Browsing snapshot: {snapshot_name}")
        
        # Get snapshot file listing
        listing = self.list_snapshot_files(snapshot_name, protected_path_name)
        
        if listing['status'] != 'success':
            return listing
        
        # Display snapshot information
        self.logger.info(f"📸 Snapshot: {snapshot_name}")
        self.logger.info(f"📁 Path: {listing['snapshot_path']}")
        self.logger.info(f"📅 Created: {listing['snapshot_created']}")
        self.logger.info(f"📂 Snapshot Directory: {listing['snapshot_dir']}")
        
        # Display files
        if listing['files']:
            self.logger.info(f"\n📄 Files ({listing['total_files']}):")
            for file_info in listing['files']:
                size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] else 0
                self.logger.info(f"  📄 {file_info['name']} ({size_mb:.1f} MB)")
        
        # Display directories
        if listing['directories']:
            self.logger.info(f"\n📁 Directories ({listing['total_directories']}):")
            for dir_info in listing['directories']:
                self.logger.info(f"  📁 {dir_info['name']}/")
        
        if not listing['files'] and not listing['directories']:
            self.logger.info("📭 Snapshot appears to be empty")
        
        return listing
    
    def list_snapshot_directory(self, view_path: str) -> Dict[str, Any]:
        """
        List the contents of the .snapshot directory for a given view path.
        
        Args:
            view_path: The view path to check for .snapshot directory
            
        Returns:
            Dict containing directory listing information
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Listing .snapshot directory for view: {view_path}")
        
        try:
            # Construct .snapshot directory path
            snapshot_dir = f"{view_path}/.snapshot"
            
            # Use S3 to list .snapshot directory contents
            files_info = self._list_s3_directory_contents(
                snapshot_dir, 
                path_prefix="",
                max_depth=1  # Only list top level
            )
            
            self.logger.info(f"📂 .snapshot directory: {snapshot_dir}")
            self.logger.info(f"📄 Found {files_info['total_files']} files")
            self.logger.info(f"📁 Found {files_info['total_directories']} directories")
            
            # Display files
            if files_info['files']:
                self.logger.info(f"\n📄 Files:")
                for file_info in files_info['files']:
                    size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] else 0
                    self.logger.info(f"  📄 {file_info['name']} ({size_mb:.1f} MB)")
            
            # Display directories (these are the snapshots)
            if files_info['directories']:
                self.logger.info(f"\n📁 Snapshots:")
                for dir_info in files_info['directories']:
                    self.logger.info(f"  📁 {dir_info['name']}/")
            
            if not files_info['files'] and not files_info['directories']:
                self.logger.info("📭 .snapshot directory appears to be empty")
            
            return {
                'view_path': view_path,
                'snapshot_dir': snapshot_dir,
                'files': files_info['files'],
                'directories': files_info['directories'],
                'total_files': files_info['total_files'],
                'total_directories': files_info['total_directories'],
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list .snapshot directory: {e}")
            return {
                'view_path': view_path,
                'status': 'failed',
                'error': str(e)
            }
    
    def validate_restoration(self, snapshot_name: str, view_path: str) -> Dict[str, Any]:
        """
        Validate that a restoration can be performed.
        
        Args:
            snapshot_name: Name of the snapshot to restore
            view_path: Path of the view to restore
            
        Returns:
            Dict containing validation results
        """
        self.logger.info(f"Validating restoration: {snapshot_name} -> {view_path}")
        
        validation_result = {
            'snapshot_name': snapshot_name,
            'view_path': view_path,
            'valid': False,
            'issues': []
        }
        
        try:
            # Check if protected path exists
            protected_path_id = self.get_protected_path_id(view_path)
            if not protected_path_id:
                validation_result['issues'].append(f"No protected path found for view: {view_path}")
            else:
                validation_result['protected_path_id'] = protected_path_id
            
            # Check if snapshot exists
            snapshot_id = self.get_snapshot_id(snapshot_name, view_path)
            if not snapshot_id:
                validation_result['issues'].append(f"No snapshot found with name: {snapshot_name}")
            else:
                validation_result['snapshot_id'] = snapshot_id
            
            # If no issues, restoration is valid
            if not validation_result['issues']:
                validation_result['valid'] = True
                self.logger.info(f"✅ Restoration validation passed")
            else:
                self.logger.warning(f"⚠️  Restoration validation failed: {validation_result['issues']}")
            
            return validation_result
            
        except Exception as e:
            validation_result['issues'].append(f"Validation error: {str(e)}")
            self.logger.error(f"❌ Validation failed: {e}")
            return validation_result


def main():
    """Test the snapshot restore manager."""
    print("Testing Snapshot Restore Manager...")
    
    try:
        config = Lab4Config()
        manager = SnapshotRestoreManager(config)
        
        print("✅ Snapshot restore manager initialized")
        
        # Test listing snapshots
        try:
            snapshots = manager.list_available_snapshots()
            print(f"✅ Found {len(snapshots)} available snapshots")
        except Exception as e:
            print(f"⚠️  Could not list snapshots (expected if no VAST connection): {str(e)}")
        
        # Test validation (dry run)
        try:
            validation = manager.validate_restoration("test-snapshot", "/test/path")
            print(f"✅ Validation test completed: {validation['valid']}")
        except Exception as e:
            print(f"⚠️  Could not test validation: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error testing snapshot restore manager: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

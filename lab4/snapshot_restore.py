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
            # Build query parameters - use name_contains for efficient filtering
            params = {'name__contains': snapshot_name}
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
            
            self.logger.info(f"Querying snapshots with name containing: {snapshot_name}")
            snapshots = self.vast_client.snapshots.get(**params)
            
            self.logger.info(f"Found {len(snapshots)} snapshots matching name filter")
            
            # Find exact match first
            for snapshot in snapshots:
                if snapshot.get('name') == snapshot_name:
                    snapshot_id = snapshot.get('id')
                    self.logger.info(f"✅ Found exact match: {snapshot_name} (ID: {snapshot_id})")
                    return snapshot_id
            
            # If no exact match, return the first partial match
            if snapshots:
                snapshot = snapshots[0]
                snapshot_id = snapshot.get('id')
                snapshot_full_name = snapshot.get('name', 'Unknown')
                self.logger.info(f"✅ Found partial match: {snapshot_full_name} (ID: {snapshot_id})")
                return snapshot_id
            
            self.logger.warning(f"⚠️  No snapshot found with name containing: {snapshot_name}")
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
            
            # Step 2: Create backup snapshot before restore (if not dry run)
            backup_snapshot_id = None
            if not dry_run:
                self.logger.info(f"Step 1: Creating backup snapshot before restore...")
                backup_snapshot_name = f"pre-restore-{snapshot_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                try:
                    # Create backup snapshot using the snapshot manager
                    from snapshot_manager import SnapshotManager
                    snapshot_manager = SnapshotManager(self.config)
                    backup_result = snapshot_manager.create_snapshot(
                        name=backup_snapshot_name,
                        view_path=f"/cosmos/lab4-{protected_path_name}",
                        dry_run=False
                    )
                    
                    if backup_result and 'id' in backup_result:
                        backup_snapshot_id = backup_result['id']
                        self.logger.info(f"✅ Backup snapshot created: {backup_snapshot_name} (ID: {backup_snapshot_id})")
                    else:
                        self.logger.warning(f"⚠️ Backup snapshot creation may have failed: {backup_result}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to create backup snapshot: {e}")
                    self.logger.info("Proceeding with restore without backup...")
            
            # Step 3: Get snapshot ID for restore
            snapshot_id = self.get_snapshot_id(snapshot_name)
            if not snapshot_id:
                raise Exception(f"No snapshot found with name: {snapshot_name}")
            
            if dry_run:
                self.logger.info(f"Would restore protected path '{protected_path_name}' from snapshot '{snapshot_name}'")
                self.logger.info(f"Protected path ID: {protected_path_id}")
                self.logger.info(f"Snapshot ID: {snapshot_id}")
                if backup_snapshot_id:
                    self.logger.info(f"Would create backup snapshot: pre-restore-{snapshot_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
                return {
                    'snapshot_name': snapshot_name,
                    'snapshot_id': snapshot_id,
                    'protected_path_name': protected_path_name,
                    'protected_path_id': protected_path_id,
                    'backup_snapshot_id': backup_snapshot_id,
                    'dry_run': True,
                    'status': 'preview'
                }
            
            # Step 4: Create clone from snapshot (POST /protectedpaths/{id}/restore)
            self.logger.info(f"Step 2: Creating clone from snapshot...")
            
            # Generate a shorter restore name to fit within 64 character limit
            timestamp = datetime.now().strftime('%m%d-%H%M')
            # Truncate snapshot name if needed to keep total under 64 chars
            max_snapshot_len = 64 - len(f"restore-{timestamp}") - 1  # -1 for dash
            short_snapshot_name = snapshot_name[:max_snapshot_len] if len(snapshot_name) > max_snapshot_len else snapshot_name
            
            restore_payload = {
                "name": f"restore-{short_snapshot_name}-{timestamp}",
                "loanee_snapshot_id": snapshot_id
            }
            
            self.logger.debug(f"Restore payload: {json.dumps(restore_payload, indent=2)}")
            
            restore_result = self.vast_client.protectedpaths[protected_path_id].restore.post(**restore_payload)
            self.logger.info(f"✅ Step 2 completed: Clone created from snapshot")
            
            # Step 5: Wait for clone to be ready, then commit
            self.logger.info(f"Step 3: Waiting for clone to be ready...")
            self._wait_for_clone_ready(protected_path_id, max_wait_seconds=60)
            
            self.logger.info(f"Step 4: Committing restored path...")
            commit_result = self.vast_client.protectedpaths[protected_path_id].commit.patch()
            self.logger.info(f"✅ Step 4 completed: Restored path committed")
            
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
            # Get snapshot ID to verify it exists
            snapshot_id = self.get_snapshot_id(snapshot_name)
            if not snapshot_id:
                raise Exception(f"No snapshot found with name: {snapshot_name}")
            
            # Try to get snapshot details, but fall back to S3 if it fails
            snapshot_path = None
            snapshot_created = 'Unknown'
            
            try:
                snapshot = self.vast_client.snapshots.get(id=snapshot_id)
                if isinstance(snapshot, dict):
                    snapshot_path = snapshot.get('path', '')
                    snapshot_created = snapshot.get('created', 'Unknown')
                    self.logger.info(f"📸 Snapshot details from VAST API:")
                    self.logger.info(f"   Path: {snapshot_path}")
                    self.logger.info(f"   Created: {snapshot_created}")
                    self.logger.info(f"   Full snapshot data: {json.dumps(snapshot, indent=2, default=str)}")
                else:
                    self.logger.warning(f"Unexpected snapshot response type: {type(snapshot)}")
                    snapshot_path = None
            except Exception as e:
                self.logger.warning(f"Could not get snapshot details from VAST API: {e}")
                self.logger.info("Falling back to S3-based snapshot browsing")
                snapshot_path = None
            
            # If we couldn't get the path from VAST API, try to find it from the snapshot name
            if not snapshot_path:
                # Try to extract path from snapshot name patterns
                if 'raw-6h-policy' in snapshot_name:
                    snapshot_path = '/cosmos/lab4-raw'
                elif 'processed-daily-policy' in snapshot_name:
                    snapshot_path = '/cosmos/lab4-processed'
                elif 'analysis-weekly-policy' in snapshot_name:
                    # Check if there's a .tmp version (from previous restore)
                    snapshot_path = '/cosmos/lab4-analysis.tmp'
                elif 'test-snapshot' in snapshot_name:
                    snapshot_path = '/cosmos/lab4-test-snapshot'
                else:
                    # Default fallback
                    snapshot_path = '/cosmos/lab4-raw'
                
                self.logger.info(f"Using inferred snapshot path: {snapshot_path}")
            
            # Get the bucket name for the snapshot path
            bucket_name = self._get_bucket_name_for_view(snapshot_path)
            if not bucket_name:
                raise Exception(f"No bucket found for snapshot path: {snapshot_path}")
            
            # Construct snapshot directory path using bucket name
            snapshot_dir = f"{bucket_name}/.snapshot/{snapshot_name}"
            
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
            endpoint_url = self.config.get('s3.endpoint_url')
            region_name = self.config.get('s3.region', 'us-east-1')
            path_style = self.config.get('s3.compatibility.path_style_addressing', True)
            ssl_verify = self.config.get('s3.ssl_verify', self.config.get('s3.verify_ssl', True))
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
            # Get the bucket name for this view path
            bucket_name = self._get_bucket_name_for_view(view_path)
            if not bucket_name:
                raise Exception(f"No bucket found for view path: {view_path}")
            
            # Construct .snapshot directory path using bucket name
            snapshot_dir = f"{bucket_name}/.snapshot"
            
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
    
    def _get_bucket_name_for_view(self, view_path: str) -> Optional[str]:
        """
        Get the bucket name for a given view path.
        
        Args:
            view_path: The view path to get bucket name for
            
        Returns:
            Bucket name if found, None otherwise
        """
        # Get Lab 4 views configuration
        lab_config = self.config.get_lab_config()
        views_config = lab_config.get('views', {})
        
        # Look for exact match first
        for view_name, view_config in views_config.items():
            if view_config.get('path') == view_path:
                bucket_name = view_config.get('bucket_name')
                if bucket_name:
                    self.logger.info(f"Found bucket name for view {view_path}: {bucket_name}")
                    return bucket_name
        
        # If no exact match, try to derive bucket name from path
        # Convert view path to bucket name (remove leading slash, replace slashes with dashes)
        derived_bucket = view_path.lstrip('/').replace('/', '-')
        self.logger.info(f"Using derived bucket name for view {view_path}: {derived_bucket}")
        return derived_bucket
    
    def _wait_for_clone_ready(self, protected_path_id: int, max_wait_seconds: int = 60) -> bool:
        """
        Wait for a snapshot clone to be ready for commit.
        
        Args:
            protected_path_id: ID of the protected path
            max_wait_seconds: Maximum time to wait in seconds
            
        Returns:
            True if clone is ready, False if timeout
        """
        import time
        
        self.logger.info(f"Waiting for clone to be ready (max {max_wait_seconds}s)...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check protected path status
                protected_path = self.vast_client.protectedpaths.get(id=protected_path_id)
                
                # Debug: Log the full response to understand the structure
                self.logger.info(f"🔍 Full protected path response: {json.dumps(protected_path, indent=2, default=str)}")
                
                if isinstance(protected_path, dict):
                    # Check the main state field
                    state = protected_path.get('state', 'unknown')
                    self.logger.info(f"📊 Protected path state: '{state}'")
                    
                    # Check the nested status object
                    status_obj = protected_path.get('status', {})
                    self.logger.info(f"📊 Status object type: {type(status_obj)}")
                    self.logger.info(f"📊 Status object content: {status_obj}")
                    
                    if isinstance(status_obj, dict):
                        # Look for status indicators in the nested object
                        status_value = status_obj.get('state', status_obj.get('status', 'unknown'))
                        self.logger.info(f"📊 Status value from nested object: '{status_value}'")
                    else:
                        status_value = str(status_obj)
                        self.logger.info(f"📊 Status value (converted to string): '{status_value}'")
                    
                    # Check all relevant fields for debugging
                    relevant_fields = ['state', 'status', 'health', 'external_state', 'restore_task', 'loanee_snapshot']
                    for field in relevant_fields:
                        value = protected_path.get(field, 'NOT_FOUND')
                        self.logger.info(f"📊 Field '{field}': {value}")
                    
                    # Check if clone is ready based on state and status
                    ready_indicators = ['ready', 'completed', 'active', 'success', 'available', 'idle']
                    self.logger.info(f"📊 Checking if ready - state: '{state}' in {ready_indicators} = {state in ready_indicators}")
                    self.logger.info(f"📊 Checking if ready - status: '{status_value}' in {ready_indicators} = {status_value in ready_indicators}")
                    
                    if state in ready_indicators or status_value in ready_indicators:
                        self.logger.info(f"✅ Clone is ready for commit (state: {state}, status: {status_value})")
                        return True
                    
                    # Check if there's a restore task that might indicate progress
                    restore_task = protected_path.get('restore_task')
                    if restore_task:
                        self.logger.info(f"📊 Restore task ID: {restore_task}")
                    
                    self.logger.info(f"⏳ Clone not ready yet (state: {state}, status: {status_value}), waiting...")
                
                # Wait 2 seconds before checking again
                time.sleep(2)
                
            except Exception as e:
                self.logger.debug(f"Error checking clone status: {e}")
                time.sleep(2)
        
        self.logger.warning(f"⚠️ Clone may not be ready after {max_wait_seconds}s, proceeding anyway")
        return False
    
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

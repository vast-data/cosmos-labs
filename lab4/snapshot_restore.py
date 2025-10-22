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
    
    def get_protected_path_id(self, view_path: str) -> Optional[int]:
        """
        Get the protected path ID for a given view path.
        
        Args:
            view_path: The view path to find the protected path for
            
        Returns:
            Protected path ID if found, None otherwise
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Looking up protected path ID for view: {view_path}")
        
        try:
            protected_paths = self.vast_client.protectedpaths.get()
            
            # Find protected path that matches the view path
            for path in protected_paths:
                if path.get('source_dir') == view_path:
                    path_id = path.get('id')
                    path_name = path.get('name', 'Unknown')
                    self.logger.info(f"✅ Found protected path: {path_name} (ID: {path_id}) for view: {view_path}")
                    return path_id
            
            self.logger.warning(f"⚠️  No protected path found for view: {view_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to lookup protected path for view {view_path}: {e}")
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
                params['path'] = view_path
            
            snapshots = self.vast_client.snapshots.get(**params)
            
            # Find snapshot by name (exact match)
            for snapshot in snapshots:
                if snapshot.get('name') == snapshot_name:
                    snapshot_id = snapshot.get('id')
                    self.logger.info(f"✅ Found snapshot: {snapshot_name} (ID: {snapshot_id})")
                    return snapshot_id
            
            # If no exact match, try partial match
            for snapshot in snapshots:
                if snapshot_name in snapshot.get('name', ''):
                    snapshot_id = snapshot.get('id')
                    snapshot_full_name = snapshot.get('name', 'Unknown')
                    self.logger.info(f"✅ Found partial match: {snapshot_full_name} (ID: {snapshot_id})")
                    return snapshot_id
            
            self.logger.warning(f"⚠️  No snapshot found with name: {snapshot_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to lookup snapshot {snapshot_name}: {e}")
            raise
    
    def restore_from_snapshot(self, 
                            snapshot_name: str, 
                            view_path: str,
                            dry_run: bool = True) -> Dict[str, Any]:
        """
        Restore a view from a snapshot using VAST's protected path restore API.
        
        Args:
            snapshot_name: Name of the snapshot to restore from
            view_path: Path of the view to restore
            dry_run: If True, only show what would be done
            
        Returns:
            Dict containing restoration result information
        """
        self.logger.info(f"Starting snapshot restoration process")
        self.logger.info(f"Snapshot: {snapshot_name}")
        self.logger.info(f"View: {view_path}")
        self.logger.info(f"Dry run: {dry_run}")
        
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        try:
            # Step 1: Get protected path ID
            protected_path_id = self.get_protected_path_id(view_path)
            if not protected_path_id:
                raise Exception(f"No protected path found for view: {view_path}")
            
            # Step 2: Get snapshot ID
            snapshot_id = self.get_snapshot_id(snapshot_name, view_path)
            if not snapshot_id:
                raise Exception(f"No snapshot found with name: {snapshot_name}")
            
            if dry_run:
                self.logger.info(f"Would restore view '{view_path}' from snapshot '{snapshot_name}'")
                self.logger.info(f"Protected path ID: {protected_path_id}")
                self.logger.info(f"Snapshot ID: {snapshot_id}")
                return {
                    'snapshot_name': snapshot_name,
                    'snapshot_id': snapshot_id,
                    'view_path': view_path,
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
                'view_path': view_path,
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
                'view_path': view_path,
                'dry_run': dry_run,
                'status': 'failed',
                'error': str(e)
            }
    
    def list_available_snapshots(self, view_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available snapshots for restoration.
        
        Args:
            view_path: Optional specific view path to filter snapshots
            
        Returns:
            List of available snapshots
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Listing available snapshots")
        if view_path:
            self.logger.info(f"View filter: {view_path}")
        
        try:
            # Build query parameters
            params = {}
            if view_path:
                params['path'] = view_path
            
            snapshots = self.vast_client.snapshots.get(**params)
            
            self.logger.info(f"Found {len(snapshots)} available snapshots")
            
            # Display snapshots
            for i, snapshot in enumerate(snapshots, 1):
                snapshot_name = snapshot.get('name', 'Unknown')
                snapshot_path = snapshot.get('path', 'Unknown')
                created = snapshot.get('created', 'Unknown')
                state = snapshot.get('state', 'Unknown')
                self.logger.info(f"  {i}. {snapshot_name} -> {snapshot_path} (State: {state}, Created: {created})")
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list snapshots: {e}")
            raise
    
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

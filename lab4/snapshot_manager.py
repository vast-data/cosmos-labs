#!/usr/bin/env python3
"""
VAST Snapshot Manager

This module provides functionality to create, list, and manage VAST snapshots
for automated snapshot creation and management.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Lab 4 configuration
from lab4_config import Lab4Config
from vastpy import VASTClient


class SnapshotManager:
    """
    Manager for VAST snapshots.
    
    Provides methods to create, list, and manage snapshots
    using the VAST Management System API.
    """
    
    def __init__(self, config: Optional[Lab4Config] = None):
        """
        Initialize the snapshot manager.
        
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
            self.logger.info(f"✅ VAST client initialized for snapshot management")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize VAST client: {e}")
            self.vast_client = None
    
    def create_snapshot(self, 
                       name: str, 
                       path: str,
                       expiration_time: Optional[str] = None,
                       cluster_id: int = 0,
                       locked: bool = False,
                       indestructible: bool = False,
                       tenant_id: int = 0) -> Dict[str, Any]:
        """
        Create a new snapshot.
        
        Args:
            name: Name of the snapshot
            path: Path to snapshot
            expiration_time: Optional expiration time (ISO format)
            cluster_id: Cluster ID (default: 0)
            locked: Whether the snapshot is locked
            indestructible: Whether the snapshot is indestructible
            tenant_id: Tenant ID (default: 0)
            
        Returns:
            Dict containing the created snapshot information
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        payload = {
            "name": name,
            "path": path,
            "locked": locked,
            "indestructible": indestructible,
            "tenant_id": tenant_id
        }
        
        # Add optional parameters
        if expiration_time:
            payload["expiration_time"] = expiration_time
        
        self.logger.info(f"Creating snapshot: {name} for path: {path}")
        self.logger.debug(f"Snapshot payload: {json.dumps(payload, indent=2)}")
        
        try:
            snapshots = self.vast_client.snapshots.post(**payload)
            # vastpy returns a dict with the snapshot data
            if isinstance(snapshots, dict):
                self.logger.info(f"✅ Successfully created snapshot: {name} (ID: {snapshots.get('id')})")
                return snapshots
            elif snapshots == 0:
                # vastpy sometimes returns 0 for successful creation
                self.logger.info(f"✅ Successfully created snapshot: {name} (vastpy returned 0)")
                return {"name": name, "id": "unknown", "status": "created"}
            else:
                raise Exception(f"Failed to create snapshot {name} - unexpected response: {snapshots}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create snapshot {name}: {str(e)}")
            raise
    
    def list_snapshots(self, 
                      page: Optional[int] = None,
                      page_size: Optional[int] = None,
                      path: Optional[str] = None,
                      name_contains: Optional[str] = None,
                      expiration_time: Optional[str] = None,
                      protection_policy_name: Optional[str] = None,
                      protection_policy_id: Optional[int] = None,
                      state: Optional[str] = None,
                      created: Optional[str] = None,
                      locked: Optional[bool] = None,
                      tenant_id: Optional[int] = None,
                      tenant_name_contains: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List snapshots with optional filtering.
        
        Args:
            page: Page number for pagination
            page_size: Number of items per page
            path: Filter by snapshot path
            name_contains: Filter by part of snapshot name
            expiration_time: Filter by expiration time
            protection_policy_name: Filter by snapshot policy name
            protection_policy_id: Filter by snapshot policy ID
            state: Filter by state
            created: Filter by creation time
            locked: Filter for locked snapshots
            tenant_id: Filter by tenant ID
            tenant_name_contains: Tenant name to filter by
            
        Returns:
            List of snapshot dictionaries
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        # Build query parameters
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size
        if path:
            params['path'] = path
        if name_contains:
            params['name__contains'] = name_contains
        if expiration_time:
            params['expiration_time'] = expiration_time
        if protection_policy_name:
            params['protection_policy__name'] = protection_policy_name
        if protection_policy_id is not None:
            params['protection_policy__id'] = protection_policy_id
        if state:
            params['state'] = state
        if created:
            params['created'] = created
        if locked is not None:
            params['locked'] = locked
        if tenant_id is not None:
            params['tenant_id'] = tenant_id
        if tenant_name_contains:
            params['tenant_name__icontains'] = tenant_name_contains
        
        self.logger.info(f"Listing snapshots with filters: {params}")
        
        try:
            snapshots = self.vast_client.snapshots.get(**params)
            self.logger.info(f"Found {len(snapshots)} snapshots")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list snapshots: {str(e)}")
            raise
    
    def get_snapshot(self, snapshot_id: int) -> Dict[str, Any]:
        """
        Get a specific snapshot by ID.
        
        Args:
            snapshot_id: ID of the snapshot
            
        Returns:
            Dict containing the snapshot information
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Getting snapshot: {snapshot_id}")
        
        try:
            snapshots = self.vast_client.snapshots.get(id=snapshot_id)
            # vastpy returns a dict with the snapshot data
            if isinstance(snapshots, dict):
                self.logger.info(f"✅ Retrieved snapshot: {snapshots.get('name')}")
                return snapshots
            else:
                raise Exception(f"Snapshot with ID {snapshot_id} not found")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get snapshot {snapshot_id}: {str(e)}")
            raise
    
    def delete_snapshot(self, snapshot_id: int) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Deleting snapshot: {snapshot_id}")
        
        try:
            # Use vastpy DELETE method - the correct way to call it
            result = self.vast_client.snapshots[snapshot_id].delete()
            self.logger.info(f"✅ Successfully deleted snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete snapshot {snapshot_id}: {str(e)}")
            # Provide helpful guidance for manual cleanup
            self.logger.info("💡 Manual cleanup may be required:")
            self.logger.info("   1. Check VAST Web UI for snapshots")
            self.logger.info("   2. Disable or remove snapshots manually if needed")
            self.logger.info("   3. Some snapshots may be protected from deletion")
            # Don't raise the exception, just return False to allow cleanup to continue
            return False
    
    def create_named_snapshot(self, 
                             name: str, 
                             view_path: str,
                             milestone: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None,
                             locked: bool = False,
                             indestructible: bool = False) -> Dict[str, Any]:
        """
        Create a named snapshot with descriptive metadata.
        
        Args:
            name: Base name for the snapshot
            view_path: Path of the view to snapshot
            milestone: Optional milestone description
            metadata: Optional metadata dictionary
            locked: Whether the snapshot is locked
            indestructible: Whether the snapshot is indestructible
            
        Returns:
            Created snapshot information
        """
        # Generate snapshot name using config naming rules
        snapshot_name = self.config.generate_snapshot_name(name, milestone)
        
        self.logger.info(f"Creating named snapshot: {snapshot_name}")
        self.logger.info(f"View: {view_path}")
        if milestone:
            self.logger.info(f"Milestone: {milestone}")
        if metadata:
            self.logger.info(f"Metadata: {metadata}")
        
        # Get tenant ID from views
        tenant_id = self._get_tenant_id_from_views()
        
        return self.create_snapshot(
            name=snapshot_name,
            path=view_path,
            locked=locked,
            indestructible=indestructible,
            tenant_id=tenant_id
        )
    
    def list_snapshots_for_view(self, view_path: str) -> List[Dict[str, Any]]:
        """
        List all snapshots for a specific view.
        
        Args:
            view_path: Path of the view to list snapshots for
            
        Returns:
            List of snapshots for the view
        """
        self.logger.info(f"Listing snapshots for view: {view_path}")
        
        try:
            snapshots = self.list_snapshots(path=view_path)
            self.logger.info(f"Found {len(snapshots)} snapshots for view {view_path}")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Failed to list snapshots for view {view_path}: {e}")
            return []
    
    def search_snapshots(self, 
                        search_term: str,
                        view_path: Optional[str] = None,
                        date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Search snapshots by name, metadata, or date range.
        
        Args:
            search_term: Search term for snapshot names
            view_path: Optional specific view path
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            List of matching snapshots
        """
        self.logger.info(f"Searching snapshots with term: {search_term}")
        if view_path:
            self.logger.info(f"View filter: {view_path}")
        if date_range:
            self.logger.info(f"Date range: {date_range[0]} to {date_range[1]}")
        
        try:
            snapshots = self.list_snapshots(
                path=view_path,
                name_contains=search_term
            )
            
            # Filter by date range if provided
            if date_range:
                start_date, end_date = date_range
                filtered_snapshots = []
                for snapshot in snapshots:
                    created_time = snapshot.get('created')
                    if created_time:
                        # Parse and compare dates
                        snapshot_date = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        if start_date <= snapshot_date <= end_date:
                            filtered_snapshots.append(snapshot)
                snapshots = filtered_snapshots
            
            self.logger.info(f"Found {len(snapshots)} matching snapshots")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Failed to search snapshots: {e}")
            return []
    
    def _get_tenant_id_from_views(self) -> int:
        """
        Get the tenant ID from existing views.
        
        Returns:
            Tenant ID (defaults to 1 if not found)
        """
        # Import here to avoid circular imports
        from protection_policies import ProtectionPoliciesManager
        temp_manager = ProtectionPoliciesManager()
        return temp_manager.get_tenant_id_from_views()
    
    def cleanup_old_snapshots(self, 
                             view_path: Optional[str] = None,
                             older_than_days: int = 30,
                             dry_run: bool = True) -> List[str]:
        """
        Clean up old snapshots.
        
        Args:
            view_path: Optional specific view path to clean up
            older_than_days: Delete snapshots older than this many days
            dry_run: If True, only show what would be deleted
            
        Returns:
            List of deleted snapshot names
        """
        self.logger.info(f"Cleaning up snapshots older than {older_than_days} days (dry_run={dry_run})")
        
        try:
            snapshots = self.list_snapshots(path=view_path)
        except Exception as e:
            self.logger.error(f"Failed to list snapshots: {e}")
            return []
        
        cutoff_date = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        deleted_snapshots = []
        
        for snapshot in snapshots:
            created_time = snapshot.get('created')
            if created_time:
                # Parse creation time
                snapshot_date = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                if snapshot_date.timestamp() < cutoff_date:
                    snapshot_name = snapshot.get('name', 'unknown')
                    if dry_run:
                        self.logger.info(f"Would delete old snapshot: {snapshot_name}")
                        deleted_snapshots.append(snapshot_name)
                    else:
                        try:
                            if self.delete_snapshot(snapshot['id']):
                                self.logger.info(f"✅ Deleted old snapshot: {snapshot_name}")
                                deleted_snapshots.append(snapshot_name)
                        except Exception as e:
                            self.logger.error(f"❌ Failed to delete snapshot {snapshot_name}: {e}")
        
        self.logger.info(f"Deleted {len(deleted_snapshots)} old snapshots")
        return deleted_snapshots


def main():
    """Test the snapshot manager."""
    print("Testing Snapshot Manager...")
    
    try:
        config = Lab4Config()
        manager = SnapshotManager(config)
        
        print("✅ Snapshot manager initialized")
        
        # Test listing snapshots
        try:
            snapshots = manager.list_snapshots()
            print(f"✅ Found {len(snapshots)} existing snapshots")
        except Exception as e:
            print(f"⚠️  Could not list snapshots (expected if no VAST connection): {str(e)}")
        
        # Test dry run cleanup
        try:
            deleted_snapshots = manager.cleanup_old_snapshots(dry_run=True)
            print(f"✅ Dry run would delete {len(deleted_snapshots)} old snapshots")
        except Exception as e:
            print(f"⚠️  Could not test cleanup: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error testing snapshot manager: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

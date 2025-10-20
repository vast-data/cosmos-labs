#!/usr/bin/env python3
"""
VAST Protection Policies Manager

This module provides functionality to create, manage, and apply VAST protection policies
for automated snapshot creation with configurable schedules and retention.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Lab 4 configuration
from lab4_config import Lab4Config
from vastpy import VASTClient


class ProtectionPoliciesManager:
    """
    Manager for VAST protection policies.
    
    Provides methods to create, list, update, and delete protection policies
    using the VAST Management System API.
    """
    
    def __init__(self, config: Optional[Lab4Config] = None):
        """
        Initialize the protection policies manager.
        
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
            self.logger.info(f"✅ VAST client initialized for protection policies")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize VAST client: {e}")
            self.vast_client = None
    
    def _parse_frames_string(self, frames_string: str) -> list:
        """
        Parse frames string into the required array format for VAST API.
        
        Args:
            frames_string: String like "every 6h start-at 2025-10-16 00:00:00 keep-local 3d"
            
        Returns:
            List of frame objects for the API
        """
        import re
        from datetime import datetime
        
        # Parse the frames string
        # Example: "every 6h start-at 2025-10-16 00:00:00 keep-local 3d"
        
        frame_obj = {}
        
        # Find "every" and extract interval
        every_match = re.search(r'every\s+(\d+[hmd])', frames_string)
        if every_match:
            frame_obj['every'] = every_match.group(1)
        
        # Find "start-at" and extract timestamp
        start_match = re.search(r'start-at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', frames_string)
        if start_match:
            # Convert to ISO format
            start_str = start_match.group(1)
            dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
            frame_obj['start-at'] = dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Find "keep-local" and extract duration
        local_match = re.search(r'keep-local\s+(\d+[hmd])', frames_string)
        if local_match:
            frame_obj['keep-local'] = local_match.group(1)
        
        # Find "keep-remote" and extract duration (default to 0s if not specified)
        remote_match = re.search(r'keep-remote\s+(\d+[hmd])', frames_string)
        if remote_match:
            frame_obj['keep-remote'] = remote_match.group(1)
        else:
            frame_obj['keep-remote'] = '0s'
        
        return [frame_obj]
    
    def create_protection_policy(self, 
                               name: str, 
                               frames: str, 
                               prefix: str = "",
                               clone_type: str = "LOCAL",
                               indestructible: bool = False,
                               big_catalog: bool = False,
                               tenant_id: Optional[int] = None,
                               remote_tenant_guid: Optional[str] = None,
                               target_object_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new protection policy.
        
        Args:
            name: Name of the protection policy
            frames: Schedule string (e.g., "every 24h keep-local 7d")
            prefix: Prefix for snapshot names
            clone_type: Type of protection (LOCAL, NATIVE_REPLICATION, CLOUD_REPLICATION)
            indestructible: Whether to protect from deletion
            big_catalog: Whether this is for VAST Catalog
            tenant_id: Tenant ID
            remote_tenant_guid: Remote tenant GUID
            target_object_id: ID of remote peer for replication
            
        Returns:
            Dict containing the created policy information
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        # Parse frames string into the required array format
        frames_array = self._parse_frames_string(frames)
        
        payload = {
            "name": name,
            "frames": frames_array,
            "prefix": prefix,
            "clone_type": clone_type,
            "indestructible": indestructible,
            "big_catalog": big_catalog
        }
        
        # Add optional parameters
        if tenant_id is not None:
            payload["tenant_id"] = tenant_id
        if remote_tenant_guid is not None:
            payload["remote_tenant_guid"] = remote_tenant_guid
        if target_object_id is not None:
            payload["target_object_id"] = target_object_id
        
        self.logger.info(f"Creating protection policy: {name}")
        self.logger.debug(f"Frames: {frames}")
        self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            policies = self.vast_client.protectionpolicies.post(**payload)
            # vastpy returns a list, so get the first (and should be only) item
            if policies and len(policies) > 0:
                policy_data = policies[0]
                self.logger.info(f"✅ Successfully created protection policy: {name} (ID: {policy_data.get('id')})")
                return policy_data
            else:
                raise Exception(f"Failed to create protection policy {name} - no data returned")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create protection policy {name}: {str(e)}")
            raise
    
    def list_replication_policies(self, name_filter: str = None) -> List[Dict[str, Any]]:
        """
        List all replication policies.
        
        Args:
            name_filter: Optional filter by replication policy name
            
        Returns:
            List of replication policy dictionaries
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Listing replication policies{' (filtered by name: ' + name_filter + ')' if name_filter else ''}")
        
        try:
            params = {}
            if name_filter:
                params['name'] = name_filter
            
            policies = self.vast_client.replicationpolicies.get(**params)
            self.logger.info(f"Found {len(policies)} replication policies")
            return policies
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list replication policies: {str(e)}")
            raise

    def list_protection_policies(self, name_filter: str = None) -> List[Dict[str, Any]]:
        """
        List all protection policies.
        
        Args:
            name_filter: Optional filter by protection policy name
            
        Returns:
            List of protection policy dictionaries
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Listing protection policies{' (filtered by name: ' + name_filter + ')' if name_filter else ''}")
        
        try:
            params = {}
            if name_filter:
                params['name'] = name_filter
            
            policies = self.vast_client.protectionpolicies.get(**params)
            self.logger.info(f"Found {len(policies)} protection policies")
            return policies
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list protection policies: {str(e)}")
            raise
    
    def get_policy_by_name(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a protection policy by name using the API.
        
        Args:
            policy_name: Name of the protection policy to find
            
        Returns:
            Policy dictionary if found, None otherwise
        """
        try:
            policies = self.list_protection_policies(name_filter=policy_name)
            
            # Find exact match
            for policy in policies:
                if policy.get('name') == policy_name:
                    self.logger.info(f"Found policy '{policy_name}' with ID: {policy.get('id')}")
                    return policy
            
            self.logger.warning(f"Policy '{policy_name}' not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get policy by name '{policy_name}': {e}")
            return None
    
    def get_replication_policy_by_name(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a replication policy by name using the API.
        
        Args:
            policy_name: Name of the replication policy to find
            
        Returns:
            Policy dictionary if found, None otherwise
        """
        try:
            policies = self.list_replication_policies(name_filter=policy_name)
            
            # Find exact match
            for policy in policies:
                if policy.get('name') == policy_name:
                    self.logger.info(f"Found replication policy '{policy_name}' with ID: {policy.get('id')}")
                    return policy
            
            self.logger.warning(f"Replication policy '{policy_name}' not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get replication policy by name '{policy_name}': {e}")
            return None
    
    def get_tenant_id_from_views(self) -> int:
        """
        Get the tenant ID from existing views.
        
        Returns:
            Tenant ID (defaults to 1 if not found)
        """
        if not self.vast_client:
            self.logger.warning("VAST client not initialized, using default tenant ID: 1")
            return 1
        
        try:
            views = self.vast_client.views.get()
            if views and len(views) > 0:
                # Get tenant_id from the first view
                tenant_id = views[0].get('tenant_id', 1)
                self.logger.info(f"Using tenant ID: {tenant_id} from views")
                return tenant_id
            else:
                self.logger.warning("No views found, using default tenant ID: 1")
                return 1
                
        except Exception as e:
            self.logger.warning(f"Could not get tenant ID from views: {e}, using default: 1")
            return 1
    
    def get_protection_policy(self, policy_id: int) -> Dict[str, Any]:
        """
        Get a specific protection policy by ID.
        
        Args:
            policy_id: ID of the protection policy
            
        Returns:
            Dict containing the policy information
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Getting protection policy: {policy_id}")
        
        try:
            policies = self.vast_client.protectionpolicies.get(id=policy_id)
            # vastpy returns a list, so get the first (and should be only) item
            if policies and len(policies) > 0:
                policy = policies[0]
                self.logger.info(f"✅ Retrieved protection policy: {policy.get('name')}")
                return policy
            else:
                raise Exception(f"Policy with ID {policy_id} not found")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get protection policy {policy_id}: {str(e)}")
            raise
    
    def update_protection_policy(self, 
                                policy_id: int, 
                                **kwargs) -> Dict[str, Any]:
        """
        Update an existing protection policy.
        
        Args:
            policy_id: ID of the protection policy to update
            **kwargs: Fields to update
            
        Returns:
            Dict containing the updated policy information
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Updating protection policy: {policy_id}")
        self.logger.debug(f"Update fields: {kwargs}")
        
        try:
            policies = self.vast_client.protectionpolicies.patch(id=policy_id, **kwargs)
            # vastpy returns a list, so get the first (and should be only) item
            if policies and len(policies) > 0:
                policy = policies[0]
                self.logger.info(f"✅ Successfully updated protection policy: {policy.get('name')}")
                return policy
            else:
                raise Exception(f"Policy with ID {policy_id} not found after update")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update protection policy {policy_id}: {str(e)}")
            raise
    
    def delete_protection_policy(self, policy_id: int) -> bool:
        """
        Delete a protection policy.
        
        Args:
            policy_id: ID of the protection policy to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            Exception: If API request fails
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Deleting protection policy: {policy_id}")
        
        try:
            # Use vastpy DELETE method - the correct way to call it
            result = self.vast_client.protectionpolicies[policy_id].delete()
            self.logger.info(f"✅ Successfully deleted protection policy: {policy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete protection policy {policy_id}: {str(e)}")
            # Provide helpful guidance for manual cleanup
            self.logger.info("💡 Manual cleanup may be required:")
            self.logger.info("   1. Check VAST Web UI for protection policies")
            self.logger.info("   2. Disable or remove policies manually if needed")
            self.logger.info("   3. Some policies may be protected from deletion")
            # Don't raise the exception, just return False to allow cleanup to continue
            return False
    
    def delete_protection_policy_by_name(self, policy_name: str) -> bool:
        """
        Delete a protection policy by name.
        
        Args:
            policy_name: Name of the protection policy to delete
            
        Returns:
            True if deletion was successful, False if policy not found
            
        Raises:
            Exception: If API request fails
        """
        policy = self.get_policy_by_name(policy_name)
        if not policy:
            self.logger.warning(f"Policy '{policy_name}' not found, cannot delete")
            return False
        
        policy_id = policy['id']
        return self.delete_protection_policy(policy_id)
    
    def create_policy_from_template(self, 
                                   template_name: str, 
                                   policy_name: str,
                                   view_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a protection policy from a template.
        
        Args:
            template_name: Name of the template to use
            policy_name: Name for the new policy
            view_path: Optional view path to include in policy name
            
        Returns:
            Dict containing the created policy information
            
        Raises:
            ValueError: If template not found
            requests.RequestException: If API request fails
        """
        templates = self.config.get_policy_templates()
        
        if template_name not in templates:
            available_templates = list(templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available templates: {available_templates}")
        
        template = templates[template_name]
        
        # Generate policy name (only modify if view_path is provided)
        if view_path:
            policy_name = f"{policy_name}-{view_path.replace('/', '-').strip('-')}"
        
        # Create policy from template
        return self.create_protection_policy(
            name=policy_name,
            frames=template.get('schedule', ''),
            prefix=template.get('prefix', ''),
            clone_type=template.get('clone_type', 'LOCAL'),
            indestructible=template.get('indestructible', False),
            big_catalog=template.get('big_catalog', False)
        )
    
    def setup_default_policies(self, dry_run: bool = True) -> List[Dict[str, Any]]:
        """
        Set up default protection policies based on configuration.
        
        Args:
            dry_run: If True, only show what would be created
            
        Returns:
            List of created or would-be-created policies
            
        Raises:
            Exception: If API request fails
        """
        policies = []
        templates = self.config.get_policy_templates()
        views = self.config.get_views_config()
        
        self.logger.info(f"Setting up default protection policies (dry_run={dry_run})")
        
        # First, check existing policies to avoid duplicates and policy limit
        existing_policies = []
        if not dry_run:
            try:
                existing_policies = self.list_protection_policies()
                self.logger.info(f"Found {len(existing_policies)} existing protection policies")
            except Exception as e:
                self.logger.warning(f"Could not list existing policies: {e}")
        
        existing_names = {policy.get('name') for policy in existing_policies}
        
        # Create one policy per template (not per view)
        for template_name, template_config in templates.items():
            policy_name = f"lab4-{template_name}-policy"
            
            # Skip if policy already exists
            if policy_name in existing_names:
                self.logger.info(f"Policy already exists, skipping: {policy_name}")
                continue
            
            if dry_run:
                self.logger.info(f"Would create policy: {policy_name}")
                policies.append({
                    'name': policy_name,
                    'template': template_name,
                    'dry_run': True
                })
            else:
                try:
                    policy = self.create_policy_from_template(
                        template_name=template_name,
                        policy_name=policy_name,
                        view_path=None  # No specific view, this is a template policy
                    )
                    policies.append(policy)
                    self.logger.info(f"Created policy: {policy_name}")
                except Exception as e:
                    self.logger.error(f"Failed to create policy {policy_name}: {str(e)}")
        
        # Apply policies to views (this would be a separate step)
        if not dry_run and policies:
            self.logger.info("Policies created. Next step would be to apply them to views.")
        
        return policies
    
    def cleanup_all_lab4_policies(self, dry_run: bool = True) -> List[str]:
        """
        Clean up all lab4 policies (since we're not published yet).
        
        Args:
            dry_run: If True, only show what would be deleted
            
        Returns:
            List of deleted policy names
        """
        self.logger.info(f"Cleaning up all lab4 policies (dry_run={dry_run})")
        
        try:
            all_policies = self.list_protection_policies()
        except Exception as e:
            self.logger.error(f"Failed to list policies: {e}")
            return []
        
        # Find all lab4 policies
        lab4_policies = [policy for policy in all_policies if policy.get('name', '').startswith('lab4-')]
        
        deleted_policies = []
        failed_deletions = []
        
        for policy in lab4_policies:
            policy_name = policy.get('name')
            if dry_run:
                self.logger.info(f"Would delete policy: {policy_name}")
                deleted_policies.append(policy_name)
            else:
                try:
                    if self.delete_protection_policy(policy['id']):
                        deleted_policies.append(policy_name)
                        self.logger.info(f"✅ Deleted policy: {policy_name}")
                    else:
                        self.logger.warning(f"⚠️  Failed to delete policy: {policy_name}")
                except Exception as e:
                    self.logger.warning(f"⚠️  Could not delete policy {policy_name}: {e}")
                    failed_deletions.append(policy_name)
        
        self.logger.info(f"Deleted {len(deleted_policies)} lab4 policies")
        if failed_deletions:
            self.logger.warning(f"Could not delete {len(failed_deletions)} policies (may be in use): {failed_deletions}")
        
        return deleted_policies
    
    def cleanup_all_lab4_protected_paths(self, dry_run: bool = True) -> List[str]:
        """
        Clean up all lab4 protected paths (since we're not published yet).
        
        Args:
            dry_run: If True, only show what would be deleted
            
        Returns:
            List of deleted protected path names
        """
        self.logger.info(f"Cleaning up all lab4 protected paths (dry_run={dry_run})")
        
        try:
            protected_paths = self.list_protected_paths()
        except Exception as e:
            self.logger.error(f"Failed to list protected paths: {e}")
            return []
        
        # Find protected paths that use lab4 policies
        paths_to_delete = []
        for path in protected_paths:
            policy_id = path.get('protection_policy_id')
            if policy_id:
                # Get the policy to check its name
                try:
                    policy = self.get_protection_policy(policy_id)
                    policy_name = policy.get('name', '')
                    if policy_name.startswith('lab4-'):
                        paths_to_delete.append({
                            'id': path.get('id'),
                            'name': path.get('name'),
                            'policy_name': policy_name
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get policy {policy_id}: {e}")
        
        deleted_paths = []
        for path_info in paths_to_delete:
            if dry_run:
                self.logger.info(f"Would delete protected path: {path_info['name']} (policy: {path_info['policy_name']})")
                deleted_paths.append(path_info['name'])
            else:
                try:
                    if self.delete_protected_path(path_info['id']):
                        self.logger.info(f"✅ Deleted protected path: {path_info['name']}")
                        deleted_paths.append(path_info['name'])
                    else:
                        self.logger.warning(f"⚠️  Failed to delete protected path: {path_info['name']}")
                except Exception as e:
                    self.logger.error(f"❌ Error deleting protected path {path_info['name']}: {e}")
        
        self.logger.info(f"Deleted {len(deleted_paths)} protected paths")
        return deleted_paths
    
    def full_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Complete cleanup: protected paths -> policies (in dependency order).
        
        Args:
            dry_run: If True, only show what would be deleted
            
        Returns:
            Dict with cleanup results
        """
        self.logger.info(f"Starting full cleanup (dry_run={dry_run})")
        
        results = {
            'deleted_protected_paths': [],
            'deleted_policies': [],
            'dry_run': dry_run
        }
        
        # Step 1: Clean up protected paths first (they depend on policies)
        self.logger.info("Step 1: Cleaning up protected paths")
        deleted_paths = self.cleanup_all_lab4_protected_paths(dry_run=dry_run)
        results['deleted_protected_paths'] = deleted_paths
        
        # Step 2: Clean up policies (should work now that protected paths are gone)
        self.logger.info("Step 2: Cleaning up old policies")
        deleted_policies = self.cleanup_all_lab4_policies(dry_run=dry_run)
        results['deleted_policies'] = deleted_policies
        
        self.logger.info("✅ Full cleanup completed")
        
        # Provide summary of manual cleanup needed
        if results['deleted_protected_paths'] == [] and results['deleted_policies'] == []:
            self.logger.warning("⚠️  No resources were deleted automatically")
            self.logger.info("💡 This may be due to VAST API limitations or resource protection")
            self.logger.info("   Manual cleanup via VAST Web UI may be required")
        
        return results
    
    def create_protected_path(self, 
                             name: str, 
                             source_dir: str, 
                             policy_id: int,
                             tenant_id: int = 0,
                             enabled: bool = True,
                             target_exported_dir: str = None,
                             capabilities: str = None) -> Dict[str, Any]:
        """
        Create a protected path for a view.
        
        Args:
            name: Name for the protected path (typically view name)
            source_dir: Path on the local cluster to protect
            policy_id: ID of the protection policy to use
            tenant_id: Tenant ID (default: 0)
            enabled: Whether the protected path is enabled
            target_exported_dir: Remote replication path (optional)
            capabilities: Protection capabilities (optional)
            
        Returns:
            Dict containing the created protected path data
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        payload = {
            "name": name,
            "source_dir": source_dir,
            "protection_policy_id": policy_id,
            "enabled": enabled,
            "tenant_id": tenant_id
        }
        
        # Add optional parameters
        if target_exported_dir:
            payload["target_exported_dir"] = target_exported_dir
        if capabilities:
            payload["capabilities"] = capabilities
        
        self.logger.info(f"Creating protected path: {name} -> {source_dir}")
        self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            paths = self.vast_client.protectedpaths.post(**payload)
            # vastpy returns a list, so get the first (and should be only) item
            if paths and len(paths) > 0:
                protected_path_data = paths[0]
                self.logger.info(f"✅ Created protected path: {name} (ID: {protected_path_data.get('id')})")
                return protected_path_data
            else:
                raise Exception(f"Failed to create protected path {name} - no data returned")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create protected path {name}: {e}")
            raise
    
    def list_protected_paths(self) -> List[Dict[str, Any]]:
        """
        List all protected paths.
        
        Returns:
            List of protected path dictionaries
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info("Listing protected paths...")
        
        try:
            protected_paths = self.vast_client.protectedpaths.get()
            self.logger.info(f"Found {len(protected_paths)} protected paths")
            return protected_paths
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list protected paths: {e}")
            raise
    
    def get_protected_path(self, path_id: int) -> Dict[str, Any]:
        """
        Get a specific protected path by ID.
        
        Args:
            path_id: ID of the protected path
            
        Returns:
            Dict containing the protected path data
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Getting protected path ID: {path_id}")
        
        try:
            paths = self.vast_client.protectedpaths.get(id=path_id)
            # vastpy returns a list, so get the first (and should be only) item
            if paths and len(paths) > 0:
                protected_path_data = paths[0]
                self.logger.info(f"✅ Retrieved protected path: {protected_path_data.get('name')}")
                return protected_path_data
            else:
                raise Exception(f"Protected path with ID {path_id} not found")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get protected path {path_id}: {e}")
            raise
    
    def get_protected_path_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a protected path by name.
        
        Args:
            name: Name of the protected path
            
        Returns:
            Protected path data if found, None otherwise
        """
        try:
            protected_paths = self.list_protected_paths()
            
            # Find exact match
            for path in protected_paths:
                if path.get('name') == name:
                    self.logger.info(f"Found protected path '{name}' with ID: {path.get('id')}")
                    return path
            
            self.logger.debug(f"Protected path '{name}' not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get protected path by name '{name}': {e}")
            return None
    
    def delete_protected_path(self, path_id: int) -> bool:
        """
        Delete a protected path.
        
        Args:
            path_id: ID of the protected path to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.vast_client:
            raise Exception("VAST client not initialized")
        
        self.logger.info(f"Deleting protected path ID: {path_id}")
        
        try:
            # Use vastpy DELETE method - the correct way to call it
            result = self.vast_client.protectedpaths[path_id].delete()
            self.logger.info(f"✅ Deleted protected path ID: {path_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete protected path {path_id}: {e}")
            # Provide helpful guidance for manual cleanup
            self.logger.info("💡 Manual cleanup may be required:")
            self.logger.info("   1. Check VAST Web UI for protected paths")
            self.logger.info("   2. Disable or remove protected paths manually if needed")
            self.logger.info("   3. Some protected paths may be protected from deletion")
            # Don't raise the exception, just return False to allow cleanup to continue
            return False
    
    def setup_protected_paths_for_views(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Create protected paths for all configured views.
        
        Args:
            dry_run: If True, only show what would be created
            
        Returns:
            List of created protected path data
        """
        # Get views configuration
        views_config = self.config.get_lab_config().get('views', {})
        
        # Get tenant ID from existing views
        tenant_id = self.get_tenant_id_from_views()
        
        protected_paths = []
        
        self.logger.info(f"Setting up protected paths for views (dry_run={dry_run})")
        
        # Get existing protected paths to avoid duplicates
        existing_protected_paths = []
        if not dry_run:
            try:
                existing_protected_paths = self.list_protected_paths()
                self.logger.info(f"Found {len(existing_protected_paths)} existing protected paths")
            except Exception as e:
                self.logger.warning(f"Could not list existing protected paths: {e}")
        
        existing_names = {path.get('name') for path in existing_protected_paths}
        
        for view_name, view_config in views_config.items():
            if not isinstance(view_config, dict) or 'path' not in view_config:
                self.logger.warning(f"Skipping invalid view config: {view_name}")
                continue
            
            source_dir = view_config['path']
            
            # Check if protected path already exists
            if view_name in existing_names:
                self.logger.info(f"Protected path already exists, skipping: {view_name}")
                continue
            
            # Find matching policy for this view using exact name match
            # The policy name should match the template name, not necessarily the view name
            policy_name = f"lab4-{view_name}-policy"
            policy = self.get_policy_by_name(policy_name)
            
            if not policy:
                self.logger.warning(f"No policy found for view {view_name} (policy: {policy_name}), skipping")
                continue
            
            policy_id = int(policy['id'])  # Ensure it's an integer
            
            # Debug: Log policy details
            self.logger.debug(f"Found policy: {policy_name} (ID: {policy_id}, Type: {policy.get('type', 'unknown')})")
            self.logger.debug(f"Policy details: {json.dumps(policy, indent=2)}")
            
            if dry_run:
                self.logger.info(f"Would create protected path: {view_name} -> {source_dir} (policy: {policy_name}, ID: {policy_id}, tenant: {tenant_id})")
                protected_paths.append({
                    'name': view_name,
                    'source_dir': source_dir,
                    'policy_id': policy_id,
                    'tenant_id': tenant_id,
                    'dry_run': True
                })
            else:
                try:
                    protected_path = self.create_protected_path(
                        name=view_name,
                        source_dir=source_dir,
                        policy_id=policy_id,
                        tenant_id=tenant_id,  # Use actual tenant ID from API
                        enabled=True
                    )
                    protected_paths.append(protected_path)
                    self.logger.info(f"✅ Created protected path: {view_name}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to create protected path for {view_name}: {e}")
        
        return protected_paths
    
    def validate_policy_configuration(self, policy_data: Dict[str, Any]) -> List[str]:
        """
        Validate protection policy configuration.
        
        Args:
            policy_data: Policy configuration to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        required_fields = ['name', 'frames']
        for field in required_fields:
            if field not in policy_data or not policy_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate clone_type
        valid_clone_types = ['LOCAL', 'NATIVE_REPLICATION', 'CLOUD_REPLICATION']
        if 'clone_type' in policy_data and policy_data['clone_type'] not in valid_clone_types:
            errors.append(f"Invalid clone_type: {policy_data['clone_type']}. Must be one of: {valid_clone_types}")
        
        # Validate frames format (basic validation)
        if 'frames' in policy_data:
            frames = policy_data['frames']
            if not isinstance(frames, str) or len(frames.strip()) == 0:
                errors.append("Frames must be a non-empty string")
        
        return errors
    
    def policy_exists(self, name: str) -> bool:
        """
        Check if a protection policy exists by name.
        
        Args:
            name: Name of the protection policy
            
        Returns:
            True if policy exists, False otherwise
            
        Raises:
            Exception: If API request fails
        """
        return self.get_policy_by_name(name) is not None


def main():
    """Test the protection policies manager."""
    print("Testing Protection Policies Manager...")
    
    try:
        config = Lab4Config()
        manager = ProtectionPoliciesManager(config)
        
        print("✅ Protection policies manager initialized")
        
        # Test listing policies
        try:
            policies = manager.list_protection_policies()
            print(f"✅ Found {len(policies)} existing protection policies")
        except Exception as e:
            print(f"⚠️  Could not list policies (expected if no VAST connection): {str(e)}")
        
        # Test template validation
        templates = config.get_policy_templates()
        print(f"✅ Found {len(templates)} policy templates: {list(templates.keys())}")
        
        # Test dry run setup
        dry_run_policies = manager.setup_default_policies(dry_run=True)
        print(f"✅ Dry run would create {len(dry_run_policies)} policies")
        
    except Exception as e:
        print(f"❌ Error testing protection policies manager: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

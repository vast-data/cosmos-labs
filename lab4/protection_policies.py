#!/usr/bin/env python3
"""
VAST Protection Policies Manager

This module provides functionality to create, manage, and apply VAST protection policies
for automated snapshot creation with configurable schedules and retention.
"""

import json
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Lab 4 configuration
from lab4_config import Lab4Config


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
        self.vast_config = self.config.get_vast_api_config()
        
        # Strip protocol from address (like other labs do)
        address = self.vast_config['address']
        if address.startswith('https://'):
            address = address[8:]
        elif address.startswith('http://'):
            address = address[7:]
        
        self.base_url = f"https://{address}/api"
        self.session = requests.Session()
        self.session.verify = self.vast_config['ssl_verify']
        self.session.timeout = self.vast_config['timeout']
        
        # Debug logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"VAST API Config - SSL Verify: {self.vast_config['ssl_verify']}")
        self.logger.info(f"Session verify setting: {self.session.verify}")
        self.logger.info(f"Base URL: {self.base_url}")
        
        # Suppress SSL warnings if verification is disabled (like other labs)
        if not self.vast_config['ssl_verify']:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.logger.info("SSL verification disabled and warnings suppressed")
        
        # Set up authentication
        self.session.auth = (self.vast_config['user'], self.vast_config['password'])
    
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
        parts = frames_string.split()
        
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
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/protectionpolicies/"
        
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
        self.logger.info(f"Original frames string: {frames}")
        self.logger.info(f"Parsed frames array: {json.dumps(frames_array, indent=2)}")
        self.logger.info(f"Policy payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Explicitly pass verify parameter to ensure SSL verification is disabled
            ssl_verify = self.vast_config['ssl_verify']
            self.logger.info(f"Making POST request with ssl_verify={ssl_verify}")
            response = self.session.post(url, json=payload, verify=ssl_verify)
            response.raise_for_status()
            
            policy_data = response.json()
            self.logger.info(f"Successfully created protection policy: {name} (ID: {policy_data.get('id')})")
            
            return policy_data
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to create protection policy {name}: {str(e)}")
            # Log the response content for debugging
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    self.logger.error(f"API Error Details: {error_detail}")
                except:
                    self.logger.error(f"API Error Response: {e.response.text}")
            raise
    
    def list_protection_policies(self) -> List[Dict[str, Any]]:
        """
        List all protection policies.
        
        Returns:
            List of protection policy dictionaries
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/protectionpolicies/"
        
        self.logger.info("Listing protection policies")
        
        try:
            response = self.session.get(url, verify=self.vast_config['ssl_verify'])
            response.raise_for_status()
            
            policies = response.json()
            self.logger.info(f"Found {len(policies)} protection policies")
            
            return policies
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to list protection policies: {str(e)}")
            raise
    
    def get_protection_policy(self, policy_id: int) -> Dict[str, Any]:
        """
        Get a specific protection policy by ID.
        
        Args:
            policy_id: ID of the protection policy
            
        Returns:
            Dict containing the policy information
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/protectionpolicies/{policy_id}/"
        
        self.logger.info(f"Getting protection policy: {policy_id}")
        
        try:
            response = self.session.get(url, verify=self.vast_config['ssl_verify'])
            response.raise_for_status()
            
            policy = response.json()
            self.logger.info(f"Retrieved protection policy: {policy.get('name')}")
            
            return policy
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get protection policy {policy_id}: {str(e)}")
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
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/protectionpolicies/{policy_id}/"
        
        self.logger.info(f"Updating protection policy: {policy_id}")
        self.logger.debug(f"Update fields: {kwargs}")
        
        try:
            response = self.session.patch(url, json=kwargs, verify=self.vast_config['ssl_verify'])
            response.raise_for_status()
            
            policy = response.json()
            self.logger.info(f"Successfully updated protection policy: {policy.get('name')}")
            
            return policy
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to update protection policy {policy_id}: {str(e)}")
            raise
    
    def delete_protection_policy(self, policy_id: int) -> bool:
        """
        Delete a protection policy.
        
        Args:
            policy_id: ID of the protection policy to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.base_url}/protectionpolicies/{policy_id}/"
        
        self.logger.info(f"Deleting protection policy: {policy_id}")
        
        try:
            response = self.session.delete(url, verify=self.vast_config['ssl_verify'])
            response.raise_for_status()
            
            self.logger.info(f"Successfully deleted protection policy: {policy_id}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to delete protection policy {policy_id}: {str(e)}")
            raise
    
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
            requests.RequestException: If API request fails
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
    
    def apply_policy_to_view(self, policy_id: int, view_path: str) -> bool:
        """
        Apply a protection policy to a specific view.
        
        Note: This method would need to be implemented based on VAST's
        protected path API endpoints.
        
        Args:
            policy_id: ID of the protection policy
            view_path: Path of the view to protect
            
        Returns:
            True if application was successful
            
        Raises:
            NotImplementedError: This method needs VAST protected path API implementation
        """
        # This would require VAST's protected path API
        # Implementation depends on specific VAST API endpoints
        raise NotImplementedError("apply_policy_to_view requires VAST protected path API implementation")
    
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
    
    def get_policy_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a protection policy by name.
        
        Args:
            name: Name of the protection policy
            
        Returns:
            Policy data if found, None otherwise
            
        Raises:
            requests.RequestException: If API request fails
        """
        policies = self.list_protection_policies()
        
        for policy in policies:
            if policy.get('name') == name:
                return policy
        
        return None
    
    def policy_exists(self, name: str) -> bool:
        """
        Check if a protection policy exists by name.
        
        Args:
            name: Name of the protection policy
            
        Returns:
            True if policy exists, False otherwise
            
        Raises:
            requests.RequestException: If API request fails
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

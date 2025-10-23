#!/usr/bin/env python3
"""
Lab 4 Configuration Loader

This module provides lab-specific configuration methods for the Snapshot Strategy lab.
It inherits from the centralized config loader and adds Lab 4 specific functionality.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Import the centralized config loader
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import ConfigLoader


class Lab4Config(ConfigLoader):
    """
    Lab 4 specific configuration loader.
    
    Extends the centralized ConfigLoader with Lab 4 specific methods for
    snapshot strategy configuration.
    """
    
    def __init__(self):
        """Initialize Lab 4 configuration loader."""
        # Get the project root directory (parent of lab4)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config.yaml")
        secrets_path = os.path.join(project_root, "secrets.yaml")
        
        super().__init__(config_path=config_path, secrets_path=secrets_path)
        self.lab_name = "lab4"
    
    def get_lab_config(self) -> Dict[str, Any]:
        """
        Return Lab 4's configuration block from the centralized config.
        """
        return super().get_lab_config(self.lab_name)
    
    def get_protection_policy_config(self) -> Dict[str, Any]:
        """
        Get protection policy configuration.
        
        Returns:
            Dict containing protection policy settings
        """
        config = self.get_lab_config()
        return config.get('protection_policies', {})
    
    def get_policy_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get protection policy templates.
        
        Returns:
            Dict mapping template names to template configurations
        """
        policy_config = self.get_protection_policy_config()
        # Remove the 'templates' key since we flattened the structure
        return policy_config
    
    def get_views_config(self) -> List[str]:
        """
        Get list of view paths to apply protection policies to.
        
        Returns:
            List of view paths
        """
        config = self.get_lab_config()
        views_config = config.get('views', {})
        
        # Extract paths from the standardized views structure
        view_paths = []
        for view_name, view_config in views_config.items():
            if isinstance(view_config, dict) and 'path' in view_config:
                view_paths.append(view_config['path'])
        
        return view_paths
    
    def get_snapshot_naming_config(self) -> Dict[str, Any]:
        """
        Get snapshot naming configuration.
        
        Returns:
            Dict containing naming configuration options
        """
        config = self.get_lab_config()
        return config.get('snapshot_naming', {})
    
    def get_restoration_config(self) -> Dict[str, Any]:
        """
        Get restoration configuration.
        
        Returns:
            Dict containing restoration settings
        """
        config = self.get_lab_config()
        return config.get('restoration', {})
    
    def get_retention_settings(self) -> Dict[str, int]:
        """
        Get retention settings for different snapshot types.
        
        Based on industry best practices and research data requirements:
        - Hourly: 3 days (active work)
        - Daily: 14 days (recent work) 
        - Weekly: 90 days (milestones)
        - Monthly: 365 days (releases)
        - Yearly: 1825 days (5 years, long-term archival)
        
        Returns:
            Dict mapping snapshot types to retention days
        """
        policy_config = self.get_protection_policy_config()
        return {
            'hourly': policy_config.get('hourly_retention_days', 3),
            'daily': policy_config.get('daily_retention_days', 14),
            'weekly': policy_config.get('weekly_retention_days', 90),
            'monthly': policy_config.get('monthly_retention_days', 365),
            'yearly': policy_config.get('yearly_retention_days', 1825)
        }
    
    def validate_protection_policy_config(self) -> List[str]:
        """
        Validate protection policy configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            # Check required sections
            policy_config = self.get_protection_policy_config()
            if not policy_config:
                errors.append("Missing 'protection_policies' section in lab4 config")
                return errors
            
            # Validate protection policies (now directly under protection_policies)
            templates = self.get_policy_templates()
            if not templates:
                errors.append("Missing protection policies in lab4 config")
            
            # Validate views
            views = self.get_views_config()
            if not views:
                errors.append("Missing 'views' in lab4 config")
            
            # Validate retention settings
            retention = self.get_retention_settings()
            for key, value in retention.items():
                if not isinstance(value, int) or value <= 0:
                    errors.append(f"Invalid retention setting for {key}: {value}")
            
        except Exception as e:
            errors.append(f"Error validating protection policy config: {str(e)}")
        
        return errors
    
    def get_protection_policy_schedule(self, policy_type: str) -> str:
        """
        Get schedule string for a specific policy type.
        
        Args:
            policy_type: Type of policy (daily, weekly, monthly, hourly)
            
        Returns:
            Schedule string for the policy type
        """
        schedules = self.get_snapshot_schedules()
        return schedules.get(policy_type, "")
    
    def get_policy_template(self, template_name: str) -> Dict[str, Any]:
        """
        Get a specific policy template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template configuration dict
        """
        templates = self.get_policy_templates()
        return templates.get(template_name, {})
    
    def should_include_timestamp_in_names(self) -> bool:
        """
        Check if timestamps should be included in snapshot names.
        
        Returns:
            True if timestamps should be included
        """
        naming_config = self.get_snapshot_naming_config()
        return naming_config.get('include_timestamp', True)
    
    def should_include_user_in_names(self) -> bool:
        """
        Check if user should be included in snapshot names.
        
        Returns:
            True if user should be included
        """
        naming_config = self.get_snapshot_naming_config()
        return naming_config.get('include_user', True)
    
    def should_include_milestone_in_names(self) -> bool:
        """
        Check if milestone should be included in snapshot names.
        
        Returns:
            True if milestone should be included
        """
        naming_config = self.get_snapshot_naming_config()
        return naming_config.get('include_milestone', True)
    
    def get_max_snapshot_name_length(self) -> int:
        """
        Get maximum length for snapshot names.
        
        Returns:
            Maximum name length
        """
        naming_config = self.get_snapshot_naming_config()
        return naming_config.get('max_name_length', 100)
    
    def is_dry_run_default(self) -> bool:
        """
        Check if dry run should be the default mode.
        
        Returns:
            True if dry run is default
        """
        restoration_config = self.get_restoration_config()
        return restoration_config.get('dry_run_default', True)
    
    def should_backup_before_restore(self) -> bool:
        """
        Check if backup should be created before restoration.
        
        Returns:
            True if backup should be created
        """
        restoration_config = self.get_restoration_config()
        return restoration_config.get('backup_before_restore', True)
    
    def is_confirmation_required(self) -> bool:
        """
        Check if confirmation is required for restoration.
        
        Returns:
            True if confirmation is required
        """
        restoration_config = self.get_restoration_config()
        return restoration_config.get('confirmation_required', True)
    
    def generate_snapshot_name(self, base_name: str, milestone: Optional[str] = None) -> str:
        """
        Generate a snapshot name based on configuration.
        
        Args:
            base_name: Base name for the snapshot
            milestone: Optional milestone description
            
        Returns:
            Generated snapshot name
        """
        name_parts = [base_name]
        
        if milestone and self.should_include_milestone_in_names():
            name_parts.append(milestone)
        
        if self.should_include_timestamp_in_names():
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            name_parts.append(timestamp)
        
        if self.should_include_user_in_names():
            user = os.getenv('USER', 'unknown')
            name_parts.append(user)
        
        full_name = "-".join(name_parts)
        max_length = self.get_max_snapshot_name_length()
        
        if len(full_name) > max_length:
            # Truncate base name if needed
            available_length = max_length - len("-".join(name_parts[1:])) - len(name_parts) + 1
            if available_length > 0:
                base_name = base_name[:available_length]
                full_name = "-".join([base_name] + name_parts[1:])
            else:
                full_name = full_name[:max_length]
        
        return full_name
    
    def get_vast_api_config(self) -> Dict[str, Any]:
        """
        Get VAST API configuration for protection policies.
        
        Returns:
            Dict containing VAST API settings
        """
        vast_config = self.get_vast_config()
        return {
            'user': vast_config.get('user'),
            'address': vast_config.get('address'),
            'password': vast_config.get('password'),
            'ssl_verify': vast_config.get('ssl_verify', False),
            'timeout': vast_config.get('timeout', 30)
        }


def main():
    """Test the Lab 4 configuration loader."""
    print("Testing Lab 4 Configuration Loader...")
    
    try:
        config = Lab4Config()
        
        print("✅ Configuration loaded successfully")
        
        # Test basic configuration
        print(f"Lab name: {config.lab_name}")
        
        # Test protection policy config
        policy_config = config.get_protection_policy_config()
        print(f"Protection policies configured: {len(policy_config) > 0}")
        
        # Test schedules
        schedules = config.get_snapshot_schedules()
        print(f"Snapshot schedules: {list(schedules.keys())}")
        
        # Test templates
        templates = config.get_policy_templates()
        print(f"Policy templates: {list(templates.keys())}")
        
        # Test views
        views = config.get_views_config()
        print(f"Configured views: {views}")
        
        # Test retention settings
        retention = config.get_retention_settings()
        print(f"Retention settings: {retention}")
        
        # Test snapshot naming
        test_name = config.generate_snapshot_name("test-snapshot", "milestone-1")
        print(f"Generated snapshot name: {test_name}")
        
        # Validate configuration
        errors = config.validate_protection_policy_config()
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Configuration validation passed")
        
    except Exception as e:
        print(f"❌ Error testing configuration: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

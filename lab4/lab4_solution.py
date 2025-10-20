#!/usr/bin/env python3
"""
Lab 4: The Snapshot Strategy - Main Solution

This is the main orchestrator script for Lab 4, providing a comprehensive
snapshot strategy system using VAST protection policies and snapshot capabilities.
"""

import argparse
import logging
import sys
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from lab4_config import Lab4Config
from protection_policies import ProtectionPoliciesManager
from snapshot_manager import SnapshotManager

from vastpy import VASTClient


class Lab4Solution:
    """
    Main Lab 4 solution orchestrator.
    
    Provides command-line interface and orchestration for all Lab 4 functionality
    including protection policies, snapshot management, and restoration tools.
    """
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize the Lab 4 solution.
        
        Args:
            dry_run: Whether to run in dry-run mode (default: True)
        """
        self.dry_run = dry_run
        self.config = Lab4Config()
        
        # Initialize components
        self.protection_policies = ProtectionPoliciesManager(self.config)
        self.snapshot_manager = SnapshotManager(self.config)
        self.vast_client = None
        # Initialize vast client (used for view checks/creation)
        vast_cfg = self.config.get_vast_config()
        
        # Strip protocol from address (like Lab 1 does)
        address = vast_cfg.get('address')
        if address.startswith('https://'):
            address = address[8:]  # Remove 'https://' prefix
        elif address.startswith('http://'):
            address = address[7:]  # Remove 'http://' prefix
        
        try:
            self.vast_client = VASTClient(
                address=address,
                user=vast_cfg.get('user'),  # Use 'user' not 'username'
                password=vast_cfg.get('password')
            )
        except Exception as e:
            self.logger.warning(f"Failed to initialize VAST client: {e}")
            self.vast_client = None
        
        # Set up logging
        self.setup_logging()
        
        # Validate configuration
        self.validate_configuration()
    
    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        if self.dry_run:
            self.logger.info("🛡️  Running in DRY RUN mode - no changes will be made")
        else:
            self.logger.info("🚀 Running in PRODUCTION mode - changes will be made")
    
    def validate_configuration(self):
        """Validate Lab 4 configuration."""
        self.logger.info("Validating Lab 4 configuration...")
        
        errors = self.config.validate_protection_policy_config()
        if errors:
            self.logger.error("Configuration validation failed:")
            for error in errors:
                self.logger.error(f"  - {error}")
            raise ValueError("Invalid configuration")
        
        self.logger.info("✅ Configuration validation passed")
    
    def setup_protection_policies(self) -> List[Dict[str, Any]]:
        """
        Set up protection policies based on configuration.
        
        Returns:
            List of created or would-be-created policies
        """
        self.logger.info("Setting up protection policies...")
        # Ensure views exist (or would be created) before applying policies
        self.ensure_views_exist()
        
        policies = self.protection_policies.setup_default_policies(dry_run=self.dry_run)
        
        if self.dry_run:
            self.logger.info(f"Would create {len(policies)} protection policies:")
            for policy in policies:
                view_info = f", view: {policy['view']}" if 'view' in policy else ""
                self.logger.info(f"  - {policy['name']} (template: {policy['template']}{view_info})")
        else:
            self.logger.info(f"Created {len(policies)} protection policies")
        
        return policies

    def setup_protected_paths(self) -> List[Dict[str, Any]]:
        """
        Set up protected paths for all configured views.
        
        Returns:
            List of created or would-be-created protected paths
        """
        self.logger.info("Setting up protected paths...")
        
        protected_paths = self.protection_policies.setup_protected_paths_for_views(dry_run=self.dry_run)
        
        if self.dry_run:
            self.logger.info(f"Would create {len(protected_paths)} protected paths:")
            for path in protected_paths:
                tenant_info = f", tenant: {path['tenant_id']}" if 'tenant_id' in path else ""
                self.logger.info(f"  - {path['name']} -> {path['source_dir']} (policy ID: {path['policy_id']}{tenant_info})")
        else:
            self.logger.info(f"Created {len(protected_paths)} protected paths")
        
        return protected_paths

    def ensure_views_exist(self) -> bool:
        """
        Ensure the views referenced by Lab 4 exist; create them using standardized view definitions.
        
        Uses the same pattern as Lab 1: lab4.views.{view_name} with path, bucket_name, quota_gb, etc.
        """
        config = self.config.get_lab_config()
        views_config = config.get('views', {})
        
        if not views_config:
            self.logger.warning("No views configured for Lab 4; nothing to ensure.")
            return True

        if self.dry_run:
            self.logger.info("[DRY RUN] Would verify/create the following views:")
            for view_name, view_config in views_config.items():
                if isinstance(view_config, dict) and 'path' in view_config:
                    path = view_config['path']
                    bucket = view_config.get('bucket_name', 'unknown')
                    quota_gb = view_config.get('quota_gb', 0)
                    self.logger.info(f"  - {path} (bucket: {bucket}, quota: {quota_gb}GB)")
            return True
        
        if self.vast_client is None:
            self.logger.warning("VAST client not available; cannot create views. Check VAST connection or run in dry-run.")
            return False
        
        success = True
        for view_name, view_config in views_config.items():
            if not isinstance(view_config, dict) or 'path' not in view_config:
                continue
                
            view_path = view_config['path']
            bucket_name = view_config.get('bucket_name')
            policy_name = view_config.get('policy_name', 's3_default_policy')
            quota_gb = int(view_config.get('quota_gb', 10240))
            protocols = view_config.get('protocols', ['S3', 'NFS'])
            bucket_owner = view_config.get('bucket_owner')
            
            if not bucket_name:
                self.logger.error(f"Missing bucket_name for view '{view_path}'")
                success = False
                continue
            
            try:
                existing = self.vast_client.views.get(path=view_path)
                if existing:
                    self.logger.info(f"View exists: {view_path}")
                    continue
            except Exception:
                # Proceed to attempt creation
                existing = []

            try:
                policies = self.vast_client.viewpolicies.get(name=policy_name)
                if not policies:
                    self.logger.error(f"Policy '{policy_name}' not found; cannot create view {view_path}")
                    success = False
                    continue
                policy_id = policies[0]['id']

                kwargs = {
                    'path': view_path,
                    'bucket': bucket_name,
                    'policy_id': policy_id,
                    'protocols': protocols,
                    'create_dir': True,
                }
                if bucket_owner:
                    kwargs['bucket_owner'] = bucket_owner

                self.vast_client.views.post(**kwargs)
                self.logger.info(f"✅ Created view '{view_path}'")

                # Set quota
                quota_bytes = quota_gb * 1024 * 1024 * 1024
                quota_data = {
                    'name': f"{bucket_name}-quota",
                    'path': view_path,
                    'hard_limit': quota_bytes,
                    'soft_limit': int(quota_bytes * 0.8),
                }
                self.vast_client.quotas.post(**quota_data)
                self.logger.info(f"✅ Set quota for '{view_path}': {quota_gb} GB")

            except Exception as e:
                self.logger.error(f"Failed to create view '{view_path}': {e}")
                success = False

        return success
    
    def create_protection_policy(self, 
                                template_name: str, 
                                view_path: str,
                                custom_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a specific protection policy.
        
        Args:
            template_name: Template to use for the policy
            view_path: View path to apply the policy to
            custom_name: Custom name for the policy (optional)
            
        Returns:
            Created policy information
        """
        policy_name = custom_name or f"{template_name}-{view_path.replace('/', '-').strip('-')}"
        
        self.logger.info(f"Creating protection policy: {policy_name}")
        
        if self.dry_run:
            self.logger.info(f"Would create policy '{policy_name}' using template '{template_name}' for view '{view_path}'")
            return {
                'name': policy_name,
                'template': template_name,
                'view': view_path,
                'dry_run': True
            }
        else:
            return self.protection_policies.create_policy_from_template(
                template_name=template_name,
                policy_name=policy_name,
                view_path=view_path
            )
    
    def list_protection_policies(self) -> List[Dict[str, Any]]:
        """
        List all protection policies.
        
        Returns:
            List of protection policies
        """
        self.logger.info("Listing protection policies...")
        
        try:
            policies = self.protection_policies.list_protection_policies()
            self.logger.info(f"Found {len(policies)} protection policies:")
            
            for policy in policies:
                self.logger.info(f"  - {policy.get('name', 'Unknown')} (ID: {policy.get('id', 'Unknown')})")
                self.logger.info(f"    Schedule: {policy.get('frames', 'Unknown')}")
                self.logger.info(f"    Type: {policy.get('clone_type', 'Unknown')}")
            
            return policies
            
        except Exception as e:
            self.logger.error(f"Failed to list protection policies: {str(e)}")
            return []
    
    def create_named_snapshot(self, 
                             name: str, 
                             view_path: str,
                             milestone: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a named snapshot with descriptive metadata.
        
        Args:
            name: Base name for the snapshot
            view_path: Path of the view to snapshot
            milestone: Optional milestone description
            metadata: Optional metadata dictionary
            
        Returns:
            Created snapshot information
        """
        snapshot_name = self.config.generate_snapshot_name(name, milestone)
        
        self.logger.info(f"Creating named snapshot: {snapshot_name}")
        self.logger.info(f"View: {view_path}")
        if milestone:
            self.logger.info(f"Milestone: {milestone}")
        if metadata:
            self.logger.info(f"Metadata: {metadata}")
        
        if self.dry_run:
            self.logger.info(f"Would create snapshot '{snapshot_name}' for view '{view_path}'")
            return {
                'name': snapshot_name,
                'view': view_path,
                'milestone': milestone,
                'metadata': metadata,
                'dry_run': True
            }
        else:
            try:
                snapshot = self.snapshot_manager.create_named_snapshot(
                    name=name,
                    view_path=view_path,
                    milestone=milestone,
                    metadata=metadata
                )
                self.logger.info(f"✅ Created snapshot: {snapshot_name}")
                return snapshot
            except Exception as e:
                self.logger.error(f"❌ Failed to create snapshot: {e}")
                return {
                    'name': snapshot_name,
                    'view': view_path,
                    'milestone': milestone,
                    'metadata': metadata,
                    'dry_run': False,
                    'error': str(e)
                }
    
    def list_snapshots(self, view_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List snapshots for a specific view or all views.
        
        Args:
            view_path: Optional specific view path
            
        Returns:
            List of snapshots
        """
        if view_path:
            self.logger.info(f"Listing snapshots for view: {view_path}")
        else:
            self.logger.info("Listing all snapshots")
        
        try:
            if view_path:
                snapshots = self.snapshot_manager.list_snapshots_for_view(view_path)
            else:
                snapshots = self.snapshot_manager.list_snapshots()
            
            self.logger.info(f"Found {len(snapshots)} snapshots")
            return snapshots
        except Exception as e:
            self.logger.error(f"❌ Failed to list snapshots: {e}")
            return []
    
    def search_snapshots(self, 
                        search_term: str,
                        view_path: Optional[str] = None,
                        date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Search snapshots by name, metadata, or date range.
        
        Args:
            search_term: Search term for snapshot names or metadata
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
            snapshots = self.snapshot_manager.search_snapshots(
                search_term=search_term,
                view_path=view_path,
                date_range=date_range
            )
            self.logger.info(f"Found {len(snapshots)} matching snapshots")
            return snapshots
        except Exception as e:
            self.logger.error(f"❌ Failed to search snapshots: {e}")
            return []
    
    def restore_snapshot(self, 
                        snapshot_name: str, 
                        view_path: str,
                        backup_first: bool = True) -> Dict[str, Any]:
        """
        Restore a view from a snapshot.
        
        Args:
            snapshot_name: Name of the snapshot to restore from
            view_path: Path of the view to restore
            backup_first: Whether to create a backup before restoration
            
        Returns:
            Restoration result information
        """
        self.logger.info(f"Restoring snapshot: {snapshot_name}")
        self.logger.info(f"Target view: {view_path}")
        self.logger.info(f"Backup first: {backup_first}")
        
        if self.dry_run:
            self.logger.info(f"Would restore view '{view_path}' from snapshot '{snapshot_name}'")
            if backup_first:
                self.logger.info("Would create backup before restoration")
            return {
                'snapshot': snapshot_name,
                'view': view_path,
                'backup_first': backup_first,
                'dry_run': True
            }
        else:
            # This would use the SnapshotRestore when implemented
            self.logger.warning("Snapshot restoration not yet implemented - use dry run mode")
            return {
                'snapshot': snapshot_name,
                'view': view_path,
                'backup_first': backup_first,
                'dry_run': False,
                'status': 'not_implemented'
            }
    
    def cleanup_old_snapshots(self, 
                             view_path: Optional[str] = None,
                             older_than_days: int = 30) -> List[str]:
        """
        Clean up old snapshots.
        
        Args:
            view_path: Optional specific view path to clean up
            older_than_days: Delete snapshots older than this many days
            
        Returns:
            List of deleted snapshot names
        """
        self.logger.info(f"Cleaning up snapshots older than {older_than_days} days")
        if view_path:
            self.logger.info(f"View filter: {view_path}")
        
        try:
            deleted_snapshots = self.snapshot_manager.cleanup_old_snapshots(
                view_path=view_path,
                older_than_days=older_than_days,
                dry_run=self.dry_run
            )
            
            if self.dry_run:
                self.logger.info(f"Would delete {len(deleted_snapshots)} old snapshots")
            else:
                self.logger.info(f"✅ Deleted {len(deleted_snapshots)} old snapshots")
            
            return deleted_snapshots
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup snapshots: {e}")
            return []
    
    def show_snapshot_details(self, snapshot_name: str) -> Dict[str, Any]:
        """
        Show detailed information about a snapshot.
        
        Args:
            snapshot_name: Name of the snapshot
            
        Returns:
            Snapshot details
        """
        self.logger.info(f"Getting details for snapshot: {snapshot_name}")
        
        # This would use the SnapshotBrowser when implemented
        self.logger.warning("Snapshot details not yet implemented")
        return {
            'name': snapshot_name,
            'status': 'not_implemented'
        }
    
    def run_complete_workflow(self) -> Dict[str, Any]:
        """
        Run the complete Lab 4 workflow.
        
        Returns:
            Workflow results
        """
        self.logger.info("Running complete Lab 4 workflow...")
        
        results = {
            'protection_policies': [],
            'protected_paths': [],
            'snapshots': [],
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run
        }
        
        try:
            # Step 1: Set up protection policies
            self.logger.info("Step 1: Setting up protection policies")
            policies = self.setup_protection_policies()
            results['protection_policies'] = policies
            
            # Step 2: Set up protected paths
            self.logger.info("Step 2: Setting up protected paths")
            protected_paths = self.setup_protected_paths()
            results['protected_paths'] = protected_paths
            
            # Step 3: Create initial snapshots
            self.logger.info("Step 3: Creating initial snapshots")
            views = self.config.get_views_config()
            for view_path in views:
                snapshot = self.create_named_snapshot(
                    name="initial-setup",
                    view_path=view_path,
                    milestone="lab4-initial-setup"
                )
                results['snapshots'].append(snapshot)
            
            # Step 4: List policies, protected paths, and snapshots
            self.logger.info("Step 4: Listing created resources")
            self.list_protection_policies()
            
            self.logger.info("✅ Complete workflow finished successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {str(e)}")
            results['error'] = str(e)
        
        return results


def main():
    """Main entry point for Lab 4 solution."""
    parser = argparse.ArgumentParser(
        description="Lab 4: The Snapshot Strategy - VAST Protection Policies and Snapshot Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - show what would be done
  python lab4_solution.py --setup-policies
  
  # Production - actually create policies
  python lab4_solution.py --setup-policies --pushtoprod
  
  # Clean up old policies with verbose names
  python lab4_solution.py --cleanup-policies --pushtoprod
  
  # Clean up protected paths that use old policy names
  python lab4_solution.py --cleanup-protected-paths --pushtoprod
  
  # Complete cleanup: protected paths -> policies (in dependency order)
  python lab4_solution.py --full-cleanup --pushtoprod
  
  # Set up protected paths for all views
  python lab4_solution.py --setup-protected-paths --pushtoprod
  
  # List protected paths
  python lab4_solution.py --list-protected-paths
  
  # Clean up old snapshots
  python lab4_solution.py --cleanup-snapshots --snapshot-age-days 30 --pushtoprod
  
  # Create named snapshot
  python lab4_solution.py --create-snapshot "pre-calibration-change" --view "/cosmos7/processed"
  
  # List snapshots
  python lab4_solution.py --list-snapshots
  
  # Restore from snapshot (dry run)
  python lab4_solution.py --restore-snapshot "pre-calibration-change" --view "/cosmos7/processed"
  
  # Complete workflow (includes policies, protected paths, and snapshots)
  python lab4_solution.py --complete --pushtoprod
        """
    )
    
    # Main operation flags
    parser.add_argument('--setup-policies', action='store_true',
                       help='Set up protection policies based on configuration')
    parser.add_argument('--cleanup-policies', action='store_true',
                       help='Clean up all lab4 policies')
    parser.add_argument('--cleanup-protected-paths', action='store_true',
                       help='Clean up all lab4 protected paths')
    parser.add_argument('--full-cleanup', action='store_true',
                       help='Complete cleanup: protected paths -> policies (in dependency order)')
    parser.add_argument('--setup-protected-paths', action='store_true',
                       help='Set up protected paths for all configured views')
    parser.add_argument('--list-policies', action='store_true',
                       help='List all protection policies')
    parser.add_argument('--list-protected-paths', action='store_true',
                       help='List all protected paths')
    parser.add_argument('--create-snapshot', type=str, metavar='NAME',
                       help='Create a named snapshot')
    parser.add_argument('--list-snapshots', action='store_true',
                       help='List all snapshots')
    parser.add_argument('--search-snapshots', type=str, metavar='TERM',
                       help='Search snapshots by name or metadata')
    parser.add_argument('--restore-snapshot', type=str, metavar='NAME',
                       help='Restore from a snapshot')
    parser.add_argument('--cleanup-snapshots', action='store_true',
                       help='Clean up old snapshots')
    parser.add_argument('--snapshot-age-days', type=int, default=30,
                       help='Age in days for snapshot cleanup (default: 30)')
    
    # Configuration options
    parser.add_argument('--view', type=str, metavar='PATH',
                       help='View path for snapshot operations')
    parser.add_argument('--views', nargs='+', metavar='PATH',
                       help='Multiple view paths for batch operations')
    parser.add_argument('--milestone', type=str, metavar='DESCRIPTION',
                       help='Milestone description for named snapshots')
    parser.add_argument('--template', type=str, metavar='NAME',
                       help='Protection policy template name')
    parser.add_argument('--date-range', nargs=2, metavar=('START', 'END'),
                       help='Date range for search operations (YYYY-MM-DD format)')
    
    # Safety and mode options
    parser.add_argument('--pushtoprod', action='store_true',
                       help='Enable production mode (make actual changes)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run in dry-run mode (default)')
    parser.add_argument('--no-dry-run', action='store_true',
                       help='Disable dry-run mode')
    parser.add_argument('--backup-first', action='store_true', default=True,
                       help='Create backup before restoration (default)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup before restoration')
    
    # Output options
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Determine dry run mode
    dry_run = not args.pushtoprod and not args.no_dry_run
    
    # Set up logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize solution
        solution = Lab4Solution(dry_run=dry_run)
        
        # Execute requested operations
        if args.setup_policies:
            solution.setup_protection_policies()
        
        elif args.cleanup_policies:
            solution.protection_policies.cleanup_all_lab4_policies(dry_run=dry_run)
        
        elif args.cleanup_protected_paths:
            solution.protection_policies.cleanup_all_lab4_protected_paths(dry_run=dry_run)
        
        elif args.full_cleanup:
            results = solution.protection_policies.full_cleanup(dry_run=dry_run)
            if args.json:
                import json
                print(json.dumps(results, indent=2))
        
        elif args.setup_protected_paths:
            solution.setup_protected_paths()
        
        elif args.list_policies:
            solution.list_protection_policies()
        
        elif args.list_protected_paths:
            solution.protection_policies.list_protected_paths()
        
        elif args.create_snapshot:
            if not args.view:
                print("Error: --view is required for snapshot creation")
                return 1
            
            solution.create_named_snapshot(
                name=args.create_snapshot,
                view_path=args.view,
                milestone=args.milestone
            )
        
        elif args.list_snapshots:
            solution.list_snapshots(args.view)
        
        elif args.search_snapshots:
            solution.search_snapshots(
                search_term=args.search_snapshots,
                view_path=args.view,
                date_range=args.date_range
            )
        
        elif args.restore_snapshot:
            if not args.view:
                print("Error: --view is required for snapshot restoration")
                return 1
            
            solution.restore_snapshot(
                snapshot_name=args.restore_snapshot,
                view_path=args.view,
                backup_first=args.backup_first and not args.no_backup
            )
        
        elif args.cleanup_snapshots:
            solution.cleanup_old_snapshots(
                view_path=args.view,
                older_than_days=args.snapshot_age_days
            )
        
        elif args.snapshot_details:
            solution.show_snapshot_details(args.snapshot_details)
        
        elif args.complete:
            results = solution.run_complete_workflow()
            if args.json:
                import json
                print(json.dumps(results, indent=2))
        
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

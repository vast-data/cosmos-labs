#!/usr/bin/env python3
"""
Lab 2 Main Orchestrator
Coordinates the complete Lab 2 workflow using focused scripts
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Lab2Orchestrator:
    """Orchestrates the complete Lab 2 workflow"""
    
    def __init__(self, config_path: str = None, secrets_path: str = None):
        # Default to parent directory for config files
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config.yaml")
        if secrets_path is None:
            secrets_path = str(Path(__file__).parent.parent / "secrets.yaml")
            
        self.config_path = config_path
        self.secrets_path = secrets_path
        self.script_dir = Path(__file__).parent
    
    def run_command(self, script_name: str, args: list = None) -> bool:
        """Run a Lab 2 script with given arguments"""
        script_path = self.script_dir / script_name
        cmd = [sys.executable, str(script_path)]
        
        if args:
            cmd.extend(args)
        
        logger.info(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            # Run with real-time output streaming
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Stream output in real-time
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            
            # Wait for completion and get return code
            return_code = process.wait()
            
            if return_code == 0:
                logger.info("✅ Command completed successfully")
                return True
            else:
                logger.error(f"❌ Command failed with exit code {return_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Command failed with exception: {e}")
            return False
    
    def setup_infrastructure(self, dry_run: bool = False) -> bool:
        """Set up VAST views and database infrastructure"""
        logger.info("🔧 Setting up infrastructure...")
        
        args = ["--config", self.config_path, "--secrets", self.secrets_path]
        if dry_run:
            args.append("--dry-run")
        
        return self.run_command("setup_infrastructure.py", args)
    
    def upload_datasets(self, dry_run: bool = False) -> bool:
        """Upload Swift datasets to S3"""
        logger.info("📤 Uploading datasets to S3...")
        
        args = ["--config", self.config_path, "--secrets", self.secrets_path]
        if dry_run:
            args.append("--dry-run")
        
        return self.run_command("upload_datasets.py", args)
    
    def process_metadata(self, dry_run: bool = False, dataset: str = None) -> bool:
        """Process metadata from S3 datasets"""
        logger.info("🔍 Processing metadata from S3...")
        
        args = ["--config", self.config_path, "--secrets", self.secrets_path]
        if dry_run:
            args.append("--dry-run")
        if dataset:
            args.extend(["--dataset", dataset])
        
        return self.run_command("process_metadata.py", args)
    
    def search_metadata(self, pattern: str = None, obs_id: str = None, file_type: str = None, 
                       recent: int = None, stats: bool = False, interactive: bool = False) -> bool:
        """Search metadata in VAST Database"""
        logger.info("🔍 Searching metadata...")
        
        args = ["--config", self.config_path, "--secrets", self.secrets_path]
        
        if pattern:
            args.extend(["--pattern", pattern])
        if obs_id:
            args.extend(["--obs-id", obs_id])
        if file_type:
            args.extend(["--file-type", file_type])
        if recent:
            args.extend(["--recent", str(recent)])
        if stats:
            args.append("--stats")
        if interactive:
            args.append("--interactive")
        
        return self.run_command("search_metadata.py", args)
    
    def run_complete_workflow(self, dry_run: bool = False) -> bool:
        """Run the complete Lab 2 workflow"""
        logger.info("🚀 Starting complete Lab 2 workflow...")
        
        # Step 1: Setup infrastructure
        if not self.setup_infrastructure(dry_run):
            logger.error("❌ Infrastructure setup failed")
            return False
        
        # Step 2: Upload datasets
        if not self.upload_datasets(dry_run):
            logger.error("❌ Dataset upload failed")
            return False
        
        # Step 3: Process metadata
        if not self.process_metadata(dry_run):
            logger.error("❌ Metadata processing failed")
            return False
        
        logger.info("✅ Complete workflow finished successfully")
        return True
    
    def list_uploaded_datasets(self) -> bool:
        """List datasets uploaded to S3"""
        logger.info("📁 Listing uploaded datasets...")
        return self.run_command("upload_datasets.py", ["--list", "--config", self.config_path, "--secrets", self.secrets_path])

def main():
    """Main entry point for Lab 2 orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lab 2 Complete Solution Orchestrator')
    parser.add_argument('--config', default=None, help='Config file path (default: ../config.yaml)')
    parser.add_argument('--secrets', default=None, help='Secrets file path (default: ../secrets.yaml)')
    parser.add_argument('--pushtoprod', action='store_true', help='Push to production (make actual changes)')
    
    # Workflow options
    parser.add_argument('--setup-only', action='store_true', help='Setup infrastructure only')
    parser.add_argument('--upload-only', action='store_true', help='Upload datasets only')
    parser.add_argument('--process-only', action='store_true', help='Process metadata only')
    parser.add_argument('--search-only', action='store_true', help='Search metadata only')
    parser.add_argument('--complete', action='store_true', help='Run complete workflow')
    
    # Search options
    parser.add_argument('--pattern', help='Search by file pattern')
    parser.add_argument('--obs-id', help='Search by observation ID')
    parser.add_argument('--file-type', help='Search by file type')
    parser.add_argument('--recent', type=int, help='Show recent N files')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--interactive', action='store_true', help='Interactive search')
    
    # Dataset options
    parser.add_argument('--dataset', help='Process specific dataset')
    parser.add_argument('--list-datasets', action='store_true', help='List uploaded datasets')
    
    args = parser.parse_args()
    
    orchestrator = Lab2Orchestrator(args.config, args.secrets)
    
    # Default to dry-run mode unless --pushtoprod is specified
    dry_run = not args.pushtoprod
    
    if dry_run:
        print("⚠️  DRY RUN MODE: No actual changes will be made")
        print("   Use --pushtoprod to make actual changes")
    else:
        print("🚨 WARNING: PRODUCTION MODE ENABLED")
        print("   This will make actual changes to your VAST Database!")
        confirm = input("   Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("❌ Operation cancelled")
            return
        print("✅ Production mode confirmed. Proceeding with actual changes...")
    
    if args.list_datasets:
        success = orchestrator.list_uploaded_datasets()
    elif args.setup_only:
        success = orchestrator.setup_infrastructure(dry_run)
    elif args.upload_only:
        success = orchestrator.upload_datasets(dry_run)
    elif args.process_only:
        success = orchestrator.process_metadata(dry_run, args.dataset)
    elif args.search_only:
        success = orchestrator.search_metadata(
            args.pattern, args.obs_id, args.file_type, 
            args.recent, args.stats, args.interactive
        )
    elif args.complete or (not any([args.setup_only, args.upload_only, args.process_only, args.search_only, args.list_datasets])):
        success = orchestrator.run_complete_workflow(dry_run)
    else:
        parser.print_help()
        return
    
    if success:
        logger.info("✅ Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

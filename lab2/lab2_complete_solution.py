#!/usr/bin/env python3
"""
Lab 2 Complete Solution: Metadata Infrastructure Project
Integrates VAST Database, Swift metadata extraction, and S3 file handling
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config_loader import ConfigLoader
    from vast_database_manager import VASTDatabaseManager
    from swift_metadata_extractor import SwiftMetadataExtractor
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required modules are available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Lab2CompleteSolution:
    """Complete Lab 2 solution integrating database, metadata extraction, and S3"""
    
    def __init__(self, config_path: str = None, production_mode: bool = False):
        """Initialize the complete Lab 2 solution"""
        self.production_mode = production_mode
        
        # Load configuration
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = str(project_root / "config.yaml")
        
        self.config = ConfigLoader(config_path)
        
        # Initialize components
        self.db_manager = VASTDatabaseManager(self.config)
        self.metadata_extractor = SwiftMetadataExtractor(self.config)
        
        # Swift datasets configuration
        self.swift_datasets_dir = Path(__file__).parent.parent / "scripts" / "swift_datasets"
        
        mode_text = "PRODUCTION" if production_mode else "DRY RUN"
        logger.info(f"Lab 2 Complete Solution initialized in {mode_text} mode")
    
    def setup_database_infrastructure(self) -> bool:
        """Safely set up the database infrastructure"""
        try:
            logger.info("🔧 Setting up VAST Database infrastructure...")
            
            # Step 1: Connect to database server
            if not self.db_manager.connect():
                logger.error("❌ Failed to connect to VAST Database server")
                return False
            
            # Step 2: Check if bucket exists, create schema and table if needed
            if not self.db_manager.database_exists():
                if self.production_mode:
                    if not self.db_manager.create_schema_and_table():
                        logger.error("❌ Failed to create schema and table")
                        return False
                else:
                    logger.info("🔍 DRY RUN: Would create schema and table")
            else:
                # Bucket exists, check if we need to create schema and table
                if self.production_mode:
                    if not self.db_manager.create_schema_and_table():
                        logger.error("❌ Failed to create schema and table")
                        return False
                else:
                    logger.info("🔍 DRY RUN: Would create schema and table")
            
            logger.info("✅ Database infrastructure setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database infrastructure setup failed: {e}")
            return False
    
    def get_available_datasets(self) -> List[Dict[str, Any]]:
        """Get list of available Swift datasets"""
        if not self.swift_datasets_dir.exists():
            logger.warning(f"⚠️  Swift datasets directory not found: {self.swift_datasets_dir}")
            return []
        
        logger.info(f"🔍 Scanning Swift datasets directory: {self.swift_datasets_dir}")
        datasets = []
        
        for dataset_dir in self.swift_datasets_dir.iterdir():
            if dataset_dir.is_dir():
                # Calculate total size
                total_size = sum(f.stat().st_size for f in dataset_dir.rglob('*') if f.is_file())
                total_size_gb = total_size / (1024**3)
                
                # Count files
                file_count = sum(1 for f in dataset_dir.rglob('*') if f.is_file())
                
                datasets.append({
                    'name': dataset_dir.name,
                    'path': str(dataset_dir),
                    'size_gb': round(total_size_gb, 2),
                    'file_count': file_count
                })
        
        return sorted(datasets, key=lambda x: x['size_gb'], reverse=True)
    
    def process_dataset_metadata(self, dataset_path: str) -> Dict[str, Any]:
        """Process metadata for a single dataset"""
        dataset_name = Path(dataset_path).name
        
        logger.info(f"📊 Processing dataset: {dataset_name}")
        logger.info(f"   Path: {dataset_path}")
        
        if self.production_mode:
            logger.info("🚨 PRODUCTION MODE: Processing actual files")
        else:
            logger.info("🔍 DRY RUN MODE: No actual processing")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
        
        # Extract metadata from all files in the dataset
        metadata_list = self.metadata_extractor.extract_metadata_from_dataset(dataset_path)
        
        if not metadata_list:
            logger.warning(f"⚠️  No metadata extracted from dataset: {dataset_name}")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}
        
        logger.info(f"📊 Extracted metadata for {len(metadata_list)} files")
        
        # Process each metadata record
        processed_count = 0
        inserted_count = 0
        skipped_count = 0
        failed_count = 0
        
        for metadata in metadata_list:
            try:
                processed_count += 1
                
                # Check if metadata already exists in database
                if self.db_manager.metadata_exists(metadata['file_path']):
                    logger.debug(f"ℹ️  Metadata already exists for: {metadata['file_name']}")
                    skipped_count += 1
                    continue
                
                # Insert metadata into database
                if self.db_manager.insert_metadata(metadata):
                    inserted_count += 1
                    logger.debug(f"✅ Inserted metadata for: {metadata['file_name']}")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to insert metadata for: {metadata['file_name']}")
                
                # Progress logging
                if processed_count % 10 == 0:
                    logger.info(f"📊 Progress: {processed_count}/{len(metadata_list)} files processed")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error processing metadata for {metadata.get('file_name', 'unknown')}: {e}")
        
        logger.info(f"✅ Dataset '{dataset_name}' processing completed:")
        logger.info(f"   📊 Processed: {processed_count}")
        logger.info(f"   ✅ Inserted: {inserted_count}")
        logger.info(f"   ⏭️  Skipped: {skipped_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        
        return {
            'processed': processed_count,
            'inserted': inserted_count,
            'skipped': skipped_count,
            'failed': failed_count
        }
    
    def process_all_datasets(self) -> Dict[str, Any]:
        """Process metadata for all available datasets"""
        logger.info("🚀 Starting metadata processing for all datasets")
        
        # Get available datasets
        datasets = self.get_available_datasets()
        
        if not datasets:
            logger.warning("⚠️  No datasets found for processing")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"📊 Found {len(datasets)} datasets ready for processing")
        
        # Process each dataset
        success_count = 0
        failed_count = 0
        total_processed = 0
        total_inserted = 0
        
        for dataset in datasets:
            logger.info(f"\n{'='*60}")
            logger.info(f"📤 Processing: {dataset['name']}")
            logger.info(f"{'='*60}")
            
            # Process dataset
            result = self.process_dataset_metadata(dataset['path'])
            
            if result['failed'] == 0:
                success_count += 1
                logger.info(f"✅ Dataset processed successfully: {dataset['name']}")
            else:
                failed_count += 1
                logger.error(f"❌ Dataset processing failed: {dataset['name']}")
            
            # Update totals
            total_processed += result['processed']
            total_inserted += result['inserted']
            
            # Summary for this dataset
            logger.info(f"📊 Processing Summary for {dataset['name']}:")
            logger.info(f"   📊 Processed: {result['processed']}")
            logger.info(f"   ✅ Inserted: {result['inserted']}")
            logger.info(f"   ⏭️  Skipped: {result['skipped']}")
            logger.info(f"   ❌ Failed: {result['failed']}")
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("📊 OVERALL PROCESSING SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"  ✅ Successful datasets: {success_count}")
        logger.info(f"  ❌ Failed datasets: {failed_count}")
        logger.info(f"  📊 Total datasets: {len(datasets)}")
        logger.info(f"  📁 Total files processed: {total_processed}")
        logger.info(f"  💾 Total metadata records inserted: {total_inserted}")
        
        if self.production_mode:
            logger.info("✅ Production mode: All changes were applied")
        else:
            logger.info("⚠️  DRY RUN MODE: No actual changes were made")
            logger.info("💡 Use --pushtoprod to perform actual processing")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(datasets),
            'files_processed': total_processed,
            'metadata_inserted': total_inserted
        }
    
    def show_database_stats(self) -> bool:
        """Display current database statistics"""
        try:
            logger.info("📊 Retrieving database statistics...")
            
            stats = self.db_manager.get_metadata_stats()
            
            if not stats:
                logger.warning("⚠️  No statistics available")
                return False
            
            logger.info(f"📊 Database Statistics:")
            logger.info(f"   📁 Total files: {stats.get('total_files', 0)}")
            
            if stats.get('mission_counts'):
                logger.info(f"   🚀 Missions:")
                for mission, count in stats['mission_counts'].items():
                    logger.info(f"      {mission}: {count} files")
            
            if stats.get('dataset_counts'):
                logger.info(f"   📂 Datasets:")
                for dataset, count in stats['dataset_counts'].items():
                    logger.info(f"      {dataset}: {count} files")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve database stats: {e}")
            return False
    
    def search_metadata(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata in the database"""
        try:
            logger.info(f"🔍 Searching metadata with criteria: {search_criteria}")
            
            results = self.db_manager.search_metadata(search_criteria)
            
            logger.info(f"🔍 Search completed: {len(results)} results found")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def close(self):
        """Clean up resources"""
        if self.db_manager:
            self.db_manager.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Lab 2 Complete Solution: Metadata Infrastructure')
    parser.add_argument('--pushtoprod', action='store_true', help='Enable production mode (actual changes)')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--setup-only', action='store_true', help='Only set up database infrastructure')
    parser.add_argument('--process-only', action='store_true', help='Only process metadata (assumes setup is complete)')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--search', type=str, help='Search metadata (e.g., "mission_id=SWIFT")')
    
    args = parser.parse_args()
    
    if args.pushtoprod:
        print("🚨 WARNING: PRODUCTION MODE ENABLED")
        print("This will make actual changes to your VAST Database!")
        confirm = input("Type 'YES' to confirm: ")
        
        if confirm != 'YES':
            print("❌ Production mode not confirmed. Exiting.")
            return
        
        print("✅ Production mode confirmed. Proceeding with actual changes...")
        production_mode = True
    else:
        print("⚠️  DRY RUN MODE: No actual changes will be made")
        production_mode = False
    
    try:
        # Create solution instance
        solution = Lab2CompleteSolution(config_path=args.config, production_mode=production_mode)
        
        if args.stats:
            # Show database statistics
            solution.show_database_stats()
            
        elif args.search:
            # Search metadata
            # Parse search criteria (simple format: key=value)
            search_criteria = {}
            if '=' in args.search:
                key, value = args.search.split('=', 1)
                search_criteria[key.strip()] = value.strip()
            
            results = solution.search_metadata(search_criteria)
            
            if results:
                print(f"\n🔍 Search Results ({len(results)} found):")
                for i, result in enumerate(results[:10], 1):  # Show first 10
                    print(f"{i}. {result.get('file_name', 'Unknown')} - {result.get('mission_id', 'Unknown')}")
                if len(results) > 10:
                    print(f"... and {len(results) - 10} more results")
            else:
                print("🔍 No search results found")
                
        elif args.setup_only:
            # Only set up database infrastructure
            if solution.setup_database_infrastructure():
                print("✅ Database infrastructure setup completed successfully")
            else:
                print("❌ Database infrastructure setup failed")
                return 1
                
        elif args.process_only:
            # Only process metadata (assumes setup is complete)
            result = solution.process_all_datasets()
            if result['failed'] == 0:
                print("✅ Metadata processing completed successfully")
            else:
                print(f"⚠️  Metadata processing completed with {result['failed']} failures")
                
        else:
            # Full solution: setup + process
            print("🔧 Setting up database infrastructure...")
            if not solution.setup_database_infrastructure():
                print("❌ Database infrastructure setup failed")
                return 1
            
            print("📊 Processing metadata...")
            result = solution.process_all_datasets()
            
            if result['failed'] == 0:
                print("🎉 Lab 2 solution completed successfully!")
            else:
                print(f"⚠️  Lab 2 solution completed with {result['failed']} failures")
        
    except Exception as e:
        logger.error(f"❌ Lab 2 solution failed: {e}")
        return 1
    finally:
        if 'solution' in locals():
            solution.close()
    
    return 0

if __name__ == "__main__":
    exit(main())

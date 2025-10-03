#!/usr/bin/env python3
"""
Lab 2 Metadata Search
Search and query interface for metadata stored in VAST Database
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader
from lab2.vast_database_manager import VASTDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetadataSearcher:
    """Handles searching and querying metadata in VAST Database"""
    
    def __init__(self, config_path: str = None, secrets_path: str = None):
        # Default to parent directory for config files
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config.yaml")
        if secrets_path is None:
            secrets_path = str(Path(__file__).parent.parent / "secrets.yaml")
        self.config = ConfigLoader(config_path, secrets_path)
        self.db_manager = VASTDatabaseManager(self.config)
    
    def search_metadata(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata using various criteria"""
        try:
            if not self.db_manager.connect():
                logger.error("❌ Failed to connect to database")
                return []
            
            results = self.db_manager.search_metadata(search_criteria)
            logger.info(f"🔍 Found {len(results)} matching records")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
        finally:
            self.db_manager.close()
    
    def get_metadata_stats(self) -> Dict[str, Any]:
        """Get metadata statistics"""
        try:
            if not self.db_manager.connect():
                logger.error("❌ Failed to connect to database")
                return {}
            
            stats = self.db_manager.get_metadata_stats()
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
        finally:
            self.db_manager.close()
    
    def get_recent_metadata(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metadata records"""
        try:
            if not self.db_manager.connect():
                logger.error("❌ Failed to connect to database")
                return []
            
            results = self.db_manager.get_recent_metadata(limit)
            logger.info(f"📊 Retrieved {len(results)} recent records")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent metadata: {e}")
            return []
        finally:
            self.db_manager.close()
    
    def get_latest_files(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get latest files by timestamp"""
        try:
            if not self.db_manager.connect():
                logger.error("❌ Failed to connect to database")
                return []
            
            results = self.db_manager.get_latest_files(count)
            logger.info(f"📊 Retrieved {len(results)} latest files")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest files: {e}")
            return []
        finally:
            self.db_manager.close()
    
    def display_results(self, results: List[Dict[str, Any]], max_display: int = 10):
        """Display search results in a formatted way"""
        if not results:
            print("📭 No results found")
            return
        
        print(f"\n📊 Found {len(results)} results:")
        print("-" * 80)
        
        for i, result in enumerate(results[:max_display]):
            print(f"\n{i+1}. File: {result.get('file_name', 'N/A')}")
            print(f"   Mission: {result.get('mission_id', 'N/A')}")
            print(f"   Satellite: {result.get('satellite_name', 'N/A')}")
            print(f"   Instrument: {result.get('instrument_type', 'N/A')}")
            print(f"   Target: {result.get('target_object', 'N/A')}")
            print(f"   Observation Date: {result.get('observation_timestamp', 'N/A')}")
            print(f"   File Format: {result.get('file_format', 'N/A')}")
            print(f"   Size: {result.get('file_size_bytes', 'N/A')} bytes")
            print(f"   Dataset: {result.get('dataset_name', 'N/A')}")
            print(f"   Processing Status: {result.get('processing_status', 'N/A')}")
        
        if len(results) > max_display:
            print(f"\n... and {len(results) - max_display} more results")
    
    def display_stats(self, stats: Dict[str, Any]):
        """Display metadata statistics"""
        if not stats:
            print("📊 No statistics available")
            return
        
        print("\n📊 Metadata Statistics:")
        print("-" * 40)
        print(f"Total files: {stats.get('total_files', 'N/A')}")
        
        # Show mission breakdown
        mission_counts = stats.get('mission_counts', {})
        if mission_counts:
            print(f"Missions: {len(mission_counts)}")
            for mission, count in mission_counts.items():
                print(f"  - {mission}: {count} files")
        
        # Show dataset breakdown
        dataset_counts = stats.get('dataset_counts', {})
        if dataset_counts:
            print(f"Datasets: {len(dataset_counts)}")
            for dataset, count in dataset_counts.items():
                print(f"  - {dataset}: {count} files")

def main():
    """Main entry point for metadata search"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Search metadata in VAST Database')
    parser.add_argument('--config', default=None, help='Config file path (default: ../config.yaml)')
    parser.add_argument('--secrets', default=None, help='Secrets file path (default: ../secrets.yaml)')
    parser.add_argument('--pattern', help='Search by file pattern (e.g., swbj1421* for observation ID 1421)')
    parser.add_argument('--file-type', help='Search by file type')
    parser.add_argument('--target', help='Search by target object')
    parser.add_argument('--recent', type=int, help='Show recent N files')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    searcher = MetadataSearcher(args.config, args.secrets)
    
    
    # Show stats first if requested
    if args.stats:
        stats = searcher.get_metadata_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            searcher.display_stats(stats)
        
        # If only stats requested, return here
        if not any([args.pattern, args.file_type, args.target, args.recent]):
            return
    
    if args.recent:
        results = searcher.get_recent_metadata(args.recent)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            searcher.display_results(results)
        return
    
    # Build search criteria
    criteria = {}
    
    if args.pattern:
        criteria['file_name'] = {'type': 'wildcard', 'pattern': args.pattern}
    
    if args.file_type:
        criteria['file_format'] = {'type': 'exact', 'value': args.file_type}
    
    if args.target:
        criteria['target_object'] = {'type': 'wildcard', 'pattern': args.target}
    
    if not criteria:
        print("❌ No search criteria provided. Use --help for options.")
        return
    
    results = searcher.search_metadata(criteria)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        searcher.display_results(results)

if __name__ == "__main__":
    main()

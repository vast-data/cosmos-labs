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
    
    def interactive_search(self):
        """Interactive search interface"""
        print("\n🔍 Interactive Metadata Search")
        print("=" * 50)
        
        while True:
            print("\nSearch Options:")
            print("1. Search by file pattern")
            print("2. Search by observation ID")
            print("3. Search by date range")
            print("4. Search by file type")
            print("5. Show recent files")
            print("6. Show statistics")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                pattern = input("Enter file pattern (e.g., *swbj*): ").strip()
                if pattern:
                    criteria = {
                        'file_name': {'type': 'wildcard', 'pattern': pattern}
                    }
                    results = self.search_metadata(criteria)
                    self.display_results(results)
            
            elif choice == '2':
                obs_id = input("Enter observation ID: ").strip()
                if obs_id:
                    criteria = {
                        'observation_id': {'type': 'exact', 'value': obs_id}
                    }
                    results = self.search_metadata(criteria)
                    self.display_results(results)
            
            elif choice == '3':
                start_date = input("Enter start date (YYYY-MM-DD): ").strip()
                end_date = input("Enter end date (YYYY-MM-DD): ").strip()
                if start_date and end_date:
                    criteria = {
                        'observation_date': {
                            'type': 'comparison',
                            'operator': '>=',
                            'value': start_date
                        }
                    }
                    results = self.search_metadata(criteria)
                    # Filter by end date
                    filtered_results = [
                        r for r in results 
                        if r.get('observation_date', '') <= end_date
                    ]
                    self.display_results(filtered_results)
            
            elif choice == '4':
                file_type = input("Enter file type (e.g., lc, evt): ").strip()
                if file_type:
                    criteria = {
                        'file_type': {'type': 'exact', 'value': file_type}
                    }
                    results = self.search_metadata(criteria)
                    self.display_results(results)
            
            elif choice == '5':
                limit = input("Enter number of recent files (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                results = self.get_recent_metadata(limit)
                self.display_results(results)
            
            elif choice == '6':
                stats = self.get_metadata_stats()
                self.display_stats(stats)
            
            elif choice == '7':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
    
    def display_results(self, results: List[Dict[str, Any]], max_display: int = 10):
        """Display search results in a formatted way"""
        if not results:
            print("📭 No results found")
            return
        
        print(f"\n📊 Found {len(results)} results:")
        print("-" * 80)
        
        for i, result in enumerate(results[:max_display]):
            print(f"\n{i+1}. File: {result.get('file_name', 'N/A')}")
            print(f"   Observation ID: {result.get('observation_id', 'N/A')}")
            print(f"   Date: {result.get('observation_date', 'N/A')}")
            print(f"   Type: {result.get('file_type', 'N/A')}")
            print(f"   Size: {result.get('file_size', 'N/A')} bytes")
            print(f"   S3 Key: {result.get('s3_key', 'N/A')}")
        
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
        print(f"Total size: {stats.get('total_size_gb', 'N/A')} GB")
        print(f"File types: {stats.get('file_types', 'N/A')}")
        print(f"Date range: {stats.get('date_range', 'N/A')}")
        print(f"Datasets: {stats.get('datasets', 'N/A')}")

def main():
    """Main entry point for metadata search"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Search metadata in VAST Database')
    parser.add_argument('--config', default=None, help='Config file path (default: ../config.yaml)')
    parser.add_argument('--secrets', default=None, help='Secrets file path (default: ../secrets.yaml)')
    parser.add_argument('--pattern', help='Search by file pattern')
    parser.add_argument('--obs-id', help='Search by observation ID')
    parser.add_argument('--file-type', help='Search by file type')
    parser.add_argument('--recent', type=int, help='Show recent N files')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--interactive', action='store_true', help='Interactive search mode')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    searcher = MetadataSearcher(args.config, args.secrets)
    
    if args.interactive:
        searcher.interactive_search()
        return
    
    if args.stats:
        stats = searcher.get_metadata_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            searcher.display_stats(stats)
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
    
    if args.obs_id:
        criteria['observation_id'] = {'type': 'exact', 'value': args.obs_id}
    
    if args.file_type:
        criteria['file_type'] = {'type': 'exact', 'value': args.file_type}
    
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

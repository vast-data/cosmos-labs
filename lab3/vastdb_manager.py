#!/usr/bin/env python3
"""
Weather VAST DB Manager
Command-line tool for managing VAST Database operations for weather data
"""

import sys
import argparse
import logging
import urllib3
from pathlib import Path

# Suppress insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Use centralized config files at repo root
sys.path.append(str(Path(__file__).parent.parent))
from lab3.lab3_config import Lab3ConfigLoader
from lab3.weather_database import WeatherVASTDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Manage VAST Database for weather data")
    parser.add_argument("--drop", action="store_true", help="Drop existing weather and air quality tables")
    parser.add_argument("--setup", action="store_true", help="Setup database infrastructure (tables, schema, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Lab3ConfigLoader()
    if not config.validate_config():
        logger.error("❌ Configuration validation failed")
        return 1
    
    # Initialize VAST DB manager
    db = WeatherVASTDB(config)
    
    # Handle drop operation
    if args.drop:
        logger.info("🗑️ Dropping weather and air quality tables...")
        if db.drop_tables():
            logger.info("✅ Successfully dropped tables")
            return 0
        else:
            logger.error("❌ Failed to drop tables")
            return 1
    
    # Handle setup operation
    if args.setup:
        logger.info("🔧 Setting up database infrastructure...")
        if db.setup_infrastructure(dry_run=args.dry_run):
            if args.dry_run:
                logger.info("✅ Dry run completed - infrastructure setup would succeed")
            else:
                logger.info("✅ Successfully set up database infrastructure")
            return 0
        else:
            logger.error("❌ Failed to setup database infrastructure")
            return 1
    
    # If no operation specified, show help
    if not args.drop and not args.setup:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

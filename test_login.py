#!/usr/bin/env python3
"""
Simple test script to verify VAST Management System (VMS) login credentials.
This script tests the connection and basic authentication using the vastpy SDK.
"""

import sys
import logging
from vastpy import VASTClient
from config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vast_login():
    """Test VAST VMS login with provided credentials"""
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = ConfigLoader()
        
        # Validate configuration using strict validation
        if not config.validate_config():
            logger.error("Configuration validation failed - all required values must be explicitly configured")
            return False
        
        # Get VAST configuration
        vast_config = config.get_vast_config()
        logger.info(f"Testing connection to VAST VMS at: {vast_config.get('address')}")
        logger.info(f"Using user: {vast_config.get('user')}")
        
        # Check authentication method
        if vast_config.get('token'):
            logger.info("Using API token authentication")
        elif vast_config.get('password'):
            logger.info("Using password authentication")
        else:
            logger.error("No authentication method specified")
            return False
        
        # Initialize VAST client
        logger.info("Initializing VAST client...")
        client = VASTClient(
            user=vast_config.get('user'),
            password=vast_config.get('password'),
            address=vast_config.get('address'),
            token=vast_config.get('token'),
            tenant_name=vast_config.get('tenant_name'),
            version=vast_config.get('version', 'v1')
        )
        
        # Test basic connection by retrieving views
        logger.info("Testing connection by retrieving views...")
        views = client.views.get()
        
        # If successful, display results
        logger.info("✅ Login successful! Connection to VAST VMS established.")
        logger.info(f"Retrieved {len(views)} views:")
        
        for view in views[:5]:  # Show first 5 views
            logger.info(f"  - {view.get('name', 'Unknown')}: {view.get('path', 'No path')}")
        
        if len(views) > 5:
            logger.info(f"  ... and {len(views) - 5} more views")
        
        # Test additional basic operations
        logger.info("Testing additional operations...")
        
        # Test view policies
        policies = client.viewpolicies.get()
        logger.info(f"✅ Retrieved {len(policies)} view policies")
        
        # Test cluster info
        clusters = client.clusters.get()
        logger.info(f"✅ Retrieved {len(clusters)} cluster(s)")
        
        logger.info("🎉 All basic tests passed! Your VAST VMS connection is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        logger.error("Please check your credentials and network connectivity.")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("VAST VMS Login Test")
    print("=" * 60)
    
    success = test_vast_login()
    
    print("=" * 60)
    if success:
        print("✅ SUCCESS: VAST VMS connection verified")
        print("You can now proceed with the lab exercises.")
    else:
        print("❌ FAILED: VAST VMS connection failed")
        print("Please check your configuration and try again.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

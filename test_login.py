#!/usr/bin/env python3
"""
Simple test script to verify VAST Management System (VMS) login credentials.
This script tests the connection and basic authentication using the vastpy SDK.
"""

import sys
import logging
from vastpy import VASTClient
from config_loader import ConfigLoader

# Try to get vastpy version for debugging
try:
    import vastpy
    vastpy_version = getattr(vastpy, '__version__', 'unknown')
    logger = logging.getLogger(__name__)
    logger.info(f"vastpy version: {vastpy_version}")
except ImportError:
    vastpy_version = 'not installed'

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
        
        # Build client parameters based on available config
        client_params = {
            'user': vast_config.get('user'),
            'password': vast_config.get('password'),
            'address': vast_config.get('address')
        }
        
        # Add optional parameters only if they exist and are supported
        if vast_config.get('token'):
            client_params['token'] = vast_config.get('token')
        
        # Remove None values to avoid passing them to VASTClient
        client_params = {k: v for k, v in client_params.items() if v is not None}
        
        logger.info(f"Initializing VAST client with parameters: {list(client_params.keys())}")
        
        # Try to initialize the client
        try:
            client = VASTClient(**client_params)
        except TypeError as e:
            logger.error(f"VASTClient initialization failed: {e}")
            logger.error("This might be due to an incompatible vastpy version or unsupported parameters")
            logger.error("Try updating vastpy: pip install --upgrade vastpy")
            return False
        
        # Test basic connection by retrieving views
        logger.info("Testing connection by retrieving views...")
        try:
            views = client.views.get()
        except Exception as e:
            logger.error(f"Failed to retrieve views: {e}")
            logger.error("This might indicate a connection or authentication issue")
            return False
        
        # If successful, display results
        logger.info("✅ Login successful! Connection to VAST VMS established.")
        logger.info(f"Retrieved {len(views)} views:")
        
        for view in views[:5]:  # Show first 5 views
            logger.info(f"  - {view.get('name', 'Unknown')}: {view.get('path', 'No path')}")
        
        if len(views) > 5:
            logger.info(f"  ... and {len(views) - 5} more views")
        
        # Test additional basic operations
        logger.info("Testing additional operations...")
        
        try:
            # Test view policies
            policies = client.viewpolicies.get()
            logger.info(f"✅ Retrieved {len(policies)} view policies")
        except Exception as e:
            logger.warning(f"Could not retrieve view policies: {e}")
        
        try:
            # Test cluster info
            clusters = client.clusters.get()
            logger.info(f"✅ Retrieved {len(clusters)} cluster(s)")
        except Exception as e:
            logger.warning(f"Could not retrieve cluster info: {e}")
        
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
    
    # Show vastpy version for debugging
    try:
        import vastpy
        version = getattr(vastpy, '__version__', 'unknown')
        print(f"vastpy version: {version}")
    except ImportError:
        print("vastpy version: not installed")
    print()
    
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

# lab3_solution.py
import time
import logging
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path for centralized config
sys.path.append(str(Path(__file__).parent.parent))

from lab3.lab3_config import Lab3ConfigLoader
from lab3.multi_observatory_storage_manager import MultiObservatoryStorageManager
from lab3.cross_observatory_analytics import CrossObservatoryAnalytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Lab3CompleteSolution:
    """Complete Lab 3 solution for multi-observatory storage and analytics"""
    
    def __init__(self, config: Lab3ConfigLoader, production_mode: bool = False, show_api_calls: bool = False):
        """
        Initialize the Lab 3 complete solution
        
        Args:
            config: Lab3ConfigLoader instance with loaded configuration
            production_mode: If True, allows actual changes. If False, dry-run only.
            show_api_calls: If True, show API calls being made (credentials obfuscated).
        """
        self.config = config
        self.production_mode = production_mode
        self.show_api_calls = show_api_calls
        
        # Initialize components
        self.storage_manager = MultiObservatoryStorageManager(config, production_mode, show_api_calls)
        self.analytics_manager = CrossObservatoryAnalytics(config, show_api_calls)
        
        logger.info("✅ Lab 3 solution initialized successfully")
    
    def setup_multi_observatory_infrastructure(self) -> bool:
        """Set up complete multi-observatory infrastructure"""
        logger.info("🏗️  Setting up multi-observatory infrastructure...")
        
        try:
            # Set up storage infrastructure
            storage_success = self.storage_manager.setup_observatory_storage_views()
            
            # Set up analytics infrastructure
            analytics_success = self.analytics_manager.setup_observatory_tables()
            
            if storage_success and analytics_success:
                logger.info("✅ Multi-observatory infrastructure setup completed successfully")
                return True
            else:
                logger.error("❌ Failed to setup some infrastructure components")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting up multi-observatory infrastructure: {e}")
            return False
    
    def run_cross_observatory_analytics(self) -> bool:
        """Run cross-observatory analytics demonstrations"""
        logger.info("🔬 Running cross-observatory analytics demonstrations...")
        
        try:
            # Find cross-observatory objects
            print("\n" + "="*80)
            print("🌌 CROSS-OBSERVATORY ANALYTICS DEMONSTRATION")
            print("="*80)
            
            cross_objects = self.analytics_manager.find_cross_observatory_objects()
            print(f"\n📡 Cross-Observatory Objects Found: {len(cross_objects)}")
            for obj in cross_objects[:5]:  # Show first 5
                print(f"   • {obj['target_object']}: {obj['swift_observations']} SWIFT, {obj['chandra_observations']} Chandra")
            
            # Generate multi-wavelength light curves for first object
            if cross_objects:
                target = cross_objects[0]['target_object']
                print(f"\n📈 Multi-Wavelength Light Curve for {target}:")
                light_curve = self.analytics_manager.generate_multi_wavelength_light_curves(target)
                for point in light_curve[:3]:  # Show first 3 points
                    print(f"   • {point['observatory']}: {point['observation_time']} - X-ray: {point['xray_flux']}")
            
            # Detect burst follow-up sequences
            print(f"\n🚨 Burst Follow-up Sequences:")
            burst_sequences = self.analytics_manager.detect_burst_followup_sequences()
            print(f"   Found {len(burst_sequences)} burst follow-up sequences")
            for seq in burst_sequences[:3]:  # Show first 3
                print(f"   • {seq['target_object']}: {seq['hours_delay']:.1f}h delay, flux ratio: {seq['flux_ratio']:.2f}")
            
            # Analyze data quality correlation
            print(f"\n📊 Data Quality Analysis:")
            quality_analysis = self.analytics_manager.analyze_data_quality_correlation()
            for obs in quality_analysis:
                print(f"   • {obs['observatory']}: avg={obs['avg_quality']:.2f}, count={obs['observation_count']}")
            
            logger.info("✅ Cross-observatory analytics demonstrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running cross-observatory analytics: {e}")
            return False
    
    def monitor_observatory_systems(self) -> bool:
        """Monitor both observatory storage systems"""
        logger.info("🔍 Monitoring observatory systems...")
        
        try:
            # Monitor storage
            storage_success = self.storage_manager.monitor_observatory_storage()
            
            # Show storage summary
            self.storage_manager.show_observatory_storage_summary()
            
            # Get analytics summary
            analytics_summary = self.analytics_manager.get_analytics_summary()
            print(f"\n📊 Analytics Capabilities:")
            for capability in analytics_summary.get('analytics_capabilities', []):
                print(f"   • {capability}")
            
            if storage_success:
                logger.info("✅ Observatory systems monitoring completed successfully")
                return True
            else:
                logger.error("❌ Some observatory systems monitoring failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error monitoring observatory systems: {e}")
            return False
    
    def run_continuous_monitoring(self, interval_seconds: int = 300):
        """Run continuous monitoring of observatory systems"""
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_seconds}s)...")
        
        try:
            while True:
                logger.info("🔍 Running monitoring cycle...")
                
                # Monitor storage systems
                self.monitor_observatory_systems()
                
                # Run analytics demonstrations
                self.run_cross_observatory_analytics()
                
                logger.info(f"✅ Monitoring cycle completed. Next cycle in {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("🛑 Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in continuous monitoring: {e}")

def main():
    """Main function to run the Lab 3 solution"""
    parser = argparse.ArgumentParser(description='Lab 3: Multi-Observatory Data Storage and Analytics')
    parser.add_argument('--pushtoprod', action='store_true', 
                       help='Enable production mode (makes actual changes)')
    parser.add_argument('--showapicalls', action='store_true',
                       help='Show API calls being made (credentials obfuscated)')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only setup infrastructure, then exit')
    parser.add_argument('--analytics-only', action='store_true',
                       help='Only run analytics demonstrations, then exit')
    parser.add_argument('--monitor-only', action='store_true',
                       help='Only run monitoring, then exit')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring interval in seconds (default: 300)')
    
    args = parser.parse_args()
    
    # Determine production mode
    production_mode = args.pushtoprod
    
    if production_mode:
        print("🚨 PRODUCTION MODE ENABLED - ACTUAL CHANGES WILL BE MADE")
        confirmation = input("Type 'YES' to confirm: ")
        if confirmation != 'YES':
            print("❌ Production mode cancelled")
            return
    else:
        print("🔍 DRY RUN MODE - No actual changes will be made")
        print("💡 Use --pushtoprod to enable production mode")
    
    try:
        # Load configuration
        config = Lab3ConfigLoader()
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Initialize solution
        solution = Lab3CompleteSolution(config, production_mode, args.showapicalls)
        
        # Handle different operation modes
        if args.setup_only:
            # Only setup infrastructure
            logger.info("Setting up multi-observatory infrastructure...")
            if solution.setup_multi_observatory_infrastructure():
                logger.info("✅ Infrastructure setup complete. Exiting.")
                return
            else:
                logger.error("❌ Infrastructure setup failed")
                return
        
        elif args.analytics_only:
            # Only run analytics
            logger.info("Running cross-observatory analytics...")
            if solution.run_cross_observatory_analytics():
                logger.info("✅ Analytics demonstrations complete. Exiting.")
                return
            else:
                logger.error("❌ Analytics demonstrations failed")
                return
        
        elif args.monitor_only:
            # Only run monitoring
            logger.info("Running observatory systems monitoring...")
            if solution.monitor_observatory_systems():
                logger.info("✅ Monitoring complete. Exiting.")
                return
            else:
                logger.error("❌ Monitoring failed")
                return
        
        elif args.continuous:
            # Run continuous monitoring
            logger.info("Starting continuous monitoring...")
            solution.run_continuous_monitoring(args.interval)
            return
        
        else:
            # Normal mode: setup + analytics + monitoring
            logger.info("Running complete Lab 3 solution...")
            
            # Setup infrastructure
            if not solution.setup_multi_observatory_infrastructure():
                logger.error("Failed to setup infrastructure")
                return
            
            # Run analytics demonstrations
            if not solution.run_cross_observatory_analytics():
                logger.error("Failed to run analytics demonstrations")
                return
            
            # Monitor systems
            if not solution.monitor_observatory_systems():
                logger.error("Failed to monitor systems")
                return
            
            logger.info("✅ Lab 3 solution completed successfully")
            
    except KeyboardInterrupt:
        logger.info("🛑 Solution stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()

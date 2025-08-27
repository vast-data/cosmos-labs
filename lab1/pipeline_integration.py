# pipeline_integration.py
import sys
import logging
from vastpy import VASTClient
from lab1_config import Lab1ConfigLoader

logger = logging.getLogger(__name__)

class PipelineStorageChecker:
    """Integration script for Jordan's processing pipeline"""
    
    def __init__(self):
        self.config = Lab1ConfigLoader()
        self.client = VASTClient(**self.config.get_vast_config())
    
    def check_storage_availability(self, required_space_tb: float) -> bool:
        """
        Check if there's enough space in processed data view
        
        Args:
            required_space_tb: Required space in terabytes
            
        Returns:
            True if enough space is available, False otherwise
        """
        try:
            processed_path = self.config.get('storage.processed_data_path', '/cosmos7/processed')
            views = self.client.views.get(path=processed_path)
            if not views:
                logger.error(f"No view found for {processed_path}")
                return False
            
            view = views[0]
            view_id = view['id']
            
            # Get detailed view information
            view_details = self.client.views[view_id].get()
            
            current_usage = view_details.get('size', 0)
            quota = view_details.get('quota', 0)
            
            if quota == 0:
                logger.warning("No quota set for processed data view")
                return True  # Assume unlimited if no quota
            
            available_space = quota - current_usage
            required_space_bytes = required_space_tb * 1024 * 1024 * 1024
            
            utilization_percent = (current_usage / quota) * 100 if quota > 0 else 0
            
            logger.info(f"Processed data view status:")
            logger.info(f"  Current usage: {current_usage / (1024**3):.2f} TB")
            logger.info(f"  Quota: {quota / (1024**3):.2f} TB")
            logger.info(f"  Available: {available_space / (1024**3):.2f} TB")
            logger.info(f"  Utilization: {utilization_percent:.1f}%")
            logger.info(f"  Required: {required_space_tb:.2f} TB")
            
            if available_space >= required_space_bytes:
                logger.info("✓ Sufficient space available for processing")
                return True
            else:
                logger.error("✗ Insufficient space for processing")
                logger.error(f"  Need {required_space_tb:.2f} TB, but only {available_space / (1024**3):.2f} TB available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to check storage availability: {e}")
            return False
    
    def request_storage_expansion(self, additional_space_tb: float) -> bool:
        """
        Request storage expansion for processed data view
        
        Args:
            additional_space_tb: Additional space needed in terabytes
            
        Returns:
            True if expansion was successful, False otherwise
        """
        try:
            processed_path = self.config.get('storage.processed_data_path', '/cosmos7/processed')
            views = self.client.views.get(path=processed_path)
            if not views:
                logger.error(f"No view found for {processed_path}")
                return False
            
            view = views[0]
            view_id = view['id']
            
            # Get current quota
            current_quota = view.get('quota', 0)
            new_quota = current_quota + (additional_space_tb * 1024 * 1024 * 1024)
            
            # Update the view with new quota
            updated_view = self.client.views[view_id].patch(quota=new_quota)
            
            logger.info(f"Successfully expanded quota: {current_quota / (1024**3):.2f} TB → {new_quota / (1024**3):.2f} TB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to expand storage: {e}")
            return False

def main():
    """Main function for pipeline integration"""
    if len(sys.argv) < 2:
        print("Usage: python pipeline_integration.py <required_space_tb>")
        print("Example: python pipeline_integration.py 5.0")
        sys.exit(1)
    
    try:
        required_space = float(sys.argv[1])
    except ValueError:
        print("Error: required_space_tb must be a number")
        sys.exit(1)
    
    checker = PipelineStorageChecker()
    
    # Check if enough space is available
    if checker.check_storage_availability(required_space):
        print("SUCCESS: Sufficient storage space available")
        sys.exit(0)
    else:
        print("ERROR: Insufficient storage space")
        
        # Optionally request expansion
        response = input("Would you like to request storage expansion? (y/n): ")
        if response.lower() == 'y':
            if checker.request_storage_expansion(required_space):
                print("SUCCESS: Storage expansion completed")
                sys.exit(0)
            else:
                print("ERROR: Storage expansion failed")
                sys.exit(1)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main() 
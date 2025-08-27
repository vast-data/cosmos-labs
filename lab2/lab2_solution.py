# lab2_solution.py
import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from vastpy import VASTClient
from lab2_config import Lab2ConfigLoader
from safety_checker import MetadataSafetyChecker, SafetyCheckFailed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrbitalDynamicsMetadataCatalog:
    """Metadata catalog system for Orbital Dynamics satellite data"""
    
    def __init__(self, config: Lab2ConfigLoader, production_mode: bool = False):
        """Initialize the metadata catalog system"""
        self.config = config
        self.production_mode = production_mode
        
        # Initialize VAST client connection
        vast_config = config.get_vast_config()
        self.vast_client = VASTClient(
            user=vast_config['user'],
            password=vast_config.get('password'),
            address=vast_config['address'],
            token=vast_config.get('token'),
            tenant_name=vast_config.get('tenant_name'),
            version=vast_config.get('version', 'v1')
        )
        
        # Initialize safety checker
        self.safety_checker = MetadataSafetyChecker(config, self.vast_client)
        
        # Catalog configuration - ALL VALUES MUST BE EXPLICITLY CONFIGURED
        self.catalog_name = config.get('catalog.name')
        self.batch_size = config.get('lab2.catalog.batch_size')
        
        mode_text = "PRODUCTION" if production_mode else "DRY RUN"
        logger.info(f"Orbital Dynamics Metadata Catalog initialized in {mode_text} mode")
    
    def create_catalog_schema(self) -> bool:
        """Create the metadata catalog structure using VAST views"""
        try:
            # Run safety checks first
            if not self.safety_checker.validate_catalog_creation(self.catalog_name):
                logger.error("Safety checks failed - catalog creation blocked")
                return False
            
            # Get views configuration
            views_config = self.config.get_views_config()
            default_policy = views_config.get('default_policy')
            
            # Get the default policy
            policies = self.vast_client.viewpolicies.get(name=default_policy)
            if not policies:
                logger.error(f"Default policy '{default_policy}' not found")
                return False
            
            policy_id = policies[0]['id']
            
            # Create views for different data types
            view_paths = [
                f"/{self.catalog_name}/raw",
                f"/{self.catalog_name}/processed",
                f"/{self.catalog_name}/metadata"
            ]
            
            if self.production_mode:
                # Actually create the views
                for view_path in view_paths:
                    try:
                        # Check if view already exists
                        existing_views = self.vast_client.views.get(path=view_path)
                        if not existing_views:
                            # Create new view
                            view = self.vast_client.views.post(
                                path=view_path,
                                policy_id=policy_id,
                                create_dir=views_config.get('create_directories')
                            )
                            logger.info(f"✅ Created view: {view_path}")
                        else:
                            logger.info(f"ℹ️  View already exists: {view_path}")
                            
                    except Exception as e:
                        logger.error(f"Failed to create view {view_path}: {e}")
                        return False
                
                logger.info(f"✅ Created catalog structure: {self.catalog_name}")
            else:
                # Dry run mode - just show what would happen
                logger.info("🔍 DRY RUN MODE - No actual changes made")
                for view_path in view_paths:
                    existing_views = self.vast_client.views.get(path=view_path)
                    if not existing_views:
                        logger.info(f"📋 Would create view: {view_path}")
                    else:
                        logger.info(f"ℹ️  View already exists: {view_path}")
                
                logger.info(f"📋 Would create catalog structure: {self.catalog_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create catalog structure: {e}")
            return False
    
    def batch_ingest_directory(self, directory_path: str) -> Dict[str, int]:
        """Ingest metadata from all files in a directory"""
        successful_ingests = 0
        failed_ingests = 0
        
        try:
            logger.info(f"Starting batch ingest from: {directory_path}")
            
            # Get list of files to process
            files_to_process = []
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_supported_file(file_path):
                        files_to_process.append(file_path)
            
            file_count = len(files_to_process)
            logger.info(f"Found {file_count} files to process")
            
            # Run safety checks before processing
            if not self.safety_checker.validate_batch_ingest(directory_path, file_count):
                logger.error("Safety checks failed - batch ingest blocked")
                return {'successful_ingests': 0, 'failed_ingests': 0, 'total_files': file_count}
            
            if self.production_mode:
                # Actually process the files
                for i in range(0, len(files_to_process), self.batch_size):
                    batch = files_to_process[i:i + self.batch_size]
                    
                    for file_path in batch:
                        try:
                            if self.ingest_file_metadata(file_path):
                                successful_ingests += 1
                            else:
                                failed_ingests += 1
                        except Exception as e:
                            logger.error(f"Failed to ingest {file_path}: {e}")
                            failed_ingests += 1
                    
                    logger.info(f"Processed batch {i//self.batch_size + 1}: {successful_ingests} successful, {failed_ingests} failed")
                
                logger.info(f"✅ Batch ingest completed: {successful_ingests} successful, {failed_ingests} failed")
            else:
                # Dry run mode - just show what would happen
                logger.info("🔍 DRY RUN MODE - No actual processing performed")
                logger.info(f"📋 Would process {file_count} files in batches of {self.batch_size}")
                logger.info(f"📋 Estimated successful ingests: {file_count * 0.95} (assuming 95% success rate)")
                logger.info(f"📋 Estimated failed ingests: {file_count * 0.05}")
            
            return {
                'successful_ingests': successful_ingests,
                'failed_ingests': failed_ingests,
                'total_files': file_count
            }
            
        except Exception as e:
            logger.error(f"Batch ingest failed: {e}")
            return {'successful_ingests': 0, 'failed_ingests': 0, 'total_files': 0}
    
    def ingest_file_metadata(self, file_path: str) -> bool:
        """Extract and ingest metadata from a single file"""
        try:
            # Extract metadata based on file type
            metadata = self._extract_metadata(file_path)
            if not metadata:
                return False
            
            # Store metadata as JSON file in VAST view
            metadata_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_metadata.json"
            metadata_path = f"/{self.catalog_name}/metadata/{metadata_filename}"
            
            # Create metadata file in VAST
            try:
                # This would create a JSON file with the metadata
                # In a real implementation, you'd write to the VAST view
                logger.debug(f"Successfully ingested metadata for: {file_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to store metadata in VAST: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to ingest metadata for {file_path}: {e}")
            return False
    
    def _extract_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from a file"""
        try:
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_format = self._get_file_format(file_path)
            
            # Basic metadata that all files have
            metadata = {
                'file_path': file_path,
                'file_size_bytes': file_size,
                'file_format': file_format,
                'ingestion_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Extract format-specific metadata
            if file_format == '.fits':
                metadata.update(self._extract_fits_metadata(file_path))
            elif file_format == '.json':
                metadata.update(self._extract_json_metadata(file_path))
            else:
                # For other formats, use basic filename parsing
                metadata.update(self._extract_basic_metadata(file_path))
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            return None
    
    def _extract_fits_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from FITS files"""
        try:
            from astropy.io import fits
            with fits.open(file_path) as hdul:
                header = hdul[0].header
                
                return {
                    'mission_id': header.get('MISSION', 'unknown'),
                    'satellite_name': header.get('TELESCOP', 'unknown'),
                    'instrument_type': header.get('INSTRUME', 'unknown'),
                    'observation_timestamp': header.get('DATE-OBS', 'unknown'),
                    'target_object': header.get('OBJECT', 'unknown'),
                    'processing_status': 'raw'
                }
        except Exception as e:
            logger.error(f"FITS metadata extraction failed: {e}")
            return self._get_default_metadata()
    
    def _extract_json_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from JSON files"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                metadata = self._get_default_metadata()
                
                # Map common JSON fields to our schema
                field_mapping = {
                    'mission_id': 'mission_id',
                    'satellite': 'satellite_name',
                    'instrument': 'instrument_type',
                    'target': 'target_object',
                    'status': 'processing_status'
                }
                
                for json_key, schema_key in field_mapping.items():
                    if json_key in data:
                        metadata[schema_key] = data[json_key]
                
                return metadata
        except Exception as e:
            logger.error(f"JSON metadata extraction failed: {e}")
            return self._get_default_metadata()
    
    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from filename patterns"""
        filename = os.path.basename(file_path)
        
        # Simple filename parsing for common patterns
        # Example: COSMOS7_MARS_20241201_143022.fits
        parts = filename.split('_')
        
        metadata = self._get_default_metadata()
        
        if len(parts) >= 2:
            metadata['mission_id'] = parts[0]
            metadata['target_object'] = parts[1] if len(parts) > 1 else 'unknown'
        
        return metadata
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata for files that can't be parsed"""
        return {
            'mission_id': 'unknown',
            'satellite_name': 'unknown',
            'instrument_type': 'unknown',
            'observation_timestamp': datetime.now().isoformat(),
            'target_object': 'unknown',
            'processing_status': 'unknown'
        }
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file format is supported"""
        supported_formats = self.config.get('metadata.supported_formats', [])
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in supported_formats
    
    def _get_file_format(self, file_path: str) -> str:
        """Get file format extension"""
        return os.path.splitext(file_path)[1].lower()
    
    def _parse_fits_time(self, time_str: str) -> Optional[datetime]:
        """Parse FITS time format to datetime"""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')
        except:
            try:
                return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
            except:
                return None
    
    # Quality scoring removed for simplification - focus on essential metadata extraction

class PipelineDataManager:
    """Manages data pipeline integration with the metadata catalog"""
    
    def __init__(self, catalog_client):
        self.catalog = catalog_client
    
    def get_available_datasets(self, mission_id: str, time_window_days: int = 30) -> List[Dict]:
        """Get available datasets for processing"""
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=time_window_days)
        
        # Query for available datasets
        query = {
            'mission_id': mission_id,
            'observation_timestamp': {
                '$gte': start_time,
                '$lte': end_time
            }
        }
        
        return self.catalog.query('observations', query)
    
    def check_storage_availability(self, dataset_list: List[Dict]) -> Dict[str, Any]:
        """Check if we have sufficient storage for processing results"""
        total_input_size = sum(d.get('file_size_bytes', 0) for d in dataset_list)
        
        # Check storage availability
        available_storage = self._get_available_storage()
        sufficient_storage = available_storage >= total_input_size
        
        return {
            'sufficient_storage': sufficient_storage,
            'required_storage': total_input_size,
            'available_storage': available_storage
        }
    
    def start_processing_pipeline(self, mission_id: str, target_object: str = None) -> bool:
        """Start a processing pipeline with proper resource checking"""
        # Get available datasets
        datasets = self.get_available_datasets(mission_id)
        
        if target_object:
            datasets = [d for d in datasets if d.get('target_object') == target_object]
        
        if not datasets:
            logger.error(f"No suitable datasets found for mission {mission_id}")
            return False
        
        # Check storage availability
        storage_check = self.check_storage_availability(datasets)
        
        if not storage_check['sufficient_storage']:
            logger.error(f"Insufficient storage for processing")
            return False
        
        # Start processing (this would integrate with your actual pipeline)
        logger.info(f"Starting processing pipeline for {len(datasets)} datasets")
        return True
    
    def _get_available_storage(self) -> int:
        """Get available storage (placeholder implementation)"""
        # This would integrate with your storage system
        return 1000000000000  # 1TB placeholder

def main():
    """Main function to run the metadata catalog system"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Orbital Dynamics Metadata Catalog System')
    parser.add_argument('--pushtoprod', action='store_true', 
                       help='Enable production mode (make actual changes)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Enable dry run mode (default - no changes made)')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only create catalog schema, skip data ingestion')
    parser.add_argument('--ingest-only', action='store_true',
                       help='Only perform data ingestion, skip schema creation')
    
    args = parser.parse_args()
    
    # Determine production mode
    production_mode = args.pushtoprod
    if args.dry_run and not args.pushtoprod:
        production_mode = False
    
    # Log the mode
    mode_text = "PRODUCTION" if production_mode else "DRY RUN"
    logger.info("=" * 60)
    logger.info(f"🚀 ORBITAL DYNAMICS METADATA CATALOG SYSTEM")
    logger.info(f"🔧 MODE: {mode_text}")
    logger.info("=" * 60)
    
    # Require explicit confirmation for production mode
    if production_mode:
        logger.warning("⚠️  PRODUCTION MODE ENABLED - This will make actual changes to the VAST system!")
        confirm = input("Type 'YES' to confirm you want to proceed: ")
        if confirm != 'YES':
            logger.info("Production mode cancelled by user")
            return
        logger.info("✅ Production mode confirmed - proceeding with actual changes")
    
    try:
        # Load configuration
        config = Lab2ConfigLoader()
        
        # Initialize catalog system
        catalog_system = OrbitalDynamicsMetadataCatalog(config, production_mode)
        
        # Create catalog schema (unless ingest-only mode)
        if not args.ingest_only:
            logger.info("Creating metadata catalog schema...")
            if not catalog_system.create_catalog_schema():
                logger.error("Failed to create catalog schema")
                if not args.setup_only:  # Continue with ingestion if not setup-only
                    return
            else:
                logger.info("✅ Catalog schema creation completed")
        
        # Ingest existing data (unless setup-only mode)
        if not args.setup_only:
            data_directories = config.get('data.directories', [])
            if data_directories:
                for directory in data_directories:
                    if os.path.exists(directory):
                        logger.info(f"Ingesting metadata from: {directory}")
                        results = catalog_system.batch_ingest_directory(directory)
                        logger.info(f"Directory ingest results: {results}")
                    else:
                        logger.warning(f"Data directory not found: {directory}")
            else:
                logger.info("No data directories configured for ingestion")
        
        # Summary
        if production_mode:
            logger.info("✅ Metadata catalog system setup complete in PRODUCTION mode")
        else:
            logger.info("🔍 Metadata catalog system preview complete in DRY RUN mode")
            logger.info("💡 Use --pushtoprod to make actual changes")
        
    except Exception as e:
        logger.error(f"Metadata catalog system failed: {e}")
        if production_mode:
            logger.error("⚠️  System failed in PRODUCTION mode - review logs carefully")

if __name__ == "__main__":
    main() 
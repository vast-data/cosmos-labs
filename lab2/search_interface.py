# search_interface.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from vastpy import VASTClient
from config_loader import Lab2ConfigLoader

logger = logging.getLogger(__name__)

class MetadataSearchInterface:
    """Search interface for the metadata catalog"""
    
    def __init__(self, config: Lab2ConfigLoader):
        """Initialize the search interface"""
        self.config = config
        
        # Initialize VAST client connection
        vast_config = config.get_vast_config()
        self.vast_client = VASTClient(
            user=vast_config['user'],
            password=vast_config.get('password'),
            address=vast_config['address'],
            token=vast_config.get('token'),
            tenant_name=vast_config['tenant_name'],
            version=vast_config['version']
        )
        
        self.catalog_name = config.get('catalog.name', 'orbital_dynamics_metadata')
    
    def search_by_mission(self, mission_id: str) -> List[Dict[str, Any]]:
        """Search for all data from a specific mission"""
        try:
            # Search through metadata files in VAST views
            # This is a simplified implementation - in practice you'd need to
            # implement a proper search index or database
            logger.info(f"Searching for mission: {mission_id}")
            
            # For now, return empty list - this would need a proper search implementation
            # using VAST views and metadata files
            return []
            
        except Exception as e:
            logger.error(f"Failed to search by mission {mission_id}: {e}")
            return []
    
    def search_by_time_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Search for data within a specific time range"""
        try:
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            query = f"observation_timestamp BETWEEN '{start_str}' AND '{end_str}'"
            
            results = self.catalog.search(
                catalog_name=self.catalog_name,
                query=query
            )
            
            logger.info(f"Found {len(results)} records between {start_str} and {end_str}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search by time range: {e}")
            return []
    
    def search_by_quality(self, min_quality: float) -> List[Dict[str, Any]]:
        """Search for data with quality score above threshold"""
        try:
            query = f"data_quality_score >= {min_quality}"
            
            results = self.catalog.search(
                catalog_name=self.catalog_name,
                query=query
            )
            
            logger.info(f"Found {len(results)} records with quality >= {min_quality}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search by quality: {e}")
            return []
    
    def search_by_target(self, target_object: str) -> List[Dict[str, Any]]:
        """Search for data of a specific target object"""
        try:
            query = f"target_object = '{target_object}'"
            
            results = self.catalog.search(
                catalog_name=self.catalog_name,
                query=query
            )
            
            logger.info(f"Found {len(results)} records for target: {target_object}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search by target {target_object}: {e}")
            return []
    
    def search_by_calibration_status(self, status: str) -> List[Dict[str, Any]]:
        """Search for data with specific calibration status"""
        try:
            query = f"calibration_status = '{status}'"
            
            results = self.catalog.search(
                catalog_name=self.catalog_name,
                query=query
            )
            
            logger.info(f"Found {len(results)} records with calibration status: {status}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search by calibration status {status}: {e}")
            return []
    
    def search_by_processing_status(self, status: str) -> List[Dict[str, Any]]:
        """Search for data with specific processing status"""
        try:
            query = f"processing_status = '{status}'"
            
            results = self.catalog.search(
                catalog_name=self.catalog_name,
                query=query
            )
            
            logger.info(f"Found {len(results)} records with processing status: {status}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search by processing status {status}: {e}")
            return []
    
    def advanced_search(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced search with multiple criteria"""
        try:
            conditions = []
            
            # Mission-based filtering
            if 'mission_id' in criteria:
                conditions.append(f"mission_id = '{criteria['mission_id']}'")
            
            # Time-based filtering
            if 'start_date' in criteria and 'end_date' in criteria:
                start_str = criteria['start_date'].strftime('%Y-%m-%d %H:%M:%S')
                end_str = criteria['end_date'].strftime('%Y-%m-%d %H:%M:%S')
                conditions.append(f"observation_timestamp BETWEEN '{start_str}' AND '{end_str}'")
            
            # Quality-based filtering
            if 'min_quality' in criteria:
                conditions.append(f"data_quality_score >= {criteria['min_quality']}")
            
            # Status-based filtering
            if 'processing_status' in criteria:
                conditions.append(f"processing_status = '{criteria['processing_status']}'")
            
            if 'calibration_status' in criteria:
                conditions.append(f"calibration_status = '{criteria['calibration_status']}'")
            
            # Target-based filtering
            if 'target_object' in criteria:
                conditions.append(f"target_object = '{criteria['target_object']}'")
            
            # Build final query
            if conditions:
                query = " AND ".join(conditions)
            else:
                query = "*"  # Return all records
            
            results = self.catalog.search(
                catalog_name=self.catalog_name,
                query=query
            )
            
            logger.info(f"Advanced search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return []
    
    def find_mars_rover_data(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Find Mars rover data from the last N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            criteria = {
                'mission_id': 'MARS_ROVER',
                'start_date': start_date,
                'end_date': end_date
            }
            
            return self.advanced_search(criteria)
            
        except Exception as e:
            logger.error(f"Failed to find Mars rover data: {e}")
            return []
    
    def find_high_quality_observations(self, min_quality: float = 0.8) -> List[Dict[str, Any]]:
        """Find high-quality observations above threshold"""
        return self.search_by_quality(min_quality)
    
    def get_mission_summary(self, mission_id: str) -> Dict[str, Any]:
        """Get summary statistics for a mission"""
        try:
            mission_data = self.search_by_mission(mission_id)
            
            if not mission_data:
                return {
                    'mission_id': mission_id,
                    'total_observations': 0,
                    'total_data_size': 0,
                    'avg_quality_score': 0.0,
                    'calibration_complete': 0
                }
            
            total_size = sum(d.get('file_size_bytes', 0) for d in mission_data)
            quality_scores = [d.get('data_quality_score', 0) for d in mission_data if d.get('data_quality_score')]
            calibration_complete = sum(1 for d in mission_data if d.get('calibration_status') == 'COMPLETE')
            
            return {
                'mission_id': mission_id,
                'total_observations': len(mission_data),
                'total_data_size': total_size,
                'avg_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
                'calibration_complete': calibration_complete
            }
            
        except Exception as e:
            logger.error(f"Failed to get mission summary for {mission_id}: {e}")
            return {} 
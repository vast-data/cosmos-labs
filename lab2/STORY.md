# Lab 2: The Metadata Infrastructure Project

## The Situation

It's Monday morning, and Dr. Alex Sterling is already in her office reviewing the quarterly infrastructure assessment when Maya Chen knocks on her door. The look on Maya's face tells Alex everything she needs to know - they've got another problem brewing.

"Alex, we need to talk about our data organization strategy," Maya says, dropping into the chair across from Alex's desk. "I've been looking at our current file structure, and it's not going to scale with COSMOS-7."

Alex leans back in her chair. "What are we looking at?"

"Right now, we're managing about 5TB of data daily across our existing missions. Each mission has its own directory structure, its own naming conventions, and its own metadata files. It's manageable because we're only dealing with a few hundred files per day. But COSMOS-7 is going to generate 50TB daily - that's ten times our current volume."

Alex nods slowly. "And you're thinking we need to fix this before it becomes a crisis."

"Exactly. We're three months out from launch. If we don't get our metadata house in order now, we'll be spending more time finding data than analyzing it."

## The Technical Challenge

The team needs to build a VAST Database-based metadata system that can handle current and future data volumes. The key technical requirements are:

### Primary Objectives:
1. **Design Comprehensive Metadata Schema** - Create a scalable metadata structure for satellite observation data
2. **Build Automated Ingest Workflows** - Implement systems that extract and populate metadata from existing and new data files
3. **Create Search and Query Interfaces** - Develop tools for finding datasets by various criteria
4. **Establish Scalable Data Organization** - Build a system that can handle current and future data volumes

## The Implementation Plan

Sam presents his plan to Alex. "Here's what I'm thinking," he says, drawing on the whiteboard. "We build this in phases over the next eight weeks."

**Phase 1 (Weeks 1-2): Schema Design and Core Infrastructure**
- Design the metadata schema for satellite observations
- Set up the VAST Database system using vastdb
- Create the basic ingest workflows

**Phase 2 (Weeks 3-4): Metadata Extraction and Population**
- Build automated processes to extract metadata from existing files
- Populate the catalog with current data
- Validate data integrity during migration

**Phase 3 (Weeks 5-6): Query Interfaces and Integration**
- Create search and filtering capabilities
- Build APIs for programmatic access
- Integrate with existing tools and pipelines

**Phase 4 (Weeks 7-8): Testing and Optimization**
- Load test with simulated COSMOS-7 data volumes
- Performance tuning and optimization
- Final validation and go-live preparation

Alex studies the timeline. "This gives us a week buffer before launch. What's our biggest risk?"

"Schema design and data validation," Sam says immediately. "We need to ensure our metadata extraction correctly interprets all the different file formats and naming conventions we have. I'm thinking we run everything in parallel - keep the old system running while we build the new one, then switch over once we're confident the catalog is accurately indexing everything."

## Technical Implementation Details

### 1. VAST Catalog Schema Design

The core of the system is a comprehensive metadata schema that captures all relevant information about satellite observations:

```python
# Core metadata schema for satellite observations
observation_schema = {
    'mission_id': 'string',           # Unique mission identifier
    'satellite_name': 'string',       # Name of the satellite
    'instrument_type': 'string',      # Type of instrument used
    'observation_timestamp': 'datetime', # When observation was taken
    'target_object': 'string',        # Astronomical target
    'data_quality_score': 'float',    # Quality metric (0.0-1.0)
    'calibration_status': 'string',   # Calibration state
    'file_path': 'string',            # Path to data file
    'file_size': 'int64',             # File size in bytes
    'processing_status': 'string',    # Raw/Processed/Archived
    'version': 'string',              # Data version
    'mission_specific': 'json'        # Flexible field for mission-specific data
}

# Relationship schema for linked datasets
dataset_relationship = {
    'parent_dataset_id': 'string',    # Parent observation
    'child_dataset_id': 'string',     # Related dataset
    'relationship_type': 'string',    # Raw->Processed, Calibration, etc.
    'relationship_metadata': 'json'   # Additional relationship info
}
```

### 2. Automated Metadata Extraction Workflows

The system uses Python scripts with the `vastdb_sdk` to automatically extract metadata from various file types. These workflows handle the entire lifecycle of metadata management:

**Initial Bulk Ingest Workflow:**
- Scans existing file systems to discover all satellite data files
- Extracts metadata from file headers, names, and directory structures
- Populates the catalog with historical data (one-time process)
- Validates metadata completeness and flags incomplete records

**Continuous Monitoring Workflow:**
- Watches designated directories for new files (real-time file system monitoring)
- Automatically triggers metadata extraction when new files arrive
- Ensures COSMOS-7 data gets cataloged immediately upon arrival
- Maintains catalog freshness without manual intervention

**Metadata Validation Workflow:**
- Runs scheduled checks to ensure metadata quality and consistency
- Identifies files with missing or corrupted metadata
- Triggers re-extraction for problematic files
- Maintains data integrity across the catalog

```python
import vastdb_sdk
import os
import json
from datetime import datetime
from pathlib import Path

class MetadataExtractor:
    def __init__(self, catalog_client):
        self.client = catalog_client
        self.supported_formats = ['.fits', '.hdf5', '.netcdf', '.csv']
    
    def extract_from_file(self, file_path):
        """Extract metadata from a single file"""
        file_info = self._get_file_info(file_path)
        
        if file_path.suffix == '.fits':
            return self._extract_fits_metadata(file_path, file_info)
        elif file_path.suffix == '.hdf5':
            return self._extract_hdf5_metadata(file_path, file_info)
        # Add other format handlers
        
        return None
    
    def _get_file_info(self, file_path):
        """Get basic file information"""
        stat = file_path.stat()
        return {
            'file_path': str(file_path),
            'file_size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime)
        }
    
    def _extract_fits_metadata(self, file_path, file_info):
        """Extract metadata from FITS files"""
        try:
            from astropy.io import fits
            with fits.open(file_path) as hdul:
                header = hdul[0].header
                
                return {
                    **file_info,
                    'mission_id': header.get('MISSION', 'unknown'),
                    'satellite_name': header.get('TELESCOP', 'unknown'),
                    'instrument_type': header.get('INSTRUME', 'unknown'),
                    'observation_timestamp': self._parse_fits_time(header.get('DATE-OBS')),
                    'target_object': header.get('OBJECT', 'unknown'),
                    'data_quality_score': self._calculate_quality_score(header),
                    'calibration_status': header.get('CALIB', 'unknown'),
                    'processing_status': 'raw',
                    'version': header.get('VERSION', '1.0')
                }
        except Exception as e:
            print(f"Error extracting FITS metadata from {file_path}: {e}")
            return None
    
    def _parse_fits_time(self, time_str):
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
    
    def _calculate_quality_score(self, header):
        """Calculate quality score from header information"""
        # Implement quality scoring algorithm based on header values
        # This is a simplified example
        score = 1.0
        
        # Check for required keywords
        required_keywords = ['MISSION', 'TELESCOP', 'INSTRUME', 'DATE-OBS']
        for keyword in required_keywords:
            if not header.get(keyword):
                score -= 0.2
        
        # Check for calibration status
        if header.get('CALIB') == 'COMPLETE':
            score += 0.1
        
        return max(0.0, min(1.0, score))

class CatalogIngestManager:
    def __init__(self, catalog_client):
        self.client = catalog_client
        self.extractor = MetadataExtractor(catalog_client)
    
    def ingest_directory(self, directory_path, recursive=True):
        """Ingest all files in a directory"""
        path = Path(directory_path)
        files = list(path.rglob('*')) if recursive else list(path.iterdir())
        files = [f for f in files if f.is_file() and f.suffix in self.extractor.supported_formats]
        
        successful = 0
        failed = 0
        
        for file_path in files:
            try:
                metadata = self.extractor.extract_from_file(file_path)
                if metadata:
                    self.client.insert_record('observations', metadata)
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Failed to ingest {file_path}: {e}")
                failed += 1
        
        return successful, failed
    
    def watch_directory(self, directory_path):
        """Set up file system monitoring for new files"""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class NewFileHandler(FileSystemEventHandler):
            def __init__(self, ingest_manager):
                self.ingest_manager = ingest_manager
            
            def on_created(self, event):
                if not event.is_directory:
                    self.ingest_manager.ingest_single_file(event.src_path)
        
        handler = NewFileHandler(self)
        observer = Observer()
        observer.schedule(handler, directory_path, recursive=True)
        observer.start()
        return observer
```

### 3. Query Interface Development

The system provides multiple ways to search and filter data. These interfaces enable researchers and pipelines to efficiently locate and access satellite data:

**Interactive Search Interface:**
- Web-based dashboard for manual data discovery
- Advanced filtering by mission, time range, quality, and target object
- Visual representation of data relationships and processing status
- Export capabilities for selected datasets

**Programmatic API Interface:**
- RESTful API endpoints for integration with existing tools
- Query language support for complex search criteria
- Batch operations for processing multiple datasets
- Real-time updates on data availability and status

**Pipeline Integration Interface:**
- Direct integration with Jordan's data processing workflows
- Pre-flight checks for data availability and quality
- Automatic resource allocation based on dataset requirements
- Status monitoring and progress tracking during processing

```python
class CatalogQueryInterface:
    def __init__(self, catalog_client):
        self.client = catalog_client
    
    def search_by_time_range(self, start_time, end_time, mission_id=None):
        """Search for observations within a time range"""
        query = {
            'observation_timestamp': {
                '$gte': start_time,
                '$lte': end_time
            }
        }
        
        if mission_id:
            query['mission_id'] = mission_id
        
        return self.client.query('observations', query)
    
    def search_by_quality(self, min_quality_score, mission_id=None):
        """Search for high-quality observations"""
        query = {
            'data_quality_score': {'$gte': min_quality_score}
        }
        
        if mission_id:
            query['mission_id'] = mission_id
        
        return self.client.query('observations', query)
    
    def search_by_target(self, target_object, mission_id=None):
        """Search for observations of specific targets"""
        query = {'target_object': target_object}
        
        if mission_id:
            query['mission_id'] = mission_id
        
        return self.client.query('observations', query)
    
    def get_mission_summary(self, mission_id):
        """Get summary statistics for a mission"""
        pipeline = [
            {'$match': {'mission_id': mission_id}},
            {'$group': {
                '_id': None,
                'total_observations': {'$sum': 1},
                'total_data_size': {'$sum': '$file_size'},
                'avg_quality_score': {'$avg': '$data_quality_score'},
                'calibration_complete': {
                    '$sum': {'$cond': [{'$eq': ['$calibration_status', 'COMPLETE']}, 1, 0]}
                }
            }}
        ]
        
        return self.client.aggregate('observations', pipeline)
    
    def find_related_datasets(self, dataset_id):
        """Find datasets related to a specific observation"""
        relationships = self.client.query('dataset_relationships', {
            '$or': [
                {'parent_dataset_id': dataset_id},
                {'child_dataset_id': dataset_id}
            ]
        })
        
        related_ids = set()
        for rel in relationships:
            related_ids.add(rel['parent_dataset_id'])
            related_ids.add(rel['child_dataset_id'])
        
        related_ids.discard(dataset_id)
        
        return self.client.query('observations', {
            '_id': {'$in': list(related_ids)}
        })
```

### 4. Integration with Existing Pipelines

Jordan's processing pipeline can now query the catalog before starting analysis. This integration transforms how data processing workflows operate:

**Pre-Processing Workflow:**
- Pipeline queries catalog for available datasets matching criteria
- Validates data quality and completeness before processing
- Checks storage availability for output results
- Ensures all required data is accessible before starting analysis

**Processing Execution Workflow:**
- Pipeline receives validated dataset list with metadata
- Processes data with confidence in source quality
- Updates catalog with processing status and results
- Maintains audit trail of all processing operations

**Post-Processing Workflow:**
- Results automatically cataloged with processing metadata
- Quality metrics updated based on processing outcomes
- Relationships established between input and output datasets
- Enables traceability from raw data to final results

```python
class PipelineDataManager:
    def __init__(self, catalog_client):
        self.catalog = CatalogQueryInterface(catalog_client)
    
    def get_available_datasets(self, mission_id, min_quality=0.8, time_window_days=30):
        """Get available datasets for processing"""
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=time_window_days)
        
        datasets = self.catalog.search_by_time_range(
            start_time, end_time, mission_id
        )
        
        # Filter by quality
        high_quality_datasets = [
            d for d in datasets 
            if d.get('data_quality_score', 0) >= min_quality
        ]
        
        return high_quality_datasets
    
    def check_storage_availability(self, dataset_list):
        """Check if we have sufficient storage for processing results"""
        total_input_size = sum(d['file_size'] for d in dataset_list)
        estimated_output_size = total_input_size * 2.5  # Rough estimate
        
        # Check available storage (this would integrate with your storage system)
        available_storage = self._get_available_storage()
        
        return {
            'sufficient_storage': available_storage >= estimated_output_size,
            'required_storage': estimated_output_size,
            'available_storage': available_storage
        }
    
    def start_processing_pipeline(self, mission_id, target_object=None):
        """Start a processing pipeline with proper resource checking"""
        # Get available datasets
        datasets = self.get_available_datasets(mission_id)
        
        if target_object:
            datasets = [d for d in datasets if d['target_object'] == target_object]
        
        if not datasets:
            raise ValueError(f"No suitable datasets found for mission {mission_id}")
        
        # Check storage availability
        storage_check = self.check_storage_availability(datasets)
        
        if not storage_check['sufficient_storage']:
            raise ResourceError(
                f"Insufficient storage. Need {storage_check['required_storage']} bytes, "
                f"have {storage_check['available_storage']} bytes"
            )
        
        # Start processing
        return self._execute_processing_pipeline(datasets)
```

## Success Criteria and Business Impact

### Core Success Metrics
The system succeeds when it can:
- **Ingest**: Catalog existing files and automatically index new ones
- **Query**: Find datasets by mission, time, quality, and target criteria  
- **Integrate**: Enable pipelines to validate data and track processing status

### Business Value
- **Efficiency**: Reduce data discovery from 2 hours to 2 minutes
- **Automation**: Eliminate 20+ hours/week of manual metadata management
- **Reliability**: Prevent processing failures through pre-flight validation
- **Scalability**: Handle 10x data volume without manual intervention

## Next Steps

The team will implement this system in phases, with each phase delivering working functionality that can be tested and validated before moving to the next phase. The key is starting early enough to ensure the system is ready before COSMOS-7 launches.

*"The best time to fix your data organization is before you need to fix your data organization."* - Sam Rodriguez, DevOps Engineer 
# Lab 2: Proactive Metadata Infrastructure Planning

## Overview

This lab demonstrates how to build a metadata system using the VAST Management System (VMS) and the official vastpy Python SDK. You'll create a storage organization system that can handle current and future data volumes, enabling researchers to quickly locate datasets by mission parameters, timestamps, and data quality metrics.

**Note:** This lab focuses on the infrastructure and workflow design.

## Learning Objectives

By the end of this lab, you will be able to:
- Design and implement a comprehensive metadata schema for satellite observations
- Build automated workflows for extracting metadata from various file formats
- Create search and query interfaces for efficient data discovery
- Integrate metadata systems with existing data processing pipelines

## Files

- **`lab2_solution.py`** - Main metadata catalog system with extraction and pipeline integration
- **`search_interface.py`** - Search and query interface for the catalog
- **`config_loader.py`** - Lab-specific configuration loader (inherits from centralized config)
- **`test_solution.py`** - Unit tests for the solution
- **`requirements.txt`** - Python dependencies

**Note:** Configuration files are centralized in the root directory. Copy `../config.yaml.example` to `../config.yaml` and `../secrets.yaml.example` to `../secrets.yaml`, then edit them with your settings.
**Note:** `test_login.py` is now available in the root directory for testing VAST VMS connectivity.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure the Solution
```bash
# Edit configuration files
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml

# Update config.yaml with your VAST connection settings (non-sensitive)
# Update secrets.yaml with your authentication credentials (sensitive)
```

### 3. Test Your Connection
```bash
# First, test your VAST VMS connection
python test_login.py

# If successful, proceed with the lab
```

### 4. Run the Solution
```bash
# DRY RUN MODE (default - no changes made)
python lab2_solution.py

# PRODUCTION MODE (actual changes - requires confirmation)
python lab2_solution.py --pushtoprod

# Setup only (create schema, skip ingestion)
python lab2_solution.py --setup-only

# Ingest only (skip schema creation)
python lab2_solution.py --ingest-only

# Test search functionality
python search_interface.py

# Run unit tests
python test_solution.py
```

## Core Workflows

### 1. Metadata Ingestion Workflow
The system automatically extracts and catalogs metadata from satellite data files:

- **Bulk Ingest**: Scan existing directories to catalog historical data
- **Format Support**: FITS, JSON, and basic filename parsing
- **Format Support**: FITS, JSON, and basic filename parsing

### 2. Search and Query Workflow
Researchers can find data through multiple interfaces:

- **Interactive Search**: Web-based dashboard for manual discovery
- **Programmatic API**: Integration with existing tools and scripts
- **Advanced Filtering**: Search by mission, time, quality, and target

### 3. Pipeline Integration Workflow
Data processing pipelines can query the catalog before starting analysis:

- **Pre-flight Checks**: Validate data availability
- **Resource Validation**: Ensure sufficient storage for processing
- **Simple Queries**: Basic filtering by mission and time

## Configuration

### Main Configuration (`config.yaml`)
```yaml
# VAST Connection Settings (non-sensitive)
vast:
  user: admin
  address: "localhost"
  # Note: password, token, and tenant_name are stored in secrets.yaml

# VAST Catalog Settings
catalog:
  name: "orbital_dynamics_metadata"
  port: 8080
  batch_size: 1000

# Data Directories
data:
  directories:
    - "/cosmos7/raw"
    - "/cosmos7/processed"
    - "/mars_rover/data"
```

### Secrets Configuration (`secrets.yaml`)
```yaml
# VAST Connection Secrets
vast_password: "your_vast_password_here"
vast_token: ""  # Optional: API token for Vast 5.3+
vast_tenant_name: ""  # Optional: Tenant name for Vast 5.3+
vast_api_version: "v1"  # Optional: API version
```

## Safety System

Lab 2 includes a comprehensive safety system to prevent accidental changes to the VAST system:

### **Dry Run Mode (Default)**
- **No actual changes** are made to the VAST system
- **Preview operations** before execution
- **Safety checks** run automatically
- **Estimated results** are shown

### **Production Mode**
- **Explicit confirmation** required (`--pushtoprod`)
- **Actual changes** made to VAST views and storage
- **Comprehensive safety checks** before any operation
- **User must type 'YES'** to confirm

### **Safety Checks Performed**
1. **View Policy Validation** - Check required policies exist
2. **Storage Availability** - Ensure sufficient space
3. **Catalog Name Conflicts** - Prevent duplicate catalogs
4. **Directory Access** - Verify read permissions
5. **File Count Limits** - Prevent overwhelming operations
6. **Storage Impact Assessment** - Estimate resource usage

## Usage Examples

### Basic Catalog Operations
```python
from lab2_solution import OrbitalDynamicsMetadataCatalog

# Initialize the catalog system (dry run mode by default)
catalog_system = OrbitalDynamicsMetadataCatalog(config)

# For production mode, use production_mode=True
catalog_system = OrbitalDynamicsMetadataCatalog(config, production_mode=True)

# Create the catalog schema
catalog_system.create_catalog_schema()

# Ingest metadata from directories
results = catalog_system.batch_ingest_directory('/cosmos7/raw')
print(f"Ingested {results['successful_ingests']} files")
```

### Search Operations
```python
from search_interface import MetadataSearchInterface

# Initialize search interface
search_interface = MetadataSearchInterface(config)

# Find Mars rover data from last 30 days
mars_data = search_interface.find_mars_rover_data(30)

# Find high-quality observations
high_quality = search_interface.find_high_quality_observations()

# Advanced search with multiple criteria
criteria = {
    'mission_id': 'COSMOS7',
    'min_quality': 0.8,
    'processing_status': 'PROCESSED'
}
results = search_interface.advanced_search(criteria)
```

### Pipeline Integration
```python
from lab2_solution import PipelineDataManager

# Initialize pipeline manager
pipeline_manager = PipelineDataManager(catalog_client)

# Get available datasets for processing
datasets = pipeline_manager.get_available_datasets('COSMOS7', min_quality=0.8)

# Check storage availability
storage_check = pipeline_manager.check_storage_availability(datasets)

# Start processing if resources are available
if storage_check['sufficient_storage']:
    pipeline_manager.start_processing_pipeline('COSMOS7')
```

## Success Criteria

The system succeeds when it can:
- **Ingest**: Catalog existing files and automatically index new ones
- **Query**: Find datasets by mission, time, quality, and target criteria  
- **Integrate**: Enable pipelines to validate data and track processing status

## Testing

```bash
# Run all unit tests
python test_solution.py

# Run specific test classes
python -m unittest test_solution.TestMetadataExtractor
python -m unittest test_solution.TestSearchInterface
```

## Troubleshooting

### Common Issues

1. **Catalog Connection Failed**
   - Verify VAST Catalog service is running
   - Check credentials in `secrets.yaml`
   - Ensure network connectivity

2. **Metadata Extraction Failed**
   - Check file permissions and accessibility
   - Verify file format is supported
   - Review extraction logs

3. **Search Performance Issues**
   - Check catalog indexing status
   - Verify query complexity
   - Monitor catalog performance

## Next Steps

After completing this lab, consider:
1. **Web Interface**: Build a user-friendly search dashboard
2. **Real-time Ingestion**: Set up automated monitoring for new data
3. **Advanced Analytics**: Add data quality trends and usage patterns
4. **Integration**: Connect with external astronomical databases 
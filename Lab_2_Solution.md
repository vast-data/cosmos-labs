# Lab 2 Solution: The Metadata Infrastructure Project

## Overview

This solution demonstrates how to use `vastpy` for storage management and `vastdb` for metadata catalog functionality to create a comprehensive metadata system for Orbital Dynamics' satellite data. The complete implementation is organized in the `lab2/` folder.

## Solution Structure

All solution files are located in the `lab2/` folder:

```
lab2/
├── lab2_solution.py          # Main metadata catalog system
├── search_interface.py       # Search and query interface for the catalog
├── config_loader.py          # Lab-specific configuration loader (inherits from centralized config)
├── test_solution.py          # Unit tests
└── requirements.txt          # Python dependencies
```

**Note:** Configuration files (`config.yaml` and `secrets.yaml`) are now centralized in the root directory for all labs.

## Quick Start

### 1. Navigate to Lab 2 Directory
```bash
cd lab2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Solution
```bash
# Edit configuration files in the root directory
# ../config.yaml - Main configuration for all labs
# ../secrets.yaml - Sensitive data (passwords, API keys)
```

### 4. Run the Solution
```bash
# Create catalog schema and ingest existing data
python lab2_solution.py

# Test search functionality
python search_interface.py

# Run unit tests
python test_solution.py
```

## Key Features

### ✅ Comprehensive Metadata Schema
- Mission identification and parameters
- Observation timestamps and durations
- Data quality metrics and calibration status
- File locations and storage paths
- Processing status and version information

### ✅ Multi-Format Metadata Extraction
- **FITS files** - Astronomical data format (using astropy)
- **HDF5 files** - Processed data format (using h5py)
- **JSON files** - Metadata and configuration
- **CSV files** - Tabular data
- **Text files** - Logs and documentation

### ✅ Advanced Search Capabilities
- Time-based queries (date ranges, observation periods)
- Mission-specific filtering (satellite, instrument, target)
- Quality-based filtering (signal-to-noise ratios, calibration status)
- Status-based queries (processed, raw, archived)
- Multi-criteria advanced search

### ✅ VAST Database Integration
- Uses `vastdb` for metadata catalog storage and querying
- Creates structured metadata schema for satellite observations
- Leverages VAST's database capabilities for fast searches
- Integrates with existing VAST management workflows

### ✅ Real-time Query Performance
- Sub-5-second query response times
- Indexed fields for fast searches
- Batch processing for large datasets
- Caching for frequently accessed data

## Configuration

### Main Configuration (`../config.yaml`)
```yaml
# Lab 2 specific settings
lab2:
  catalog:
    batch_size: 1000
    max_concurrent_extractions: 10
    extraction_timeout_seconds: 60
  
  search:
    default_limit: 100
    max_limit: 1000
    enable_fuzzy_search: true

# VAST Connection Settings
vast:
  user: admin
  address: "localhost"

# Catalog settings
catalog:
  name: "orbital_dynamics_metadata"
  port: 8080
  batch_size: 1000
  timeout_seconds: 30
  max_retries: 3

# Metadata extraction settings
metadata:
  supported_formats:
    - ".fits"
    - ".hdf5"
    - ".json"
    - ".csv"
    - ".txt"
  quality_threshold: 0.7

# VAST View Management
views:
  default_policy: "default"
  create_directories: true
  protocols: ["NFS", "SMB"]

# VAST Database Settings (for metadata catalog)
vastdb:
  host: "localhost"
  port: 5432
  database: "orbital_dynamics_metadata"
  schema: "satellite_observations"
```

### Secrets Configuration (`../secrets.yaml`)
```yaml
# VAST Connection Secrets
vast_password: "your_vast_password_here"

# Note: vastpy 0.3.17 only supports basic authentication
# vast_token: ""  # Not supported in vastpy 0.3.17
# vast_tenant_name: ""  # Not supported in vastpy 0.3.17
# vast_api_version: "v1"  # Not supported in vastpy 0.3.17
```

## Implementation Details

### Metadata Catalog System
The solution implements a comprehensive metadata management system by:
1. **Schema Design** - Defines structured metadata for satellite observations
2. **Automated Extraction** - Extracts metadata from various file formats automatically
3. **VAST Views Integration** - Uses VAST views for data organization and access
4. **Search Interface** - Provides powerful querying capabilities for finding datasets

### VAST Integration
Uses both `vastpy` and `vastdb`:
- **vastpy**: Create and manage VAST views for data organization
- **vastdb**: Store and query metadata in VAST database
- Organize data in a hierarchical structure with rich metadata
- Provide fast search capabilities across all metadata fields
- Integrate with existing VAST management workflows

### Metadata Extraction Workflows
The system handles metadata extraction through:
1. **Format-Specific Extractors** - Specialized handlers for FITS, HDF5, JSON, CSV, and text files
2. **Batch Processing** - Efficient processing of large numbers of files
3. **Quality Validation** - Ensures metadata completeness and accuracy
4. **Real-time Monitoring** - Watches for new files and extracts metadata automatically

## Testing

Run the comprehensive test suite to verify all functionality:

```bash
python test_solution.py
```

## Success Metrics

- **Comprehensive Coverage** - All satellite data files properly cataloged with metadata
- **Fast Search Performance** - Sub-5-second response times for complex queries
- **Automated Management** - Metadata extraction and catalog updates happen automatically
- **Scalable Architecture** - System can handle current and future data volumes
- **Integration Success** - Seamless integration with existing VAST infrastructure 
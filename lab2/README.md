# Lab 2: Metadata Infrastructure Project

## 🎯 Overview

A complete metadata infrastructure system that processes Swift satellite data and provides search capabilities using VAST Database and S3 storage. This solution demonstrates how to use `vastpy` for storage management and `vastdb` for metadata catalog functionality to create a comprehensive metadata system for Orbital Dynamics' satellite data.

**Key Features:**
- Creates VAST views using `vastpy` for raw data and metadata storage
- Uploads Swift datasets to S3 using `boto3`
- Extracts comprehensive metadata from Swift files (FITS, lightcurves, etc.)
- Stores metadata in VAST Database with duplicate detection
- Provides efficient search and query capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Swift Data    │    │  vastpy creates  │    │  Raw Data       │
│   (Local Files) │───▶│  views           │───▶│  View (S3)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  boto3 uploads   │    │  Metadata       │
                       │  files to S3     │    │  Extractor      │
                       └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  VAST Database  │
                                                │  (vastdb SDK)   │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Search & Query │
                                                │  Interface      │
                                                └─────────────────┘
```

## 📁 Solution Structure

All solution files are located in the `lab2/` folder:

```
lab2/
├── lab2_solution.py          # Main orchestrator script
├── setup_infrastructure.py   # Creates VAST views and database schema
├── upload_datasets.py        # Handles S3 dataset uploads
├── process_metadata.py       # Processes metadata from S3 to vastdb
├── search_metadata.py        # Provides search and query functionality
├── vast_database_manager.py  # Manages VAST Database operations
├── swift_metadata_extractor.py # Extracts metadata from Swift files
├── test_solution.py          # Unit tests
└── requirements.txt          # Python dependencies
```

**Note:** Configuration files (`config.yaml` and `secrets.yaml`) are now centralized in the root directory for all labs.

## 🚀 Quick Start

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
# Copy the example configuration files (if you haven't already)
cp ../config.yaml.example ../config.yaml
cp ../secrets.yaml.example ../secrets.yaml

# Edit configuration files in the root directory
# ../config.yaml - Main configuration for all labs
# ../secrets.yaml - Sensitive data (passwords, API keys)
```

### 4. Run the Solution

#### Setup Infrastructure
```bash
# Dry run (safe - tests connections)
python lab2_solution.py --setup-only

# Production (creates views and database)
python lab2_solution.py --setup-only --pushtoprod
```

#### Upload Datasets
```bash
# Dry run
python lab2_solution.py --upload-only

# Production
python lab2_solution.py --upload-only --pushtoprod
```

#### Process Metadata
```bash
# Dry run
python lab2_solution.py --process-only

# Production
python lab2_solution.py --process-only --pushtoprod
```

#### Search Metadata
```bash
# Show statistics
python lab2_solution.py --search-only --stats

# Show recent files
python lab2_solution.py --search-only --recent 10

# Search by pattern
python lab2_solution.py --search-only --pattern "*.gz"

# Search by mission
python lab2_solution.py --search-only --obs-id "SWIFT"
```

#### Complete Workflow
```bash
# Run everything in sequence
python lab2_solution.py --complete --pushtoprod
```

## 🔧 Configuration

### Main Configuration (`../config.yaml` - copy from `../config.yaml.example`)

```yaml
# Lab 2 specific settings
lab2:
  raw_data:
    view_path: "/lab2-raw-data"
    policy_name: "s3_default_policy"
    bucket_owner: "your-email@domain.com"
  
  metadata_database:
    view_path: "/lab2-metadata-db"
    database_name: "lab2-metadata-db"
    schema: "satellite_observations"
    policy_name: "s3_default_policy"
    bucket_owner: "your-email@domain.com"
  
  catalog:
    batch_size: 1000
    max_concurrent_extractions: 10
    extraction_timeout_seconds: 60
  
  search:
    default_limit: 100
    max_limit: 1000
    enable_fuzzy_search: true
```

## ✨ Key Features

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

## 🔍 Search Capabilities

### Available Search Options
- **`--stats`** - Show comprehensive statistics
- **`--recent N`** - Show recent N files
- **`--pattern PATTERN`** - Search by file pattern
- **`--obs-id ID`** - Search by observation ID
- **`--file-type TYPE`** - Search by file type

### Sample Search Results
```
📊 Found 10 results:
--------------------------------------------------------------------------------

1. File: swbj0042_6p5203_a_s157.lc.gz
   Mission: SWIFT
   Satellite: SWIFT
   Instrument: BAT
   Target: SWIFT J0042.6+5203
   Observation Date: 2004-12-23 12:58:52
   File Format: .lc
   Size: 8478 bytes
   Dataset: batsources_survey_north
   Processing Status: raw
```

## 🛡️ Safety Features

- **Default dry-run mode** - All operations safe by default
- **`--pushtoprod` flag** - Required for actual changes
- **Confirmation prompts** - Production mode requires "YES" confirmation
- **Real validation** - Tests connections and checks existing infrastructure

## 📊 Metadata Schema

The system extracts and stores:
- **File Information**: Name, path, size, format, checksum
- **Mission Data**: Mission ID, satellite name, instrument type
- **Observation Data**: Timestamp, target object, processing status
- **System Data**: Dataset name, ingestion timestamp, metadata version

## 🧪 Testing

Run the comprehensive test suite to verify all functionality:

```bash
python test_solution.py
```

## 🎯 Success Criteria

- **Comprehensive Coverage** - All satellite data files properly cataloged with metadata
- **Fast Search Performance** - Sub-5-second response times for complex queries
- **Automated Management** - Metadata extraction and catalog updates happen automatically
- **Scalable Architecture** - System can handle current and future data volumes
- **Integration Success** - Seamless integration with existing VAST infrastructure

## 🚨 Troubleshooting

### Common Issues
1. **SSL Warnings**: Expected for internal networks with `ssl_verify: false`
2. **Connection Errors**: Verify VMS and database endpoints in config
3. **Permission Errors**: Ensure bucket owner matches your VAST user
4. **Empty Results**: Check if data has been uploaded and processed

### Debug Tools
```bash
# Debug raw database data
python debug_metadata.py

# Test individual components
python setup_infrastructure.py --dry-run
python upload_datasets.py --dry-run
python process_metadata.py --dry-run
```

## 📈 Performance

- **Efficient Querying**: Uses VAST DB QueryConfig for optimal performance
- **Batch Processing**: Processes metadata in configurable batches
- **Memory Management**: Streams large datasets without loading everything into memory
- **Connection Pooling**: Reuses database connections efficiently

## 🔮 Next Steps

1. **Advanced Analytics** - Add data quality analysis and trend reporting
2. **API Development** - Create REST API for external system integration
3. **Machine Learning** - Implement automated data classification and anomaly detection
4. **Web Interface** - Build web-based search and visualization interface
5. **Real-time Processing** - Add streaming metadata extraction for live data feeds
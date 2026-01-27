# Lab 2: Metadata Infrastructure Project

> 📖 **Hey, remember to read the [story](STORY.md) to understand what we're doing and why!** This will help you understand the business context and challenges the Orbital Dynamics team is facing.

## 🎯 Overview

A complete metadata infrastructure system that processes Swift satellite data and provides search capabilities using VAST Database and S3 storage. This solution demonstrates how to use `vastpy` for storage management and `vastdb` for metadata catalog functionality to create a comprehensive metadata system for Orbital Dynamics' satellite data.

## Build our Infrastructure: Code Lab Server Access
The VAST Data Labs gives our entire community remote access to our data infrastructure platform for hands-on exploration and testing. The lab environment is a practical way to get familiar with VAST systems, try out different configurations, and build automation workflows - all without needing your own hardware setup.

If you do not have access to a VAST cluster, complete this lab using our data infrastructure platform, [join our Community to get Code Lab Server access](https://community.vastdata.com/t/official-vast-data-labs-user-guide/1774#p-2216-infrastructure-automation-with-python-and-the-vast-api-3).

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

# Search by mission (using pattern matching)
python lab2_solution.py --search-only --pattern "SWIFT*"

# Search by observation ID (if in filename)
python lab2_solution.py --search-only --pattern "swbj1421*"
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
- **`--pattern PATTERN`** - Search by file pattern (supports wildcards)
- **`--target TARGET`** - Search by target object (supports wildcards)
- **`--file-type TYPE`** - Search by file type/format
- **`--json`** - Output results in JSON format

### Sample Search Results
```
📊 Found 3 results:
--------------------------------------------------------------------------------

1. File: swbj0007_0p7303_d2507.lc.gz
   Mission: SWIFT
   Satellite: SWIFT
   Instrument: BAT
   Target: PSR J0007+7303
   Observation Date: 2005-02-15
   Observation End: 2025-07-31
   RA: 1.756°
   Dec: 73.052°
   Energy Range: 15.0 - 50.0 keV
   On-target Time: 7471 seconds
   Catalog Number: 33730
   Catalog Name: SWIFT J0007.0+7303
   Lightcurve Type: DAILYMON
   Background Applied: True
   File Format: .gz
   Size: 75107520 bytes
   Dataset: batsources_monitoring_north
   Processing Status: raw

2. File: swbj0005_3m7443_c_s157.lc.gz
   Mission: SWIFT
   Satellite: SWIFT
   Instrument: BAT
   Target: 2MASX J00004876-0709117
   Observation Date: 2004-12-23
   Observation End: 2018-01-16
   RA: 0.220°
   Dec: -7.140°
   Energy Range: 15.0 - 50.0 keV
   On-target Time: 17960117 seconds
   Catalog Number: 3180
   Catalog Name: SWIFT J0001.0-0708
   Lightcurve Type: SURCRABWEIG
   Background Applied: True
   File Format: .gz
   Size: 40320 bytes
   Dataset: batsources_survey_south
   Processing Status: raw
```

### Example Searches
```bash
# Search by target object
python lab2_solution.py --search-only --target "PSR J0007+7303"

# Search by observation ID pattern
python lab2_solution.py --search-only --pattern "swbj0007_*"

# Search by file type
python lab2_solution.py --search-only --file-type "gz"

# Search by mission (using pattern matching)
python lab2_solution.py --search-only --pattern "SWIFT*"

# Search with JSON output for analysis
python lab2_solution.py --search-only --target "PSR*" --json

# Search for files with energy > 20 keV (using JSON output)
python lab2_solution.py --search-only --pattern "*" --json | grep -A 5 "energy_max_kev.*[2-9][0-9]"
```

## 🛡️ Safety Features

- **Default dry-run mode** - All operations safe by default
- **`--pushtoprod` flag** - Required for actual changes
- **Confirmation prompts** - Production mode requires "YES" confirmation
- **Real validation** - Tests connections and checks existing infrastructure

## 📊 Metadata Schema

The system extracts and stores comprehensive metadata from Swift FITS files:

### **Core File Information**
- **File Details**: Name, path, size, format, checksum
- **Dataset Info**: Dataset name, ingestion timestamp, metadata version

### **Mission & Instrument Data**
- **Mission Info**: Mission ID, satellite name, instrument type
- **Energy Range**: Minimum and maximum energy in keV
- **Data Quality**: Background applied flag, lightcurve type

### **Astronomical Data**
- **Target Object**: Object name, catalog name, catalog number
- **Coordinates**: Right Ascension (RA) and Declination (Dec) in degrees
- **Observation Times**: Start date, end date, on-target time, elapsed time

### **Processing Information**
- **Status**: Processing status, file format, last modified
- **System Data**: Creation timestamp, update timestamp

### **Example Metadata Fields**
```
File: swbj0007_0p7303_d2507.lc.gz
├── Basic Info: file_name, file_size_bytes, file_format, dataset_name
├── Mission: mission_id, satellite_name, instrument_type
├── Target: target_object, catalog_name, catalog_number
├── Coordinates: ra_deg, dec_deg
├── Time: observation_timestamp, observation_end, on_target_time_s
├── Energy: energy_min_kev, energy_max_kev
├── Quality: background_applied, lightcurve_type
└── System: processing_status, checksum, metadata_version
```

## 🧪 Testing

The solution includes comprehensive error handling and validation built into the main functionality.

### Test Script
```bash
# Test all components
python test_lab2_solution.py
```

This will verify that all components can be imported and initialized correctly.

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

# Test complete solution
python test_lab2_solution.py
```

## 📈 Performance

- **Efficient Querying**: Uses VAST DB QueryConfig for optimal performance
- **Batch Processing**: Processes metadata in configurable batches
- **Memory Management**: Streams large datasets without loading everything into memory
- **Connection Pooling**: Reuses database connections efficiently

## 📚 API Reference

### VASTDatabaseManager
- `connect()` - Connect to database server
- `database_exists()` - Check if database exists
- `create_database()` - Create database if needed
- `create_schema()` - Create schema if needed
- `create_metadata_table()` - Create metadata table if needed
- `insert_metadata(metadata)` - Insert metadata record
- `search_metadata(criteria)` - Search metadata
- `get_metadata_stats()` - Get database statistics

### SwiftMetadataExtractor
- `extract_metadata_from_file(file_path)` - Extract from single file
- `extract_metadata_from_dataset(dataset_path)` - Extract from dataset
- `_extract_fits_metadata(file_path)` - FITS-specific extraction
- `_extract_swift_lightcurve_metadata(file_path)` - Swift-specific extraction

### Lab2Solution
- `setup_database_infrastructure()` - Set up database infrastructure
- `process_all_datasets()` - Process all available datasets
- `show_database_stats()` - Display database statistics
- `search_metadata(criteria)` - Search metadata

## 🔮 Next Steps

1. **Advanced Analytics** - Add data quality analysis and trend reporting
2. **API Development** - Create REST API for external system integration
3. **Machine Learning** - Implement automated data classification and anomaly detection
4. **Web Interface** - Build web-based search and visualization interface
5. **Real-time Processing** - Add streaming metadata extraction for live data feeds

## 📞 Support

If you encounter issues:

1. **Check the test script** output for specific errors
2. **Verify configuration** in config.yaml and secrets.yaml
3. **Check dependencies** are properly installed
4. **Review logs** for detailed error messages

---

**🎉 Congratulations!** You now have a complete metadata infrastructure system that safely manages VAST Database operations and processes Swift satellite data.
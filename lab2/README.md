# Lab 2: Metadata Infrastructure Project

## 🎯 Overview

A complete metadata infrastructure system that processes Swift satellite data and provides search capabilities using VAST Database and S3 storage.

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

## 📁 Modular Scripts

- **`lab2_solution.py`** - Main orchestrator script
- **`setup_infrastructure.py`** - Creates VAST views and database schema
- **`upload_datasets.py`** - Handles S3 dataset uploads
- **`process_metadata.py`** - Processes metadata from S3 to vastdb
- **`search_metadata.py`** - Provides search and query functionality
- **`vast_database_manager.py`** - Manages VAST Database operations
- **`swift_metadata_extractor.py`** - Extracts metadata from Swift files

## 🚀 Quick Start

### 1. Setup Infrastructure
```bash
# Dry run (safe - tests connections)
python lab2_solution.py --setup-only

# Production (creates views and database)
python lab2_solution.py --setup-only --pushtoprod
```

### 2. Upload Datasets
```bash
# Dry run
python lab2_solution.py --upload-only

# Production
python lab2_solution.py --upload-only --pushtoprod
```

### 3. Process Metadata
```bash
# Dry run
python lab2_solution.py --process-only

# Production
python lab2_solution.py --process-only --pushtoprod
```

### 4. Search Metadata
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

### 5. Complete Workflow
```bash
# Run everything in sequence
python lab2_solution.py --complete --pushtoprod
```

## 🔧 Configuration

### Required Files
- **`config.yaml`** - Non-sensitive configuration
- **`secrets.yaml`** - Sensitive credentials

### Key Configuration Sections
```yaml
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
```

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
# Lab 2 Complete Solution: Metadata Infrastructure Project

## 🎯 Overview

This Lab 2 solution provides a complete metadata infrastructure system that:

1. **Creates two VAST views using vastpy** - Raw data view and metadata database view
2. **Uploads Swift datasets to S3** - Uses boto3 to upload files to the raw data view
3. **Extracts comprehensive metadata** - From Swift data files (FITS, lightcurves, etc.)
4. **Stores metadata in VAST Database** - With duplicate detection and safe insertion
5. **Provides search capabilities** - Query metadata across all datasets

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Swift Data    │    │  vastpy creates  │    │  Raw Data       │
│   (Local Files) │───▶│  buckets         │───▶│  Bucket (S3)    │
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

## 📁 Files

- **`vast_database_manager.py`** - Manages VAST Database operations safely
- **`swift_metadata_extractor.py`** - Extracts metadata from Swift data files
- **`lab2_solution.py`** - Main solution integrating all components
- **`test_lab2_solution.py`** - Test script to verify everything works

## 🚀 Quick Start

### 1. Test the Solution

```bash
cd lab2
python test_lab2_solution.py
```

This will verify that all components can be imported and initialized correctly.

### 2. Set Up VAST Database Infrastructure (Dry Run)

```bash
python lab2_solution.py --setup-only
```

This will check what VAST Database infrastructure exists and what would be created.

### 3. Set Up VAST Database Infrastructure (Production)

```bash
python lab2_solution.py --setup-only --pushtoprod
```

This will actually create the bucket, schema, and tables in VAST Database.

### 4. Process Metadata (Dry Run)

```bash
python lab2_solution.py --process-only
```

This will extract metadata from Swift datasets and show what would be inserted.

### 5. Process Metadata (Production)

```bash
python lab2_solution.py --process-only --pushtoprod
```

This will actually extract and store metadata in VAST Database.

### 6. Full Solution (Setup + Process)

```bash
python lab2_solution.py --pushtoprod
```

This will set up the VAST Database infrastructure and process all metadata.

## 🔧 Configuration

### VAST Database Settings

The solution uses these configuration keys from your `config.yaml`:

```yaml
lab2:
  raw_data:
    bucket: "lab2-raw-data"  # Bucket for Swift dataset uploads
    view_path: "/lab2-raw-data"  # View path for raw data access
    policy_id: 3  # Default policy ID for raw data
  
  metadata_database:
    bucket: "lab2-metadata-db"  # Bucket for VAST Database metadata storage
    schema: "satellite_observations"  # Schema name for metadata tables
    endpoint: "http://your-vast-cluster.example.com"  # VAST Management System endpoint
    ssl_verify: false  # Disable SSL verification for internal networks
    timeout: 30  # Connection timeout in seconds
```

### Secrets

Add these to your `secrets.yaml`:

```yaml
vast_password: "your_vast_password"   # VAST Management System password
s3_access_key: "your_access_key"     # S3 access key for uploads and database
s3_secret_key: "your_secret_key"     # S3 secret key for uploads and database
```

The solution uses two separate buckets:
- **Raw Data Bucket**: Stores the actual Swift dataset files (uploaded via boto3)
- **Metadata Database Bucket**: Stores metadata in VAST Database (managed via vastpy)

## 📊 Metadata Schema

The solution creates a comprehensive metadata table:

```sql
CREATE TABLE satellite_observations.swift_metadata (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    file_format VARCHAR(50),
    dataset_name VARCHAR(100),
    
    -- Swift-specific metadata
    mission_id VARCHAR(100),
    satellite_name VARCHAR(100),
    instrument_type VARCHAR(100),
    observation_timestamp TIMESTAMP,
    target_object VARCHAR(100),
    processing_status VARCHAR(50),
    
    -- File metadata
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP,
    checksum VARCHAR(64),
    metadata_version VARCHAR(20),
    
    -- Search optimization
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 Metadata Extraction

### Supported File Formats

- **FITS files** - Full astronomical header parsing (requires astropy)
- **Swift lightcurves** - Pattern-based metadata extraction
- **JSON files** - Structured metadata extraction
- **Generic files** - Filename pattern analysis

### Extracted Metadata

- **File information**: Path, name, size, format, checksum
- **Swift-specific**: Mission ID, satellite, instrument, target, timestamp
- **Processing**: Status, version, ingestion timestamp
- **Search optimization**: Indexed fields for fast queries

## 🛡️ Safety Features

### Dry Run Mode (Default)

- **No actual changes** to VAST Database or files
- **Shows what would happen** without making changes
- **Safe for testing** and understanding the solution

### Production Mode (`--pushtoprod`)

- **Requires explicit confirmation** ("YES")
- **Makes actual changes** to VAST Database and files
- **Safety checks always run** before any operation

### VAST Database Safety

- **Checks existence** before creating anything
- **No overwrites** - skips existing records
- **Transaction safety** - rollback on errors
- **Connection management** - proper cleanup

## 📈 Usage Examples

### Show VAST Database Statistics

```bash
python lab2_solution.py --stats
```

### Search Metadata

```bash
# Search by mission
python lab2_solution.py --search "mission_id=SWIFT"

# Search by target object
python lab2_solution.py --search "target_object=BAT_0001"
```

### Process Specific Datasets

The solution automatically detects and processes all datasets in the `swift_datasets/` directory:

- `batsources_survey_north/`
- `batsources_survey_south/`
- `batsources_monitoring_north/`
- `batsources_monitoring_south/`

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   pip install -r ../requirements.txt
   ```

2. **Database Connection Issues**
   - Check VAST Database is running
   - Verify host/port in config.yaml
   - Check credentials in secrets.yaml

3. **Swift Datasets Not Found**
   - Run the Swift download script first
   - Check `swift_datasets/` directory exists
   - Verify VAST Database configuration

4. **Metadata Extraction Failures**
   - Install astropy for FITS support
   - Check file permissions
   - Verify file formats

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

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

### Lab2CompleteSolution

- `setup_database_infrastructure()` - Set up database infrastructure
- `process_all_datasets()` - Process all available datasets
- `show_database_stats()` - Display database statistics
- `search_metadata(criteria)` - Search metadata

## 🎯 Next Steps

After completing Lab 2:

1. **Verify metadata** is correctly stored in database
2. **Test search queries** for different criteria
3. **Explore the data** using database tools
4. **Move to Lab 3** for pipeline orchestration

## 📞 Support

If you encounter issues:

1. **Check the test script** output for specific errors
2. **Verify configuration** in config.yaml and secrets.yaml
3. **Check dependencies** are properly installed
4. **Review logs** for detailed error messages

---

**🎉 Congratulations!** You now have a complete metadata infrastructure system that safely manages VAST Database operations and processes Swift satellite data.

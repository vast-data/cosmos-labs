# Scripts Directory

This directory contains utility scripts for the Orbital Dynamics lab exercises.

## Test Data Generator

The `generate_test_data.py` script creates realistic test data for various lab scenarios, including storage testing, snapshot strategy validation, and performance benchmarking.

### Features

- **Multiple Data Types**: Raw telescope data, processed files, analysis results, and published datasets
- **Configurable Sizes**: Generate files from MB to GB sizes
- **Realistic Content**: Uses Faker library for scientific data patterns
- **High Performance**: Uses elbencho for efficient large file generation
- **Cross-Lab Usage**: Useful for Lab 1 (storage testing) and Lab 4 (snapshot testing)
- **Configuration Required**: Reads lab-specific view paths from config.yaml

### Usage

```bash
# Lab 1 storage testing
python scripts/generate_test_data.py --lab-type lab1 --raw-files 50 --raw-size-mb 1000

# Lab 4 snapshot testing (default)
python scripts/generate_test_data.py --lab-type lab4

# Performance testing with large files
python scripts/generate_test_data.py --lab-type lab4 --raw-size-mb 1000 --processed-size-mb 500

# High-volume testing
python scripts/generate_test_data.py --lab-type lab4 --raw-files 100 --processed-files 200 --analysis-files 500
```

### Lab Integration

- **Lab 1**: Generate large files to test storage monitoring and auto-expansion
- **Lab 4**: Create realistic data volumes for snapshot strategy testing
- **General**: Any lab needing test data for performance validation

## Swift Dataset Preparation Tool

The main script `swift_dataset_prep.sh` downloads Swift GRB datasets from NASA HEASARC and prepares them for VAST Data platform integration. This is a **pure bash implementation** with no Python dependencies required.

**Note**: This tool prepares datasets locally for later VAST upload. It does not actually upload to VAST systems yet.

### Features

- **Pure Bash**: No Python dependencies or requirements to install
- **Standalone Operation**: No external configuration files needed
- **Automated Downloads**: Downloads recommended Swift datasets with progress tracking
- **VAST Preparation**: Creates metadata files and organizes data for VAST integration
- **Dry Run Mode**: Test the script without making actual changes
- **Comprehensive Logging**: Detailed logs for troubleshooting
- **Respectful Downloads**: Includes delays between downloads to be respectful to NASA servers
- **Cross-Platform**: Works on macOS, Linux, and other Unix-like systems

### Available Datasets

| Dataset | Priority | Size | Description | Lab Usage |
|---------|----------|------|-------------|-----------|
| `grbsummary` | High | 50-100 MB | GRB summary products (2005-2012) | Lab 5: Event Detection |
| `batsources_survey` | High | 100-200 MB | BAT source catalog (157 months) | Lab 2: Metadata Catalog |
| `batsources_monitoring` | Medium | 200-500 MB | BAT source monitoring data | Lab 3: Pipeline Orchestration |
| `archive_metadata` | Low | 10-50 MB | Archive metadata tables | General: Reference Data |

### System Requirements

#### Required Commands
- **curl** OR **wget** (for downloading files)
- **bash** (version 4.0 or higher recommended)

#### Optional Commands
- **jq** (for enhanced JSON parsing if needed)

#### Installation by Platform

**macOS:**
```bash
# Install curl (usually pre-installed)
brew install curl

# Install jq (optional)
brew install jq
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install curl wget jq
```

**CentOS/RHEL:**
```bash
sudo yum install curl wget jq
# or for newer versions:
sudo dnf install curl wget jq
```

### Usage

#### Quick Start
```bash
# From project root directory - see what the script does
./scripts/swift_dataset_prep.sh

# Test run without downloading
./scripts/swift_dataset_prep.sh --dry-run

# Download all datasets
./scripts/swift_dataset_prep.sh --download
```

#### Command Line Options

- `--download`: Download all Swift datasets
- `--dry-run`: Show what would be done without actually doing it
- `--force`: Force re-download of existing datasets
- `--help`: Show help message

**Note**: Running the script without any options will display the help message and exit safely.

#### Examples

```bash
# Show help (default behavior)
./scripts/swift_dataset_prep.sh

# Test run without downloading
./scripts/swift_dataset_prep.sh --dry-run

# Download all datasets
./scripts/swift_dataset_prep.sh --download

# Force re-download existing datasets
./scripts/swift_dataset_prep.sh --download --force

# Show help explicitly
./scripts/swift_dataset_prep.sh --help
```

### Output

The script creates:
- `swift_datasets/` directory with downloaded datasets
- `swift_download.log` with detailed execution logs

### Example Output

```
============================================================
SWIFT DATASET PROCESSING SUMMARY
============================================================

DOWNLOAD RESULTS:
  grbsummary: ✅ SUCCESS
  batsources_survey: ✅ SUCCESS
  batsources_monitoring: ✅ SUCCESS
  archive_metadata: ✅ SUCCESS

NEXT STEPS:
  1. Review downloaded datasets in 'swift_datasets/' directory
  2. Use datasets for lab exercises
  3. Integrate with VAST systems as needed
```

#### Log Files

- `swift_download.log`: Contains detailed execution logs
- Check for ERROR level messages for troubleshooting
- INFO level messages show progress and success

## Swift Dataset Upload Tool

The `upload_swift_to_vast_s3.py` script uploads locally prepared Swift datasets to the VAST Data Platform via S3. This script complements the Swift dataset preparation tool by handling the actual transfer of data to VAST.

### Features

- **S3-Based Upload**: Uses boto3 to upload datasets via VAST's S3-compatible interface
- **Safe by Default**: Dry-run mode enabled by default to preview uploads
- **Comprehensive Logging**: Detailed progress and error reporting
- **Batch Processing**: Uploads all available datasets or specific ones
- **Configuration-Based**: Reads S3 credentials and settings from config.yaml and secrets.yaml
- **VAST-Compatible**: Configured for VAST S3 endpoint requirements

### Prerequisites

- Swift datasets must be prepared using `swift_dataset_prep.sh`
- S3 configuration must be set in `config.yaml` (endpoint_url, bucket)
- S3 credentials must be set in `secrets.yaml` (s3_access_key, s3_secret_key)
- Python dependencies: `boto3` (install via `pip install -r requirements.txt`)

### Usage

#### Quick Start

```bash
# Dry run (default - safe, no actual uploads)
python scripts/upload_swift_to_vast_s3.py

# Production mode (actual uploads)
python scripts/upload_swift_to_vast_s3.py --pushtoprod
```

#### Command Line Options

- `--pushtoprod`: Enable production mode (requires confirmation, performs actual uploads)
- `--config`: Path to custom config file (default: config.yaml in project root)

**Note**: The script runs in dry-run mode by default. Use `--pushtoprod` to perform actual uploads.

#### Examples

```bash
# Preview what would be uploaded (dry run)
python scripts/upload_swift_to_vast_s3.py

# Upload all datasets to VAST S3
python scripts/upload_swift_to_vast_s3.py --pushtoprod

# Use custom config file
python scripts/upload_swift_to_vast_s3.py --config my_config.yaml --pushtoprod
```

### Upload Process

1. **Discovery**: Scans `scripts/swift_datasets/` directory for available datasets
2. **Validation**: Verifies S3 connection and bucket accessibility
3. **Upload**: Transfers all files from each dataset to S3 bucket under `swift/{dataset_name}/` prefix
4. **Reporting**: Provides detailed summary of upload results

### Output

- Datasets are uploaded to: `s3://{bucket}/swift/{dataset_name}/`
- Upload progress is logged to console
- Detailed logs include file counts, sizes, and success/failure status

### Example Output

```
🚀 Starting Swift datasets upload process
📊 Found 4 datasets ready for upload

============================================================
📤 Processing: grbsummary
============================================================
📤 Uploading dataset: grbsummary
   From: scripts/swift_datasets/grbsummary
   To S3: s3://cosmos-lab-raw/swift/grbsummary/
📊 Dataset contains 150 files
✅ Successfully uploaded: file1.fits
...
📊 Upload Summary for grbsummary:
  ✅ Successfully uploaded: 150
  ❌ Failed: 0
  📊 Total: 150
```

### Safety Features

- **Dry Run Default**: No uploads performed unless `--pushtoprod` is specified
- **Confirmation Required**: Production mode requires typing 'YES' to confirm
- **Error Handling**: Continues processing other datasets if one fails
- **Detailed Logging**: Full audit trail of all operations

### Troubleshooting

1. **S3 Connection Errors**
   - Verify S3 endpoint URL in config.yaml
   - Check S3 credentials in secrets.yaml
   - Ensure bucket exists and is accessible

2. **Upload Failures**
   - Check network connectivity
   - Verify sufficient S3 bucket capacity
   - Review error messages in console output

3. **Missing Datasets**
   - Ensure `swift_dataset_prep.sh` has been run successfully
   - Verify `scripts/swift_datasets/` directory exists and contains datasets

## Lab Environment Cleanup Tool

The `cleanup_lab_environment.py` script provides comprehensive cleanup capabilities for resetting the lab environment between exercises or at the end of a lab session.

### Features

- **S3 Bucket Cleanup**: Delete all objects from configured S3 bucket
- **Database Cleanup**: Clear all tables or remove entire database
- **Local File Cleanup**: Remove downloaded Swift datasets
- **Status Reporting**: Show current state of lab environment components
- **Safe by Default**: Dry-run mode enabled by default
- **Selective Operations**: Clean specific components or everything at once
- **Configuration-Based**: Automatically detects configured components

### Prerequisites

- Python dependencies: `boto3` (for S3 cleanup), database dependencies (for database cleanup)
- Configuration must be set in `config.yaml` and `secrets.yaml`
- Appropriate permissions for S3 bucket and database access

### Usage

#### Quick Start

```bash
# Show current status
python scripts/cleanup_lab_environment.py --status

# Clean S3 bucket only (dry run)
python scripts/cleanup_lab_environment.py --s3-only

# Clean everything (production mode)
python scripts/cleanup_lab_environment.py --all --pushtoprod
```

#### Command Line Options

- `--status`: Show current status of lab environment (no cleanup performed)
- `--s3-only`: Clean up S3 bucket only (delete all objects)
- `--db-only`: Clean up database tables only (preserve database structure)
- `--db-remove`: Remove entire database
- `--all`: Clean up everything (S3, database, local files)
- `--pushtoprod`: Enable production mode (required for actual cleanup)
- `--config`: Path to custom config file

**Note**: All cleanup operations run in dry-run mode by default. Use `--pushtoprod` to perform actual cleanup.

#### Examples

```bash
# Check current status
python scripts/cleanup_lab_environment.py --status

# Preview S3 cleanup (dry run)
python scripts/cleanup_lab_environment.py --s3-only

# Actually clean S3 bucket
python scripts/cleanup_lab_environment.py --s3-only --pushtoprod

# Clear database tables (preserve structure)
python scripts/cleanup_lab_environment.py --db-only --pushtoprod

# Remove entire database
python scripts/cleanup_lab_environment.py --db-remove --pushtoprod

# Clean everything (S3, database, local files)
python scripts/cleanup_lab_environment.py --all --pushtoprod
```

### Cleanup Operations

#### S3 Bucket Cleanup
- Lists all objects in the configured S3 bucket
- Deletes objects in batches of 1000 (S3 API limit)
- Provides progress reporting during deletion
- Safe: Only deletes objects, never deletes the bucket itself

#### Database Cleanup
- **Table Cleanup** (`--db-only`): Clears all data from tables while preserving structure
- **Database Removal** (`--db-remove`): Completely removes the database
- Automatically detects if database exists before attempting cleanup

#### Local File Cleanup
- Removes the `scripts/swift_datasets/` directory
- Calculates and reports total size of files removed
- Safe: Only removes Swift datasets, not other script files

### Status Reporting

The `--status` option provides a comprehensive overview:

```
📊 Lab Environment Status
==================================================
📦 S3 Bucket 'cosmos-lab-raw': 1,234 objects
🗄️  Database: Connected and exists
📁 Local Files: 4 datasets, 2.45 GB
```

### Safety Features

- **Dry Run Default**: No changes made unless `--pushtoprod` is specified
- **Selective Operations**: Clean only what you need
- **Status Check**: Preview current state before cleanup
- **Batch Processing**: Efficient S3 deletion in batches
- **Error Handling**: Continues with other operations if one fails

### Use Cases

1. **Between Lab Exercises**: Clean specific components to reset state
2. **End of Lab Session**: Use `--all` to clean everything
3. **Troubleshooting**: Use `--status` to diagnose environment issues
4. **Storage Management**: Clean S3 bucket to free up space

### Troubleshooting

1. **Permission Errors**
   - Verify S3 credentials have delete permissions
   - Check database user has DROP/CLEAR permissions
   - Ensure write permissions for local file cleanup

2. **Connection Failures**
   - Verify S3 endpoint and credentials in config
   - Check database connection settings
   - Review error messages for specific issues

3. **Partial Cleanup**
   - Script continues even if one component fails
   - Check logs for specific error messages
   - Re-run cleanup for failed components

### Contributing

When modifying scripts in this directory:
1. **Bash Scripts**: Maintain bash compatibility (test on multiple systems)
2. **Python Scripts**: Follow Python best practices and use type hints where appropriate
3. **Logging**: Add comprehensive logging for all operations
4. **Safety**: Default to dry-run mode for destructive operations
5. **Documentation**: Update this README with new features and usage examples
6. **Testing**: Test with various system configurations
7. **Error Handling**: Ensure proper error handling and exit codes
8. **Configuration**: Use config.yaml and secrets.yaml for all settings (no environment variables)

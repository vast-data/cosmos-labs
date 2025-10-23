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

### What This Tool Does (and Doesn't Do)

#### ✅ What It Does:
- Downloads Swift datasets from NASA HEASARC
- Organizes data into structured directories
- Creates organized dataset structure for lab use

#### ❌ What It Doesn't Do:
- Connect to VAST clusters
- Create actual VAST views
- Upload files to VAST systems
- Handle VAST authentication
- Create VAST preparation metadata files

#### 🔄 Next Steps for VAST Integration:
After running this preparation tool, you would need to:
1. Use VAST client tools to create views
2. Transfer prepared datasets to VAST
3. Configure VAST storage policies
4. Set up VAST access controls

### Lab Integration

#### Lab 2: Metadata Catalog
- Use `batsources_survey` data to build metadata catalog
- Practice extracting metadata from FITS files
- Implement search and query interfaces

#### Lab 3: Pipeline Orchestration
- Use `batsources_monitoring` data for pipeline testing
- Practice managing multiple data sources
- Implement job scheduling and monitoring

#### Lab 5: Event Detection
- Use `grbsummary` data for GRB event detection
- Practice pattern recognition algorithms
- Implement alerting systems

### Troubleshooting

#### Common Issues

1. **Download Failures**
   - Check internet connectivity
   - Verify NASA HEASARC server status
   - Review logs for specific error messages
   - Ensure curl or wget is available

2. **Permission Errors**
   - Ensure write permissions in current directory
   - Check if script is executable: `chmod +x scripts/*.sh`

3. **Bash Version Issues**
   - Ensure bash version 4.0+: `bash --version`
   - Some systems use `/bin/sh` instead of `/bin/bash`

#### Log Files

- `swift_download.log`: Contains detailed execution logs
- Check for ERROR level messages for troubleshooting
- INFO level messages show progress and success

### Advantages of Bash Implementation

1. **No Dependencies**: Works out of the box on most Unix-like systems
2. **Faster Execution**: No Python interpreter startup time
3. **Smaller Footprint**: No need to install Python packages
4. **System Integration**: Better integration with shell environment
5. **Easier Distribution**: Single script file, no requirements.txt needed
6. **Simpler Usage**: Direct execution without wrapper complexity
7. **Clear Purpose**: Preparation tool, not upload tool

### Future Enhancements

- **VAST Integration**: Add actual VAST client connectivity
- **Real-time Streaming**: Integration with Kafka for live data feeds
- **Advanced Analytics**: Machine learning models for event detection
- **Multi-mission Support**: Expand to other NASA missions (Kepler, Hubble, etc.)
- **Automated Updates**: Scheduled downloads of new data releases

### Contributing

When modifying the script:
1. Maintain bash compatibility (test on multiple systems)
2. Add comprehensive logging
3. Include dry-run mode for new operations
4. Update this README with new features
5. Test with various system configurations
6. Ensure proper error handling and exit codes

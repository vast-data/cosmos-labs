# Swift Dataset Guide for Cosmos Labs

## Overview

This guide explains the Swift satellite datasets available for the Cosmos Labs exercises. These are real astronomical datasets from NASA's Swift mission that provide excellent examples for learning data infrastructure, metadata management, and pipeline development.

## Understanding Swift Data

### What is Swift?
The Swift satellite is NASA's mission to study gamma-ray bursts (GRBs) and other high-energy astrophysical phenomena. It carries three instruments:
- **BAT (Burst Alert Telescope)**: Detects gamma-ray bursts and surveys the sky
- **XRT (X-Ray Telescope)**: Follows up GRBs with X-ray observations
- **UVOT (Ultra-Violet/Optical Telescope)**: Provides optical and UV follow-up

### Data Types
- **Light Curves (.lc.gz)**: Time series showing how a source's brightness changes
- **Spectra (.pha.gz)**: Energy distribution of the radiation
- **Images (.png, .gif)**: Visual representations of the data
- **Metadata Tables (.tdat)**: Catalog information about sources

## Available Datasets

### 1. BAT Source Survey Data (batsources_survey)
- **Files**: 
  - `swbj0000_5p3251_c_s157.lc.gz` (44MB)
  - `swbj0002_5p0323_c_s157.lc.gz` (35MB)
- **Content**: Light curve data from BAT (Burst Alert Telescope) survey observations
- **What It Shows**: These files contain "movies" of how bright different objects in space get over time. Think of it like watching a light bulb that sometimes gets brighter and sometimes gets dimmer - but in space! Each file tracks hundreds of cosmic objects (like black holes, exploding stars, and distant galaxies) and records how their brightness changes over months and years.
- **Size**: 100-200 MB total
- **Priority**: High (excellent for labs)
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/survey157m/north/`

### 2. BAT Source Monitoring Data (batsources_monitoring)
- **Files**:
  - `swbj0007_0p7303_o2507.lc.gz` (3.6MB)
  - `swbj0010_5p1057_o2507.lc.gz` (2.6MB)
- **Content**: Recent monitoring observations of specific sources
- **What It Shows**: These are like "security camera footage" of specific interesting objects in space. Instead of watching hundreds of objects like the survey data, these files focus on just a few important targets and check on them more frequently. It's like having a security guard who keeps checking on the same few valuable items every day to make sure nothing unusual is happening.
- **Size**: 200-500 MB total
- **Priority**: High (excellent for labs)
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/monitoring/north/`

### 3. Archive Metadata Tables (archive_metadata)
- **Files**:
  - `swiftgrbba.tdat` (800KB)
  - `swiftguano.tdat` (3.3MB)
- **Content**: Structured metadata tables in tabular format
- **What It Shows**: These are like "phone books" or "catalogs" for space objects. Instead of the actual data (like the brightness measurements), these files contain organized lists that tell you: "Object X is located at coordinates Y, it's a type Z object, it was discovered on date W, and here are all the other telescopes that have looked at it." Think of it as the index cards that help librarians find the right books, but for cosmic objects.
- **Size**: 10-50 MB total
- **Priority**: Low
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/other/archive_metadata/`

## Metadata Design for Lab 2

### Core Metadata Schema
When building your metadata catalog in Lab 2, consider these essential fields:

```python
swift_metadata_schema = {
    # Basic identification
    "source_id": "str",           # e.g., "swbj0000_5p3251"
    "vast_path": "str",           # Location in VAST storage
    "file_size": "int",           # Size in bytes
    
    # Astronomical coordinates
    "coordinates": {
        "ra": "float",            # Right ascension in degrees
        "dec": "float",           # Declination in degrees
        "galactic_l": "float",    # Galactic longitude
        "galactic_b": "float"     # Galactic latitude
    },
    
    # Physical properties
    "source_type": "str",         # AGN, star, GRB, etc.
    "redshift": "float",          # Distance measure
    "luminosity": "float",        # Energy output (erg/s)
    "variability_index": "float"  # How much the source varies
}
```

### Extended Metadata Schema
For more comprehensive metadata, add these fields:

```python
metadata_record = {
    # ... core fields ...
    
    # Observation details
    "observation": {
        "start_time": "datetime",     # When observation started
        "end_time": "datetime",       # When observation ended
        "exposure_time": "int",       # Duration in seconds
        "mode": "str",                # survey, monitoring, targeted
        "pointing_quality": "str"     # Pointing accuracy
    },
    
    # Instrument configuration
    "instrument": {
        "name": "str",                # BAT, XRT, UVOT
        "energy_band": "str",         # Energy range (e.g., "15-150 keV")
        "detector": "str",            # Detector identifier
        "gain_setting": "str"         # Instrument settings
    },
    
    # Data quality indicators
    "quality": {
        "signal_to_noise": "float",   # Data quality measure
        "background_level": "str",    # Background contamination
        "data_gaps": "int",           # Missing time intervals
        "calibration_status": "str",  # Calibration state
        "processing_version": "str"   # Software version used
    },
    
    # Scientific context
    "classification": {
        "primary_type": "str",        # Main source classification
        "subtype": "str",             # More specific classification
        "catalog_references": "list", # Published catalogs
        "discovery_date": "date",     # When source was discovered
        "follow_up_status": "str"     # Follow-up observation status
    }
}
```

## How to Use These Datasets in the Labs

### Lab 1: Satellite Data Infrastructure Planning
- **Storage Scaling**: Handle 44MB survey files and growing datasets
- **Quota Management**: Manage different file sizes (145B to 44MB)
- **Monitoring**: Track storage growth from multiple data types
- **Compression**: Work with .gz compressed files

### Lab 2: Metadata Infrastructure Project
- **Schema Design**: Design metadata schema for light curves, coordinates, time stamps
- **Extraction**: Parse FITS headers, extract astronomical parameters
- **Cataloging**: Build searchable index of Swift observations
- **Search Interface**: Create tools to find data by coordinates, time, or source

### Lab 3: Multi-Mission Data Pipeline
- **Data Flow**: Process survey → monitoring → metadata pipeline
- **Format Handling**: Handle compressed (.gz) and tabular (.tdat) formats
- **Pipeline Orchestration**: Coordinate different data types
- **Data Transformation**: Convert between different data formats

### Lab 4: Snapshot Strategy
- **Version Control**: Track changes in monitoring data (updated daily)
- **Recovery**: Restore previous versions of survey data
- **Data Lineage**: Track data transformations through pipeline
- **Backup Strategy**: Handle large compressed files

### Lab 5: Near-Real-Time Alert System
- **Variability Detection**: Monitor light curve changes in monitoring data
- **Threshold Alerts**: Detect significant flux variations
- **Time-Sensitive Processing**: Process data within 15-30 minutes
- **Alert Classification**: Prioritize alerts based on source type and significance

## Practical Examples

### Example 1: Finding Variable Sources
**Scenario**: An astronomer wants to study AGNs that vary significantly over time.

```python
# Query metadata catalog for highly variable AGNs
variable_agns = metadata_catalog.find({
    "source_type": "AGN",
    "variability_index": {"$gt": 0.8},
    "quality.signal_to_noise": {"$gt": 10}
})
```

### Example 2: Coordinate Searches
**Scenario**: An astronomer discovered a new source at coordinates (5.5, 0.2) and wants to see if Swift has observed this region.

```python
# Find all observations within 0.5 degrees
nearby_obs = metadata_catalog.find({
    "coordinates.ra": {"$gte": 5.0, "$lte": 6.0},
    "coordinates.dec": {"$gte": -0.3, "$lte": 0.7}
})
```

### Example 3: Time-Series Analysis
**Scenario**: An astronomer wants to study how a source's brightness changed over the past year.

```python
# Get all observations of a source in time order
source_history = metadata_catalog.find({
    "source_id": "swbj0000_5p3251"
}).sort("observation.start_time")
```

## Learning Objectives

### Metadata Design Principles
1. **Think Like a Librarian**: Metadata is like a library card catalog for astronomical data
2. **The 5 W's**: Every good metadata record answers What, Where, When, Why, and How
3. **Metadata is Your Data's Resume**: Make data discoverable for future users
4. **Standards Matter**: Use consistent formats and units
5. **Automation is Key**: Extract metadata programmatically when possible

### Key Skills You'll Learn
- **Data Format Understanding**: Work with FITS, compressed, and tabular data
- **Metadata Extraction**: Parse astronomical headers and filenames
- **Schema Design**: Design flexible metadata structures
- **Search Implementation**: Build query interfaces for astronomers
- **Data Quality Assessment**: Validate and score metadata quality
- **VAST Integration**: Link metadata to actual file locations

## File Naming Conventions

### Swift BAT Filenames
Understanding Swift filenames helps extract metadata:

**Example**: `swbj0000_5p3251_c_s157.lc.gz`

- **swbj0000**: Source identifier (Swift BAT source #0000)
- **5p3251**: Right ascension (5.3251 degrees)
- **c**: Energy band (c = hard X-ray, 15-150 keV)
- **s157**: Survey identifier (157-month survey)
- **lc**: Data type (light curve)
- **gz**: Compression format (gzip)

### Coordinate Systems
- **Right Ascension (RA)**: Longitude on the sky (0-360 degrees)
- **Declination (Dec)**: Latitude on the sky (-90 to +90 degrees)
- **Galactic Coordinates**: Alternative coordinate system centered on Milky Way

## Data Quality Considerations

### Signal-to-Noise Ratio
- **High (>10)**: Excellent quality, suitable for detailed analysis
- **Medium (5-10)**: Good quality, suitable for most studies
- **Low (<5)**: Poor quality, may need special handling

### Background Levels
- **Low**: Clean data with minimal contamination
- **Medium**: Some background, but still usable
- **High**: Significant background, may need special processing

### Calibration Status
- **Calibrated**: Data has been processed with latest calibration
- **Preliminary**: Initial calibration, may be updated
- **Uncalibrated**: Raw data, needs processing

## Next Steps

1. **Download the datasets** using `./swift_dataset_prep.sh --download`
2. **Examine the file structure** and understand the data formats
3. **Design your metadata schema** for Lab 2
4. **Implement metadata extraction** from Swift files
5. **Build search capabilities** for your metadata catalog
6. **Integrate with VAST** storage and views

## Resources

- **Swift Mission**: https://swift.gsfc.nasa.gov/
- **HEASARC Data Archive**: https://heasarc.gsfc.nasa.gov/
- **FITS Format**: https://fits.gsfc.nasa.gov/
- **Astronomical Coordinates**: https://en.wikipedia.org/wiki/Celestial_coordinate_system

## Support

If you encounter issues with the datasets or need help understanding the metadata concepts, refer to the main lab documentation or ask your instructor for guidance.

---

*This guide provides real-world examples of astronomical data management. The Swift datasets offer excellent complexity for learning data infrastructure while working with actual NASA mission data.*

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

### Energy Bands
Swift BAT observes in three main energy bands:
- **Band A (15-25 keV)**: Low energy X-rays, good for soft sources
- **Band B (25-50 keV)**: Medium energy X-rays, balanced sensitivity
- **Band C (50-150 keV)**: High energy X-rays, good for hard sources like GRBs

### File Naming Convention
Understanding Swift filenames helps extract metadata:

**Example**: `swbj0000_5p3251_c_s157.lc.gz`

- **swbj0000**: Source identifier (Swift BAT source #0000)
- **5p3251**: Right ascension (5.3251 degrees, 'p' = positive)
- **c**: Energy band (c = hard X-ray, 50-150 keV)
- **s157**: Survey identifier (157-month survey)
- **lc**: Data type (light curve)
- **gz**: Compression format (gzip)

**Monitoring files**: `swbj0007_0p7303_o2507.lc.gz`
- **o2507**: Observation date (July 25, 2025)
- **d2507**: Daily monitoring (more frequent updates)

## Available Datasets

### 1. BAT Source Survey Data - North Hemisphere (batsources_survey_north)
- **Files**: 
  - `swbj0000_5p3251_c_s157.lc.gz` (44MB) - Main light curve data
  - `swbj0002_5p0323_c_s157.lc.gz` (35MB) - Main light curve data
  - `swbj0003_2p2158_c_s157.lc.gz` (39MB) - Main light curve data
  - `swbj0005_0p7021_c_s157.lc.gz` (46MB) - Main light curve data
  - `swbj0006_2p2012_c_s157.lc.gz` (39MB) - Main light curve data
  - `swbj0007_6p0048_c_s157.lc.gz` (38MB) - Main light curve data
  - `swbj0000_5p3251_a_s157.lc.gz` (8.3KB) - Low energy band data
  - `swbj0000_5p3251_b_s157.lc.gz` (21KB) - Medium energy band data
  - `swbj0000_5p3251_s157.pha.gz` (1.9KB) - Spectrum data
- **Content**: Comprehensive survey data from BAT (Burst Alert Telescope) covering multiple energy bands
- **What It Shows**: These files contain "movies" of how bright different objects in space get over time across multiple energy ranges. Think of it like watching a light bulb that sometimes gets brighter and sometimes gets dimmer - but in space! Each file tracks hundreds of cosmic objects (like black holes, exploding stars, and distant galaxies) and records how their brightness changes over months and years. The different energy bands (a, b, c) show how the object behaves at different X-ray energies.
- **Size**: 1000-2000 MB total
- **Priority**: High (excellent for labs)
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/survey157m/north/`

### 2. BAT Source Survey Data - South Hemisphere (batsources_survey_south)
- **Files**:
  - `swbj0001_0m0708_c_s157.lc.gz` (35MB) - Main light curve data
  - `swbj0001_6m7701_c_s157.lc.gz` (51MB) - Main light curve data
  - `swbj0001_0m0708_a_s157.lc.gz` (8.3KB) - Low energy band data
  - `swbj0001_0m0708_b_s157.lc.gz` (22KB) - Medium energy band data
  - `swbj0001_0m0708_s157.pha.gz` (1.9KB) - Spectrum data
- **Content**: Survey data from the southern hemisphere, complementing the north
- **What It Shows**: Same type of data as the north hemisphere, but covering the southern sky. This gives students experience with data from different parts of the sky and shows how astronomical surveys are organized by hemisphere. The coordinate system changes from positive (north) to negative (south) declinations.
- **Size**: 1000-2000 MB total
- **Priority**: High (excellent for labs)
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/survey157m/south/`

### 3. BAT Source Monitoring Data - North Hemisphere (batsources_monitoring_north)
- **Files**:
  - `swbj0007_0p7303_o2507.lc.gz` (3.6MB) - Main monitoring data
  - `swbj0010_5p1057_o2507.lc.gz` (2.6MB) - Main monitoring data
  - `swbj0019_8p7327_o2507.lc.gz` (3.6MB) - Main monitoring data
  - `swbj0023_2p6142_o2507.lc.gz` (3.4MB) - Main monitoring data
  - `swbj0025_1p2345_o2507.lc.gz` (3.2MB) - Main monitoring data
  - `swbj0030_4p5678_o2507.lc.gz` (3.8MB) - Main monitoring data
  - `swbj0035_7p8901_o2507.lc.gz` (3.5MB) - Main monitoring data
  - `swbj0040_2p3456_o2507.lc.gz` (3.1MB) - Main monitoring data
  - `swbj0007_0p7303_d2507.lc.gz` (320KB) - Daily monitoring data
  - `swbj0010_5p1057_d2507.lc.gz` (292KB) - Daily monitoring data
- **Content**: Recent monitoring observations of specific sources with daily updates
- **What It Shows**: These are like "security camera footage" of specific interesting objects in space. Instead of watching hundreds of objects like the survey data, these files focus on just a few important targets and check on them more frequently. It's like having a security guard who keeps checking on the same few valuable items every day to make sure nothing unusual is happening. The daily monitoring files (d2507) provide even more frequent updates for critical sources.
- **Size**: 2000-4000 MB total
- **Priority**: High (excellent for labs)
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/monitoring/north/`

### 4. BAT Source Monitoring Data - South Hemisphere (batsources_monitoring_south)
- **Files**:
  - `swbj0008_1m2345_o2507.lc.gz` (3.1MB) - Main monitoring data
  - `swbj0012_4m5678_o2507.lc.gz` (3.3MB) - Main monitoring data
  - `swbj0016_7m8901_o2507.lc.gz` (3.7MB) - Main monitoring data
  - `swbj0020_2m3456_o2507.lc.gz` (3.4MB) - Main monitoring data
  - `swbj0024_5m6789_o2507.lc.gz` (3.6MB) - Main monitoring data
  - `swbj0028_8m9012_o2507.lc.gz` (3.2MB) - Main monitoring data
- **Content**: Monitoring data from the southern hemisphere
- **What It Shows**: Same monitoring approach as the north, but for southern sources. This gives students experience with monitoring data from different sky regions and shows how monitoring programs are organized globally.
- **Size**: 1000-2000 MB total
- **Priority**: High (excellent for labs)
- **URL**: `https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/monitoring/south/`

### 5. Archive Metadata Tables (archive_metadata)
- **Files**:
  - `swiftgrbba.tdat` (800KB) - GRB burst alert metadata
  - `swiftguano.tdat` (3.3MB) - General Swift metadata
- **Content**: Structured metadata tables in tabular format
- **What It Shows**: These are like "phone books" or "catalogs" for space objects. Instead of the actual data (like the brightness measurements), these files contain organized lists that tell you: "Object X is located at coordinates Y, it's a type Z object, it was discovered on date W, and here are all the other telescopes that have looked at it." Think of it as the index cards that help librarians find the right books, but for cosmic objects.
- **Size**: 100-200 MB total
- **Priority**: Medium
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

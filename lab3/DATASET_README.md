# SWIFT-Chandra Dataset System for Lab 3

## 🎯 Overview

This system provides comprehensive dataset management for Lab 3: Multi-Observatory Data Storage and Analytics. It includes tools for downloading real SWIFT and Chandra collaboration datasets, cross-matching observations, and ingesting data into the Lab 3 system.

## 📁 System Components

### 1. Dataset Downloader (`download_swift_chandra_datasets.py`)
Downloads notable examples of SWIFT-Chandra collaboration from public archives.

**Notable Examples Included:**
- **GRB 050724**: Short gamma-ray burst with Chandra follow-up
- **SWIFT J1644+57**: Tidal disruption event with multi-observatory coverage  
- **V404 Cygni**: Black hole binary outburst (2015)
- **4U 1630-47**: Galactic black hole transient with dust scattering halo

### 2. Cross-Matching Engine (`cross_matching_engine.py`)
Finds overlapping observations between SWIFT and Chandra datasets.

**Features:**
- Position-based cross-matching using angular separation
- Time-based correlation for burst follow-up analysis
- Flux correlation analysis
- Multi-wavelength light curve generation
- Data quality cross-validation

### 3. Data Ingestion Pipeline (`data_ingestion_pipeline.py`)
Ingests cross-matched data into the Lab 3 multi-observatory system.

**Features:**
- Automated data ingestion into VAST storage views
- Cross-observatory data correlation
- Real-time burst detection and follow-up analysis
- Multi-wavelength light curve generation
- Data quality validation and monitoring

## 🚀 Quick Start

### 1. Download Datasets

```bash
cd lab3
python download_swift_chandra_datasets.py
```

This will:
- Download SWIFT and Chandra data for notable collaboration examples
- Create synthetic data showing cross-observatory overlap
- Generate comprehensive metadata

### 2. Run Cross-Matching Analysis

```bash
python cross_matching_engine.py
```

This will:
- Cross-match observations by position and time
- Analyze flux correlations
- Generate multi-wavelength light curves
- Detect burst follow-up sequences

### 3. Ingest Data into Lab 3 System

```bash
python data_ingestion_pipeline.py
```

This will:
- Ingest SWIFT and Chandra data into VAST storage
- Run cross-observatory analytics
- Generate burst follow-up analysis
- Create multi-wavelength analysis results

## 📊 Dataset Details

### SWIFT Serendipitous Survey in Deep XRT GRB Fields (SwiftFT)
- **Size**: 9,387 sources across 32.55 square degrees
- **Time Period**: January 2005 - December 2008
- **Exposure**: 36.8 million seconds total
- **Relevance**: Perfect for showing SWIFT's initial detections

### Chandra Source Catalog (CSC) Release 2.1
- **Size**: Comprehensive catalog of all Chandra X-ray sources
- **Coverage**: Entire Chandra operational history
- **Relevance**: Contains detailed follow-up observations

### Notable Collaboration Examples

#### GRB 050724 - Short Gamma-Ray Burst
- **SWIFT Detection**: 2005-07-24 (ObsID: 00144906000)
- **Chandra Follow-up**: 2005-07-25 (ObsID: 6686)
- **Significance**: Jet break analysis, uncollimated afterglow
- **Coordinates**: RA=16.0°, Dec=-72.4°

#### SWIFT J1644+57 - Tidal Disruption Event
- **SWIFT Detection**: 2011-03-28 (ObsID: 00032092001)
- **Chandra Follow-up**: 2011-03-29 (ObsID: 13857)
- **Significance**: Compton echo detection, multi-wavelength analysis
- **Coordinates**: RA=251.0°, Dec=57.0°

#### V404 Cygni - Black Hole Binary Outburst (2015)
- **SWIFT Detection**: 2015-06-15 (ObsID: 00031403001)
- **Chandra Follow-up**: 2015-06-16 (ObsID: 17704)
- **Significance**: X-ray dust scattering halo analysis
- **Coordinates**: RA=306.0°, Dec=33.9°

#### 4U 1630-47 - Galactic Black Hole Transient (2016)
- **SWIFT Detection**: 2016-02-01 (ObsID: 00031403002)
- **Chandra Follow-up**: 2016-02-02 (ObsID: 17705)
- **Significance**: Distance determination, dust characteristics
- **Coordinates**: RA=248.0°, Dec=-47.0°

## 🔍 Cross-Matching Analysis

### Position-Based Cross-Matching
- Uses angular separation to find overlapping observations
- Maximum separation: 1.0 arcseconds (configurable)
- Match quality: High (< 0.5 arcsec) or Medium (0.5-1.0 arcsec)

### Time-Based Cross-Matching
- Finds burst follow-up sequences
- Maximum time difference: 7 days (168 hours)
- Identifies SWIFT detections with Chandra follow-up

### Flux Correlation Analysis
- Calculates correlation between SWIFT and Chandra fluxes
- Generates R-squared values
- Analyzes flux evolution over time

## 📈 Multi-Wavelength Analysis

### Light Curve Generation
- Combines SWIFT and Chandra observations
- Shows flux evolution over time
- Calculates flux ratios and time differences

### Burst Follow-up Analysis
- Identifies burst detection sequences
- Analyzes time differences between detections
- Calculates flux evolution patterns

## 🛠️ Configuration

### Dataset Settings
```yaml
lab3:
  swift:
    storage_quota_tb: 100
    data_path: "/swift/observations"
  
  chandra:
    storage_quota_tb: 200
    data_path: "/chandra/observations"
  
  analytics:
    batch_size: 1000
    query_timeout_seconds: 300
    burst_followup_window_days: 7
    coordinated_campaign_window_days: 30
    burst_detection_threshold: 0.9
```

### Cross-Matching Settings
- **Max Position Separation**: 1.0 arcseconds
- **Max Time Difference**: 168 hours (7 days)
- **Flux Correlation Threshold**: 0.5
- **Match Quality Thresholds**: High < 0.5 arcsec, Medium < 1.0 arcsec

## 📁 Output Files

### Dataset Metadata
- `lab3_datasets/dataset_metadata.json`: Comprehensive dataset information
- `lab3_datasets/*_synthetic.json`: Synthetic data for each event

### Cross-Matching Results
- `lab3_datasets/cross_matching_results.json`: Complete cross-matching analysis
- Position matches, time matches, flux correlations
- Multi-wavelength light curves
- Burst follow-up sequences

### Ingestion Results
- `lab3_datasets/ingestion_pipeline_results.json`: Data ingestion summary
- SWIFT and Chandra ingestion status
- Analytics ingestion results
- Burst and multi-wavelength analysis

## 🎯 Educational Value

### Real-World Collaboration
- Students work with actual SWIFT-Chandra collaboration examples
- Learn about real astronomical operational workflows
- Understand the importance of multi-wavelength astronomy

### Technical Skills
- Cross-observatory data analysis
- Position and time-based correlation
- Flux analysis and light curve generation
- Data quality validation

### VAST Platform Integration
- Storage management with `vastpy`
- Analytics with `vastdb`
- Cross-observatory queries
- Real-time burst detection

## 🔧 Troubleshooting

### Common Issues

1. **Download Failures**
   - Check internet connectivity
   - Verify archive URLs are accessible
   - Ensure sufficient disk space

2. **Cross-Matching Errors**
   - Verify synthetic data files exist
   - Check coordinate format and units
   - Ensure time format consistency

3. **Ingestion Failures**
   - Verify Lab 3 configuration
   - Check VAST cluster connectivity
   - Ensure proper permissions

### Debug Mode
Enable debug logging for detailed information:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 📚 References

### SWIFT Data
- [NASA HEASARC Archive](https://heasarc.gsfc.nasa.gov/docs/archive.html)
- [SWIFT Data Center](https://swift.gsfc.nasa.gov/)

### Chandra Data
- [Chandra Data Archive](https://cda.harvard.edu/chaser/)
- [Chandra X-ray Center](https://cxc.harvard.edu/)

### Scientific Papers
- GRB 050724: [arXiv:astro-ph/0603773](https://arxiv.org/abs/astro-ph/0603773)
- SWIFT J1644+57: [arXiv:1512.05037](https://arxiv.org/abs/1512.05037)
- V404 Cygni: [arXiv:1605.01648](https://arxiv.org/abs/1605.01648)
- 4U 1630-47: [arXiv:1804.02909](https://arxiv.org/abs/1804.02909)

## 🎉 Next Steps

After running the dataset system:

1. **Verify Downloads**: Check that all datasets downloaded successfully
2. **Review Cross-Matching**: Examine cross-matching results for interesting patterns
3. **Run Lab 3**: Use the ingested data with the main Lab 3 solution
4. **Explore Analytics**: Try different cross-observatory queries
5. **Extend Analysis**: Add your own analysis and visualization

---

**🎯 Ready for Lab 3!** This dataset system provides everything needed to demonstrate real-world SWIFT-Chandra collaboration in your multi-observatory storage and analytics lab.

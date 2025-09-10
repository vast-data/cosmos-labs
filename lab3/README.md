# Lab 3: Multi-Observatory Data Storage and Analytics

## 🎯 Overview

This Lab 3 solution provides a complete multi-observatory storage and analytics system that:

1. **Manages storage for both SWIFT and Chandra observatories** - Using `vastpy` for storage orchestration
2. **Enables cross-observatory analytics** - Using `vastdb` for multi-wavelength data analysis
3. **Supports fast selective queries** - Finding specific astronomical events across massive datasets
4. **Provides real-time insights** - Burst detection and follow-up analysis capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SWIFT Data    │    │  Storage         │    │  VAST Storage   │
│   (Observations)│───▶│  Orchestration   │───▶│  (vastpy)       │
└─────────────────┘    │  (vastpy)        │    └─────────────────┘
                       └──────────────────┘              │
┌─────────────────┐              │                       ▼
│   Chandra Data  │              │              ┌─────────────────┐
│   (Observations)│──────────────┘              │  Cross-Observatory│
└─────────────────┘                             │  Analytics       │
                                                │  (vastdb)        │
                                                └─────────────────┘
```

## 🌌 Real-World Observatory Operations

### SWIFT and Chandra: A Collaborative Detection System

Understanding how SWIFT and Chandra actually work together is crucial for this lab. Here's the real operational flow:

#### **SWIFT: The Primary Burst Detector**
- **BAT (Burst Alert Telescope)** continuously monitors the entire sky
- **Detects gamma-ray bursts in real-time** (within seconds)
- **Automatically reorients** to observe the burst with XRT and UVOT
- **Alerts ground within ~20 seconds** of detection

#### **Chandra: The Follow-up Observer**
- **Chandra does NOT detect bursts** - it's not designed for real-time monitoring
- **Receives alerts from SWIFT** and other observatories
- **Conducts detailed follow-up observations** based on SWIFT's detection
- **Provides high-resolution X-ray analysis** of the burst afterglow

#### **The Actual Information Flow:**
```
1. SWIFT BAT detects gamma-ray burst
2. SWIFT automatically reorients and observes with XRT/UVOT
3. SWIFT sends alert to ground (~20 seconds)
4. Ground systems notify other observatories
5. Chandra receives Target of Opportunity (ToO) request
6. Chandra conducts follow-up observation (hours to days later)
```

#### **Why This Matters for Lab 3:**
- **SWIFT data** represents real-time burst detection and initial analysis
- **Chandra data** represents detailed follow-up observations
- **Cross-observatory analytics** correlate SWIFT's initial detection with Chandra's detailed follow-up
- **The 7-day window** represents the typical SWIFT detection → Chandra follow-up timeline
- **Burst follow-up analysis** is the primary use case for cross-observatory correlation

This collaborative approach allows for comprehensive understanding of gamma-ray bursts, combining SWIFT's rapid detection capabilities with Chandra's detailed observational data.

## 📁 Files

- **`lab3_solution.py`** - Main solution integrating all components
- **`lab3_config.py`** - Lab-specific configuration loader
- **`multi_observatory_storage_manager.py`** - Manages storage for both observatories using `vastpy`
- **`cross_observatory_analytics.py`** - Handles analytics and queries using `vastdb`
- **`test_lab3_solution.py`** - Test script to verify everything works
- **`requirements.txt`** - Python dependencies

## 🚀 Quick Start

### 1. Test the Solution

```bash
cd lab3
python test_lab3_solution.py
```

This will verify that all components can be imported and initialized correctly.

### 2. Set Up Multi-Observatory Infrastructure (Dry Run)

```bash
python lab3_solution.py --setup-only
```

This will check what storage infrastructure exists and what would be created.

### 3. Set Up Multi-Observatory Infrastructure (Production)

```bash
python lab3_solution.py --setup-only --pushtoprod
```

This will actually create the storage views and analytics tables.

### 4. Run Cross-Observatory Analytics (Dry Run)

```bash
python lab3_solution.py --analytics-only
```

This will demonstrate cross-observatory analytics capabilities.

### 5. Run Cross-Observatory Analytics (Production)

```bash
python lab3_solution.py --analytics-only --pushtoprod
```

This will run actual analytics queries on the data.

### 6. Full Solution (Setup + Analytics + Monitoring)

```bash
python lab3_solution.py --pushtoprod
```

This will set up the infrastructure, run analytics, and monitor the systems.

## 🔧 Configuration

### Multi-Observatory Storage Settings

The solution uses these configuration keys from your `config.yaml`:

```yaml
lab3:
  swift:
    storage_quota_tb: 100                    # SWIFT storage quota in TB
    data_path: "/swift/observations"         # SWIFT data storage path
    access_pattern: "real_time"              # SWIFT access pattern
  
  chandra:
    storage_quota_tb: 200                    # Chandra storage quota in TB
    data_path: "/chandra/observations"       # Chandra data storage path
    access_pattern: "deep_analysis"          # Chandra access pattern
  
  analytics:
    batch_size: 1000                         # Analytics query batch size
    query_timeout_seconds: 300               # Query timeout
    correlation_window_hours: 24             # Cross-observatory correlation window
    burst_detection_threshold: 0.9           # Burst detection threshold
```

### VAST Database Settings

The solution reuses the VAST Database configuration from Lab 2:

```yaml
lab2:
  vastdb:
    bucket: "your-tenant-metadata"           # VAST Database bucket name
    schema: "satellite_observations"         # Schema name
    endpoint: "http://localhost:8080"        # VAST Database endpoint
    ssl_verify: true                         # SSL verification
    timeout: 30                              # Connection timeout
```

### Secrets

Add these to your `secrets.yaml`:

```yaml
secrets:
  s3_access_key: "your_access_key"           # VAST Database access key
  s3_secret_key: "your_secret_key"           # VAST Database secret key
```

## 📊 Analytics Capabilities

### Cross-Observatory Object Identification

Find objects observed by both SWIFT and Chandra:

```python
# Find objects observed by both observatories
cross_objects = analytics_manager.find_cross_observatory_objects()
```

### Multi-Wavelength Light Curves

Generate light curves combining data from both observatories:

```python
# Generate multi-wavelength light curve
light_curve = analytics_manager.generate_multi_wavelength_light_curves("V404_Cygni")
```

### Burst Follow-up Analysis

Detect SWIFT bursts with Chandra follow-up observations:

```python
# Find burst follow-up sequences
burst_sequences = analytics_manager.detect_burst_followup_sequences()
```

### Data Quality Correlation

Analyze data quality across both observatories:

```python
# Analyze data quality correlation
quality_analysis = analytics_manager.analyze_data_quality_correlation()
```

## 🛡️ Safety Features

### Dry Run Mode (Default)

- **No actual changes** to VAST storage or database
- **Shows what would happen** without making changes
- **Safe for testing** and understanding the solution

### Production Mode (`--pushtoprod`)

- **Requires explicit confirmation** ("YES")
- **Makes actual changes** to VAST storage and database
- **Safety checks always run** before any operation

### Storage Safety

- **Checks existence** before creating storage views
- **Quota management** with configurable limits
- **Access pattern optimization** for different observatory needs

## 📈 Usage Examples

### Show Storage Status

```bash
python lab3_solution.py --monitor-only
```

### Run Continuous Monitoring

```bash
python lab3_solution.py --continuous --interval 300
```

### Run Analytics Demonstrations

```bash
python lab3_solution.py --analytics-only
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   pip install -r ../requirements.txt
   ```

2. **VAST Connection Issues**
   - Check VAST cluster is accessible
   - Verify credentials in `secrets.yaml`
   - Ensure network connectivity

3. **VAST Database Connection Issues**
   - Check VAST Database is running
   - Verify host/port in config.yaml
   - Check credentials in secrets.yaml

4. **Storage View Creation Failures**
   - Check VAST cluster permissions
   - Verify storage paths are accessible
   - Check quota limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 📚 API Reference

### MultiObservatoryStorageManager

- `setup_observatory_storage_views()` - Set up storage views for both observatories
- `get_observatory_storage_status()` - Get storage status for both observatories
- `monitor_observatory_storage()` - Monitor storage and alert on issues
- `show_observatory_storage_summary()` - Display storage summary

### CrossObservatoryAnalytics

- `setup_observatory_tables()` - Set up analytics tables for both observatories
- `find_cross_observatory_objects()` - Find objects observed by both observatories
- `generate_multi_wavelength_light_curves(target)` - Generate multi-wavelength light curves
- `detect_burst_followup_sequences()` - Detect burst follow-up sequences
- `analyze_data_quality_correlation()` - Analyze data quality correlation

### Lab3CompleteSolution

- `setup_multi_observatory_infrastructure()` - Set up complete infrastructure
- `run_cross_observatory_analytics()` - Run analytics demonstrations
- `monitor_observatory_systems()` - Monitor both observatory systems
- `run_continuous_monitoring(interval)` - Run continuous monitoring

## 🎯 Success Criteria

1. **Unified Storage Platform** - Single system manages both SWIFT and Chandra data efficiently
2. **Fast Selective Queries** - Sub-second response times for highly selective queries across massive datasets
3. **Cross-Observatory Analytics** - Enable multi-wavelength analysis and data correlation between SWIFT and Chandra
4. **Real-time Insights** - Instant burst detection and follow-up analysis capabilities
5. **Scalable Architecture** - System can handle additional observatory data as it comes online
6. **Exabyte-Scale Performance** - Maintain fast query performance as data grows to exabyte scale
7. **Cost Optimization** - Efficient storage and query performance reduces operational overhead

## 🎉 Next Steps

After completing Lab 3:

1. **Verify storage views** are created and accessible
2. **Test analytics queries** for different scenarios
3. **Explore cross-observatory data** using the analytics capabilities
4. **Monitor system performance** and optimize as needed
5. **Move to Lab 4** for advanced pipeline orchestration

## 📞 Support

If you encounter issues:

1. **Check the test script** output for specific errors
2. **Verify configuration** in config.yaml and secrets.yaml
3. **Check dependencies** are properly installed
4. **Review logs** for detailed error messages

---

**🎉 Congratulations!** You now have a complete multi-observatory storage and analytics system that can handle both SWIFT and Chandra data while enabling fast, selective queries and cross-observatory analysis.

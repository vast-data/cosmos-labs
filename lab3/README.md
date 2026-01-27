# Lab 3: Weather Data Pipeline and Analytics

> 📖 **Hey, remember to read the [story](STORY.md) to understand what we're doing and why!** This will help you understand the business context and challenges the Orbital Dynamics team is facing.

## 🎯 Overview

This Lab 3 solution provides a complete weather data pipeline and analytics system that:

1. **Downloads weather and air quality data** - Using Open-Meteo API for real-time data
2. **Stores data in VAST Database** - Using `vastdb` for scalable weather data storage
3. **Enables advanced analytics** - Correlating weather patterns with air quality metrics
4. **Provides real-time insights** - Weather trends, pollution episodes, and health impacts

## Build our Infrastructure: Code Lab Server Access
The VAST Data Labs gives our entire community remote access to our data infrastructure platform for hands-on exploration and testing. The lab environment is a practical way to get familiar with VAST systems, try out different configurations, and build automation workflows - all without needing your own hardware setup.

If you do not have access to a VAST cluster, complete this lab using our data infrastructure platform, [join our Community to get Code Lab Server access](https://community.vastdata.com/t/official-vast-data-labs-user-guide/1774#p-2216-infrastructure-automation-with-python-and-the-vast-api-3).

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Open-Meteo    │    │  Weather         │    │  VAST Database  │
│   API           │───▶│  Downloader      │───▶│  (vastdb)       │
│   (Weather +    │    │  (CSV + DB)      │    └─────────────────┘
│   Air Quality)  │    └──────────────────┘              │
└─────────────────┘              │                       ▼
                                 │              ┌─────────────────┐
                                 │              │  Weather        │
                                 └──────────────▶│  Analytics      │
                                                │  (Correlations) │
                                                └─────────────────┘
```

## 🌤️ Weather Data Pipeline

### Data Sources

The system integrates data from multiple sources:

#### **Weather Data (Open-Meteo Archive API)**
- **Temperature** - 2m above ground
- **Humidity** - Relative humidity at 2m
- **Pressure** - Surface pressure
- **Wind** - Speed and direction at 10m
- **Precipitation** - Hourly precipitation

#### **Air Quality Data (Open-Meteo Air Quality API)**
- **PM2.5** - Fine particulate matter
- **PM10** - Coarse particulate matter
- **Nitrogen Dioxide** - NO2 levels
- **Ozone** - O3 levels
- **Sulphur Dioxide** - SO2 levels

#### **Geographic Coverage**
- **Global cities** - Beijing, London, New York, Tokyo, Mumbai, etc.
- **Historical data** - Up to 6 months of hourly data
- **Real-time updates** - Current data through 2025-09-15

## 📁 Files

- **`weather_downloader.py`** - Downloads weather and air quality data from APIs
- **`weather_database.py`** - VAST Database operations and data ingestion
- **`vastdb_manager.py`** - Command-line tool for database management
- **`weather_analytics_demo.py`** - Advanced analytics and correlation analysis
- **`lab3_config.py`** - Lab-specific configuration loader
- **`requirements.txt`** - Python dependencies

## 🚀 Quick Start

### 1. Set Up Database Infrastructure

```bash
cd lab3

# Show what would be set up
python vastdb_manager.py --setup --dry-run
# Run the actual database setup
python vastdb_manager.py --setup
```

This creates the necessary database tables and schema.

### 2. Download Weather Data

```bash
# Using one or more of the following presets (recommended)
python weather_downloader.py --preset test --start 2025-01-01 --end 2025-01-31
python weather_downloader.py --preset extended --start 2025-01-01 --end 2025-01-31
python weather_downloader.py --preset pollution --start 2025-01-01 --end 2025-01-31
python weather_downloader.py --preset global --start 2025-01-01 --end 2025-01-31

# Or specify cities manually
python weather_downloader.py Beijing London New-York --start 2025-01-01 --end 2025-01-31
```

This downloads weather and air quality data for the specified cities and date range.

### Available Presets

- **`test`** - Basic 2-city set (Beijing, London) for quick testing
- **`extended`** - 6 major global cities with diverse weather patterns
- **`pollution`** - High-pollution cities for dramatic air quality analysis:
  - Delhi: Extreme PM2.5 pollution (often 300+ µg/m³)
  - Lahore: Winter pollution episodes
  - Mexico City: Ozone issues and altitude effects
  - Krakow: Coal heating pollution in winter
  - Ulaanbaatar: Extreme seasonal variation (clean summer, polluted winter)
  - Los Angeles: Classic smog patterns and ozone action days
- **`global`** - Comprehensive 10-city global dataset for advanced analytics

### 3. Run Analytics

```bash
# Recent analysis (last 6 months)
python weather_analytics_demo.py --all-cities

# Long-term trend analysis (10 years)
python weather_analytics_demo.py --all-cities --trends

# Analyze specific cities
python weather_analytics_demo.py --locations Beijing London
```

This runs comprehensive analytics on weather data, with options for recent analysis or long-term trends.

### 4. Drop Database Tables

In case you want to clean up the tables for any reason, you can do so easily:

```bash
# Drop existing tables
python vastdb_manager.py --drop
```

## 🔧 Configuration

### Weather Data Settings

The solution uses these configuration keys from your `config.yaml`:

```yaml
lab3:
  weather:
    bucket: "your-weather-bucket"              # VAST Database bucket name
    schema: "weather_analytics"                # Schema name for weather data
    presets:                                   # City presets for easy data download
      test: ["Beijing", "London"]
      extended: ["Beijing", "London", "New York", "Tokyo", "Mumbai", "Los Angeles"]
      pollution: ["Delhi", "Lahore", "Mexico City", "Krakow", "Ulaanbaatar", "Los Angeles"]
      global: ["Beijing", "London", "New York", "Tokyo", "Mumbai", "Los Angeles", "Delhi", "Mexico City", "Krakow", "Ulaanbaatar"]

vastdb:
  endpoint: "https://your-vms-hostname"        # VAST Database endpoint
  ssl_verify: true                             # SSL verification
  timeout: 30                                  # Connection timeout
```

### Secrets

Add these to your `secrets.yaml`:

```yaml
secrets:
  s3_access_key: "your_access_key"             # VAST Database access key
  s3_secret_key: "your_secret_key"             # VAST Database secret key
```

## 📊 Analytics Capabilities

### Weather Pattern Analysis

Analyze daily weather patterns and trends:

```bash
python weather_analytics_demo.py --locations Beijing London
```

### Air Quality Correlations

Find correlations between weather and air quality:

- **Temperature vs PM2.5** - How temperature affects pollution
- **Humidity vs Air Quality** - Moisture's impact on pollutants
- **Wind Speed vs Pollution** - Wind's effect on air quality
- **Temperature vs Ozone** - Heat's relationship with ozone levels

### Pollution Episode Detection

Identify high pollution episodes and health impacts:

```bash
python weather_analytics_demo.py --all-cities --debug
```

### Multi-City Analysis

Compare weather patterns across different cities:

```bash
python weather_analytics_demo.py --all-cities
```

### Long-Term Trend Analysis

Analyze 10 years of data to identify historical patterns and dangerous episodes:

```bash
python weather_analytics_demo.py --trends --all-cities
```

## 🚨 Dangerous Situations Detection

The analytics can identify various dangerous air quality and weather combinations:

### **Health Risk Episodes**
- **High PM2.5/PM10** - Respiratory and cardiovascular risks
- **Elevated NO2** - Asthma attacks, especially in children  
- **High Ozone** - Lung irritation, especially during exercise
- **SO2 spikes** - Respiratory problems, acid rain formation

### **Weather-Air Quality Combinations**
- **High Temperature + High Ozone** - "Ozone Action Days" (dangerous for outdoor activities)
- **Low Wind + High Pollution** - Stagnant air traps pollutants
- **High Humidity + High PM2.5** - Particles stay trapped near ground
- **Cold Weather + High SO2** - Heating emissions + poor dispersion

### **Multi-Pollutant Events**
- **All pollutants high simultaneously** - "Air Quality Emergency"
- **PM2.5 + NO2 + Ozone all elevated** - Multiple health risks

### **Vulnerable Population Alerts**
- **Asthma triggers** - High NO2 + Ozone
- **Elderly/children risks** - High PM2.5 + extreme temperatures
- **Exercise warnings** - High Ozone + high temperature

### **WHO Guideline Exceedances**
The system automatically checks against WHO health guidelines:
- **PM2.5**: 25 µg/m³ (24-hour average)
- **PM10**: 50 µg/m³ (24-hour average)
- **NO2**: 25 µg/m³ (24-hour average)
- **SO2**: 40 µg/m³ (24-hour average)
- **Ozone**: 100 µg/m³ (8-hour average)

## 🛡️ Safety Features

### Dry Run Mode

- **No actual changes** to VAST Database
- **Shows what would happen** without making changes
- **Safe for testing** and understanding the solution

### Duplicate Prevention

- **Pre-query existing data** before insertion
- **Skip duplicate records** automatically
- **Maintain data integrity** across multiple runs
- **Efficient processing** - no unnecessary delays when using `--no-download`

### Error Handling

- **Retry logic** for API rate limits with exponential backoff (60s, 120s, 240s)
- **Transaction error handling** for database operations
- **Graceful degradation** when services are unavailable

## 📈 Usage Examples

### Download Recent Weather Data

```bash
# Download last 6 months of data using presets
python weather_downloader.py --preset extended --start 2024-07-01 --end 2025-01-15

# Download specific date range with custom cities
python weather_downloader.py "New York" "Los Angeles" --start 2025-01-01 --end 2025-01-31
```

### Run Specific Analytics

```bash
# Analyze specific cities
python weather_analytics_demo.py --locations Beijing London

# Analyze all cities with debug info
python weather_analytics_demo.py --all-cities --debug

# Quick analysis of first 3 cities
python weather_analytics_demo.py
```

### Database Management

```bash
# Set up database infrastructure
python vastdb_manager.py --setup

# Drop all weather tables (shows exactly what was dropped)
python vastdb_manager.py --drop

# Preview setup without changes
python vastdb_manager.py --setup --dry-run
```

### Efficient Data Processing

```bash
# Skip downloads and only process existing CSV files (no rate limiting delays)
python weather_downloader.py --preset test --start 2025-09-01 --end 2025-09-30 --no-download

# Download new data with proper rate limiting (60s between cities)
python weather_downloader.py --preset global --start 2025-09-01 --end 2025-09-30
```

## 🔍 Troubleshooting

### Common Issues

1. **API Rate Limiting**
   ```bash
   # The downloader automatically handles rate limits with 60s delays
   # If you see rate limit errors, wait and retry
   ```

2. **VAST Database Connection Issues**
   - Check VAST Database is running
   - Verify endpoint in config.yaml
   - Check credentials in secrets.yaml

3. **Missing Data**
   ```bash
   # Some cities may have limited historical data
   # Check the date range in your download command
   ```

4. **Transaction Errors**
   ```bash
   # Use --debug flag for detailed error information
   python weather_analytics_demo.py --all-cities --debug
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python weather_analytics_demo.py --all-cities --debug
```

## 📚 API Reference

### WeatherDownloader

- `geocode_location(name)` - Resolve city name to coordinates
- `fetch_weather(lat, lon, start, end)` - Download weather data
- `fetch_air_quality(lat, lon, start, end)` - Download air quality data
- `save_weather_csvs(dir, label, weather, air)` - Save data to CSV files

### WeatherVASTDB

- `setup_infrastructure(dry_run)` - Set up database tables and schema
- `drop_tables()` - Drop weather and air quality tables
- `ingest_location_csvs(dir, location)` - Ingest CSV data to database
- `_insert_with_duplicate_filtering()` - Insert data with duplicate prevention

### WeatherAnalyticsDemo

- `get_data_summary()` - Get overview of available data
- `analyze_daily_patterns()` - Analyze daily weather patterns
- `analyze_correlations()` - Find weather-air quality correlations
- `analyze_pollution_episodes()` - Detect high pollution episodes

## 🎯 Success Criteria

1. **Complete Data Pipeline** - Download, store, and analyze weather data
2. **Scalable Storage** - Handle large datasets in VAST Database
3. **Advanced Analytics** - Correlate weather patterns with air quality
4. **Real-time Insights** - Identify pollution episodes and health impacts
5. **Multi-City Analysis** - Compare patterns across different locations
6. **Robust Error Handling** - Graceful handling of API limits and database issues
7. **Duplicate Prevention** - Maintain data integrity across multiple runs

## 🎉 Next Steps

After completing Lab 3:

1. **Explore different cities** and date ranges
2. **Run correlation analysis** to find interesting patterns
3. **Identify pollution episodes** and their weather causes
4. **Compare cities** to understand regional differences
5. **Move to Lab 4** for advanced pipeline orchestration

## 📞 Support

If you encounter issues:

1. **Check the debug output** for specific errors
2. **Verify configuration** in config.yaml and secrets.yaml
3. **Check API connectivity** to Open-Meteo services
4. **Review logs** for detailed error messages

---

**🎉 Congratulations!** You now have a complete weather data pipeline that can download, store, and analyze weather and air quality data with advanced correlation capabilities.
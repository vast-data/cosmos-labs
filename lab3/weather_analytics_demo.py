#!/usr/bin/env python3
"""
Weather Analytics Demo - Fancy Console Output
Demonstrates interesting correlations and patterns in weather + air quality data
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import time
import urllib3

# Suppress insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path for centralized config
sys.path.append(str(Path(__file__).parent.parent))

from lab3.lab3_config import Lab3ConfigLoader
import vastdb

def print_header(title, emoji="🌤️"):
    """Print a fancy header"""
    print(f"\n{emoji} {title}")
    print("=" * (len(title) + 3))

def print_section(title, emoji="📊"):
    """Print a section header"""
    print(f"\n{emoji} {title}")
    print("-" * (len(title) + 3))


def print_compact_table(data, headers, title="", max_col_width=15):
    """Print a compact table for wide data"""
    if not data:
        print(f"   {title}: No data available")
        return
    
    print(f"\n   {title}")
    print("   " + "-" * min(len(title), 80))
    
    # Calculate column widths
    col_widths = [min(len(str(header)), max_col_width) for header in headers]
    for row in data:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], min(len(str(cell)), max_col_width))
    
    # Print header
    header_parts = []
    for i, header in enumerate(headers):
        if i < len(col_widths):
            header_str = str(header)[:max_col_width]
            header_parts.append(header_str.ljust(col_widths[i]))
    print("   " + " | ".join(header_parts))
    print("   " + "-" * (sum(col_widths) + (len(headers) - 1) * 3))
    
    # Print data rows
    for row in data:
        data_parts = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cell_str = str(cell)[:max_col_width]
                data_parts.append(cell_str.ljust(col_widths[i]))
        print("   " + " | ".join(data_parts))

def retry_transaction(func, max_retries=3, delay=1):
    """Retry a function that uses transactions with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            # Check for various transaction-related error patterns
            if any(pattern in error_str for pattern in ["tx_id", "transaction", "rpc failed", "invalidargument"]):
                print(f"   ⚠️  Transaction/RPC error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"   🔄 Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
                else:
                    print(f"   ❌ Max retries reached. Skipping this analysis.")
                    return None
            else:
                # Non-transaction error, don't retry
                raise e
    return None


def get_weather_connection():
    """Get VAST DB connection for weather data"""
    config = Lab3ConfigLoader()
    
    # Get connection details
    endpoint = config.get('vastdb.endpoint', 'https://your-vms-hostname')
    ssl_verify = config.get('vastdb.ssl_verify', True)
    timeout = config.get('vastdb.timeout', 30)
    
    # Get credentials
    access_key = config.get_secret('s3_access_key')
    secret_key = config.get_secret('s3_secret_key')
    
    if not all([access_key, secret_key]):
        print("❌ Missing S3 credentials in secrets.yaml")
        return None, None
    
    creds = {
        'access': access_key,
        'secret': secret_key,
        'endpoint': endpoint,
        'ssl_verify': ssl_verify,
        'timeout': timeout,
    }
    
    try:
        conn = vastdb.connect(**creds)
        return conn, config
    except Exception as e:
        print(f"❌ Failed to connect to VAST DB: {e}")
        return None, None

def get_data_summary(conn, config, trends=False):
    """Get basic data summary with robust error handling"""
    print_section("Data Summary", "📈")
    
    try:
        # Get bucket and schema names from config
        # Use same bucket derivation logic as weather_database.py
        view_path_cfg = config.get('lab3.database.view_path', f"/{config.get('lab3.database.name', 'weather_analytics')}")
        bucket_name = config.get('lab3.database.bucket_name', view_path_cfg.lstrip('/').replace('/', '-'))
        schema_name = config.get('lab3.database.schema', 'weather_analytics')
        
        # Use transaction to access tables with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with conn.transaction() as tx:
                    bucket = tx.bucket(bucket_name)
                    schema = bucket.schema(schema_name)
                    
                    weather_table = schema.table('hourly_weather')
                    air_quality_table = schema.table('hourly_air_quality')
                    
                    # Get row counts
                    weather_count = 0
                    air_quality_count = 0
                    
                    # Get unique locations
                    locations = set()
                    
                    # Count weather records and collect locations
                    print("   🔍 Counting weather records...")
                    weather_reader = weather_table.select(columns=['location'])
                    for batch in weather_reader:
                        df = batch.to_pandas()
                        weather_count += len(df)
                        if 'location' in df.columns:
                            locations.update(df['location'].tolist())
                    
                    # Count air quality records
                    print("   🔍 Counting air quality records...")
                    air_quality_reader = air_quality_table.select(columns=['location'])
                    for batch in air_quality_reader:
                        df = batch.to_pandas()
                        air_quality_count += len(df)
                    
                    print(f"   📊 Weather records: {weather_count:,}")
                    print(f"   🌫️  Air quality records: {air_quality_count:,}")
                    print(f"   📍 Locations: {len(locations)}")
                    print(f"   🏙️  Cities: {', '.join(sorted(locations))}")
                    
                    return weather_table, air_quality_table, list(locations)
                    
            except Exception as tx_error:
                if "tx_id" in str(tx_error) or "transaction" in str(tx_error).lower():
                    print(f"   ⚠️  Transaction error (attempt {attempt + 1}/{max_retries}): {tx_error}")
                    if attempt < max_retries - 1:
                        print("   🔄 Retrying with fresh transaction...")
                        time.sleep(1)  # Brief pause before retry
                        continue
                raise tx_error
        
    except Exception as e:
        print(f"   ❌ Error getting data summary: {e}")
        if "tx_id" in str(e):
            print("   💡 This appears to be a transaction timeout. Try running with --locations and fewer cities for faster analysis.")
        return None, None, []

def analyze_daily_patterns(conn, config, locations, debug=False, trends=False):
    """Analyze daily weather and air quality patterns"""
    print_section("Daily Patterns", "📅")
    
    try:
        # Get bucket and schema names from config
        # Use same bucket derivation logic as weather_database.py
        view_path_cfg = config.get('lab3.database.view_path', f"/{config.get('lab3.database.name', 'weather_analytics')}")
        bucket_name = config.get('lab3.database.bucket_name', view_path_cfg.lstrip('/').replace('/', '-'))
        schema_name = config.get('lab3.database.schema', 'weather_analytics')
        
        # Use transaction to access tables
        with conn.transaction() as tx:
            bucket = tx.bucket(bucket_name)
            schema = bucket.schema(schema_name)
            
            weather_table = schema.table('hourly_weather')
            air_quality_table = schema.table('hourly_air_quality')
            
            # Set date range based on trends flag
            if trends:
                end_date = datetime(2025, 9, 15)
                start_date = datetime(2015, 1, 1)  # 10 years of data
            else:
                end_date = datetime(2025, 9, 15)
                start_date = end_date - timedelta(days=180)  # 6 months before end date
            
            if trends:
                print(f"   📈 Analyzing 10-year trends ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
            else:
                print(f"   📅 Analyzing last 6 months ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
            
            # Sample data for each location
            total_locations = len(locations)
            for i, location in enumerate(locations, 1):
                print(f"\n   🏙️  {location} ({i}/{total_locations}):")
                
                # Get weather data for the 6-month period
                weather_data = []
                weather_reader = weather_table.select(columns=['time', 'location', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation'])
                for batch in weather_reader:
                    df = batch.to_pandas()
                    if 'location' in df.columns:
                        location_data = df[df['location'] == location]
                        for _, row in location_data.iterrows():
                            row_time = pd.to_datetime(row['time'])
                            # Filter to our 6-month date range
                            if start_date <= row_time <= end_date:
                                weather_data.append({
                                    'time': row['time'],
                                    'temp': row['temperature_2m'],
                                    'humidity': row['relative_humidity_2m'],
                                    'wind_speed': row['wind_speed_10m'],
                                    'precipitation': row['precipitation']
                                })
                
                # Get air quality data for the 6-month period
                air_quality_data = []
                air_quality_reader = air_quality_table.select(columns=['time', 'location', 'pm2_5', 'pm10', 'ozone', 'nitrogen_dioxide', 'sulphur_dioxide'])
                for batch in air_quality_reader:
                    df = batch.to_pandas()
                    print(f"🔍 Air quality batch columns: {list(df.columns)}")
                    if 'location' in df.columns:
                        location_data = df[df['location'] == location]
                        print(f"🔍 Found {len(location_data)} rows for {location}")
                        for _, row in location_data.iterrows():
                            row_time = pd.to_datetime(row['time'])
                            # Filter to our 6-month date range
                            if start_date <= row_time <= end_date:
                                air_quality_data.append({
                                    'time': row['time'],
                                    'pm2_5': row['pm2_5'],
                                    'pm10': row['pm10'],
                                    'ozone': row['ozone'],
                                    'nitrogen_dioxide': row['nitrogen_dioxide'],
                                    'sulphur_dioxide': row['sulphur_dioxide']
                                })
            
                if weather_data and air_quality_data:
                    # Calculate averages with data validation
                    avg_temp = sum(w['temp'] for w in weather_data if not pd.isna(w['temp'])) / len([w for w in weather_data if not pd.isna(w['temp'])])
                    avg_humidity = sum(w['humidity'] for w in weather_data if not pd.isna(w['humidity'])) / len([w for w in weather_data if not pd.isna(w['humidity'])])
                    
                    # Filter out NaN values for air quality
                    valid_pm25 = [a['pm2_5'] for a in air_quality_data if not pd.isna(a['pm2_5'])]
                    valid_pm10 = [a['pm10'] for a in air_quality_data if not pd.isna(a['pm10'])]
                    
                    avg_pm2_5 = sum(valid_pm25) / len(valid_pm25) if valid_pm25 else float('nan')
                    avg_pm10 = sum(valid_pm10) / len(valid_pm10) if valid_pm10 else float('nan')
                    
                    print(f"      🌡️  Avg Temperature: {avg_temp:.1f}°C")
                    print(f"      💧 Avg Humidity: {avg_humidity:.1f}%")
                    
                    # Debug air quality data
                    if debug:
                        print(f"      🔍 Debug: {len(air_quality_data)} air quality records, {len(valid_pm25)} valid PM2.5, {len(valid_pm10)} valid PM10")
                    if len(valid_pm25) == 0:
                        print(f"      ⚠️  No valid PM2.5 data found for {location}")
                    if len(valid_pm10) == 0:
                        print(f"      ⚠️  No valid PM10 data found for {location}")
                    
                    if not pd.isna(avg_pm2_5):
                        print(f"      🌫️  Avg PM2.5: {avg_pm2_5:.1f} µg/m³")
                    else:
                        print(f"      🌫️  Avg PM2.5: No valid data")
                    
                    if not pd.isna(avg_pm10):
                        print(f"      🌫️  Avg PM10: {avg_pm10:.1f} µg/m³")
                    else:
                        print(f"      🌫️  Avg PM10: No valid data")
                    
                    # Additional air quality parameters
                    valid_no2 = [a['nitrogen_dioxide'] for a in air_quality_data if 'nitrogen_dioxide' in a and not pd.isna(a['nitrogen_dioxide'])]
                    valid_so2 = [a['sulphur_dioxide'] for a in air_quality_data if 'sulphur_dioxide' in a and not pd.isna(a['sulphur_dioxide'])]
                    valid_ozone = [a['ozone'] for a in air_quality_data if 'ozone' in a and not pd.isna(a['ozone'])]
                    
                    if valid_no2:
                        avg_no2 = sum(valid_no2) / len(valid_no2)
                        print(f"      🚗  Avg NO2: {avg_no2:.1f} µg/m³")
                    if valid_so2:
                        avg_so2 = sum(valid_so2) / len(valid_so2)
                        print(f"      🏭  Avg SO2: {avg_so2:.1f} µg/m³")
                    if valid_ozone:
                        avg_ozone = sum(valid_ozone) / len(valid_ozone)
                        print(f"      ☀️  Avg Ozone: {avg_ozone:.1f} µg/m³")
                    
                    # WHO guidelines check
                    who_pm2_5_daily = 25  # µg/m³
                    who_pm10_daily = 50   # µg/m³
                    who_no2_daily = 25    # µg/m³ (24-hour average)
                    who_so2_daily = 40    # µg/m³ (24-hour average)
                    who_ozone_daily = 100 # µg/m³ (8-hour average)
                    
                    if avg_pm2_5 > who_pm2_5_daily:
                        print(f"      ⚠️  PM2.5 exceeds WHO daily guideline ({who_pm2_5_daily} µg/m³)")
                    if avg_pm10 > who_pm10_daily:
                        print(f"      ⚠️  PM10 exceeds WHO daily guideline ({who_pm10_daily} µg/m³)")
                    if valid_no2 and avg_no2 > who_no2_daily:
                        print(f"      ⚠️  NO2 exceeds WHO daily guideline ({who_no2_daily} µg/m³)")
                    if valid_so2 and avg_so2 > who_so2_daily:
                        print(f"      ⚠️  SO2 exceeds WHO daily guideline ({who_so2_daily} µg/m³)")
                    if valid_ozone and avg_ozone > who_ozone_daily:
                        print(f"      ⚠️  Ozone exceeds WHO daily guideline ({who_ozone_daily} µg/m³)")
                    
                    # Weather impact assessment
                    if avg_humidity > 70:
                        print(f"      🌧️  High humidity may trap pollutants")
                    if avg_temp < 0:
                        print(f"      ❄️  Cold weather may increase heating emissions")
                else:
                    print(f"      ⚠️  No data available for this date range")
                    if debug:
                        print(f"      🔍 Debug: Weather data: {len(weather_data) if weather_data else 0} records, Air quality data: {len(air_quality_data) if air_quality_data else 0} records")
                
    except Exception as e:
        print(f"   ❌ Error analyzing daily patterns: {e}")

def analyze_correlations(conn, config, locations, debug=False, trends=False):
    """Analyze correlations between weather and air quality"""
    print_section("Weather-Air Quality Correlations", "🔗")
    
    try:
        # Get bucket and schema names from config
        # Use same bucket derivation logic as weather_database.py
        view_path_cfg = config.get('lab3.database.view_path', f"/{config.get('lab3.database.name', 'weather_analytics')}")
        bucket_name = config.get('lab3.database.bucket_name', view_path_cfg.lstrip('/').replace('/', '-'))
        schema_name = config.get('lab3.database.schema', 'weather_analytics')
        
        # Use transaction to access tables with timeout handling
        try:
            with conn.transaction() as tx:
                bucket = tx.bucket(bucket_name)
                schema = bucket.schema(schema_name)
                
                weather_table = schema.table('hourly_weather')
                air_quality_table = schema.table('hourly_air_quality')
                
                print("   🔍 Analyzing correlations (this may take a moment)...")
                
                # Set date range based on trends flag
                if trends:
                    end_date = datetime(2025, 9, 15)
                    start_date = datetime(2015, 1, 1)  # 10 years of data
                else:
                    end_date = datetime(2025, 9, 15)
                    start_date = end_date - timedelta(days=180)  # 6 months before end date
                
                if trends:
                    print(f"   📈 Analyzing correlations for 10-year trends ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
                else:
                    print(f"   📅 Analyzing correlations for last 6 months ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
                
                # Sample data for correlation analysis
                sample_data = []
                # Limit to reasonable number of locations for performance
                max_locations = min(len(locations), 5) if len(locations) > 5 else len(locations)
                for i, location in enumerate(locations[:max_locations], 1):
                    print(f"   📍 Sampling data for {location} ({i}/{max_locations})...")
                    
                    # Get weather data for the 6-month period
                    weather_data = []
                    weather_reader = weather_table.select(columns=['time', 'location', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation'])
                    for batch in weather_reader:
                        df = batch.to_pandas()
                        if 'location' in df.columns:
                            location_data = df[df['location'] == location]
                            for _, row in location_data.iterrows():
                                row_time = pd.to_datetime(row['time'])
                                # Filter to our 6-month date range
                                if start_date <= row_time <= end_date:
                                    weather_data.append({
                                        'time': row['time'],
                                        'temp': row['temperature_2m'],
                                        'humidity': row['relative_humidity_2m'],
                                        'wind_speed': row['wind_speed_10m'],
                                        'precipitation': row['precipitation']
                                    })
                                    if len(weather_data) >= 100:  # Sample 100 points
                                        break
                        if len(weather_data) >= 100:
                            break
                    
                    # Get air quality data for the 6-month period
                    air_quality_data = []
                    air_quality_reader = air_quality_table.select(columns=['time', 'location', 'pm2_5', 'pm10', 'ozone', 'nitrogen_dioxide', 'sulphur_dioxide'])
                    for batch in air_quality_reader:
                        df = batch.to_pandas()
                        if 'location' in df.columns:
                            location_data = df[df['location'] == location]
                            for _, row in location_data.iterrows():
                                row_time = pd.to_datetime(row['time'])
                                # Filter to our 6-month date range
                                if start_date <= row_time <= end_date:
                                    air_quality_data.append({
                                        'time': row['time'],
                                        'pm2_5': row['pm2_5'],
                                        'pm10': row['pm10'],
                                        'ozone': row['ozone']
                                    })
                                    if len(air_quality_data) >= 100:  # Sample 100 points
                                        break
                        if len(air_quality_data) >= 100:
                            break
            
                    # Combine data
                    if weather_data and air_quality_data:
                        # Simple time-based matching (assuming hourly data)
                        for w in weather_data[:50]:  # Limit to 50 points for correlation
                            for a in air_quality_data[:50]:
                                if w['time'] == a['time']:
                                    sample_row = {
                                        'location': location,
                                        'temp': w['temp'],
                                        'humidity': w['humidity'],
                                        'wind_speed': w['wind_speed'],
                                        'precipitation': w['precipitation'],
                                        'pm2_5': a['pm2_5'],
                                        'pm10': a['pm10']
                                    }
                                    
                                    # Add optional air quality columns if they exist
                                    if 'ozone' in a and not pd.isna(a['ozone']):
                                        sample_row['ozone'] = a['ozone']
                                    if 'nitrogen_dioxide' in a and not pd.isna(a['nitrogen_dioxide']):
                                        sample_row['nitrogen_dioxide'] = a['nitrogen_dioxide']
                                    if 'sulphur_dioxide' in a and not pd.isna(a['sulphur_dioxide']):
                                        sample_row['sulphur_dioxide'] = a['sulphur_dioxide']
                                    
                                    sample_data.append(sample_row)
                                    break
            
                if sample_data:
                    df = pd.DataFrame(sample_data)
                    
                    print(f"\n   📊 Correlation Analysis (based on {len(df)} data points):")
                    
                    # Calculate correlations
                    correlations = []
                    for location in df['location'].unique():
                        loc_data = df[df['location'] == location]
                        
                        if len(loc_data) > 10:  # Need enough data for correlation
                            # Basic correlations (always available)
                            temp_pm25_corr = loc_data['temp'].corr(loc_data['pm2_5'])
                            humidity_pm25_corr = loc_data['humidity'].corr(loc_data['pm2_5'])
                            wind_pm25_corr = loc_data['wind_speed'].corr(loc_data['pm2_5'])
                            
                            # Optional correlations (only if columns exist)
                            temp_ozone_corr = None
                            temp_no2_corr = None
                            wind_no2_corr = None
                            wind_so2_corr = None
                            
                            if 'ozone' in loc_data.columns:
                                temp_ozone_corr = loc_data['temp'].corr(loc_data['ozone'])
                            if 'nitrogen_dioxide' in loc_data.columns:
                                temp_no2_corr = loc_data['temp'].corr(loc_data['nitrogen_dioxide'])
                                wind_no2_corr = loc_data['wind_speed'].corr(loc_data['nitrogen_dioxide'])
                            if 'sulphur_dioxide' in loc_data.columns:
                                wind_so2_corr = loc_data['wind_speed'].corr(loc_data['sulphur_dioxide'])
                            
                            correlations.append({
                                'Location': location,
                                'Temp vs PM2.5': f"{temp_pm25_corr:.3f}",
                                'Humidity vs PM2.5': f"{humidity_pm25_corr:.3f}",
                                'Wind vs PM2.5': f"{wind_pm25_corr:.3f}",
                                'Temp vs Ozone': f"{temp_ozone_corr:.3f}" if temp_ozone_corr is not None else "N/A",
                                'Temp vs NO2': f"{temp_no2_corr:.3f}" if temp_no2_corr is not None else "N/A",
                                'Wind vs NO2': f"{wind_no2_corr:.3f}" if wind_no2_corr is not None else "N/A",
                                'Wind vs SO2': f"{wind_so2_corr:.3f}" if wind_so2_corr is not None else "N/A"
                            })
                    
                    if correlations:
                        # Convert to compact table format
                        headers = ['Location', 'Temp vs PM2.5', 'Humidity vs PM2.5', 'Wind vs PM2.5', 'Temp vs Ozone', 'Temp vs NO2', 'Wind vs NO2', 'Wind vs SO2']
                        compact_data = []
                        for corr in correlations:
                            # Shorten location names for better display
                            short_location = corr['Location'].replace('_Beijing_China', '').replace('_England_United-Kingdom', '').replace('_New-York_United-States', '')
                            compact_data.append([
                                short_location,
                                corr['Temp vs PM2.5'],
                                corr['Humidity vs PM2.5'],
                                corr['Wind vs PM2.5'],
                                corr['Temp vs Ozone'],
                                corr['Temp vs NO2'],
                                corr['Wind vs NO2'],
                                corr['Wind vs SO2']
                            ])
                        print_compact_table(compact_data, headers, title="Correlation Coefficients", max_col_width=18)
                        
                        # Interpretation
                        print("\n   💡 Interpretation:")
                        print("   • Positive correlation: variables increase together")
                        print("   • Negative correlation: one increases as other decreases")
                        print("   • |r| > 0.7: strong correlation")
                        print("   • |r| > 0.5: moderate correlation")
                        print("   • |r| < 0.3: weak correlation")
                else:
                    print("   ❌ No matching data found for correlation analysis")
                    
        except Exception as e:
            print(f"   ⚠️  Correlation analysis failed: {e}")
            print("   💡 This might be due to transaction timeout or connection issues")
            
    except Exception as e:
        print(f"   ❌ Error analyzing correlations: {e}")

def analyze_pollution_episodes(conn, config, locations, debug=False, trends=False):
    """Analyze high pollution episodes"""
    print_section("Pollution Episodes", "⚠️")
    
    try:
        # Get bucket and schema names from config
        # Use same bucket derivation logic as weather_database.py
        view_path_cfg = config.get('lab3.database.view_path', f"/{config.get('lab3.database.name', 'weather_analytics')}")
        bucket_name = config.get('lab3.database.bucket_name', view_path_cfg.lstrip('/').replace('/', '-'))
        schema_name = config.get('lab3.database.schema', 'weather_analytics')
        
        # Use transaction to access tables with error handling
        try:
            with conn.transaction() as tx:
                bucket = tx.bucket(bucket_name)
                schema = bucket.schema(schema_name)
                
                air_quality_table = schema.table('hourly_air_quality')
                
                print("   🔍 Identifying high pollution episodes...")
                
                # Set date range based on trends flag
                if trends:
                    end_date = datetime(2025, 9, 15)
                    start_date = datetime(2015, 1, 1)  # 10 years of data
                else:
                    end_date = datetime(2025, 9, 15)
                    start_date = end_date - timedelta(days=180)  # 6 months before end date
                
                if trends:
                    print(f"   📈 Analyzing pollution episodes for 10-year trends ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
                else:
                    print(f"   📅 Analyzing pollution episodes for last 6 months ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
                
                # WHO guidelines
                who_pm2_5_daily = 25  # µg/m³
                who_pm10_daily = 50   # µg/m³
                
                episodes = []
                total_locations = len(locations)
                for i, location in enumerate(locations, 1):
                    print(f"   📍 Checking {location} ({i}/{total_locations})...")
                    
                    # Sample air quality data for the 6-month period
                    air_quality_data = []
                    air_quality_reader = air_quality_table.select(columns=['time', 'location', 'pm2_5', 'pm10'])
                    for batch in air_quality_reader:
                        df = batch.to_pandas()
                        if 'location' in df.columns:
                            location_data = df[df['location'] == location]
                            for _, row in location_data.iterrows():
                                row_time = pd.to_datetime(row['time'])
                                # Filter to our 6-month date range
                                if start_date <= row_time <= end_date:
                                    air_quality_data.append({
                                        'time': row['time'],
                                        'pm2_5': row['pm2_5'],
                                        'pm10': row['pm10']
                                    })
                                    if len(air_quality_data) >= 200:  # Sample 200 points
                                        break
                        if len(air_quality_data) >= 200:
                            break
                
                    if air_quality_data:
                        # Find high pollution episodes with data validation
                        valid_pm25 = [a['pm2_5'] for a in air_quality_data if not pd.isna(a['pm2_5'])]
                        valid_pm10 = [a['pm10'] for a in air_quality_data if not pd.isna(a['pm10'])]
                        
                        high_pm25_count = sum(1 for a in valid_pm25 if a > who_pm2_5_daily)
                        high_pm10_count = sum(1 for a in valid_pm10 if a > who_pm10_daily)
                        
                        avg_pm25 = sum(valid_pm25) / len(valid_pm25) if valid_pm25 else float('nan')
                        avg_pm10 = sum(valid_pm10) / len(valid_pm10) if valid_pm10 else float('nan')
                        
                        max_pm25 = max(valid_pm25) if valid_pm25 else float('nan')
                        max_pm10 = max(valid_pm10) if valid_pm10 else float('nan')
                        
                        episodes.append({
                            'Location': location,
                            'Avg PM2.5': f"{avg_pm25:.1f}" if not pd.isna(avg_pm25) else "No data",
                            'Max PM2.5': f"{max_pm25:.1f}" if not pd.isna(max_pm25) else "No data",
                            'High PM2.5 Hours': f"{high_pm25_count}",
                            'Avg PM10': f"{avg_pm10:.1f}" if not pd.isna(avg_pm10) else "No data",
                            'Max PM10': f"{max_pm10:.1f}" if not pd.isna(max_pm10) else "No data",
                            'High PM10 Hours': f"{high_pm10_count}"
                        })
                
                if episodes:
                    # Convert to compact table format
                    headers = ['Location', 'Avg PM2.5', 'Max PM2.5', 'High PM2.5 Hours', 'Avg PM10', 'Max PM10', 'High PM10 Hours']
                    compact_data = []
                    for ep in episodes:
                        # Shorten location names for better display
                        short_location = ep['Location'].replace('_Beijing_China', '').replace('_England_United-Kingdom', '').replace('_New-York_United-States', '')
                        compact_data.append([
                            short_location,
                            ep['Avg PM2.5'],
                            ep['Max PM2.5'],
                            ep['High PM2.5 Hours'],
                            ep['Avg PM10'],
                            ep['Max PM10'],
                            ep['High PM10 Hours']
                        ])
                    print_compact_table(compact_data, headers, title="Pollution Summary", max_col_width=16)
                    
                    # Health impact assessment
                    print("\n   🏥 Health Impact Assessment:")
                    for ep in episodes:
                        location = ep['Location']
                        avg_pm25_str = ep['Avg PM2.5']
                        high_pm25_hours = int(ep['High PM2.5 Hours'])
                        
                        if avg_pm25_str != "No data":
                            avg_pm25 = float(avg_pm25_str)
                            if avg_pm25 > who_pm2_5_daily:
                                print(f"   ⚠️  {location}: High PM2.5 exposure risk")
                            elif high_pm25_hours > 0:
                                print(f"   ⚡ {location}: Occasional PM2.5 spikes")
                            else:
                                print(f"   ✅ {location}: Good air quality")
                        else:
                            print(f"   ❓ {location}: No air quality data available")
                else:
                    print("   ❌ No air quality data available for analysis")
                    
        except Exception as e:
            print(f"   ⚠️  Pollution analysis failed: {e}")
            print("   💡 This might be due to transaction timeout or connection issues")
            
    except Exception as e:
        print(f"   ❌ Error analyzing pollution episodes: {e}")

def main():
    parser = argparse.ArgumentParser(description="Weather Analytics Demo - Fancy Console Output")
    parser.add_argument("--all-cities", action="store_true", help="Analyze all available cities (default: first 3)")
    parser.add_argument("--locations", nargs="+", help="Specific locations to analyze")
    parser.add_argument("--trends", action="store_true", help="Analyze long-term trends (10 years: 2015-2025)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for troubleshooting")
    
    args = parser.parse_args()
    
    print_header("Weather Analytics Demo", "🌤️")
    if args.trends:
        print("   📈 Long-term trend analysis (10 years: 2015-2025)")
        print("   🔍 Identifying historical patterns and dangerous episodes")
    else:
        print("   Demonstrating correlations between weather and air quality data")
    print("   Using VAST Database for high-performance analytics")
    
    if args.all_cities:
        print("   🌍 All cities mode enabled - analyzing all available locations")
    elif args.locations:
        print(f"   📍 Specific locations mode - analyzing: {', '.join(args.locations)}")
    else:
        print("   📍 Default mode - analyzing first 3 locations (use --all-cities for all)")
    
    print("   💡 If you encounter transaction errors, try --locations with fewer cities for faster analysis")
    if args.debug:
        print("   🐛 Debug mode enabled - will show detailed error information")
    
    # Connect to VAST DB
    print_section("Connecting to VAST Database", "🔌")
    conn, config = get_weather_connection()
    if not conn or not config:
        return 1
    
    print("   ✅ Connected to VAST Database")
    
    # Get data summary
    weather_table, air_quality_table, locations = get_data_summary(conn, config, args.trends)
    if not weather_table or not air_quality_table:
        return 1
    
    # Filter locations if specified
    if args.locations:
        locations = [loc for loc in locations if any(loc.lower().find(arg.lower()) != -1 for arg in args.locations)]
        if not locations:
            print("   ❌ No matching locations found")
            return 1
    
    # Apply location limits based on options
    if not args.all_cities and not args.locations:
        locations = locations[:3]
        print(f"   📍 Default mode: Analyzing first {len(locations)} locations")
    else:
        print(f"   🌍 All cities mode: Analyzing all {len(locations)} locations")
    
    # Run analyses with retry logic for transaction errors
    print("\n🔄 Running analyses with transaction retry logic...")
    
    # Wrap each analysis in retry logic
    def run_daily_patterns():
        analyze_daily_patterns(conn, config, locations, debug=args.debug, trends=args.trends)
    
    def run_correlations():
        analyze_correlations(conn, config, locations, debug=args.debug, trends=args.trends)
    
    def run_pollution_episodes():
        analyze_pollution_episodes(conn, config, locations, debug=args.debug, trends=args.trends)
    
    # Execute with retry logic
    print("   🔄 Starting daily patterns analysis...")
    retry_transaction(run_daily_patterns, max_retries=2, delay=1)
    
    print("   🔄 Starting correlations analysis...")
    retry_transaction(run_correlations, max_retries=2, delay=2)
    
    print("   🔄 Starting pollution episodes analysis...")
    retry_transaction(run_pollution_episodes, max_retries=2, delay=2)
    
    print_header("Analysis Complete", "✅")
    print("   🎉 Weather analytics demo completed successfully!")
    print("   💡 Try different locations or time ranges for more insights")
    
    if args.debug:
        print("\n   🐛 Debug Information:")
        print("   • If you see frequent transaction errors, try:")
        print("     - Running with fewer locations: --locations Beijing London")
        print("     - Using --locations with just 1-2 cities for faster analysis")
        print("     - Checking your network connection to VAST DB")
        print("   • Transaction errors are often caused by:")
        print("     - Large data scans taking too long")
        print("     - Network timeouts or connection issues")
        print("     - Concurrent access to the same data")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

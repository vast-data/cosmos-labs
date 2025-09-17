#!/usr/bin/env python3
"""
Weather Data Downloader
Downloads weather and air quality data from Open-Meteo API and saves to CSV files
"""

import sys
import csv
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import argparse
import requests

# Use centralized config files at repo root
sys.path.append(str(Path(__file__).parent.parent))
from lab3.lab3_config import Lab3ConfigLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def geocode_location(name_or_coords: str) -> Tuple[float, float, str]:
    """Resolve city name or "lat,lon" string to (lat, lon, label)."""
    name_or_coords = name_or_coords.strip()
    if "," in name_or_coords:
        try:
            lat_str, lon_str = [p.strip() for p in name_or_coords.split(",", 1)]
            lat, lon = float(lat_str), float(lon_str)
            return lat, lon, f"{lat:.4f},{lon:.4f}"
        except Exception:
            pass

    params = {"name": name_or_coords, "count": 1}
    r = requests.get(GEOCODE_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        raise ValueError(f"No geocoding results for '{name_or_coords}'")
    res = data["results"][0]
    lat, lon = float(res["latitude"]), float(res["longitude"])
    label_parts = [res.get("name")] + [x for x in [res.get("admin1"), res.get("country")]
                                         if x and isinstance(x, str)]
    label = "_".join(part.replace(" ", "-") for part in label_parts if part)
    return lat, lon, label


def _make_api_request(url: str, params: Dict, max_retries: int = 3, base_delay: int = 60) -> Dict:
    """Make API request with retry logic for rate limiting."""
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 60s, 120s, 240s
                    logger.warning(f"⚠️ Rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"❌ Rate limited after {max_retries} attempts")
                    raise
            elif e.response.status_code == 400:  # Bad Request - likely date range too long
                logger.error(f"❌ API doesn't support this date range. Try shorter range.")
                raise
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"⚠️ Request failed, retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
                continue
            else:
                logger.error(f"❌ Request failed after {max_retries} attempts: {e}")
                raise
    return {}


def fetch_weather(lat: float, lon: float, start: str, end: str) -> Dict:
    """Fetch weather data from Open-Meteo archive API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation",
        "timezone": "UTC"
    }
    return _make_api_request(WEATHER_URL, params)


def fetch_air_quality(lat: float, lon: float, start: str, end: str) -> Dict:
    """Fetch air quality data from Open-Meteo air quality API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": "pm10,pm2_5,nitrogen_dioxide,ozone,sulphur_dioxide",
        "timezone": "UTC"
    }
    return _make_api_request(AIR_QUALITY_URL, params)


def write_csv(path: Path, header: List[str], rows: List[List]):
    """Write data to CSV file."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def save_weather_csvs(base_dir: Path, label: str, weather: Dict, air: Dict):
    """Save weather and air quality data to CSV files."""
    loc_dir = base_dir / label
    loc_dir.mkdir(parents=True, exist_ok=True)
    
    # Save weather data
    if weather.get("hourly"):
        weather_header = ["time"] + list(weather["hourly_units"].keys())
        weather_rows = []
        for i, time_val in enumerate(weather["hourly"]["time"]):
            row = [time_val]
            for key in weather["hourly_units"].keys():
                if key != "time":
                    row.append(weather["hourly"][key][i])
            weather_rows.append(row)
        write_csv(loc_dir / "weather.csv", weather_header, weather_rows)
        logger.info(f"✅ Saved {len(weather_rows)} weather records to {loc_dir / 'weather.csv'}")
    
    # Save air quality data
    if air.get("hourly"):
        air_header = ["time"] + list(air["hourly_units"].keys())
        air_rows = []
        for i, time_val in enumerate(air["hourly"]["time"]):
            row = [time_val]
            for key in air["hourly_units"].keys():
                if key != "time":
                    row.append(air["hourly"][key][i])
            air_rows.append(row)
        write_csv(loc_dir / "air_quality.csv", air_header, air_rows)
        logger.info(f"✅ Saved {len(air_rows)} air quality records to {loc_dir / 'air_quality.csv'}")


def main():
    parser = argparse.ArgumentParser(description="Download weather and air quality data")
    parser.add_argument("locations", nargs="*", help="City names or 'lat,lon' coordinates (or use --preset)")
    parser.add_argument("--preset", choices=["test", "extended", "pollution", "global"], help="Use predefined city sets from config")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="weather_data", help="Output directory for CSV files")
    parser.add_argument("--no-download", action="store_true", help="Skip downloading, just process existing CSV files")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Lab3ConfigLoader()
    if not config.validate_config():
        logger.error("❌ Configuration validation failed")
        return 1
    
    # Determine locations to process
    if args.preset:
        presets = config.get_weather_presets()
        descriptions = config.get_weather_preset_descriptions()
        if args.preset not in presets:
            logger.error(f"❌ Preset '{args.preset}' not found in config. Available: {list(presets.keys())}")
            return 1
        locations = presets[args.preset]
        description = descriptions.get(args.preset, "No description available")
        logger.info(f"🎯 Using {args.preset} preset: {', '.join(locations)}")
        logger.info(f"📝 Description: {description}")
    elif args.locations:
        locations = args.locations
    else:
        logger.error("❌ Must specify either locations or --preset")
        parser.print_help()
        return 1
    
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each location
    for i, location in enumerate(locations, 1):
        logger.info(f"🌍 Processing {location} ({i}/{len(locations)})")
        
        try:
            # Geocode location
            lat, lon, label = geocode_location(location)
            logger.info(f"📍 {location} -> {lat:.4f}, {lon:.4f} ({label})")
            
            # Download data if not skipping
            if not args.no_download:
                logger.info(f"🌤️ Downloading weather data for {label}...")
                weather = fetch_weather(lat, lon, args.start, args.end)
                
                logger.info(f"🌫️ Downloading air quality data for {label}...")
                air = fetch_air_quality(lat, lon, args.start, args.end)
                
                # Save to CSV files
                save_weather_csvs(output_dir, label, weather, air)
                
                # Rate limiting between cities
                if i < len(locations):
                    logger.info("⏳ Waiting 60s before next city (respecting 600 calls/min limit)...")
                    time.sleep(60)
            else:
                logger.info(f"⏭️ Skipping download for {label} (--no-download)")
            
            # Ingest to VAST DB if not skipping
            if not args.no_download:
                from lab3.weather_database import WeatherVASTDB
                db = WeatherVASTDB(config)
                
                # Setup infrastructure if needed
                if not db.setup_infrastructure(dry_run=True):
                    logger.warning("⚠️ VAST DB not available, skipping ingestion")
                else:
                    db.setup_infrastructure(dry_run=False)
                    loc_dir = output_dir / label
                    if loc_dir.exists():
                        logger.info(f"📊 Ingesting {label} data to VAST DB...")
                        db.ingest_location_csvs(loc_dir, label)
                    else:
                        logger.warning(f"⚠️ No data directory found for {label}")
        
        except Exception as e:
            logger.error(f"❌ Failed to process {location}: {e}")
            continue
    
    logger.info("✅ Weather data download completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

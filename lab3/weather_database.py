#!/usr/bin/env python3
"""
Weather VAST DB Manager
Handles all VAST Database operations for weather data storage and retrieval
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pyarrow as pa

logger = logging.getLogger(__name__)


class WeatherVASTDB:
    """Minimal VAST DB manager for weather analytics (safe, lab-style)."""
    def __init__(self, config):
        self.config = config
        # Bucket is lab3-specific; endpoint and connection live under base 'vastdb.*'
        self.bucket = config.get('lab3.database.name', 'weather_analytics')
        self.schema = config.get('lab3.database.schema', 'weather_analytics')
        self.endpoint = config.get('vastdb.endpoint', 'https://your-vms-hostname')
        self.creds = {
            'access': config.get_secret('s3_access_key'),
            'secret': config.get_secret('s3_secret_key'),
            'endpoint': self.endpoint,
            'ssl_verify': config.get('vastdb.ssl_verify', True),
            'timeout': config.get('vastdb.timeout', 30),
        }
        try:
            import vastdb  # noqa: F401
            self._vastdb_available = True
        except Exception as e:
            logger.warning(f"⚠️ vastdb not available: {e}")
            self._vastdb_available = False
            
        self._conn = None

    def _connect(self):
        if not self._vastdb_available:
            return False
        try:
            import vastdb
            self._conn = vastdb.connect(**self.creds)
            return True
        except Exception as e:
            logger.error(f"❌ Connect failed: {e}")
            return False

    def setup_infrastructure(self, dry_run: bool = True) -> bool:
        if not self._vastdb_available:
            logger.warning("⚠️ vastdb not installed; skipping setup")
            return False
        if dry_run:
            logger.info(f"🔎 DRY-RUN: would ensure bucket '{self.bucket}', schema '{self.schema}', and tables")
            return True
        if not self._connect():
            return False
        # Vastpy bootstrap first (single execution at setup)
        if not self._vastpy_bootstrap_bucket():
            return False
        try:
            with self._conn.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                # Create schema if needed, else reuse existing
                try:
                    schema = bucket.create_schema(self.schema, fail_if_exists=False)
                    logger.info(f"✅ Ensured schema '{self.schema}' exists")
                except Exception:
                    try:
                        schema = bucket.schema(self.schema)
                        logger.info(f"ℹ️ Using existing schema '{self.schema}'")
                    except Exception as e:
                        logger.error(f"❌ Could not access schema '{self.schema}': {e}")
                        return False

                weather_cols = pa.schema([
                    ('location', pa.utf8()),
                    ('time', pa.timestamp('us')),
                    ('temperature_2m', pa.float64()),
                    ('relative_humidity_2m', pa.float64()),
                    ('surface_pressure', pa.float64()),
                    ('wind_speed_10m', pa.float64()),
                    ('wind_direction_10m', pa.float64()),
                    ('precipitation', pa.float64()),
                ])
                air_cols = pa.schema([
                    ('location', pa.utf8()),
                    ('time', pa.timestamp('us')),
                    ('pm10', pa.float64()),
                    ('pm2_5', pa.float64()),
                    ('nitrogen_dioxide', pa.float64()),
                    ('ozone', pa.float64()),
                    ('sulphur_dioxide', pa.float64()),
                ])
                # Create tables if missing
                try:
                    schema.create_table('hourly_weather', weather_cols)
                    logger.info("✅ Created table 'hourly_weather'")
                except Exception:
                    try:
                        schema.table('hourly_weather')
                        logger.info("ℹ️ Table 'hourly_weather' already exists")
                    except Exception as e:
                        logger.error(f"❌ Could not access table 'hourly_weather': {e}")
                        return False
                try:
                    schema.create_table('hourly_air_quality', air_cols)
                    logger.info("✅ Created table 'hourly_air_quality'")
                except Exception:
                    try:
                        schema.table('hourly_air_quality')
                        logger.info("ℹ️ Table 'hourly_air_quality' already exists")
                    except Exception as e:
                        logger.error(f"❌ Could not access table 'hourly_air_quality': {e}")
                        return False
            return True
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

    def drop_tables(self) -> bool:
        """Drop weather and air quality tables"""
        if not self._vastdb_available:
            logger.warning("⚠️ vastdb not installed; skipping drop")
            return False
        if not self._connect():
            return False
        try:
            with self._conn.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                schema = bucket.schema(self.schema)
                tables_to_drop = ['hourly_weather', 'hourly_air_quality']
                for table_name in tables_to_drop:
                    try:
                        table = schema.table(table_name)
                        table.drop()
                        logger.info(f"✅ Dropped table '{table_name}'")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not drop table {table_name}: {e}")
            return True
        except Exception as e:
            logger.error(f"❌ Drop tables failed: {e}")
            return False

    def ingest_location_csvs(self, loc_dir: Path, location_label: str) -> bool:
        """Ingest CSV files for a location into VAST DB"""
        if not self._vastdb_available:
            logger.warning("⚠️ vastdb not installed; skipping ingestion")
            return False
        if not self._connect():
            return False
        try:
            with self._conn.transaction() as tx:
                bucket = tx.bucket(self.bucket)
                schema = bucket.schema(self.schema)
                # Ingest weather data
                weather_csv = loc_dir / "weather.csv"
                if weather_csv.exists():
                    self._ingest_csv_data(schema, weather_csv, 'hourly_weather', location_label)
                # Ingest air quality data
                air_csv = loc_dir / "air_quality.csv"
                if air_csv.exists():
                    self._ingest_csv_data(schema, air_csv, 'hourly_air_quality', location_label)
            return True
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            return False


    def _ingest_csv_data(self, schema, csv_path: Path, table_name: str, location_label: str):
        """Ingest CSV data into VAST DB table with duplicate filtering"""
        try:
            table = schema.table(table_name)
        except Exception as e:
            logger.warning(f"⚠️ Table {table_name} does not exist, recreating infrastructure...")
            if not self.setup_infrastructure(dry_run=False):
                logger.error(f"❌ Failed to recreate infrastructure for {table_name}")
                return
            table = schema.table(table_name)
        
        # Load CSV data
        header, rows = self._load_csv(csv_path)
        if not rows:
            logger.warning(f"⚠️ No data in {csv_path}")
            return
        
        # Parse columns based on table type
        if table_name == 'hourly_weather':
            col_map = {
                'time': 'time',
                'temperature_2m': 'temperature_2m',
                'relative_humidity_2m': 'relative_humidity_2m',
                'surface_pressure': 'surface_pressure',
                'wind_speed_10m': 'wind_speed_10m',
                'wind_direction_10m': 'wind_direction_10m',
                'precipitation': 'precipitation',
            }
        else:
            col_map = {
                'time': 'time',
                'pm10': 'pm10',
                'pm2_5': 'pm2_5',
                'nitrogen_dioxide': 'nitrogen_dioxide',
                'ozone': 'ozone',
                'sulphur_dioxide': 'sulphur_dioxide',
            }
        
        data, times = self._parse_csv_columns(header, rows, col_map, location_label)
        if not data:
            logger.warning(f"⚠️ No valid data parsed from {csv_path}")
            return
        
        # Insert with duplicate filtering
        self._insert_with_duplicate_filtering(table, data, times, location_label)

    def _load_csv(self, path: Path) -> Tuple[List[str], List[List[str]]]:
        """Load CSV file and return header and rows"""
        import csv
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        return header, rows

    def _parse_csv_columns(self, header: List[str], rows: List[List[str]], 
                          col_map: Dict[str, str], location_label: str) -> Tuple[Dict, List[datetime]]:
        """Parse CSV columns into PyArrow-compatible format"""
        def get_index(key):
            try:
                return header.index(key)
            except ValueError:
                return None
        
        def parse_float(v):
            try:
                return float(v) if v and v != 'null' else None
            except (ValueError, TypeError):
                return None
        
        data = {col: [] for col in col_map.values()}
        times = []
        
        for row in rows:
            if len(row) < len(header):
                continue
            time_idx = get_index('time')
            if time_idx is None:
                continue
            try:
                time_val = datetime.fromisoformat(row[time_idx].replace('Z', '+00:00'))
                times.append(time_val)
                for col, key in col_map.items():
                    if col == 'time':
                        data[col].append(time_val)
                    elif col == 'location':
                        data[col].append(location_label)
                    else:
                        idx = get_index(key)
                        if idx is not None:
                            data[col].append(parse_float(row[idx]))
                        else:
                            data[col].append(None)
            except (ValueError, TypeError):
                continue
        
        return data, times

    def _insert_with_duplicate_filtering(self, table, data: Dict, times: List[datetime], 
                                       location_label: str):
        """Insert data with duplicate filtering using pre-query approach"""
        try:
            # Pre-query existing data to check for duplicates
            logger.info(f"🔍 Checking existing data for {location_label}...")
            reader = table.select(columns=['time', 'location'])
            existing_times = set()
            for batch in reader:
                df = batch.to_pandas()
                location_data = df[df['location'] == location_label]
                existing_times.update(location_data['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
            
            # Filter out duplicates
            new_data = {col: [] for col in data.keys()}
            new_times = []
            for i, time_val in enumerate(times):
                time_str = time_val.strftime('%Y-%m-%d %H:%M:%S')
                if time_str not in existing_times:
                    for col in data.keys():
                        new_data[col].append(data[col][i])
                    new_times.append(time_val)
            
            if not new_times:
                logger.info(f"ℹ️ All data for {location_label} already exists, skipping")
                return
            
            logger.info(f"📊 Inserting {len(new_times)} new records for {location_label}")
            
            # Create PyArrow table
            arrow_table = pa.Table.from_pydict(new_data)
            table.insert(arrow_table)
            logger.info(f"✅ Successfully inserted {len(new_times)} records for {location_label}")
            
        except Exception as e:
            logger.error(f"❌ Insert failed for {location_label}: {e}")

    def _vastpy_bootstrap_bucket(self) -> bool:
        """Bootstrap bucket using vastpy (VMS API)"""
        try:
            from vastpy import VASTClient
            
            # Get VMS connection details
            vms_endpoint = self.config.get('vast.address', 'https://your-vms-hostname')
            vms_username = self.config.get('vast.user')
            vms_password = self.config.get_secret('vast_password')
            
            if not vms_username or not vms_password:
                logger.warning("⚠️ VMS credentials not found, skipping bucket bootstrap")
                return True  # Not critical for lab
            
            # Strip protocol from address (vastpy expects just hostname:port)
            address = vms_endpoint
            if address.startswith('https://'):
                address = address[8:]
            elif address.startswith('http://'):
                address = address[7:]
            
            # Connect to VMS using VASTClient
            client = VASTClient(address=address, user=vms_username, password=vms_password)
            
            # Get or create view (VAST uses views, not buckets directly)
            view_path = self.config.get('lab3.database.view_path', f"/{self.bucket}")
            policy_name = self.config.get('lab3.database.policy_name', 's3_default_policy')
            bucket_owner = self.config.get('lab3.database.bucket_owner')
            
            try:
                # Check if view exists
                views = client.views.get()
                existing_view = None
                for view in views:
                    if view.get('path') == view_path:
                        existing_view = view
                        break
                
                if existing_view:
                    logger.info(f"ℹ️ Using existing view '{view_path}'")
                else:
                    # Get policy ID from policy name
                    policies = client.viewpolicies.get(name=policy_name)
                    if not policies:
                        logger.error(f"❌ Policy '{policy_name}' not found")
                        return False
                    
                    policy_id = policies[0]['id']
                    logger.info(f"🔧 Using policy '{policy_name}' (ID: {policy_id})")
                    
                    # Create view if it doesn't exist
                    view_data = {
                        'path': view_path,
                        'policy_id': policy_id,
                        'protocols': ['S3', 'DATABASE']
                    }
                    
                    # Add bucket_owner if provided
                    if bucket_owner:
                        view_data['bucket_owner'] = bucket_owner
                        logger.info(f"🔧 Setting bucket owner to '{bucket_owner}'")
                    
                    client.views.post(view_data)
                    logger.info(f"✅ Created view '{view_path}'")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not verify/create view '{view_path}': {e}")
                # Not critical for lab, continue
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Vastpy bootstrap failed: {e}")
            return True  # Not critical for lab

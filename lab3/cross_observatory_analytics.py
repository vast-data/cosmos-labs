# cross_observatory_analytics.py
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add parent directory to path for centralized config
sys.path.append(str(Path(__file__).parent.parent))

try:
    import vastdb
    VASTDB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  vastdb not found. ImportError: {e}")
    print("💡 This is required for Lab 3 analytics functionality")
    print("🔧 For now, using mock database operations")
    VASTDB_AVAILABLE = False

try:
    import ibis
    # Check for basic ibis functionality
    try:
        test_expr = ibis.literal(1) == 1
        IBIS_AVAILABLE = True
        print("✅ ibis-framework 9.0.0 loaded successfully")
    except Exception as test_error:
        print(f"⚠️  ibis functionality test failed: {test_error}")
        print("🔧 Disabling ibis support to avoid connection issues")
        IBIS_AVAILABLE = False
except ImportError as e:
    print(f"⚠️  ibis not found. ImportError: {e}")
    print("💡 This enables efficient predicate pushdown for queries")
    print("🔧 Falling back to Python-side filtering")
    IBIS_AVAILABLE = False
except Exception as e:
    print(f"⚠️  ibis compatibility issue: {e}")
    print("💡 Disabling ibis support to avoid connection issues")
    IBIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CrossObservatoryAnalytics:
    """Manages cross-observatory analytics using vastdb"""
    
    def __init__(self, config, show_api_calls: bool = False):
        """Initialize the cross-observatory analytics manager"""
        self.config = config
        self.show_api_calls = show_api_calls
        
        # Database configuration
        self.bucket_name = config.get('lab2.vastdb.bucket', 'your-tenant-metadata')
        self.schema_name = config.get('lab2.vastdb.schema', 'satellite_observations')
        
        # Database connection parameters for vastdb
        self.db_config = {
            'access': config.get_secret('s3_access_key'),
            'secret': config.get_secret('s3_secret_key'),
            'endpoint': config.get('lab2.vastdb.endpoint', 'http://localhost:8080'),
            'ssl_verify': config.get('lab2.vastdb.ssl_verify', True),
            'timeout': config.get('lab2.vastdb.timeout', 30)
        }
        
        # Analytics configuration
        self.analytics_config = config.get_analytics_config()
        self.batch_size = config.get_analytics_batch_size()
        self.query_timeout = config.get_query_timeout()
        self.burst_followup_window_days = config.get_burst_followup_window_days()
        self.coordinated_campaign_window_days = config.get_coordinated_campaign_window_days()
        self.burst_detection_threshold = config.get_burst_detection_threshold()
        
        self.connection = None
        self.database = None
    
    def _log_api_call(self, operation: str, details: str = ""):
        """Log API calls if show_api_calls is enabled"""
        if self.show_api_calls:
            print(f"\n🔧 API CALL: {operation}")
            if details:
                print(f"   Details: {details}")
            print()
    
    def connect(self) -> bool:
        """Establish connection to VAST Database"""
        if not VASTDB_AVAILABLE:
            logger.warning("⚠️  vastdb not available - using mock connection")
            self.connection = "MOCK_CONNECTION"
            return True
            
        try:
            self._log_api_call(
                "vastdb.connect()",
                f"endpoint={self.db_config['endpoint']}, ssl_verify={self.db_config['ssl_verify']}, timeout={self.db_config['timeout']}"
            )
            
            self.connection = vastdb.connect(**self.db_config)
            logger.info(f"✅ Connected to VAST Database at {self.db_config['endpoint']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to VAST Database: {e}")
            return False
    
    def setup_observatory_tables(self) -> bool:
        """Set up tables for both SWIFT and Chandra observatories"""
        logger.info("🏗️  Setting up observatory analytics tables...")
        
        try:
            if not self.connect():
                return False
            
            # Create SWIFT observations table
            swift_success = self._create_swift_observations_table()
            
            # Create Chandra observations table
            chandra_success = self._create_chandra_observations_table()
            
            # Create cross-observatory correlation table
            correlation_success = self._create_correlation_table()
            
            if swift_success and chandra_success and correlation_success:
                logger.info("✅ Observatory analytics tables setup completed successfully")
                return True
            else:
                logger.error("❌ Failed to setup some observatory analytics tables")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting up observatory analytics tables: {e}")
            return False
    
    def _create_swift_observations_table(self) -> bool:
        """Create SWIFT observations table"""
        logger.info("📡 Creating SWIFT observations table...")
        
        try:
            table_sql = """
            CREATE TABLE IF NOT EXISTS swift_observations (
                observation_id STRING PRIMARY KEY,
                target_object STRING NOT NULL,
                observation_time TIMESTAMP NOT NULL,
                xray_flux DOUBLE,
                uv_magnitude DOUBLE,
                optical_magnitude DOUBLE,
                data_quality DOUBLE,
                burst_detected BOOLEAN DEFAULT FALSE,
                exposure_time DOUBLE,
                energy_range_min DOUBLE,
                energy_range_max DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", "CREATE TABLE swift_observations")
                self.connection.execute(table_sql)
                logger.info("✅ Created SWIFT observations table")
            else:
                logger.info("🔍 MOCK: Would create SWIFT observations table")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating SWIFT observations table: {e}")
            return False
    
    def _create_chandra_observations_table(self) -> bool:
        """Create Chandra observations table"""
        logger.info("🔭 Creating Chandra observations table...")
        
        try:
            table_sql = """
            CREATE TABLE IF NOT EXISTS chandra_observations (
                observation_id STRING PRIMARY KEY,
                target_object STRING NOT NULL,
                observation_time TIMESTAMP NOT NULL,
                xray_flux DOUBLE,
                spectral_data ARRAY<DOUBLE>,
                resolution DOUBLE,
                data_quality DOUBLE,
                follow_up_observation BOOLEAN DEFAULT FALSE,
                exposure_time DOUBLE,
                energy_range_min DOUBLE,
                energy_range_max DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", "CREATE TABLE chandra_observations")
                self.connection.execute(table_sql)
                logger.info("✅ Created Chandra observations table")
            else:
                logger.info("🔍 MOCK: Would create Chandra observations table")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating Chandra observations table: {e}")
            return False
    
    def _create_correlation_table(self) -> bool:
        """Create cross-observatory correlation table"""
        logger.info("🔗 Creating cross-observatory correlation table...")
        
        try:
            table_sql = """
            CREATE TABLE IF NOT EXISTS observatory_correlations (
                correlation_id STRING PRIMARY KEY,
                target_object STRING NOT NULL,
                swift_observation_id STRING,
                chandra_observation_id STRING,
                correlation_time_window_hours DOUBLE,
                correlation_strength DOUBLE,
                multi_wavelength_flux_ratio DOUBLE,
                temporal_offset_hours DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", "CREATE TABLE observatory_correlations")
                self.connection.execute(table_sql)
                logger.info("✅ Created observatory correlations table")
            else:
                logger.info("🔍 MOCK: Would create observatory correlations table")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating correlation table: {e}")
            return False
    
    def find_cross_observatory_objects(self) -> List[Dict]:
        """Find objects observed by both SWIFT and Chandra"""
        logger.info("🔍 Finding cross-observatory objects...")
        
        try:
            query = """
            SELECT DISTINCT 
                swift.target_object,
                COUNT(swift.observation_id) as swift_observations,
                COUNT(chandra.observation_id) as chandra_observations,
                MIN(swift.observation_time) as first_swift_observation,
                MIN(chandra.observation_time) as first_chandra_observation
            FROM swift_observations swift
            INNER JOIN chandra_observations chandra 
                ON swift.target_object = chandra.target_object
            GROUP BY swift.target_object
            ORDER BY (COUNT(swift.observation_id) + COUNT(chandra.observation_id)) DESC
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", "Cross-observatory objects query")
                result = self.connection.execute(query)
                logger.info(f"✅ Found {len(result)} cross-observatory objects")
                return result
            else:
                logger.info("🔍 MOCK: Would find cross-observatory objects")
                return [
                    {
                        'target_object': 'V404_Cygni',
                        'swift_observations': 15,
                        'chandra_observations': 8,
                        'first_swift_observation': '2024-01-15 10:30:00',
                        'first_chandra_observation': '2024-01-15 11:45:00'
                    }
                ]
                
        except Exception as e:
            logger.error(f"❌ Error finding cross-observatory objects: {e}")
            return []
    
    def generate_multi_wavelength_light_curves(self, target_object: str) -> List[Dict]:
        """Generate multi-wavelength light curves for a specific target object"""
        logger.info(f"📈 Generating multi-wavelength light curves for {target_object}...")
        
        try:
            query = f"""
            SELECT 
                'swift' as observatory,
                observation_time,
                xray_flux,
                uv_magnitude,
                optical_magnitude,
                data_quality
            FROM swift_observations
            WHERE target_object = '{target_object}'
            
            UNION ALL
            
            SELECT 
                'chandra' as observatory,
                observation_time,
                xray_flux,
                NULL as uv_magnitude,
                NULL as optical_magnitude,
                data_quality
            FROM chandra_observations
            WHERE target_object = '{target_object}'
            
            ORDER BY observation_time
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", f"Multi-wavelength light curve query for {target_object}")
                result = self.connection.execute(query)
                logger.info(f"✅ Generated light curve with {len(result)} data points")
                return result
            else:
                logger.info(f"🔍 MOCK: Would generate multi-wavelength light curve for {target_object}")
                return [
                    {
                        'observatory': 'swift',
                        'observation_time': '2024-01-15 10:30:00',
                        'xray_flux': 0.85,
                        'uv_magnitude': 12.3,
                        'optical_magnitude': 11.8,
                        'data_quality': 0.95
                    },
                    {
                        'observatory': 'chandra',
                        'observation_time': '2024-01-15 11:45:00',
                        'xray_flux': 0.82,
                        'uv_magnitude': None,
                        'optical_magnitude': None,
                        'data_quality': 0.98
                    }
                ]
                
        except Exception as e:
            logger.error(f"❌ Error generating multi-wavelength light curves: {e}")
            return []
    
    def detect_burst_followup_sequences(self) -> List[Dict]:
        """Detect SWIFT bursts with Chandra follow-up observations"""
        logger.info("🚨 Detecting burst follow-up sequences...")
        
        try:
            query = f"""
            SELECT 
                swift.observation_id as swift_observation_id,
                chandra.observation_id as chandra_observation_id,
                swift.target_object,
                swift.observation_time as burst_time,
                chandra.observation_time as followup_time,
                EXTRACT(EPOCH FROM (chandra.observation_time - swift.observation_time))/3600 as hours_delay,
                swift.xray_flux as burst_flux,
                chandra.xray_flux as followup_flux,
                (chandra.xray_flux / swift.xray_flux) as flux_ratio
            FROM swift_observations swift
            INNER JOIN chandra_observations chandra 
                ON swift.target_object = chandra.target_object
            WHERE swift.burst_detected = TRUE
                AND chandra.follow_up_observation = TRUE
                AND chandra.observation_time > swift.observation_time
                AND EXTRACT(EPOCH FROM (chandra.observation_time - swift.observation_time))/86400 <= {self.burst_followup_window_days}
            ORDER BY swift.observation_time DESC
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", "Burst follow-up detection query")
                result = self.connection.execute(query)
                logger.info(f"✅ Found {len(result)} burst follow-up sequences")
                return result
            else:
                logger.info("🔍 MOCK: Would detect burst follow-up sequences")
                return [
                    {
                        'swift_observation_id': 'SWIFT_20240115_103000',
                        'chandra_observation_id': 'CHANDRA_20240115_114500',
                        'target_object': 'V404_Cygni',
                        'burst_time': '2024-01-15 10:30:00',
                        'followup_time': '2024-01-15 11:45:00',
                        'hours_delay': 1.25,
                        'burst_flux': 0.95,
                        'followup_flux': 0.82,
                        'flux_ratio': 0.86
                    }
                ]
                
        except Exception as e:
            logger.error(f"❌ Error detecting burst follow-up sequences: {e}")
            return []
    
    def analyze_data_quality_correlation(self) -> Dict:
        """Analyze data quality correlation between observatories"""
        logger.info("📊 Analyzing data quality correlation...")
        
        try:
            query = """
            SELECT 
                'swift' as observatory,
                AVG(data_quality) as avg_quality,
                MIN(data_quality) as min_quality,
                MAX(data_quality) as max_quality,
                COUNT(*) as observation_count
            FROM swift_observations
            WHERE data_quality IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'chandra' as observatory,
                AVG(data_quality) as avg_quality,
                MIN(data_quality) as min_quality,
                MAX(data_quality) as max_quality,
                COUNT(*) as observation_count
            FROM chandra_observations
            WHERE data_quality IS NOT NULL
            """
            
            if self.connection and self.connection != "MOCK_CONNECTION":
                self._log_api_call("vastdb.execute()", "Data quality correlation analysis")
                result = self.connection.execute(query)
                logger.info("✅ Completed data quality correlation analysis")
                return result
            else:
                logger.info("🔍 MOCK: Would analyze data quality correlation")
                return [
                    {
                        'observatory': 'swift',
                        'avg_quality': 0.92,
                        'min_quality': 0.75,
                        'max_quality': 0.99,
                        'observation_count': 1250
                    },
                    {
                        'observatory': 'chandra',
                        'avg_quality': 0.95,
                        'min_quality': 0.80,
                        'max_quality': 0.99,
                        'observation_count': 890
                    }
                ]
                
        except Exception as e:
            logger.error(f"❌ Error analyzing data quality correlation: {e}")
            return {}
    
    def get_analytics_summary(self) -> Dict:
        """Get a summary of cross-observatory analytics capabilities"""
        logger.info("📋 Generating analytics summary...")
        
        try:
            # Get cross-observatory objects
            cross_objects = self.find_cross_observatory_objects()
            
            # Get burst follow-up sequences
            burst_sequences = self.detect_burst_followup_sequences()
            
            # Get data quality analysis
            quality_analysis = self.analyze_data_quality_correlation()
            
            summary = {
                'cross_observatory_objects': len(cross_objects),
                'burst_followup_sequences': len(burst_sequences),
                'quality_analysis': quality_analysis,
                'analytics_capabilities': [
                    'Cross-observatory object identification',
                    'Multi-wavelength light curve generation',
                    'Burst follow-up sequence detection',
                    'Data quality correlation analysis',
                    'Temporal correlation analysis'
                ]
            }
            
            logger.info("✅ Analytics summary generated")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating analytics summary: {e}")
            return {}

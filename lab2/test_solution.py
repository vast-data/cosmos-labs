# test_solution.py
import unittest
from unittest.mock import Mock, patch
from lab2_solution import OrbitalDynamicsMetadataCatalog
from metadata_extractor import MetadataExtractor
from search_interface import MetadataSearchInterface
from lab2_config import Lab2ConfigLoader

class TestOrbitalDynamicsMetadataCatalog(unittest.TestCase):
    """Test cases for the metadata catalog system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=Lab2ConfigLoader)
        
        # Mock configuration values
        self.mock_config.get.side_effect = lambda key, default=None: {
            'catalog.name': 'orbital_dynamics_metadata',
            'catalog.batch_size': 1000,
            'catalog.max_retries': 3,
            'data.directories': ['/test/data'],
            'metadata.extractors': {},
            'metadata.quality_thresholds': {}
        }.get(key, default)
        
        self.mock_config.get_vast_config.return_value = {
            'user': 'test_user',
            'password': 'test_password',
            'address': 'test_host',
            'version': 'v1'
        }
        
        # Mock the VAST Catalog
        self.mock_catalog = Mock()
        
    @patch('lab2_solution.VASTCatalog')
    def test_initialization(self, mock_vast_catalog):
        """Test catalog system initialization"""
        mock_vast_catalog.return_value = self.mock_catalog
        
        catalog_system = OrbitalDynamicsMetadataCatalog(self.mock_config)
        
        self.assertIsNotNone(catalog_system.catalog)
        self.assertEqual(catalog_system.catalog_name, 'orbital_dynamics_metadata')
        self.assertEqual(catalog_system.batch_size, 1000)
    
    @patch('lab2_solution.VASTCatalog')
    def test_create_catalog_schema(self, mock_vast_catalog):
        """Test catalog schema creation"""
        mock_vast_catalog.return_value = self.mock_catalog
        
        catalog_system = OrbitalDynamicsMetadataCatalog(self.mock_config)
        
        # Mock successful schema creation
        self.mock_catalog.create_catalog.return_value = True
        
        result = catalog_system.create_catalog_schema()
        self.assertTrue(result)
    
    @patch('lab2_solution.VASTCatalog')
    def test_metadata_extraction(self, mock_vast_catalog):
        """Test metadata extraction from files"""
        mock_vast_catalog.return_value = self.mock_catalog
        
        catalog_system = OrbitalDynamicsMetadataCatalog(self.mock_config)
        
        # Test with a mock file path
        with patch('os.path.exists', return_value=True):
            with patch('os.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                mock_stat.return_value.st_mtime = 1234567890
                
                metadata = catalog_system.extract_metadata_from_file('/test/file.fits')
                
                self.assertIsNotNone(metadata)
                self.assertEqual(metadata['file_size_bytes'], 1024)

class TestMetadataExtractor(unittest.TestCase):
    """Test cases for metadata extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = MetadataExtractor()
    
    def test_fits_metadata_extraction(self):
        """Test FITS metadata extraction"""
        with patch('os.path.exists', return_value=True):
            with patch('os.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                mock_stat.return_value.st_mtime = 1234567890
                
                # Test with standard FITS filename
                metadata = self.extractor.extract_metadata('/test/COSMOS7_MARS_20241201_143022.fits')
                
                self.assertIsNotNone(metadata)
                self.assertEqual(metadata['file_format'], 'FITS')
                self.assertEqual(metadata['satellite_name'], 'COSMOS7')
                self.assertEqual(metadata['target_object'], 'MARS')
    
    def test_json_metadata_extraction(self):
        """Test JSON metadata extraction"""
        with patch('os.path.exists', return_value=True):
            with patch('os.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                mock_stat.return_value.st_mtime = 1234567890
                
                # Mock JSON file content
                json_content = {
                    'satellite_name': 'COSMOS7',
                    'target_object': 'MARS',
                    'quality_score': 0.9,
                    'calibration_status': 'COMPLETED'
                }
                
                with patch('builtins.open', mock_open(read_data=str(json_content))):
                    with patch('json.load', return_value=json_content):
                        metadata = self.extractor.extract_metadata('/test/data.json')
                        
                        self.assertIsNotNone(metadata)
                        self.assertEqual(metadata['file_format'], 'JSON')
                        self.assertEqual(metadata['satellite_name'], 'COSMOS7')
                        self.assertEqual(metadata['data_quality_score'], 0.9)
    
    def test_metadata_validation(self):
        """Test metadata validation"""
        test_metadata = {
            'file_path': '/test/file.fits',
            'file_format': 'FITS',
            'satellite_name': 'COSMOS7',
            'target_object': 'MARS',
            'data_quality_score': 0.8,
            'calibration_status': 'PENDING',
            'processing_status': 'RAW'
        }
        
        validated = self.extractor.validate_metadata(test_metadata)
        
        self.assertEqual(validated['file_path'], '/test/file.fits')
        self.assertEqual(validated['data_quality_score'], 0.8)
        
        # Test with invalid quality score
        test_metadata['data_quality_score'] = 1.5
        validated = self.extractor.validate_metadata(test_metadata)
        self.assertEqual(validated['data_quality_score'], 1.0)

class TestMetadataSearchInterface(unittest.TestCase):
    """Test cases for the search interface"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=Lab2ConfigLoader)
        
        # Mock configuration values
        self.mock_config.get.side_effect = lambda key, default=None: {
            'catalog.name': 'orbital_dynamics_metadata',
            'search.default_limit': 100,
            'search.max_limit': 1000
        }.get(key, default)
        
        self.mock_config.get_vast_config.return_value = {
            'user': 'test_user',
            'password': 'test_password',
            'address': 'test_host',
            'version': 'v1'
        }
        
        # Mock the VAST Catalog
        self.mock_catalog = Mock()
        
    @patch('search_interface.VASTCatalog')
    def test_search_by_mission(self, mock_vast_catalog):
        """Test searching by mission"""
        mock_vast_catalog.return_value = self.mock_catalog
        
        # Mock search results
        mock_results = [
            {'mission_id': 'COSMOS7', 'target_object': 'MARS'},
            {'mission_id': 'COSMOS7', 'target_object': 'JUPITER'}
        ]
        self.mock_catalog.search.return_value = mock_results
        
        search_interface = MetadataSearchInterface(self.mock_config)
        results = search_interface.search_by_mission('COSMOS7')
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['mission_id'], 'COSMOS7')
    
    @patch('search_interface.VASTCatalog')
    def test_advanced_search(self, mock_vast_catalog):
        """Test advanced search with multiple criteria"""
        mock_vast_catalog.return_value = self.mock_catalog
        
        # Mock search results
        mock_results = [
            {
                'mission_id': 'COSMOS7',
                'target_object': 'MARS',
                'data_quality_score': 0.9,
                'processing_status': 'PROCESSED'
            }
        ]
        self.mock_catalog.search.return_value = mock_results
        
        search_interface = MetadataSearchInterface(self.mock_config)
        
        criteria = {
            'mission_id': 'COSMOS7',
            'min_quality': 0.8,
            'processing_status': 'PROCESSED'
        }
        
        results = search_interface.advanced_search(criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['mission_id'], 'COSMOS7')
        self.assertEqual(results[0]['data_quality_score'], 0.9)

class TestConfigLoader(unittest.TestCase):
    """Test cases for the configuration loader"""
    
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_config_loading(self, mock_yaml_load, mock_open):
        """Test configuration file loading"""
        mock_yaml_load.return_value = {
            'vast': {
                'user': 'test_user',
                'password': 'test_password',
                'address': 'test_host'
            },
            'catalog': {
                'name': 'test_catalog',
                'port': 8080
            }
        }
        
        config = Lab2ConfigLoader()
        
        self.assertEqual(config.get('vast.user'), 'test_user')
        self.assertEqual(config.get('catalog.name'), 'test_catalog')
        self.assertEqual(config.get('catalog.port'), 8080)
    
    def test_dot_notation_access(self):
        """Test dot notation configuration access"""
        config = Lab2ConfigLoader()
        config.config = {
            'vast': {
                'user': 'test_user',
                'settings': {
                    'timeout': 30
                }
            },
            'catalog': {
                'name': 'test_catalog'
            }
        }
        
        self.assertEqual(config.get('vast.user'), 'test_user')
        self.assertEqual(config.get('vast.settings.timeout'), 30)
        self.assertEqual(config.get('catalog.name'), 'test_catalog')
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')

if __name__ == '__main__':
    unittest.main() 
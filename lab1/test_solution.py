# test_solution.py
import unittest
from unittest.mock import Mock, patch
from lab1_solution import OrbitalDynamicsStorageManager
from config_loader import ConfigLoader

class TestOrbitalDynamicsStorageManager(unittest.TestCase):
    """Test cases for the storage manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=ConfigLoader)
        
        # Mock configuration values
        self.mock_config.get.side_effect = lambda key, default=None: {
            'storage.raw_data_path': '/cosmos7/raw',
            'storage.processed_data_path': '/cosmos7/processed',
            'storage.temp_data_path': '/cosmos7/temp',
            'quotas.warning_threshold': 75,
            'quotas.critical_threshold': 85,
            'quotas.auto_expand_size_tb': 10,
            'monitoring.interval_seconds': 300
        }.get(key, default)
        
        self.mock_config.get_vast_config.return_value = {
            'user': 'test_user',
            'password': 'test_password',
            'address': 'test_host',
            'version': 'v1'
        }
        
        # Mock the VAST client
        self.mock_client = Mock()
        
    @patch('lab1_solution.VASTClient')
    def test_initialization(self, mock_vast_client):
        """Test storage manager initialization"""
        mock_vast_client.return_value = self.mock_client
        
        manager = OrbitalDynamicsStorageManager(self.mock_config)
        
        self.assertIsNotNone(manager.client)
        self.assertEqual(manager.raw_data_path, '/cosmos7/raw')
        self.assertEqual(manager.processed_data_path, '/cosmos7/processed')
        self.assertEqual(manager.warning_threshold, 75)
        self.assertEqual(manager.critical_threshold, 85)
    
    @patch('lab1_solution.VASTClient')
    def test_get_view_utilization(self, mock_vast_client):
        """Test view utilization calculation"""
        mock_vast_client.return_value = self.mock_client
        
        # Mock view response
        mock_view = {'id': 'test_id', 'size': 1000000000, 'quota': 2000000000}
        self.mock_client.views.get.return_value = [mock_view]
        self.mock_client.views.__getitem__.return_value.get.return_value = {
            'size': 1000000000,
            'quota': 2000000000
        }
        
        manager = OrbitalDynamicsStorageManager(self.mock_config)
        utilization = manager.get_view_utilization('/test/path')
        
        self.assertEqual(utilization, 50.0)  # 50% utilization
    
    @patch('lab1_solution.VASTClient')
    def test_status_level_determination(self, mock_vast_client):
        """Test status level determination"""
        mock_vast_client.return_value = self.mock_client
        
        manager = OrbitalDynamicsStorageManager(self.mock_config)
        
        # Test different utilization levels
        self.assertEqual(manager._get_status_level(50), 'NORMAL')
        self.assertEqual(manager._get_status_level(80), 'WARNING')
        self.assertEqual(manager._get_status_level(90), 'CRITICAL')
        self.assertEqual(manager._get_status_level(None), 'UNKNOWN')

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
            }
        }
        
        config = ConfigLoader('test_config.yaml', 'test_secrets.yaml')
        
        self.assertEqual(config.get('vast.user'), 'test_user')
        self.assertEqual(config.get('vast.password'), 'test_password')
    
    def test_dot_notation_access(self):
        """Test dot notation configuration access"""
        config = ConfigLoader()
        config.config = {
            'vast': {
                'user': 'test_user',
                'settings': {
                    'timeout': 30
                }
            }
        }
        
        self.assertEqual(config.get('vast.user'), 'test_user')
        self.assertEqual(config.get('vast.settings.timeout'), 30)
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')

if __name__ == '__main__':
    unittest.main() 
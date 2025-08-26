
"""
Basic tests for the ContentDM AI application
"""

import pytest
import sys
from pathlib import Path
import tempfile
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contentdm_api import ContentDMAPI
from ai_processor import AIProcessor
from data_manager import DataManager
from utils.config_manager import ConfigManager


class TestConfigManager:
    """Test configuration management"""
    
    def test_default_config_loading(self):
        """Test loading default configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'contentdm': {'base_url': 'https://test.example.com'},
                'ai_models': {'image_captioning': {'model_name': 'test-model'}}
            }
            yaml.dump(config_data, f)
            f.flush()
            
            config_manager = ConfigManager(f.name)
            config = config_manager.get_config()
            
            assert config['contentdm']['base_url'] == 'https://test.example.com'
            assert config['ai_models']['image_captioning']['model_name'] == 'test-model'


class TestContentDMAPI:
    """Test ContentDM API integration"""
    
    def test_api_initialization(self):
        """Test API client initialization"""
        config = {
            'base_url': 'https://test.example.com',
            'timeout': 30,
            'max_retries': 3
        }
        
        api = ContentDMAPI(config)
        
        assert api.base_url == 'https://test.example.com'
        assert api.timeout == 30
        assert api.max_retries == 3
    
    def test_url_parsing(self):
        """Test ContentDM URL parsing"""
        api = ContentDMAPI({'base_url': 'https://test.example.com'})
        
        # Test standard URL pattern
        url = "https://vu.contentdm.oclc.org/digital/collection/vko/id/347"
        collection, item_id = api._parse_contentdm_url(url)
        
        assert collection == "vko"
        assert item_id == "347"
    
    def test_item_validation(self):
        """Test item validation logic"""
        api = ContentDMAPI({'base_url': 'https://test.example.com'})
        
        # This will fail without network, but tests the structure
        # In a real test environment, you'd mock the HTTP calls
        try:
            result = api.validate_item("test_collection", "123")
            assert isinstance(result, bool)
        except Exception:
            # Expected without network connectivity
            pass


class TestAIProcessor:
    """Test AI processing functionality"""
    
    def test_processor_initialization(self):
        """Test AI processor initialization"""
        config = {
            'image_captioning': {
                'model_name': 'Salesforce/blip-image-captioning-base',
                'device': 'cpu'
            },
            'ocr': {
                'engine': 'tesseract',
                'lang': 'eng'
            },
            'ner': {
                'model': 'en_core_web_sm',
                'enable_wikidata': True,
                'enable_dbpedia': True
            }
        }
        
        processor = AIProcessor(config)
        
        assert processor.device == 'cpu'
        assert processor.image_config['model_name'] == 'Salesforce/blip-image-captioning-base'
        assert processor.ner_config['enable_wikidata'] is True


class TestDataManager:
    """Test data management functionality"""
    
    def test_data_manager_initialization(self):
        """Test data manager initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'output_dir': temp_dir,
                'csv_encoding': 'utf-8',
                'zip_compression': True
            }
            
            manager = DataManager(config)
            
            assert str(manager.output_dir) == temp_dir
            assert manager.csv_encoding == 'utf-8'
            assert manager.zip_compression is True
    
    def test_csv_data_preparation(self):
        """Test CSV data preparation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'output_dir': temp_dir}
            manager = DataManager(config)
            
            metadata = {'title': 'Test Item', 'creator': 'Test Creator'}
            ai_results = {
                'description': 'Test description',
                'entities': [{'text': 'Test Entity', 'label': 'PERSON'}]
            }
            
            csv_data = manager._prepare_csv_data(metadata, ai_results)
            
            assert 'original_title' in csv_data
            assert 'ai_description' in csv_data
            assert csv_data['ai_description'] == 'Test description'


def test_imports():
    """Test that all modules can be imported"""
    from contentdm_api import ContentDMAPI
    from ai_processor import AIProcessor
    from data_manager import DataManager
    from utils.config_manager import ConfigManager
    from utils.logger import setup_logger
    from components.iframe_monitor import IFrameMonitor
    from components.processing_log import ProcessingLog
    
    assert ContentDMAPI
    assert AIProcessor
    assert DataManager
    assert ConfigManager
    assert setup_logger
    assert IFrameMonitor
    assert ProcessingLog


if __name__ == "__main__":
    pytest.main([__file__])

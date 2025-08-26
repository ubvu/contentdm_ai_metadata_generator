
"""
Configuration Manager
Handles loading and validation of configuration files
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Default config path
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with fallbacks"""
        
        # Default configuration
        default_config = {
            'contentdm': {
                'base_url': 'https://vu.contentdm.oclc.org',
                'api_endpoint': '/digital/bl/dmwebservices/index.php',
                'default_collection': 'vko',
                'timeout': 30,
                'max_retries': 3
            },
            'ai_models': {
                'image_captioning': {
                    'model_name': 'Salesforce/blip-image-captioning-base',
                    'device': 'auto',
                    'max_length': 100,
                    'num_beams': 4
                },
                'ocr': {
                    'engine': 'tesseract',
                    'lang': 'eng',
                    'config': '--psm 6'
                },
                'ner': {
                    'model': 'en_core_web_sm',
                    'enable_wikidata': True,
                    'enable_dbpedia': True,
                    'confidence_threshold': 0.7
                }
            },
            'export': {
                'output_dir': 'outputs',
                'csv_encoding': 'utf-8',
                'include_thumbnails': True,
                'zip_compression': True
            },
            'processing': {
                'batch_size': 10,
                'max_workers': 4,
                'enable_caching': True,
                'cache_dir': '.cache'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'contentdm_ai.log'
            }
        }
        
        try:
            # Try to load user config
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                
                if user_config:
                    # Merge user config with defaults
                    config = self._merge_configs(default_config, user_config)
                    self.logger.info(f"Loaded configuration from {self.config_path}")
                else:
                    config = default_config
                    self.logger.warning(f"Empty config file, using defaults")
            else:
                config = default_config
                self.logger.info("No config file found, using default configuration")
                
                # Create example config file
                example_path = self.config_path.parent / "config.example.yaml"
                if example_path.exists():
                    self.logger.info("To customize configuration, copy config.example.yaml to config.yaml")
            
            # Validate configuration
            self._validate_config(config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")
            return default_config
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with default config"""
        result = deepcopy(default)
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration values"""
        try:
            # Validate ContentDM config
            contentdm_config = config.get('contentdm', {})
            if not contentdm_config.get('base_url'):
                raise ValueError("ContentDM base_url is required")
            
            # Validate AI models config
            ai_config = config.get('ai_models', {})
            if not ai_config.get('image_captioning', {}).get('model_name'):
                raise ValueError("Image captioning model_name is required")
            
            # Validate export config
            export_config = config.get('export', {})
            output_dir = export_config.get('output_dir', 'outputs')
            
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            self.logger.debug("Configuration validation successful")
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get specific configuration section"""
        return self.config.get(section, {})
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            # Merge updates with current config
            new_config = self._merge_configs(self.config, updates)
            
            # Validate new configuration
            self._validate_config(new_config)
            
            # Update current config
            self.config = new_config
            
            self.logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def save_config(self, save_path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            if save_path is None:
                save_path = self.config_path
            else:
                save_path = Path(save_path)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_env_var(self, var_name: str, default: Any = None) -> Any:
        """Get environment variable with fallback to config"""
        env_value = os.getenv(var_name)
        if env_value is not None:
            # Try to parse as appropriate type
            if isinstance(default, bool):
                return env_value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    pass
            elif isinstance(default, float):
                try:
                    return float(env_value)
                except ValueError:
                    pass
            return env_value
        
        return default
    
    def create_example_config(self, example_path: Optional[str] = None) -> bool:
        """Create example configuration file"""
        try:
            if example_path is None:
                example_path = self.config_path.parent / "config.example.yaml"
            else:
                example_path = Path(example_path)
            
            # Don't overwrite existing example
            if example_path.exists():
                return True
            
            with open(example_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Example configuration created at {example_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating example configuration: {e}")
            return False

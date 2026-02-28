"""
Configuration Loader Module
Loads configuration from config.yaml and supports environment overrides
"""

import os
import yaml
from typing import Any, Dict, Optional

_config: Optional[Dict[str, Any]] = None


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from YAML file with fallback defaults"""
    global _config
    
    if _config is not None and config_path is None:
        return _config
    
    # Default configuration
    default_config = {
        'app': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': True,
            'title': 'Google Workspace AI Assistant',
            'version': '1.0.0'
        },
        'google': {
            'client_id': '',
            'client_secret': '',
            'redirect_uri': 'http://localhost:8000/auth/callback',
            'scopes': []
        },
        'token': {
            'storage_type': 'file',
            'file_path': 'tokens/',
            'prefix': 'google_workspace'
        },
        'ai': {
            'provider': 'openai',
            'model': 'gpt-4',
            'api_key': '',
            'max_tokens': 2000,
            'temperature': 0.7
        },
        'session': {
            'secret_key': 'your-secret-key-change-in-production',
            'expire_minutes': 60
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'logs/app.log'
        }
    }
    
    # Try to load from file
    config = default_config.copy()
    
    if config_path is None:
        config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
    
    # Try to load local config first
    local_config_path = config_path.replace('.yaml', '.local.yaml')
    
    # Check which file exists
    file_to_load = None
    if os.path.exists(local_config_path):
        file_to_load = local_config_path
    elif os.path.exists(config_path):
        file_to_load = config_path
    
    # Load if exists
    if file_to_load:
        try:
            with open(file_to_load, 'r') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    # Merge loaded config with defaults
                    config = _merge_config(config, loaded_config)
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_to_load}: {e}")
            print("Using default configuration")
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
    else:
        print(f"Config file not found: {config_path}")
        print("Using default configuration")
    
    # Apply environment variable overrides
    config = _apply_env_overrides(config)
    
    _config = config
    return config


def _merge_config(base: Dict, override: Dict) -> Dict:
    """Recursively merge configurations"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration"""
    
    # Google credentials
    if os.environ.get('GOOGLE_CLIENT_ID'):
        config['google']['client_id'] = os.environ['GOOGLE_CLIENT_ID']
    if os.environ.get('GOOGLE_CLIENT_SECRET'):
        config['google']['client_secret'] = os.environ['GOOGLE_CLIENT_SECRET']
    
    # AI configuration
    if os.environ.get('AI_API_KEY'):
        config['ai']['api_key'] = os.environ['AI_API_KEY']
    if os.environ.get('AI_MODEL'):
        config['ai']['model'] = os.environ['AI_MODEL']
    
    # Session
    if os.environ.get('SESSION_SECRET_KEY'):
        config['session']['secret_key'] = os.environ['SESSION_SECRET_KEY']
    
    # App settings
    if os.environ.get('APP_PORT'):
        config['app']['port'] = int(os.environ['APP_PORT'])
    if os.environ.get('APP_DEBUG'):
        config['app']['debug'] = os.environ['APP_DEBUG'].lower() == 'true'
    
    return config


def get_nested(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get a nested configuration value"""
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        
        if value is None:
            return default
    
    return value


# Export commonly used functions
__all__ = ['load_config', 'apply_env_overrides', 'get_nested']

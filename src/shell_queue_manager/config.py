import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "DEBUG": False,
    "TESTING": False,
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "LOG_LEVEL": "INFO",
    "LOG_FILE": None,
    
    "MAX_QUEUE_SIZE": 1000,
    "MAX_HISTORY_SIZE": 100,
    "SCRIPT_TIMEOUT": 60*60*24*7,  # in seconds
    
    "EMAIL_ENABLED": False,
    "EMAIL_HOST": "smtp.example.com",
    "EMAIL_PORT": 587,
    "EMAIL_USERNAME": "",
    "EMAIL_PASSWORD": "",
    "EMAIL_SENDER": "shell-queue@example.com",
    "EMAIL_RECIPIENTS": ["admin@example.com"],
    "EMAIL_USE_TLS": True,
    
    "NOTIFY_QUEUE_LOW_THRESHOLD": 1,
    "NOTIFY_ON_TASK_FAILURE": True,
}

PRIVATE_CONFIG_FILES = [
    Path(__file__).parent/'private_config.json',
    Path(__file__).parent.parent.parent/'private_config.json',
]

def load_config() -> Dict[str, Any]:
    """
    Load configuration with the following priority:
    1. Environment variables
    2. Private configuration file
    3. Default configuration
    
    Returns:
        Dictionary containing configuration values
    """
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from private configuration file
    private_config = _load_private_config()
    if private_config:
        config.update(private_config)
        logger.info("Private configuration loaded")
    
    # Environment variables override configuration files
    env_config = _load_from_environment()
    if env_config:
        config.update(env_config)
    
    return config

def _load_private_config() -> Dict[str, Any]:
    """
    Load configuration from private configuration file.
    
    Returns:
        Configuration dictionary, or empty dictionary if no configuration file found
    """
    for config_file in PRIVATE_CONFIG_FILES:
        if os.path.isfile(config_file):
            try:
                with open(config_file, 'r') as f:
                    logger.info(f"Loading private configuration from {config_file}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading configuration file {config_file}: {e}")
    
    return {}

def _load_from_environment() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Configuration dictionary loaded from environment variables
    """
    env_config = {}
    
    # Iterate through default configuration keys and look for corresponding environment variables
    for key in DEFAULT_CONFIG:
        env_var = f"SHELL_QUEUE_{key}"
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert boolean values
            if value.lower() in ('true', 'yes', '1'):
                value = True
            elif value.lower() in ('false', 'no', '0'):
                value = False
            
            # Convert numbers
            elif value.isdigit():
                value = int(value)
            
            # Convert lists (comma-separated)
            elif key == "EMAIL_RECIPIENTS" and "," in value:
                value = [email.strip() for email in value.split(",")]
            
            env_config[key] = value
    
    return env_config

def get_email_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract email configuration from the main configuration.
    
    Parameters:
        config: Main configuration dictionary
        
    Returns:
        Email configuration dictionary
    """
    return {
        "enable": config.get("EMAIL_ENABLED", False),
        "host": config.get("EMAIL_HOST", ""),
        "port": config.get("EMAIL_PORT", 587),
        "username": config.get("EMAIL_USERNAME", ""),
        "password": config.get("EMAIL_PASSWORD", ""),
        "sender": config.get("EMAIL_SENDER", ""),
        "recipients": config.get("EMAIL_RECIPIENTS", []),
        "use_tls": config.get("EMAIL_USE_TLS", True)
    }

def create_private_config_template(path: str = None) -> bool:
    """
    Create a private configuration file template.
    
    Parameters:
        path: Path to save the configuration file, defaults to package location
        
    Returns:
        True if successfully created, False otherwise
    """
    # If no path specified, use default location
    if path is None:
        path = PRIVATE_CONFIG_FILES[0]
    
    # Create directory (if needed)
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            return False
    
    # Check if file already exists
    if os.path.exists(path):
        logger.warning(f"Configuration file already exists: {path}")
        return False
    
    try:
        # Create template configuration
        template = {
            "EMAIL_ENABLED": False,
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_PORT": 587,
            "EMAIL_USERNAME": "your_username",
            "EMAIL_PASSWORD": "your_password",
            "EMAIL_SENDER": "your_email@example.com",
            "EMAIL_RECIPIENTS": ["recipient@example.com"]
        }
        
        # Write to file
        with open(path, 'w') as f:
            json.dump(template, f, indent=4)
        
        logger.info(f"Configuration template created: {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create configuration template: {e}")
        return False
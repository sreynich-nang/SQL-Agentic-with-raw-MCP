"""Environment utilities for configuration management"""

import os
from dotenv import load_dotenv
from typing import Dict, List

def load_env() -> None:
    """Load environment variables from .env file"""
    load_dotenv()

def check_env_vars(required_vars: List[str]) -> Dict[str, str]:
    """
    Check if all required environment variables are set
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary of environment variables
        
    Raises:
        ValueError: If any required variables are missing
    """
    missing_vars = []
    env_dict = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_dict[var] = value
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return env_dict

def get_db_config() -> Dict[str, str]:
    """Get database configuration from environment variables"""
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME']
    return check_env_vars(required_vars)

def get_model_config() -> Dict[str, str]:
    """Get model configuration from environment variables"""
    required_vars = ['MODEL_ID', 'MODEL_API_KEY']
    return check_env_vars(required_vars)


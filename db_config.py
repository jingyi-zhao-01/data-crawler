#!/usr/bin/env python3
import os

def get_db_config():
    """
    Returns database configuration based on environment
    
    In development: Uses local Docker Compose PostgreSQL instance
    In production: Uses the PostgreSQL URL from environment variables
    """
    # Default development configuration (matches docker-compose.yml)
    config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
        'database': os.environ.get('DB_NAME', 'gpu_prices'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres')
    }
    
    # If POSTGRES_URL is set, it overrides individual settings (used in production)
    postgres_url = os.environ.get('POSTGRES_URL')
    if postgres_url:
        return {'url': postgres_url}
    
    return config

def get_connection_string():
    """
    Returns a connection string for PostgreSQL based on configuration
    """
    config = get_db_config()
    
    # If URL is directly provided, return it
    if 'url' in config:
        return config['url']
    
    # Otherwise, build connection string from individual parameters
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
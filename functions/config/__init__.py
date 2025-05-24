"""Configuration module for the application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Determine which environment settings to use
ENV = os.environ.get('ENVIRONMENT', 'development')

if ENV == 'production':
    from .prod import CONFIG
elif ENV == 'testing':
    # For testing environment
    from .settings import COMMON_CONFIG, COLLECTIONS, API_CONFIG

    # Testing specific overrides
    TEST_OVERRIDES = {
        "log_level": "DEBUG",
        "firebase_emulator": True,
        "emulator_host": "localhost:8080",
        "testing": True
    }

    # Create testing config
    CONFIG = {
        **COMMON_CONFIG,
        **TEST_OVERRIDES,
        "collections": COLLECTIONS,
        "api": API_CONFIG,
        "environment": "testing",
    }
else:
    from .dev import CONFIG

# Export the right configuration
config = CONFIG

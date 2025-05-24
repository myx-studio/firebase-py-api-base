"""Development environment specific settings."""
import copy
import os

from .settings import COMMON_CONFIG, COLLECTIONS, API_CONFIG

# Development specific overrides
DEV_OVERRIDES = {
    "log_level": os.environ.get("LOG_LEVEL", "DEBUG"),
    "firebase_emulator": True,
    "emulator_host": "localhost:8080",
    "mailgun": {
        "api_key": os.environ.get("MAILGUN_API_KEY", ""),
        "domain": os.environ.get("MAILGUN_DOMAIN", "mg.nghbr.app"),
        "from_email": os.environ.get("MAILGUN_FROM_EMAIL", "noreply@mg.nghbr.app"),
        "from_name": os.environ.get("MAILGUN_FROM_NAME", "Plek")
    },
    "firebase": {
        "web_api_key": os.environ.get("WEB_API_KEY", ""),
        "project_id": os.environ.get("PROJECT_ID", ""),
        "storage_bucket": os.environ.get("STORAGE_BUCKET", ""),
        "database_url": os.environ.get("DATABASE_URL", ""),
        "auth_domain": os.environ.get("AUTH_DOMAIN", f"{os.environ.get('PROJECT_ID', '')}.firebaseapp.com")
    },
    "expo": {
        "token": os.environ.get("EXPO_TOKEN", "")
    },
    "security": {
        "jwt_secret": os.environ.get("JWT_SECRET", "")
    }
}

# Create a deep copy of the common config
CONFIG = copy.deepcopy(COMMON_CONFIG)

# Properly merge nested dictionaries
for key, value in DEV_OVERRIDES.items():
    if key in CONFIG and isinstance(CONFIG[key], dict) and isinstance(value, dict):
        # If both are dictionaries, update the existing dictionary
        CONFIG[key].update(value)
    else:
        # Otherwise, replace the value
        CONFIG[key] = value

# Add additional configuration
CONFIG["collections"] = COLLECTIONS
CONFIG["api"] = API_CONFIG
CONFIG["environment"] = "development"

"""Production environment specific settings."""
from .settings import COMMON_CONFIG, COLLECTIONS, API_CONFIG

# Production specific overrides
PROD_OVERRIDES = {
    "log_level": "WARNING",
    "cors_origins": [
        "*",
    ],
}

# Create a deep copy of the common config
import copy
CONFIG = copy.deepcopy(COMMON_CONFIG)

# Properly merge nested dictionaries
for key, value in PROD_OVERRIDES.items():
    if key in CONFIG and isinstance(CONFIG[key], dict) and isinstance(value, dict):
        # If both are dictionaries, update the existing dictionary
        CONFIG[key].update(value)
    else:
        # Otherwise, replace the value
        CONFIG[key] = value

# Add additional configuration
CONFIG["collections"] = COLLECTIONS
CONFIG["api"] = API_CONFIG
CONFIG["environment"] = "production"

"""Common settings shared across all environments."""
import os

# Firebase settings - these should be overridden in environment-specific settings
FIREBASE_CONFIG = {
    "web_api_key": os.environ.get("WEB_API_KEY", ""),  # Should be set in environment variables
    "database_url": os.environ.get("DATABASE_URL", "https://parent-ceo-default-rtdb.firebaseio.com"),
    "project_id": os.environ.get("PROJECT_ID", "parent-ceo"),
    "storage_bucket": os.environ.get("STORAGE_BUCKET", "parent-ceo.appspot.com"),
}

# Expo Push Notification settings
EXPO_CONFIG = {
    "token": os.environ.get("EXPO_TOKEN", ""),  # Should be set in environment variables
    "push_url": "https://exp.host/--/api/v2/push/send",
}

# Mailgun Email Service settings
MAILGUN_CONFIG = {
    "api_key": os.environ.get("MAILGUN_API_KEY", ""),  # Should be set in environment variables
    "domain": os.environ.get("MAILGUN_DOMAIN", ""),
    "from_email": os.environ.get("MAILGUN_FROM_EMAIL", "noreply@parent.ceo"),
    "from_name": os.environ.get("MAILGUN_FROM_NAME", "Parent CEO"),
}

# Common application settings
COMMON_CONFIG = {
    "app_name": "ParentCEO API",
    "version": "1.0.0",
    "cors_origins": ["*"],  # Allow all origins for mobile app access
    "cors_allow_headers": ["Content-Type", "Authorization", "Content-Length", "X-Requested-With", "Accept"],
    "cors_allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "default_timezone": "UTC",
    "log_level": os.environ.get("LOG_LEVEL", "INFO"),
    "firebase": FIREBASE_CONFIG,
    "expo": EXPO_CONFIG,
    "mailgun": MAILGUN_CONFIG,
}

# Firebase collections
COLLECTIONS = {
    "users": "users",
    "password_resets": "password_resets",
    "device_tokens": "device_tokens",
    "notifications": "notifications",
    # Add more collections as needed
}

# API settings
API_CONFIG = {
    "prefix": "/v1",
    "rate_limit": 100,  # requests per minute
}

"""Main entry point for Firebase Functions and Flask API."""
import os
from pathlib import Path
from dotenv import load_dotenv
from firebase_admin import initialize_app, get_app, credentials
from flask import Flask
from firebase_functions import https_fn
import functions_framework

# Load .env file before importing config
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from config import CONFIG

# Ensure Firebase is initialized BEFORE importing any modules that use it
# This prevents circular import issues and ensures Firebase is available


def detect_emulator():
    """Detect if running in Firebase emulator environment.

    Returns:
        dict: Configuration for emulator with emulator_host and is_emulator flag
    """
    emulator_host = os.environ.get("FIREBASE_EMULATOR_HOST")
    firestore_emulator = os.environ.get("FIRESTORE_EMULATOR_HOST")
    auth_emulator = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")

    is_emulator = emulator_host is not None or firestore_emulator is not None or auth_emulator is not None

    if is_emulator:
        print("Running in emulator mode!")
        print(f"FIREBASE_EMULATOR_HOST={emulator_host}")
        print(f"FIRESTORE_EMULATOR_HOST={firestore_emulator}")
        print(f"FIREBASE_AUTH_EMULATOR_HOST={auth_emulator}")

    return {
        "is_emulator": is_emulator,
        "emulator_host": emulator_host or firestore_emulator,
        "auth_emulator": auth_emulator,
        "firestore_emulator": firestore_emulator
    }


# Initialize Firebase Admin with proper configuration
try:
    # Try to get the default app if it already exists
    app = get_app()
    print("Using existing Firebase app")
except ValueError:
    # If default app doesn't exist, initialize it
    try:
        # Check if running in emulator
        emulator_config = detect_emulator()
        is_emulator = emulator_config["is_emulator"]

        # Get Firebase config
        firebase_config = CONFIG.get("firebase", {})
        database_url = firebase_config.get("database_url", "https://parent-ceo-default-rtdb.firebaseio.com")
        project_id = firebase_config.get("project_id", "parent-ceo")

        # Setup options
        options = {
            'databaseURL': database_url,
            'projectId': project_id,
        }

        # Initialize the app with null credentials for emulator
        if is_emulator:
            print("Initializing Firebase with emulator settings")
            # For emulator, use a credentials.ApplicationDefault() object
            cred = credentials.ApplicationDefault()
            app = initialize_app(credential=cred, options=options)
        else:
            # For production, use the service account key file
            service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
            if os.path.exists(service_account_path):
                print(f"Using service account key from: {service_account_path}")
                cred = credentials.Certificate(service_account_path)
                app = initialize_app(credential=cred, options=options)
            else:
                # Fallback to default credentials if service account file not found
                print(f"Service account key file not found at {service_account_path}, using default credentials")
                app = initialize_app(options=options)

        print(f"Firebase initialized successfully with project: {project_id}")

        # Set environment variables for emulator if not already set
        if is_emulator and not os.environ.get("FIRESTORE_EMULATOR_HOST"):
            print("Setting emulator environment variables")
            if emulator_config.get("emulator_host"):
                os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_config["emulator_host"]

    except Exception as e:
        # Handle initialization errors (will be handled by mocks in test environment)
        print(f"Firebase initialization error: {str(e)}")

# Create Flask app
flask_app = Flask(__name__)

# Now that Firebase is initialized, we can import API modules
import api.v1 as api_v1

# Register API v1 routes
api_v1.register_routes(flask_app)
# Create Firebase Function from Flask app
# The @https_fn.on_request() decorator passes the request to the Flask app
@https_fn.on_request(region="us-central1")
def api(req: https_fn.Request) -> https_fn.Response:
    """Handle HTTP requests using Flask WSGI application."""
    # Use Firebase Functions with Flask as WSGI app
    return flask_app

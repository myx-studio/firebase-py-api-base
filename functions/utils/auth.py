"""Authentication utility functions."""
import re
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import firebase_admin.auth


def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password strength.

    Args:
        password: The password to validate

    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "errors": []
    }

    # Check minimum length
    if len(password) < 8:
        result["valid"] = False
        result["errors"].append("Password must be at least 8 characters long")

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one uppercase letter")

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one lowercase letter")

    # Check for digit
    if not re.search(r'\d', password):
        result["valid"] = False
        result["errors"].append("Password must contain at least one digit")

    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["valid"] = False
        result["errors"].append(
            "Password must contain at least one special character"
        )

    return result


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password as string
    """
    import bcrypt

    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Return as a string
    return hashed.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        password: Plain text password to check
        hashed_password: Hashed password to check against

    Returns:
        True if the password matches, False otherwise
    """
    import bcrypt

    # Check if the password matches the hash
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def verify_firebase_password(email: str, password: str) -> Dict[str, Any]:
    """
    Verify user credentials against Firebase Authentication.

    This function tries multiple methods to verify the password:
    1. If Firebase Web API Key is available, use Firebase Auth REST API
    2. Otherwise, use local bcrypt verification with Firebase Admin SDK

    Args:
        email: User's email address
        password: User's password to verify

    Returns:
        Dictionary with user information if successful

    Raises:
        ValueError: If authentication fails
    """
    import json
    import requests
    from logging import getLogger

    logger = getLogger("auth")
    
    # Convert email to lowercase for consistency with Firebase
    email = email.lower()
    logger.info(f"Normalized email to lowercase for authentication: {email}")

    try:
        # Get the user from Firebase Authentication first
        user = firebase_admin.auth.get_user_by_email(email)

        # Try Firebase Auth REST API if Web API Key is available
        from config import CONFIG

        # Method 1: Firebase Auth REST API (preferred for security)
        api_key = None

        # Get API key from centralized config
        try:
            firebase_config = CONFIG.get("firebase", {})
            if isinstance(firebase_config, dict):
                api_key = firebase_config.get("web_api_key", "")
        except (AttributeError, TypeError):
            api_key = ""

        if api_key:
            try:
                # Firebase Auth REST API endpoint for email/password sign-in
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

                # Prepare the request payload
                payload = {
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }

                # Make the API request
                response = requests.post(url, data=json.dumps(payload), timeout=30)
                data = response.json()

                # Check for errors in the response
                if response.status_code == 200:
                    return {
                        "uid": user.uid,
                        "email": user.email,
                        "display_name": user.display_name,
                        "email_verified": user.email_verified,
                        "id_token": data.get("idToken")
                    }
                else:
                    error_message = data.get("error", {}).get("message", "Unknown error")
                    if error_message == "INVALID_PASSWORD":
                        raise ValueError("Invalid password")
                    elif error_message == "EMAIL_NOT_FOUND":
                        raise ValueError("User not found")
                    else:
                        # Log the error but continue to next auth method
                        logger.warning(f"Firebase Auth API error: {error_message}")
            except Exception as e:
                # Log the error but continue to next auth method
                logger.warning(f"Error using Firebase Auth API: {str(e)}")

        # Since Firebase doesn't allow direct password verification via the Admin SDK,
        # we need to use the REST API. If we've reached this point, the API key method failed.
        
        # The safest approach is to consider this a failure and force using the API key method
        logger.error("Firebase password verification through REST API failed. Web API key is missing or invalid.")
        raise ValueError("Password verification failed. Please ensure the Firebase web API key is properly configured.")

        # Generate a custom token for the authenticated user
        custom_token = firebase_admin.auth.create_custom_token(user.uid)

        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "email_verified": user.email_verified,
            "custom_token": custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token
        }

    except firebase_admin.auth.UserNotFoundError as exc:
        raise ValueError("User not found") from exc
    except Exception as e:
        raise ValueError(f"Authentication failed: {str(e)}")

def create_firebase_user(
    email: str, password: str, display_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Firebase Authentication user.

    Args:
        email: User's email address
        password: User's password
        display_name: User's display name (optional)

    Returns:
        Dictionary with user information

    Raises:
        ValueError: If there's an issue creating the user
    """
    try:
        # Validate password strength
        password_validation = validate_password(password)
        if not password_validation["valid"]:
            raise ValueError("\n".join(password_validation["errors"]))
            
        # Normalize email to lowercase for consistency
        email = email.lower()
        
        # Create the user in Firebase Auth
        user_properties = {
            "email": email,  # Using lowercase email
            "password": password,
            "email_verified": False,
        }

        if display_name:
            user_properties["display_name"] = display_name

        user = firebase_admin.auth.create_user(**user_properties)

        # Generate a custom token for the new user
        custom_token = firebase_admin.auth.create_custom_token(user.uid)

        # Ensure the token is a string, not bytes
        token_str = custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token

        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "email_verified": user.email_verified,
            "custom_token": token_str  # Include the properly formatted token
        }
    except firebase_admin.auth.EmailAlreadyExistsError as exc:
        raise ValueError(f"User with email {email} already exists") from exc
    except Exception as e:
        raise ValueError(f"{str(e)}") from e


def generate_custom_token(uid: str, claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a Firebase custom authentication token.

    Args:
        uid: User ID to create token for
        claims: Optional custom claims to include in the token

    Returns:
        Custom token string

    Raises:
        ValueError: If there's an issue generating the token
    """
    try:
        token = firebase_admin.auth.create_custom_token(uid, claims)
        # Ensure we return a string, not bytes
        return token.decode('utf-8') if isinstance(token, bytes) else token
    except Exception as e:
        raise ValueError(f"Error generating custom token: {str(e)}") from e

def generate_password_reset_token() -> str:
    """
    Generate a secure token for password reset.
    
    Returns:
        str: A secure random token
    """
    # Generate a 32-byte random token
    token = secrets.token_urlsafe(32)
    
    # Prepend with a timestamp and a unique identifier
    timestamp = int(datetime.now().timestamp())
    unique_id = str(uuid.uuid4())[:8]
    
    # Combine timestamp, unique ID, and token for added security
    # Format: timestamp_uniqueid_token
    reset_token = f"{timestamp}_{unique_id}_{token}"
    
    return reset_token

def change_user_password(firebase_uid: str, new_password: str) -> bool:
    """
    Change a user's password in Firebase Authentication.
    
    Args:
        firebase_uid: The Firebase UID of the user
        new_password: The new password to set
        
    Returns:
        bool: True if password was changed successfully, False otherwise
        
    Raises:
        ValueError: If there's an issue changing the password
    """
    try:
        # Validate new password strength
        password_validation = validate_password(new_password)
        if not password_validation["valid"]:
            raise ValueError("\n".join(password_validation["errors"]))
            
        # Change password in Firebase Authentication
        firebase_admin.auth.update_user(
            firebase_uid,
            password=new_password
        )
        
        return True
    except firebase_admin.auth.UserNotFoundError as exc:
        raise ValueError("User not found") from exc
    except Exception as e:
        raise ValueError(f"Error changing password: {str(e)}") from e


"""Authentication-related API endpoints."""
from typing import Any
import firebase_admin.auth

from services import UserService
from utils.auth import generate_custom_token, verify_firebase_password
from utils.helpers import create_response
from utils.logging import setup_logger, log_exception

# Initialize services and loggers
user_service = UserService()
logger = setup_logger("api_auth")

def login_with_email(req: Any) -> Any:
    """
    Endpoint to login with email and password.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response
    """
    try:
        # Check if method is POST
        if req.method != "POST":
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only POST method is allowed for this endpoint"
            )

        # Parse the request body
        try:
            auth_data = req.get_json()
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        # Validate required fields
        if "email" not in auth_data or "password" not in auth_data:
            return create_response(
                error="Missing required fields",
                status=400,
                message="Email and password are required"
            )

        email = auth_data["email"]
        password = auth_data["password"]

        # First check if the user exists in our database
        user = user_service.get_user_by_email(email)
        if not user:
            return create_response(
                error="Authentication failed",
                status=401,
                message="Invalid email or password"
            )

        # Verify password using Firebase Authentication
        try:
            # This will raise a ValueError if authentication fails
            # It returns user info and a token if successful
            auth_result = verify_firebase_password(email, password)

            # If we get here, authentication was successful
            if not user.firebase_uid:
                raise ValueError("User has no Firebase UID")

            # Get either the ID token or custom token from the auth result
            token = auth_result.get("id_token") or auth_result.get("custom_token")

            # If no token was returned, generate a custom token
            if not token:
                token = generate_custom_token(user.firebase_uid)

            return create_response(
                data={
                    "token": token,
                    "user": user.to_dict()
                },
                message="Authentication successful"
            )
        except ValueError as auth_error:
            # Log the specific error but return a generic message to the client
            logger.warning("Authentication failed for user %s: %s", email, str(auth_error))
            return create_response(
                error="Authentication failed",
                status=401,
                message="Invalid email or password"
            )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error during login", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred during login"
        )

def register(req: Any) -> Any:
    """
    Endpoint to register a new user.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response
    """
    try:
        # Check if method is POST
        if req.method != "POST":
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only POST method is allowed for this endpoint"
            )

        # Parse the request body
        try:
            user_data = req.get_json()
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        # Create both a Firebase Auth user and a user in our database
        user = user_service.create_user(user_data, create_auth_user=True)

        # Generate a custom token for immediate login
        if not user.firebase_uid:
            raise ValueError("User was created without a Firebase UID")

        custom_token = generate_custom_token(user.firebase_uid)

        return create_response(
            data={
                "token": custom_token,
                "user": user.to_dict()
            },
            message="User registered successfully",
            status=201
        )
    except ValueError as e:
        # Handle validation errors
        return create_response(
            error=str(e),
            status=400,
            message="Invalid user data"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error during registration", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred during registration"
        )

def get_user_profile(req: Any) -> Any:
    """
    Endpoint to get the current user's profile.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response
    """
    try:
        # Get the authenticated user from the request context
        auth_user = getattr(req, "user", None)

        if not auth_user:
            return create_response(
                error="User authentication failed",
                status=401,
                message="Authentication required"
            )

        # Get the user from the database using the Firebase UID
        user = user_service.get_user_by_firebase_uid(auth_user["uid"])

        if not user:
            return create_response(
                error="User not found",
                status=404,
                message="User profile not found"
            )

        if user.id is None:
            return create_response(
                error="User not found",
                status=404,
                message="User profile not found"
            )
        # Ensure user data is serializable
        user_dict = user.to_dict()

        return create_response(
            data={"user": user_dict},
            message="User profile retrieved successfully"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Log the exception details for debugging
        log_exception(logger, "Error retrieving user profile", e)

        # Ensure we return a JSON response even for unexpected errors
        return create_response(
            error="Internal server error",
            status=500,
            message="An error occurred while retrieving the user profile"
        )

def login_with_custom_token(req: Any) -> Any:
    """
    Endpoint to login with a custom token.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response
    """
    try:
        # Check if method is POST
        if req.method != "POST":
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only POST method is allowed for this endpoint"
            )

        # Parse the request body
        try:
            token_data = req.get_json()
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        # Validate required fields
        if "token" not in token_data:
            return create_response(
                error="Missing required fields",
                status=400,
                message="Token is required"
            )

        # Verify the token and get the user
        # Note: Custom tokens are meant to be exchanged for ID tokens on the client side
        # This endpoint is mostly for demonstration purposes
        try:
            # Get the UID from the token
            decoded_token = firebase_admin.auth.verify_id_token(token_data["token"])
            uid = decoded_token["uid"]

            # Get the user from the database
            user = user_service.get_user_by_firebase_uid(uid)

            if not user:
                return create_response(
                    error="User not found",
                    status=404,
                    message="User not found for the provided token"
                )

            return create_response(
                data={"user": user.to_dict()},
                message="Authentication successful"
            )
        except firebase_admin.auth.InvalidIdTokenError:
            return create_response(
                error="Invalid token",
                status=401,
                message="The provided token is invalid or expired"
            )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error during token login", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred during login"
        )

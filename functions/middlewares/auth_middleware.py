"""Authentication middleware for Firebase Functions."""
from typing import Dict, Any, Callable
from functools import wraps
import json
import firebase_admin.auth
from flask import Response, request


def verify_auth(req: Any = None) -> Dict[str, Any]:
    """
    Verify Firebase authentication token from request.

    Args:
        req: The HTTP request object (optional, will use Flask request object if None)

    Returns:
        Dict containing auth status and user info if authenticated
    """
    # Use the global request object if no request is provided
    req = req or request

    result = {
        "authenticated": False,
        "user": None,
        "error": None
    }

    # Check if Authorization header exists
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        result["error"] = "No valid authorization header found"
        return result

    # Extract the token
    token = auth_header.split("Bearer ")[1]
    if not token:
        result["error"] = "No token provided"
        return result

    try:
        # Verify the token
        decoded_token = firebase_admin.auth.verify_id_token(token)
        result["authenticated"] = True
        result["user"] = {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
            "email_verified": decoded_token.get("email_verified", False)
        }
        return result
    except firebase_admin.auth.ExpiredIdTokenError as e:
        result["error"] = f"Token expired: {str(e)}"
        return result
    except firebase_admin.auth.RevokedIdTokenError as e:
        result["error"] = f"Token revoked: {str(e)}"
        return result
    except firebase_admin.auth.InvalidIdTokenError as e:
        result["error"] = f"Invalid ID token: {str(e)}"
        return result
    except Exception as e:  # pylint: disable=broad-exception-caught
        result["error"] = f"Authentication error: {str(e)}"
        return result


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a Firebase Function.

    Args:
        func: The function to decorate

    Returns:
        Decorated function that checks auth before execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Verify authentication
        auth_result = verify_auth()

        if not auth_result["authenticated"]:
            # Create a properly formatted JSON response
            response_body = {
                "success": False,
                "error": "Unauthorized",
                "message": auth_result["error"],
                "details": auth_result["error"]
            }

            # Convert to JSON and create response
            response = Response(
                json.dumps(response_body),
                status=401
            )

            # Set content type header
            response.headers["Content-Type"] = "application/json"

            return response

        # Add the verified user to the request
        setattr(request, "user", auth_result["user"])

        # Call the original function
        return func(*args, **kwargs)

    return wrapper


# Make functions available for import
__all__ = ['require_auth', 'verify_auth']

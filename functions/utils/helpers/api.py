"""Helper functions for API responses and request handling."""
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from config import CONFIG
from utils.logging import setup_logger

# Import Response from the correct location to avoid private import issues
from flask import Response


logger = setup_logger("api_helpers")


def create_cors_headers() -> Dict[str, str]:
    """Create CORS headers for API responses with mobile app support."""
    # Get CORS settings from config or use defaults
    cors_origins = CONFIG.get("cors_origins", ["*"])
    cors_methods = CONFIG.get("cors_allow_methods",
                             ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    cors_headers = CONFIG.get("cors_allow_headers",
                             ["Content-Type", "Authorization", "Content-Length",
                              "X-Requested-With", "Accept"])

    # Convert lists to comma-separated strings if needed
    if isinstance(cors_origins, list):
        if len(cors_origins) == 1 and cors_origins[0] == "*":
            origins_value = "*"
        else:
            origins_value = ", ".join(cors_origins)
    else:
        origins_value = cors_origins

    if isinstance(cors_methods, list):
        methods_value = ", ".join(cors_methods)
    else:
        methods_value = cors_methods

    if isinstance(cors_headers, list):
        headers_value = ", ".join(cors_headers)
    else:
        headers_value = cors_headers

    return {
        "Access-Control-Allow-Origin": origins_value,
        "Access-Control-Allow-Methods": methods_value,
        "Access-Control-Allow-Headers": headers_value,
        "Access-Control-Allow-Credentials": "true",  # Support credentials
        "Access-Control-Max-Age": "3600"
    }


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects and enums."""
    def default(self, o: Any) -> Any:
        """Encode datetime and enum objects."""
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


def create_response(
    data: Any = None,
    message: Optional[str] = None,
    status: int = 200,
    error: Optional[str] = None
) -> Any:
    """Create a standardized API response with datetime handling."""
    response_body: Dict[str, Any] = {}

    if message:
        response_body["message"] = message

    if data is not None:
        response_body["data"] = data

    if error:
        response_body["error"] = error

    # Add success flag based on status code
    response_body["success"] = 200 <= status < 300

    # Create headers with Content-Type explicitly set
    headers = create_cors_headers()
    headers["Content-Type"] = "application/json"

    try:
        # Serialize the response body to JSON string with custom encoder
        json_body = json.dumps(response_body, cls=DateTimeEncoder)
    except (TypeError, ValueError) as e:
        # Fallback if serialization fails
        error_response = {
            "success": False,
            "error": "JSON serialization error",
            "message": str(e)
        }
        json_body = json.dumps(error_response)
        status = 500


    # Create response using the properly imported Response class
    return Response(
        response=json_body,
        status=status,
        headers=headers
    )


def extract_id_from_request(
    req: Any,
    arg_name: Optional[str] = None,
    default_name: Optional[str] = None
) -> Optional[str]:
    """
    Extract ID from request - checking both query args and path.

    Args:
        req: The HTTP request object
        arg_name: Name of the query parameter to check
        default_name: Default name for logging (e.g., 'family_id')

    Returns:
        The extracted ID or None if not found
    """
    # Name for logging
    name = default_name or arg_name or "ID"

    # First try to get from query parameters if arg_name is provided
    extracted_id = None
    if arg_name and hasattr(req, 'args') and req.args:
        extracted_id = req.args.get(arg_name)
        if extracted_id:
            logger.info("Extracted %s from query args: %s", name, extracted_id)
            return extracted_id

    # If not found in query parameters, try the path
    path = getattr(req, 'path', '')
    if path:
        path_parts = path.split('/')
        # Filter out empty strings
        clean_parts = [part for part in path_parts if part]
        # Get the last non-empty segment
        if clean_parts:
            extracted_id = clean_parts[-1]
            logger.info("Extracted %s from path: %s", name, extracted_id)

    return extracted_id


def get_user_id_from_request(req: Any) -> str:
    """
    Extract authenticated user ID from request.
    
    Args:
        req: The HTTP request object with user attribute set by auth middleware
        
    Returns:
        The authenticated user's ID
        
    Raises:
        AttributeError: If user is not authenticated
    """
    if not hasattr(req, 'user') or not req.user:
        raise AttributeError("User not authenticated")
    
    return req.user.get('uid')
"""User-related API endpoints."""
from typing import Any

from services import UserService, StorageService
from utils.helpers import create_response
from utils.logging import setup_logger, log_exception

# Initialize services and loggers
user_service = UserService()
storage_service = StorageService()
logger = setup_logger("api_users")


def get_users(_: Any) -> Any:
    """
    Endpoint to retrieve all users.

    Args:
        _: The Flask request object (unused)

    Returns:
        A standardized API response with all users
    """
    try:
        users = user_service.get_all_users()

        # Convert users to dictionaries for the response
        users_data = [user.to_dict() for user in users]

        return create_response(
            data={"users": users_data},
            message="Users retrieved successfully"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error retrieving users", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while retrieving users"
        )


def get_user(req: Any) -> Any:
    """
    Endpoint to retrieve a user by ID.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response with user data
    """
    try:
        # Extract the firebase_uid from the path
        # In emulator, path format is simply /{firebase_uid}
        path_parts = req.path.split('/')
        # Log the full path for debugging
        logger.info("Get user path: %s", req.path)

        # Filter out empty parts (from leading slash)
        path_parts = [part for part in path_parts if part]
        logger.info("Path parts after filtering: %s", path_parts)

        if not path_parts:  # No path segments
            return create_response(
                error="Invalid path",
                status=400,
                message="Firebase UID not provided in the path"
            )

        firebase_uid = path_parts[0]  # First non-empty part is firebase_uid
        logger.info("Extracted firebase_uid: %s", firebase_uid)

        user = user_service.get_user_by_firebase_uid(firebase_uid)

        if not user:
            return create_response(
                error="User not found",
                status=404,
                message=f"No user found with Firebase UID: {firebase_uid}"
            )

        return create_response(
            data={"user": user.to_dict()},
            message="User retrieved successfully"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error retrieving user", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while retrieving the user"
        )


def create_user(req: Any) -> Any:
    """
    Endpoint to create a new user.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response with created user data
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

        # Create the user
        user = user_service.create_user(user_data)

        return create_response(
            data={"user": user.to_dict()},
            message="User created successfully",
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
        log_exception(logger, "Error creating user", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while creating the user"
        )


def update_user(req: Any) -> Any:
    """
    Endpoint to update an existing user.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response with updated user data
    """
    try:
        # Check if method is PUT or PATCH
        if req.method not in ["PUT", "PATCH"]:
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only PUT and PATCH methods are allowed for this endpoint"
            )

        # Extract the firebase_uid from the path
        # In emulator, path format is simply /{firebase_uid}
        path_parts = req.path.split('/')
        # Filter out empty parts (from leading slash)
        path_parts = [part for part in path_parts if part]

        if not path_parts:  # No path segments
            return create_response(
                error="Invalid path",
                status=400,
                message="Firebase UID not provided in the path"
            )

        firebase_uid = path_parts[2]  # First non-empty part is firebase_uid

        # Parse the request body
        try:
            user_data = req.get_json()
            logger.info("User data json: %s", user_data)
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        # Update the user using firebase_uid
        user = user_service.update_user(firebase_uid, user_data)

        if not user:
            return create_response(
                error="User not found",
                status=404,
                message=f"No user found with Firebase UID: {firebase_uid}"
            )

        return create_response(
            data={"user": user.to_dict()},
            message="User updated successfully"
        )
    except ValueError as e:
        # Handle validation errors
        return create_response(
            error=str(e),
            status=400,
            message="Invalid user data"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error updating user", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while updating the user"
        )



def delete_user(req: Any) -> Any:
    """
    Endpoint to delete a user.

    This endpoint supports comprehensive deletion of all user data.

    Query parameters:
    - clean_data=true|false: Whether to clean up all related data (default: true)

    Args:
        req: The Flask request object

    Returns:
        A standardized API response
    """
    try:
        # Check if method is DELETE
        if req.method != "DELETE":
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only DELETE method is allowed for this endpoint"
            )

        # Get authenticated user from req.user (set by the auth middleware)
        firebase_uid = req.user.get("uid")
        if not firebase_uid:
            return create_response(
                error="Unauthorized",
                status=401,
                message="Authentication required"
            )

        logger.info("Deleting user %s", firebase_uid)

        # Delete the user and get cleanup details
        result, cleanup_details = user_service.delete_user(firebase_uid)

        if not result:
            return create_response(
                error="User not found",
                status=404,
                message=f"No user found with Firebase UID: {firebase_uid}"
            )

        # Prepare response with cleanup details if available
        response_data = {}
        if cleanup_details:
            response_data["cleanup_details"] = cleanup_details

        return create_response(
            data=response_data if response_data else None,
            message="User deleted successfully"
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error deleting user", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while deleting the user"
        )


def update_user_photo(req: Any) -> Any:
    """
    Endpoint to update a user's profile photo.

    Accepts both base64 encoded images and URLs.
    For base64 images, they will be uploaded to Firebase Storage.
    For URLs, they will be stored directly in the user document.

    Args:
        req: The Flask request object

    Returns:
        A standardized API response with updated user data
    """
    try:
        # Check if method is POST
        if req.method != "POST":
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only POST method is allowed for this endpoint"
            )

        # Get authenticated user from req.user (set by the auth middleware)
        firebase_uid = req.user.get("uid")
        if not firebase_uid:
            return create_response(
                error="Unauthorized",
                status=401,
                message="Authentication required"
            )

        # Check if the user exists
        user = user_service.get_user_by_firebase_uid(firebase_uid)
        if not user:
            return create_response(
                error="User not found",
                status=404,
                message=f"No user found with Firebase UID: {firebase_uid}"
            )

        # Parse the request body
        try:
            data = req.get_json()
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        # Extract photo data from request
        if "photo" not in data:
            return create_response(
                error="Missing photo data",
                status=400,
                message="Request must include 'photo' field with URL or base64 image"
            )

        photo_data = data["photo"]

        # Validate the image
        is_valid, error_message = storage_service.validate_image(photo_data)
        if not is_valid:
            return create_response(
                error="Invalid image",
                status=400,
                message=error_message
            )

        # Process the photo (upload if base64, use URL directly otherwise)
        result = storage_service.process_user_photo(firebase_uid, photo_data)

        if not result.get("success"):
            return create_response(
                error=result.get("error", "Unknown error"),
                status=500,
                message="Failed to process photo"
            )

        return create_response(
            data={
                "user": result.get("user"),
                "profile_picture": result.get("photo_url")  # Rename to profile_picture
            },
            message="Profile photo updated successfully"
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error updating user photo", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while updating the profile photo"
        )


def update_onboarding(req: Any) -> Any:
    """
    Endpoint to update a user's onboarding status.
    
    Updates the onboarding_completed field for the authenticated user.
    """
    try:
        # Get firebase uid from middleware
        firebase_uid = getattr(req, 'firebase_uid', None)
        if not firebase_uid:
            return create_response(
                error="Authentication required",
                status=401,
                message="User not authenticated"
            )

        # Get request data
        data = req.get_json() if req.is_json else {}
        
        if "onboarding_completed" not in data:
            return create_response(
                error="Missing onboarding_completed field",
                status=400,
                message="Request must include 'onboarding_completed' boolean field"
            )

        onboarding_completed = data.get("onboarding_completed")
        if not isinstance(onboarding_completed, bool):
            return create_response(
                error="Invalid onboarding_completed value",
                status=400,
                message="onboarding_completed must be a boolean value"
            )

        # Update user onboarding status
        user_service = UserService()
        result = user_service.update_onboarding_status(firebase_uid, onboarding_completed)

        if not result.get("success", False):
            return create_response(
                error=result.get("error", "Failed to update onboarding status"),
                status=500,
                message="An error occurred while updating onboarding status"
            )

        return create_response(
            data=result.get("user"),
            message="Onboarding status updated successfully"
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error updating onboarding status", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while updating onboarding status"
        )

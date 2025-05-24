"""File upload API endpoints."""
from typing import Any

from services import StorageService, UserService
from utils.helpers import create_response, get_user_id_from_request
from utils.logging import setup_logger, log_exception

# Initialize services
storage_service = StorageService()
user_service = UserService()
logger = setup_logger("api_files")


def upload_profile_picture(req: Any) -> Any:
    """
    Endpoint to upload a user's profile picture.
    This demonstrates proper separation of concerns:
    - StorageService handles file upload
    - UserService handles profile updates
    
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

        # Get authenticated user
        user_id = get_user_id_from_request(req)
        
        # Parse request body
        try:
            data = req.get_json()
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        image_data = data.get('image_data')
        if not image_data:
            return create_response(
                error="Missing image data",
                status=400,
                message="image_data is required"
            )

        # Step 1: Validate image using StorageService
        is_valid, error_message = storage_service.validate_image(image_data)
        if not is_valid:
            return create_response(
                error="Invalid image",
                status=400,
                message=error_message
            )

        # Step 2: Upload file using StorageService
        upload_result = storage_service.upload_file(
            file_data=image_data,
            file_name="profile_picture.jpg",
            folder_path="user_photos"
        )
        
        if not upload_result.get('success'):
            return create_response(
                error="Upload failed",
                status=500,
                message=upload_result.get('error', 'Unknown upload error')
            )

        # Step 3: Update user profile using UserService
        updated_user = user_service.update_user(user_id, {
            'profile_picture': upload_result['file_url']
        })
        
        if not updated_user:
            return create_response(
                error="Profile update failed",
                status=500,
                message="Failed to update user profile with new photo"
            )

        return create_response(
            data={
                'user': updated_user.to_dict(),
                'file_url': upload_result['file_url']
            },
            message="Profile picture uploaded successfully"
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error uploading profile picture", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while uploading the profile picture"
        )


def upload_file(req: Any) -> Any:
    """
    Generic file upload endpoint.
    
    Args:
        req: The Flask request object
        
    Returns:
        A standardized API response with file URL
    """
    try:
        # Check if method is POST
        if req.method != "POST":
            return create_response(
                error="Method not allowed",
                status=405,
                message="Only POST method is allowed for this endpoint"
            )

        # Get authenticated user (for folder organization)
        user_id = get_user_id_from_request(req)
        
        # Parse request body
        try:
            data = req.get_json()
        except ValueError:
            return create_response(
                error="Invalid JSON",
                status=400,
                message="Request body must be valid JSON"
            )

        file_data = data.get('file_data')
        file_name = data.get('file_name')
        file_type = data.get('file_type', 'document')  # image, document, video
        
        if not file_data or not file_name:
            return create_response(
                error="Missing required fields",
                status=400,
                message="file_data and file_name are required"
            )

        # Validate file based on type
        file_extension = file_name.split('.')[-1] if '.' in file_name else ''
        
        if file_type == 'image':
            is_valid, error_message = storage_service.validate_image(file_data)
        elif file_type == 'document':
            is_valid, error_message = storage_service.validate_document(file_data, file_extension)
        elif file_type == 'video':
            is_valid, error_message = storage_service.validate_video(file_data, file_extension)
        else:
            return create_response(
                error="Invalid file type",
                status=400,
                message="file_type must be 'image', 'document', or 'video'"
            )
            
        if not is_valid:
            return create_response(
                error=f"Invalid {file_type}",
                status=400,
                message=error_message
            )

        # Upload file
        folder_path = f"user_files/{user_id}/{file_type}s"
        upload_result = storage_service.upload_file(
            file_data=file_data,
            file_name=file_name,
            folder_path=folder_path
        )
        
        if not upload_result.get('success'):
            return create_response(
                error="Upload failed",
                status=500,
                message=upload_result.get('error', 'Unknown upload error')
            )

        # Get file info
        file_info = storage_service.get_file_info(file_data)

        return create_response(
            data={
                'file_url': upload_result['file_url'],
                'file_name': file_name,
                'file_type': file_type,
                'file_info': file_info
            },
            message=f"{file_type.title()} uploaded successfully"
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log_exception(logger, "Error uploading file", e)
        return create_response(
            error=str(e),
            status=500,
            message="An error occurred while uploading the file"
        )
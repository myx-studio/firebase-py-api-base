"""Service for handling file storage operations."""
import base64
import io
import uuid
from typing import Dict, Any, Tuple, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

try:
    from firebase_admin import storage
    from google.cloud import storage as gcs
    FIREBASE_STORAGE_AVAILABLE = True
except ImportError:
    FIREBASE_STORAGE_AVAILABLE = False
    storage = None  # type: ignore
    gcs = None

from config import config
from utils.logging import setup_logger

logger = setup_logger("storage_service")


class StorageService:
    """Service for handling file storage operations including images, videos, and documents."""

    # Class-level constraints to reduce instance attributes
    CONSTRAINTS = {
        'image': {
            'max_size': 5 * 1024 * 1024,  # 5MB
            'formats': {'JPEG', 'PNG', 'GIF', 'WEBP'},
            'max_dimension': 2048,
            'min_dimension': 50
        },
        'document': {
            'max_size': 10 * 1024 * 1024,  # 10MB
            'formats': {'PDF', 'DOC', 'DOCX', 'TXT', 'RTF'}
        },
        'video': {
            'max_size': 50 * 1024 * 1024,  # 50MB
            'formats': {'MP4', 'MOV', 'AVI', 'WEBM'}
        }
    }

    def __init__(self):
        """Initialize storage service."""

    def validate_image(self, image_data: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an image provided as base64 or URL.

        Args:
            image_data: Base64 encoded image or URL

        Returns:
            tuple: (is_valid, error_message)
        """
        constraints = self.CONSTRAINTS['image']

        # Check if it's a URL
        if image_data.startswith(('http://', 'https://')):
            if len(image_data) > 2048:
                return False, "URL is too long"
            return True, None

        # Validate base64 image
        return self._validate_base64_image(image_data, constraints)

    def _validate_base64_image(self, image_data: str,
                              constraints: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Helper method to validate base64 image data."""
        try:
            # Remove data URI prefix if present
            if image_data.startswith('data:'):
                encoded = image_data.split(',', 1)[1]
            else:
                encoded = image_data
            decoded = base64.b64decode(encoded)

            # Check file size
            if len(decoded) > constraints['max_size']:
                size_mb = constraints['max_size'] / 1024 / 1024
                return False, f"Image size exceeds {size_mb}MB limit"

            # If PIL is not available, only validate size
            if not PIL_AVAILABLE:
                logger.warning(
                    "PIL not available, skipping image format and dimension validation"
                )
                return True, None

            # Validate format and dimensions using PIL
            return self._validate_image_properties(decoded, constraints)

        except (ValueError, AttributeError, TypeError, KeyError) as e:
            logger.error("Error validating image: %s", str(e))
            return False, "Invalid image data"

    def _validate_image_properties(
        self, decoded: bytes, constraints: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Helper method to validate image properties using PIL."""
        try:
            if Image is None:
                return False, "PIL not available for image validation"

            image = Image.open(io.BytesIO(decoded))

            # Check format
            if image.format not in constraints['formats']:
                formats = ', '.join(constraints['formats'])
                return False, f"Invalid image format. Allowed formats: {formats}"

            # Check dimensions
            width, height = image.size
            max_dim = constraints['max_dimension']
            min_dim = constraints['min_dimension']

            if width > max_dim or height > max_dim:
                return False, f"Image dimensions exceed {max_dim}x{max_dim} pixels"

            if width < min_dim or height < min_dim:
                return (
                    False,
                    f"Image dimensions must be at least {min_dim}x{min_dim} pixels"
                )

            return True, None

        except (ValueError, AttributeError, TypeError, KeyError) as e:
            logger.error("Error processing image with PIL: %s", str(e))
            return False, "Invalid image format or corrupted data"

    def validate_document(
        self, file_data: str, file_extension: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a document file.

        Args:
            file_data: Base64 encoded file data
            file_extension: File extension (e.g., 'pdf', 'doc')

        Returns:
            tuple: (is_valid, error_message)
        """
        constraints = self.CONSTRAINTS['document']
        return self._validate_base64_file(
            file_data, file_extension, constraints, 'document'
        )

    def validate_video(
        self, file_data: str, file_extension: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a video file.

        Args:
            file_data: Base64 encoded file data
            file_extension: File extension (e.g., 'mp4', 'mov')

        Returns:
            tuple: (is_valid, error_message)
        """
        constraints = self.CONSTRAINTS['video']
        return self._validate_base64_file(
            file_data, file_extension, constraints, 'video'
        )

    def _validate_base64_file(
        self,
        file_data: str,
        file_extension: str,
        constraints: Dict[str, Any],
        file_type: str
    ) -> Tuple[bool, Optional[str]]:
        """Helper method to validate base64 file data."""
        try:
            # Normalize extension
            ext = file_extension.upper().lstrip('.')

            if ext not in constraints['formats']:
                formats = ', '.join(constraints['formats'])
                return (
                    False,
                    f"Invalid {file_type} format. Allowed formats: {formats}"
                )

            # Remove data URI prefix if present
            if file_data.startswith('data:'):
                encoded = file_data.split(',', 1)[1]
            else:
                encoded = file_data
            decoded = base64.b64decode(encoded)

            if len(decoded) > constraints['max_size']:
                size_mb = constraints['max_size'] / 1024 / 1024
                return (
                    False,
                    f"{file_type.capitalize()} size exceeds {size_mb}MB limit"
                )

            return True, None

        except (ValueError, AttributeError, TypeError, KeyError) as e:
            logger.error("Error validating %s: %s", file_type, str(e))
            return False, f"Invalid {file_type} data"

    def upload_file(self, file_data: str, file_name: str,
                   folder_path: str = "uploads") -> Dict[str, Any]:
        """
        Upload a file to storage and return the URL.
        This method only handles the file upload, not any profile updates.

        Args:
            file_data: Base64 encoded file data or URL
            file_name: Name of the file
            folder_path: Storage folder path

        Returns:
            dict: Result with success status and file URL
        """
        try:
            # Check if it's already a URL
            if file_data.startswith(('http://', 'https://')):
                return {
                    'success': True,
                    'file_url': file_data,
                    'message': 'URL validated successfully'
                }

            # For base64 files, upload to storage
            file_url = self._upload_to_storage(file_data, file_name, folder_path)

            return {
                'success': True,
                'file_url': file_url,
                'message': 'File uploaded successfully'
            }

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error uploading file: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }

    def get_file_info(self, file_data: str) -> Dict[str, Any]:
        """
        Get information about a file from base64 data.

        Args:
            file_data: Base64 encoded file data

        Returns:
            dict: File information including size, type, etc.
        """
        try:
            if file_data.startswith('data:'):
                header, encoded = file_data.split(',', 1)
                # Extract MIME type from data URI
                mime_type = header.split(';')[0].split(':')[1]
            else:
                encoded = file_data
                mime_type = 'unknown'

            # Decode and get size
            decoded = base64.b64decode(encoded)
            size_bytes = len(decoded)
            size_mb = size_bytes / 1024 / 1024

            return {
                'success': True,
                'size_bytes': size_bytes,
                'size_mb': round(size_mb, 2),
                'mime_type': mime_type
            }

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error getting file info: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }

    def _upload_to_storage(self, base64_data: str, file_name: str,
                          folder_path: str) -> str:
        """
        Upload base64 file to Firebase Storage.

        Args:
            base64_data: Base64 encoded file data
            file_name: Name of the file
            folder_path: Storage folder path

        Returns:
            str: Public URL of the uploaded file

        Raises:
            Exception: If Firebase Storage is not available or upload fails
        """
        if not FIREBASE_STORAGE_AVAILABLE or storage is None:
            raise Exception("Firebase Storage is not available. Please install firebase-admin.")

        try:
            # Remove data URI prefix if present
            if base64_data.startswith('data:'):
                encoded = base64_data.split(',', 1)[1]
            else:
                encoded = base64_data

            # Decode base64 data
            file_data = base64.b64decode(encoded)

            # Get Firebase Storage bucket
            firebase_config = config.get("firebase", {})
            storage_bucket = firebase_config.get("storage_bucket") if isinstance(firebase_config, dict) else None
            if storage_bucket:
                bucket = storage.bucket(storage_bucket)
            else:
                bucket = storage.bucket()  # Uses default project bucket
            
            # Create unique file path
            file_id = str(uuid.uuid4())
            blob_path = f"{folder_path}/{file_id}_{file_name}"
            
            # Create blob and upload
            blob = bucket.blob(blob_path)
            
            # Set content type based on file extension
            content_type = self._get_content_type(file_name)
            blob.content_type = content_type
            
            # Upload the file data
            blob.upload_from_string(file_data, content_type=content_type)
            
            # Make the blob public
            blob.make_public()
            
            # Return the public URL
            public_url = blob.public_url
            
            logger.info("File uploaded successfully to Firebase Storage: %s", blob_path)
            return public_url

        except Exception as e:
            logger.error("Error uploading file to Firebase Storage: %s", str(e))
            raise Exception(f"Failed to upload file to storage: {str(e)}") from e

    def _get_content_type(self, file_name: str) -> str:
        """
        Get content type based on file extension.

        Args:
            file_name: Name of the file

        Returns:
            str: MIME content type
        """
        extension = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'rtf': 'application/rtf',
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'webm': 'video/webm'
        }
        
        return content_types.get(extension, 'application/octet-stream')


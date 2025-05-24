"""Business logic for user operations."""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone

from models.user import User
from repositories import (
    get_user_repository,
    get_notification_repository,
    get_password_reset_repository
)
from utils.validators import (
    validate_email,
    validate_phone_number,
    validate_required_fields,
    sanitize_input
)
from utils.logging import setup_logger, log_exception
from utils.auth import create_firebase_user

logger = setup_logger("user_service")


class UserService:
    """Service for user-related operations."""

    def __init__(self):
        """Initialize the service with all required repositories."""
        self.user_repo = get_user_repository()
        self.notification_repo = get_notification_repository()
        self.password_reset_repo = get_password_reset_repository()

    def get_all_users(self) -> List[User]:
        """
        Retrieve all users.

        Returns:
            List of User objects
        """
        try:
            return self.user_repo.get_all()
        except Exception as e:
            log_exception(logger, "Error getting all users", e)
            raise

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.

        Note: This method is maintained for backward compatibility.
        New code should use get_user_by_firebase_uid as user_id equals firebase_uid.

        Args:
            user_id: The ID of the user to retrieve (now equivalent to firebase_uid)

        Returns:
            User object if found, None otherwise
        """
        try:
            if not user_id:
                raise ValueError("User ID cannot be empty")

            # Since user_id is now the same as firebase_uid, use that method instead
            return self.get_user_by_firebase_uid(user_id)
        except Exception as e:
            log_exception(logger, f"Error getting user by ID: {user_id}", e)
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.

        Args:
            email: The email address to search for

        Returns:
            User object if found, None otherwise

        Raises:
            ValueError: If email format is invalid
        """
        try:
            # Validate email format
            if not validate_email(email):
                raise ValueError("Invalid email format")

            return self.user_repo.get_by_email(email)
        except Exception as e:
            log_exception(logger, f"Error getting user by email: {email}", e)
            raise

    def create_user(self, user_data: Dict[str, Any], create_auth_user: bool = True) -> User:
        """
        Create a new user.

        Args:
            user_data: Dictionary containing user information
            create_auth_user: Whether to create a Firebase Auth user

        Returns:
            Newly created User object

        Raises:
            ValueError: If required fields are missing or validation fails
        """
        try:
            # Validate required fields
            required_fields = ["email", "first_name", ]
            if create_auth_user:
                required_fields.append("password")

            validation = validate_required_fields(user_data, required_fields)
            if not validation["valid"]:
                missing = ', '.join(validation['missing_fields'])
                raise ValueError(f"Missing required fields: {missing}")

            # Validate email format and convert to lowercase
            email = user_data["email"]
            if not validate_email(email):
                raise ValueError("Invalid email format")

            # Store email in lowercase for consistent lookups
            email = email.lower()
            user_data["email"] = email

            # Validate phone number if provided
            phone_number = user_data.get("phone_number")
            if phone_number and not validate_phone_number(phone_number):
                raise ValueError("Invalid phone number format")

            # Check if user with this email already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise ValueError(f"User with email {email} already exists")

            # Sanitize text inputs and ensure proper capitalization
            first_name = sanitize_input(user_data["first_name"])
            last_name = sanitize_input(user_data["last_name"])

            # Ensure proper capitalization (not all uppercase)
            if first_name and first_name.isupper():
                first_name = first_name.title()
            if last_name and last_name.isupper():
                last_name = last_name.title()

            user_data["first_name"] = first_name
            user_data["last_name"] = last_name

            # Handle profile picture upload if base64 data is provided
            if "profile_picture" in user_data:
                profile_picture = user_data["profile_picture"]
                
                # If it's base64 data, upload to storage
                if profile_picture and not profile_picture.startswith(('http://', 'https://')):
                    try:
                        from services.storage_service import StorageService
                        storage_service = StorageService()
                        
                        # Generate unique filename (use temporary ID since firebase_uid may not exist yet)
                        temp_id = str(uuid.uuid4())
                        file_name = f"profile_{temp_id}.jpg"
                        upload_result = storage_service.upload_file(profile_picture, file_name, "profile_photos")
                        
                        if upload_result.get('success'):
                            user_data["profile_picture"] = upload_result.get('file_url', '')
                            logger.info("Profile picture uploaded during user creation")
                        else:
                            raise ValueError(f"Failed to upload profile picture: {upload_result.get('error', 'Unknown error')}")
                            
                    except Exception as upload_error:
                        log_exception(logger, "Error uploading profile picture during user creation", upload_error)
                        raise ValueError(f"Failed to upload profile picture: {str(upload_error)}")
                else:
                    # It's a URL, sanitize it
                    user_data["profile_picture"] = sanitize_input(profile_picture)


            # Ensure firebase_uid exists - it's now required
            if not user_data.get("firebase_uid"):
                # Create Firebase Auth user if requested
                if create_auth_user:
                    password = user_data.pop("password")  # Remove password from user_data
                    display_name = f"{user_data['first_name']} {user_data['last_name']}"
                    auth_user = create_firebase_user(email, password, display_name)
                    # Store Firebase UID in the user data
                    user_data["firebase_uid"] = auth_user["uid"]
                else:
                    raise ValueError("firebase_uid is required to create a user")

            # Create User object
            now = datetime.now(timezone.utc)
            user = User(
                email=email,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data.get("role", "user"),
                profile_picture=user_data.get("profile_picture"),
                phone_number=phone_number,
                created_at=now,
                updated_at=now,
                firebase_uid=user_data.get("firebase_uid")
            )

            # Save to repository
            created_user = self.user_repo.create(user)
            logger.info("User created: %s", created_user.id)
            return created_user

        except Exception as e:
            # Mask any sensitive data before logging
            safe_data = user_data.copy()
            if "password" in safe_data:
                safe_data["password"] = "********"

            log_exception(logger, "Error creating user", e, {"user_data": safe_data})
            raise

    def update_user(self, firebase_uid: str, user_data: Dict[str, Any]) -> Optional[User]:
        """
        Update an existing user.

        Args:
            firebase_uid: The Firebase UID of the user to update
            user_data: Dictionary containing fields to update

        Returns:
            Updated User object if found, None otherwise

        Raises:
            ValueError: If validation fails
        """
        try:
            # Check if user exists
            existing_user = self.get_user_by_firebase_uid(firebase_uid)
            if not existing_user:
                logger.warning("Attempted to update non-existent user with Firebase UID: %s", firebase_uid)
                return None

            # If email is being updated, validate it
            if "email" in user_data:
                # Validate email format
                if not validate_email(user_data["email"]):
                    raise ValueError("Invalid email format")

                # Convert email to lowercase for consistency
                user_data["email"] = user_data["email"].lower()
                logger.info(f"Normalized email to lowercase: {user_data['email']}")

                # Check if new email is already in use
                if user_data["email"] != existing_user.email.lower():  # Compare lowercase versions
                    email_check = self.get_user_by_email(user_data["email"])
                    if email_check and email_check.firebase_uid != firebase_uid:
                        raise ValueError(f"Email {user_data['email']} is already in use")

                    # Update email in Firebase Authentication
                    try:
                        import firebase_admin.auth
                        firebase_admin.auth.update_user(
                            firebase_uid,
                            email=user_data["email"]  # Already lowercase
                        )
                        logger.info(f"Updated Firebase Auth email for user: {firebase_uid}")
                    except Exception as auth_error:
                        log_exception(
                            logger,
                            f"Error updating Firebase Auth email for user: {firebase_uid}",
                            auth_error
                        )
                        raise ValueError(f"Error updating email in Firebase Authentication: {str(auth_error)}")

            # Validate phone number if provided
            if "phone_number" in user_data and user_data["phone_number"]:
                if not validate_phone_number(user_data["phone_number"]):
                    raise ValueError("Invalid phone number format")

            # Sanitize text inputs and ensure proper capitalization
            if "first_name" in user_data:
                first_name = sanitize_input(user_data["first_name"])
                # Ensure proper capitalization (not all uppercase)
                if first_name and first_name.isupper():
                    first_name = first_name.title()
                user_data["first_name"] = first_name

            if "last_name" in user_data:
                last_name = sanitize_input(user_data["last_name"])
                # Ensure proper capitalization (not all uppercase)
                if last_name and last_name.isupper():
                    last_name = last_name.title()
                user_data["last_name"] = last_name

            # Handle profile picture upload if base64 data is provided
            if "profile_picture" in user_data:
                profile_picture = user_data["profile_picture"]
                
                # If it's base64 data, upload to storage
                if profile_picture and not profile_picture.startswith(('http://', 'https://')):
                    try:
                        from services.storage_service import StorageService
                        storage_service = StorageService()
                        
                        # Generate unique filename
                        file_name = f"profile_{firebase_uid}_{uuid.uuid4()}.jpg"
                        upload_result = storage_service.upload_file(profile_picture, file_name, "profile_photos")
                        
                        if upload_result.get('success'):
                            user_data["profile_picture"] = upload_result.get('file_url', '')
                            logger.info("Profile picture uploaded for user %s", firebase_uid)
                        else:
                            raise ValueError(f"Failed to upload profile picture: {upload_result.get('error', 'Unknown error')}")
                            
                    except Exception as upload_error:
                        log_exception(logger, f"Error uploading profile picture for user {firebase_uid}", upload_error)
                        raise ValueError(f"Failed to upload profile picture: {str(upload_error)}")
                else:
                    # It's a URL, sanitize it
                    user_data["profile_picture"] = sanitize_input(profile_picture)

            # Set updated timestamp
            user_data["updated_at"] = datetime.now(timezone.utc)

            # Update in repository
            updated_user = self.user_repo.update(firebase_uid, user_data)

            if updated_user:
                logger.info("User updated with Firebase UID: %s", firebase_uid)
                logger.info("User updated data: %s", user_data)

            return updated_user

        except Exception as e:
            log_exception(
                logger,
                f"Error updating user with Firebase UID: {firebase_uid}",
                e,
                {"firebase_uid": firebase_uid, "update_data": user_data}
            )
            raise


    def delete_user(self, firebase_uid: str) -> Tuple[bool, Optional[Dict[str, int]]]:
        """
        Delete a user by Firebase UID.

        Args:
            firebase_uid: The Firebase UID of the user to delete

        Returns:
            Tuple of (success boolean, cleanup counts dictionary)
        """
        try:
            # Get user before deletion to have access to email and other data
            user = self.get_user_by_firebase_uid(firebase_uid)
            if not user:
                logger.warning("Attempted to delete non-existent user with Firebase UID: %s", firebase_uid)
                return False, None

            cleanup_counts = None
            # Note: Related data cleanup has been simplified since complex relationships were removed

            # Delete from Firestore database
            result = self.user_repo.delete(firebase_uid)

            if result:
                # Also delete the user from Firebase Authentication
                try:
                    import firebase_admin.auth
                    firebase_admin.auth.delete_user(firebase_uid)
                    logger.info("User deleted from Firebase Auth with UID: %s", firebase_uid)
                except Exception as auth_error:
                    log_exception(
                        logger,
                        f"Error deleting user from Firebase Auth: {firebase_uid}",
                        auth_error
                    )
                    # Don't raise the error here, as we've already deleted from Firestore
                    # Just log it as a warning
                    logger.warning(
                        "User deleted from database but not from Firebase Auth: %s. Error: %s",
                        firebase_uid, str(auth_error)
                    )

                logger.info("User deleted with Firebase UID: %s", firebase_uid)
            else:
                logger.warning("Attempted to delete non-existent user with Firebase UID: %s", firebase_uid)

            return result, cleanup_counts
        except Exception as e:
            log_exception(logger, f"Error deleting user with Firebase UID: {firebase_uid}", e)
            raise

    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Retrieve a user by Firebase UID.

        Args:
            firebase_uid: The Firebase UID to search for

        Returns:
            User object if found, None otherwise
        """
        try:
            if not firebase_uid:
                raise ValueError("Firebase UID cannot be empty")

            return self.user_repo.get_by_firebase_uid(firebase_uid)
        except Exception as e:
            log_exception(logger, f"Error getting user by Firebase UID: {firebase_uid}", e)
            raise

    def update_onboarding_status(self, firebase_uid: str, onboarding_completed: bool) -> Dict[str, Any]:
        """
        Update a user's onboarding completion status.

        Args:
            firebase_uid: The Firebase UID of the user
            onboarding_completed: Boolean indicating if onboarding is completed

        Returns:
            dict: Result with success status and updated user data
        """
        try:
            if not firebase_uid:
                return {
                    'success': False,
                    'error': 'Firebase UID is required'
                }

            # Check if user exists
            existing_user = self.user_repo.get_by_firebase_uid(firebase_uid)
            if not existing_user:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            # Update onboarding status
            update_data = {
                'onboarding_completed': onboarding_completed,
                'updated_at': datetime.now(timezone.utc)
            }

            updated_user = self.user_repo.update(firebase_uid, update_data)
            if not updated_user:
                return {
                    'success': False,
                    'error': 'Failed to update user onboarding status'
                }

            logger.info("Onboarding status updated for user %s: %s", firebase_uid, onboarding_completed)
            
            return {
                'success': True,
                'user': updated_user.to_dict(),
                'message': 'Onboarding status updated successfully'
            }

        except Exception as e:
            log_exception(logger, f"Error updating onboarding status for user {firebase_uid}", e)
            return {
                'success': False,
                'error': str(e)
            }

    def process_user_photo(self, user_id: str, photo_data: str) -> Dict[str, Any]:
        """
        Process a user's profile photo (upload if base64, validate if URL) and update user profile.

        Args:
            user_id: The user's Firebase UID
            photo_data: Base64 encoded photo data or URL

        Returns:
            dict: Result with success status, photo URL, and updated user data
        """
        try:
            from services.storage_service import StorageService

            storage_service = StorageService()

            # Get current user
            current_user = self.user_repo.get_by_firebase_uid(user_id)
            if not current_user:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            # Process the photo
            if photo_data.startswith(('http://', 'https://')):
                # It's already a URL, use it directly
                photo_url = photo_data
            else:
                # It's base64 data, upload it
                file_name = f"profile_{user_id}_{uuid.uuid4()}.jpg"
                upload_result = storage_service.upload_file(photo_data, file_name, "profile_photos")
                
                if not upload_result.get('success'):
                    return {
                        'success': False,
                        'error': upload_result.get('error', 'Failed to upload photo')
                    }
                
                photo_url = upload_result.get('file_url', '')

            # Update user's profile picture
            update_data = {'profile_picture': photo_url}
            updated_user = self.user_repo.update(user_id, update_data)

            if not updated_user:
                return {
                    'success': False,
                    'error': 'Failed to update user profile'
                }

            return {
                'success': True,
                'photo_url': photo_url,
                'user': updated_user.to_dict(),
                'message': 'Profile photo processed successfully'
            }

        except Exception as e:  # pylint: disable=broad-exception-caught
            log_exception(logger, f"Error processing user photo for user {user_id}", e)
            return {
                'success': False,
                'error': str(e)
            }

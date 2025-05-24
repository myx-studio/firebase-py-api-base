"""User model definition."""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class User:
    """User model representing application users."""
    email: str
    first_name: str
    last_name: str
    role: str = "user"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    profile_picture: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool = True
    firebase_uid: Optional[str] = None
    onboarding_completed: bool = False
    language: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    email_notifications: bool = True
    push_notification: bool = True
    photo_url: Optional[str] = None
    bio: Optional[str] = None
    lang: Optional[str] = None
    id: Optional[str] = None


    def __post_init__(self):
        """Set default values after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

        if self.location is None:
            self.location = {
                "address": "",
                "city": "",
                "state": "",
                "country": "",
                "postalCode": "",
                "coordinates": {
                    "latitude": 0.0,
                    "longitude": 0.0
                }
            }
        # If firebase_uid is set but id is not, use firebase_uid as id
        if self.firebase_uid and not self.id:
            self.id = self.firebase_uid

    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary for Firestore."""
        user_dict = asdict(self)

        # Convert datetime objects to ISO format strings for JSON serialization
        if self.created_at:
            if hasattr(self.created_at, 'isoformat'):
                user_dict['created_at'] = self.created_at.isoformat()
            # If it's already a string, leave it as is

        if self.updated_at:
            if hasattr(self.updated_at, 'isoformat'):
                user_dict['updated_at'] = self.updated_at.isoformat()
            # If it's already a string, leave it as is

        # Remove None values
        return {k: v for k, v in user_dict.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: Optional[str] = None) -> 'User':
        """Create a User instance from a Firestore document."""
        # Create a copy of the data to avoid modifying the original
        user_data = data.copy()

        # Handle dates if they're stored as timestamps or strings
        if 'created_at' in user_data:
            if isinstance(user_data['created_at'], (int, float)):
                user_data['created_at'] = datetime.fromtimestamp(
                    user_data['created_at'], timezone.utc
                )
            elif isinstance(user_data['created_at'], str):
                try:
                    # Parse ISO format string to datetime
                    user_data['created_at'] = datetime.fromisoformat(
                        user_data['created_at'].replace('Z', '+00:00')
                    )
                except ValueError:
                    # Keep as is if parsing fails, but handle in to_dict
                    pass

        if 'updated_at' in user_data:
            if isinstance(user_data['updated_at'], (int, float)):
                user_data['updated_at'] = datetime.fromtimestamp(
                    user_data['updated_at'], timezone.utc
                )
            elif isinstance(user_data['updated_at'], str):
                try:
                    # Parse ISO format string to datetime
                    user_data['updated_at'] = datetime.fromisoformat(
                        user_data['updated_at'].replace('Z', '+00:00')
                    )
                except ValueError:
                    # Keep as is if parsing fails, but handle in to_dict
                    pass


        # Make sure all required fields are present
        if 'email' not in user_data or not user_data['email']:
            user_data['email'] = "default@example.com"
        if 'first_name' not in user_data or not user_data['first_name']:
            user_data['first_name'] = "Default"
        if 'last_name' not in user_data or not user_data['last_name']:
            user_data['last_name'] = ""

        # Remove any unexpected fields to avoid __init__ errors
        valid_fields = {'email', 'first_name', 'last_name', 'role', 'created_at',
                        'updated_at', 'profile_picture', 'phone_number', 'is_active',
                        'firebase_uid', 'onboarding_completed', 'language', 'location',
                        'email_notifications', 'photo_url', 'lang', 'push_notification',
                        'bio', 'id'}
        filtered_data = {k: v for k, v in user_data.items() if k in valid_fields}

        # Create User instance with document data
        user = cls(**filtered_data)

        # Set the document ID if provided
        if doc_id:
            user.id = doc_id
        return user

    def update_location(self, location_data: Dict[str, Any]) -> None:
        """Update user's location information."""
        if not self.location:
            self.location = {}

        # Update the location fields
        if self.location is not None:
            for key, value in location_data.items():
                self.location[key] = value

        self.updated_at = datetime.now(timezone.utc)

    def set_language(self, language_code: str) -> None:
        """Set user's preferred language."""
        self.language = language_code
        self.updated_at = datetime.now(timezone.utc)

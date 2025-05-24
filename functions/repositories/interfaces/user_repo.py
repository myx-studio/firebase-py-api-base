"""Interface for user repository implementations."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.user import User


class UserRepositoryInterface(ABC):
    """Abstract interface for user data access."""

    @abstractmethod
    def get_all(self) -> List[User]:
        """
        Retrieve all users.

        Returns:
            List of User objects

        Raises:
            Exception: If there is an error accessing the data store
        """

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User object if found, None otherwise

        Raises:
            Exception: If there is an error accessing the data store
        """

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.

        Args:
            email: The email address to search for

        Returns:
            User object if found, None otherwise

        Raises:
            Exception: If there is an error accessing the data store
        """

    @abstractmethod
    def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: The user object to create

        Returns:
            Created User object with ID assigned

        Raises:
            Exception: If there is an error creating the user
        """

    @abstractmethod
    def update(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """
        Update an existing user.

        Args:
            user_id: The ID of the user to update
            user_data: Dictionary containing fields to update

        Returns:
            Updated User object if found, None if user doesn't exist

        Raises:
            Exception: If there is an error updating the user
        """

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """
        Delete a user by ID.

        Args:
            user_id: The ID of the user to delete

        Returns:
            True if user was deleted, False if user doesn't exist

        Raises:
            Exception: If there is an error deleting the user
        """

    @abstractmethod
    def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Retrieve a user by Firebase UID.

        Args:
            firebase_uid: The Firebase UID to search for

        Returns:
            User object if found, None otherwise

        Raises:
            Exception: If there is an error accessing the data store
        """

"""Firestore implementation of user repository."""
from typing import List, Optional, Dict, Any
from firebase_admin import firestore as admin_firestore

from models.user import User
from repositories.interfaces.user_repo import UserRepositoryInterface
from config import config
from utils.logging import setup_logger, log_exception

logger = setup_logger("user_repo")


class FirestoreUserRepository(UserRepositoryInterface):
    """Firestore implementation of UserRepositoryInterface."""

    def __init__(self):
        """Initialize the repository with Firestore client."""
        self.db = admin_firestore.client()
        self.collection_name = config["collections"]["users"]
        self.collection = self.db.collection(self.collection_name)

    def get_all(self) -> List[User]:
        """Retrieve all users from Firestore."""
        try:
            users = []
            for doc in self.collection.stream():
                doc_data = doc.to_dict()
                if doc_data is not None:
                    user = User.from_dict(doc_data, doc.id)
                    users.append(user)
            return users
        except Exception as e:
            log_exception(logger, "Error retrieving all users", e)
            raise

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID from Firestore.

        Note: This method is maintained for backward compatibility.
        New code should use get_by_firebase_uid as user_id equals firebase_uid.
        """
        # This is now equivalent to get_by_firebase_uid since we use firebase_uid as the document ID
        return self.get_by_firebase_uid(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address from Firestore (case-insensitive)."""
        try:
            # Convert the input email to lowercase
            lower_email = email.lower() if email else email
            
            # First try exact match with the lowercase email
            query = self.collection.where("email", "==", lower_email).limit(1)
            results = list(query.stream())
            
            if results:
                doc_data = results[0].to_dict()
                if doc_data is not None:
                    return User.from_dict(doc_data, results[0].id)
                return None
            
            # If no match, try a case-insensitive search by getting all users and comparing manually
            # This is not efficient but necessary because Firestore doesn't support case-insensitive queries
            logger.info(f"No exact match found for email: {lower_email}, trying case-insensitive search")
            
            # Try the original email (this covers case where email is stored with original case)
            query = self.collection.where("email", "==", email).limit(1)
            results = list(query.stream())
            
            if results:
                doc_data = results[0].to_dict()
                if doc_data is not None:
                    return User.from_dict(doc_data, results[0].id)
                return None
                
            # As a last resort, get all users and compare emails case insensitively
            # Note: This is inefficient for large user bases but ensures a match
            query = self.collection.limit(1000)  # Add a reasonable limit
            results = query.stream()
            
            for doc in results:
                user_data = doc.to_dict()
                if "email" in user_data and user_data["email"] and user_data["email"].lower() == lower_email:
                    logger.info(f"Found case-insensitive match for email: {email}")
                    return User.from_dict(user_data, doc.id)
            
            return None
        except Exception as e:
            log_exception(logger, f"Error retrieving user by email: {email}", e)
            raise

    def create(self, user: User) -> User:
        """Create a new user in Firestore using firebase_uid as document ID."""
        try:
            # Ensure email is stored in lowercase for consistent lookups
            if user.email:
                user.email = user.email.lower()
                
            user_dict = user.to_dict()

            # Remove ID if present in the dictionary
            if "id" in user_dict:
                del user_dict["id"]

            # Ensure firebase_uid exists
            if not user.firebase_uid:
                raise ValueError("firebase_uid is required to create a user")

            # Use firebase_uid as the document ID
            doc_ref = self.collection.document(user.firebase_uid)
            doc_ref.set(user_dict)

            # Set the user ID to be the same as firebase_uid
            user.id = user.firebase_uid

            logger.info("User created with ID: %s (firebase_uid)", user.id)
            return user
        except Exception as e:
            log_exception(logger, "Error creating user", e, {"user_data": user.to_dict()})
            raise

    def update(self, firebase_uid: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update an existing user in Firestore using firebase_uid."""
        try:
            # Check if user exists
            doc_ref = self.collection.document(firebase_uid)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning("Attempted to update non-existent user with Firebase UID: %s", firebase_uid)
                return None

            # Remove ID from update data if present
            if "id" in user_data:
                del user_data["id"]
                
            # Ensure email is stored in lowercase for consistent lookups
            if "email" in user_data and user_data["email"]:
                user_data["email"] = user_data["email"].lower()

            logger.info("User data to update: %s", user_data)

            # Update the document
            doc_ref.update(user_data)

            # Get the updated document
            updated_doc = doc_ref.get()

            logger.info("User updated with Firebase UID: %s", firebase_uid)
            doc_data = updated_doc.to_dict()
            if doc_data is not None:
                return User.from_dict(doc_data, updated_doc.id)
            return None
        except Exception as e:
            log_exception(
                logger,
                f"Error updating user with Firebase UID: {firebase_uid}",
                e,
                {"firebase_uid": firebase_uid, "update_data": user_data}
            )
            raise

    def delete(self, firebase_uid: str) -> bool:
        """Delete a user by Firebase UID from Firestore."""
        try:
            # Check if user exists
            doc_ref = self.collection.document(firebase_uid)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning("Attempted to delete non-existent user with Firebase UID: %s", firebase_uid)
                return False

            # Delete the document
            doc_ref.delete()

            logger.info("User deleted with Firebase UID: %s", firebase_uid)
            return True
        except Exception as e:
            log_exception(logger, f"Error deleting user with Firebase UID: {firebase_uid}", e)
            raise

    def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Retrieve a user by Firebase UID from Firestore.

        Since firebase_uid is now used as the document ID, this is a direct lookup.
        """
        try:
            # Direct lookup by document ID (which is the firebase_uid)
            doc = self.collection.document(firebase_uid).get()
            if doc.exists:
                doc_data = doc.to_dict()
                if doc_data is not None:
                    return User.from_dict(doc_data, doc.id)
                return None
            return None
        except Exception as e:
            log_exception(logger, f"Error retrieving user by Firebase UID: {firebase_uid}", e)
            raise

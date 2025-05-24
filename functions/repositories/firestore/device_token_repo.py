"""Firestore implementation of device token repository."""
from typing import List, Optional, Dict, Any
from firebase_admin import firestore as admin_firestore
from datetime import datetime

from config import config
from utils.logging import setup_logger, log_exception

logger = setup_logger("device_token_repo")


class FirestoreDeviceTokenRepository:
    """Firestore implementation for device token storage."""

    def __init__(self):
        """Initialize the repository with Firestore client."""
        self.db = admin_firestore.client()
        self.collection_name = config["collections"]["device_tokens"]
        self.collection = self.db.collection(self.collection_name)

    async def store_device_token(self, user_id: str, device_token: str, 
                               device_type: str, device_name: str = "Unknown Device") -> bool:
        """
        Store or update a device token for a user.
        
        Args:
            user_id: The user's Firebase UID
            device_token: The device token (e.g., Expo push token)
            device_type: Type of device ('ios' or 'android')
            device_name: Optional name for the device
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use device_token as document ID to avoid duplicates
            doc_ref = self.collection.document(device_token)
            
            token_data = {
                "user_id": user_id,
                "device_token": device_token,
                "device_type": device_type,
                "device_name": device_name,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            }
            
            doc_ref.set(token_data)
            logger.info("Device token stored successfully for user %s", user_id)
            return True
            
        except Exception as e:
            log_exception(logger, f"Error storing device token for user {user_id}", e)
            return False

    async def remove_device_token(self, device_token: str) -> bool:
        """
        Remove a device token.
        
        Args:
            device_token: The device token to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc_ref = self.collection.document(device_token)
            doc_ref.delete()
            logger.info("Device token removed successfully: %s", device_token)
            return True
            
        except Exception as e:
            log_exception(logger, f"Error removing device token {device_token}", e)
            return False

    async def get_user_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active device tokens for a user.
        
        Args:
            user_id: The user's Firebase UID
            
        Returns:
            List of device token data dictionaries
        """
        try:
            tokens = []
            query = self.collection.where("user_id", "==", user_id).where("is_active", "==", True)
            
            for doc in query.stream():
                token_data = doc.to_dict()
                tokens.append(token_data)
                
            return tokens
            
        except Exception as e:
            log_exception(logger, f"Error retrieving device tokens for user {user_id}", e)
            return []

    async def deactivate_user_tokens(self, user_id: str) -> bool:
        """
        Deactivate all device tokens for a user (useful for logout).
        
        Args:
            user_id: The user's Firebase UID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = self.collection.where("user_id", "==", user_id).where("is_active", "==", True)
            
            for doc in query.stream():
                doc.reference.update({
                    "is_active": False,
                    "updated_at": datetime.now()
                })
                
            logger.info("All device tokens deactivated for user %s", user_id)
            return True
            
        except Exception as e:
            log_exception(logger, f"Error deactivating device tokens for user {user_id}", e)
            return False
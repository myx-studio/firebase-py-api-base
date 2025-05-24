"""Firestore implementation of password reset repository."""
from typing import List, Optional
from datetime import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter, Query
from models.password_reset import PasswordReset
from repositories.interfaces.password_reset_repo import PasswordResetRepository
from config import config
from utils.logging import setup_logger

logger = setup_logger("password_reset_repo")


class FirestorePasswordResetRepository(PasswordResetRepository):
    """Firestore implementation of password reset repository."""
    
    def __init__(self):
        """Initialize repository with Firestore client."""
        self.db = firestore.client()
        self.collection_name = config["collections"]["password_resets"]
        self.collection = self.db.collection(self.collection_name)
    
    async def create(self, password_reset: PasswordReset) -> PasswordReset:
        """Create a new password reset record."""
        try:
            # Convert to dict and remove None id
            data = password_reset.to_dict()
            if 'id' in data:
                del data['id']
            
            # Create document
            doc_ref = self.collection.document()
            data['id'] = doc_ref.id
            doc_ref.set(data)
            
            # Return password reset with ID
            password_reset.id = doc_ref.id
            return password_reset
            
        except Exception as e:
            logger.error(f"Error creating password reset: {str(e)}")
            raise
    
    async def get_by_id(self, reset_id: str) -> Optional[PasswordReset]:
        """Get password reset by ID."""
        try:
            doc = self.collection.document(reset_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return PasswordReset.from_dict(data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting password reset {reset_id}: {str(e)}")
            raise
    
    async def get_by_token(self, token: str) -> Optional[PasswordReset]:
        """Get password reset by token."""
        try:
            query = self.collection.where(
                filter=FieldFilter('token', '==', token)
            ).limit(1)
            
            docs = query.get()
            
            for doc in docs:
                data = doc.to_dict()
                if data is not None:
                    data['id'] = doc.id
                    return PasswordReset.from_dict(data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting password reset by token: {str(e)}")
            raise
    
    async def get_active_reset_by_email(self, email: str) -> Optional[PasswordReset]:
        """Get active password reset for an email."""
        try:
            now = datetime.utcnow()
            
            query = self.collection.where(
                filter=FieldFilter('email', '==', email)
            ).where(
                filter=FieldFilter('used', '==', False)
            ).where(
                filter=FieldFilter('expires_at', '>', now)
            ).order_by(
                'created_at', direction=Query.DESCENDING
            ).limit(1)
            
            docs = query.get()
            
            for doc in docs:
                data = doc.to_dict()
                if data is not None:
                    data['id'] = doc.id
                    return PasswordReset.from_dict(data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting active reset for email {email}: {str(e)}")
            raise
    
    async def mark_as_used(self, reset_id: str) -> bool:
        """Mark a password reset as used."""
        try:
            doc_ref = self.collection.document(reset_id)
            doc_ref.update({
                'used': True,
                'used_at': datetime.utcnow()
            })
            return True
            
        except Exception as e:
            logger.error(f"Error marking password reset {reset_id} as used: {str(e)}")
            return False
    
    async def delete(self, reset_id: str) -> bool:
        """Delete a password reset record."""
        try:
            self.collection.document(reset_id).delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting password reset {reset_id}: {str(e)}")
            return False
    
    async def delete_expired_tokens(self) -> int:
        """Delete all expired password reset tokens."""
        try:
            now = datetime.utcnow()
            
            # Query expired tokens
            query = self.collection.where(
                filter=FieldFilter('expires_at', '<', now)
            )
            
            docs = query.get()
            
            # Batch delete
            batch = self.db.batch()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Firestore batch limit is 500
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Commit remaining
            if count % 500 != 0:
                batch.commit()
                
            logger.info(f"Deleted {count} expired password reset tokens")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting expired tokens: {str(e)}")
            raise
    
    async def get_by_user_id(self, user_id: str, limit: int = 10) -> List[PasswordReset]:
        """Get password resets for a user."""
        try:
            query = self.collection.where(
                filter=FieldFilter('user_id', '==', user_id)
            ).order_by(
                'created_at', direction=Query.DESCENDING
            ).limit(limit)
            
            docs = query.get()
            
            resets = []
            for doc in docs:
                data = doc.to_dict()
                if data is not None:
                    data['id'] = doc.id
                    resets.append(PasswordReset.from_dict(data))
                
            return resets
            
        except Exception as e:
            logger.error(f"Error getting password resets for user {user_id}: {str(e)}")
            raise
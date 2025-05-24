"""Interface for password reset repository."""
from abc import ABC, abstractmethod
from typing import Optional, List
from models.password_reset import PasswordReset


class PasswordResetRepository(ABC):
    """Abstract base class for password reset repository."""
    
    @abstractmethod
    async def create(self, password_reset: PasswordReset) -> PasswordReset:
        """
        Create a new password reset record.
        
        Args:
            password_reset: Password reset to create
            
        Returns:
            Created password reset with ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, reset_id: str) -> Optional[PasswordReset]:
        """
        Get password reset by ID.
        
        Args:
            reset_id: ID of the password reset
            
        Returns:
            Password reset if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[PasswordReset]:
        """
        Get password reset by token.
        
        Args:
            token: Reset token
            
        Returns:
            Password reset if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_active_reset_by_email(self, email: str) -> Optional[PasswordReset]:
        """
        Get active (non-expired, unused) password reset for an email.
        
        Args:
            email: Email address
            
        Returns:
            Active password reset if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def mark_as_used(self, reset_id: str) -> bool:
        """
        Mark a password reset as used.
        
        Args:
            reset_id: ID of the password reset
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, reset_id: str) -> bool:
        """
        Delete a password reset record.
        
        Args:
            reset_id: ID of the password reset
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_expired_tokens(self) -> int:
        """
        Delete all expired password reset tokens.
        
        Returns:
            Number of tokens deleted
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, limit: int = 10) -> List[PasswordReset]:
        """
        Get password resets for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of records to return
            
        Returns:
            List of password resets
        """
        pass
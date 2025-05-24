"""Interface for notification repository."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.notification import Notification


class NotificationRepository(ABC):
    """Abstract base class for notification repository."""
    
    @abstractmethod
    async def create(self, notification: Notification) -> Notification:
        """
        Create a new notification.
        
        Args:
            notification: Notification to create
            
        Returns:
            Created notification with ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        Get notification by ID.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            Notification if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            unread_only: If True, return only unread notifications
            
        Returns:
            List of notifications
        """
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of notifications marked as read
        """
        pass
    
    @abstractmethod
    async def delete(self, notification_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_old_notifications(self, days: int = 30) -> int:
        """
        Delete notifications older than specified days.
        
        Args:
            days: Number of days to keep notifications
            
        Returns:
            Number of notifications deleted
        """
        pass
    
    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Count of unread notifications
        """
        pass
    
    @abstractmethod
    async def get_by_type(
        self,
        user_id: str,
        notification_type: str,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications of a specific type for a user.
        
        Args:
            user_id: ID of the user
            notification_type: Type of notification
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        pass
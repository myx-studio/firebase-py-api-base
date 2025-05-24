"""Realtime Database implementation of notification repository."""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from firebase_admin import db
from models.notification import Notification
from repositories.interfaces.notification_repo import NotificationRepository
from config import config
from utils.logging import setup_logger

logger = setup_logger("realtime_notification_repo")


class RealtimeDatabaseNotificationRepository(NotificationRepository):
    """Realtime Database implementation of notification repository."""

    def __init__(self):
        """Initialize repository with Realtime Database reference."""
        self.collection_name = config["collections"]["notifications"]
        self.ref = db.reference(self.collection_name)

    async def create(self, notification: Notification) -> Notification:
        """Create a new notification."""
        try:
            # Convert to dict and remove None id
            data = notification.to_dict()
            if 'id' in data:
                del data['id']

            # Create new notification with push key
            new_ref = self.ref.push()

            # Set the data and update notification with generated ID
            new_ref.set(data)
            notification.id = new_ref.key

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise

    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        try:
            data = self.ref.child(notification_id).get()

            if data and isinstance(data, dict):
                data['id'] = notification_id
                return Notification.from_dict(data)

            return None

        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {str(e)}")
            raise

    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        try:
            # Get all notifications for the user
            all_notifications = self.ref.order_by_child('user_id').equal_to(user_id).get()

            if not all_notifications or not isinstance(all_notifications, dict):
                return []

            # Convert to list of notifications
            notifications = []
            for key, data in all_notifications.items():
                if not isinstance(data, dict):
                    continue
                data['id'] = key
                notification = Notification.from_dict(data)

                # Filter by unread if requested
                if unread_only and notification.read:
                    continue

                notifications.append(notification)

            # Sort by created_at descending
            notifications.sort(key=lambda n: n.created_at, reverse=True)

            # Apply pagination
            start_idx = offset
            end_idx = offset + limit

            return notifications[start_idx:end_idx]

        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            raise

    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            self.ref.child(notification_id).update({
                'read': True,
                'read_at': datetime.now(timezone.utc).isoformat()
            })
            return True

        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read."""
        try:
            # Get all unread notifications for user
            all_notifications = self.ref.order_by_child('user_id').equal_to(user_id).get()

            if not all_notifications or not isinstance(all_notifications, dict):
                return 0

            count = 0
            read_at = datetime.now(timezone.utc).isoformat()

            # Update each unread notification
            for key, data in all_notifications.items():
                if not isinstance(data, dict):
                    continue
                if not data.get('read', False):
                    self.ref.child(key).update({
                        'read': True,
                        'read_at': read_at
                    })
                    count += 1

            return count

        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            raise

    async def delete(self, notification_id: str) -> bool:
        """Delete a notification."""
        try:
            self.ref.child(notification_id).delete()
            return True

        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {str(e)}")
            return False

    async def delete_old_notifications(self, days: int = 30) -> int:
        """Delete notifications older than specified days."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Get all notifications
            all_notifications = self.ref.get()

            if not all_notifications or not isinstance(all_notifications, dict):
                return 0

            count = 0

            # Delete old notifications
            for key, data in all_notifications.items():
                if not isinstance(data, dict):
                    continue
                created_at_str = data.get('created_at')
                if created_at_str:
                    # Parse the datetime string
                    if isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_at < cutoff_date:
                            self.ref.child(key).delete()
                            count += 1

            logger.info(f"Deleted {count} notifications older than {days} days")
            return count

        except Exception as e:
            logger.error(f"Error deleting old notifications: {str(e)}")
            raise

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        try:
            # Get all notifications for user
            all_notifications = self.ref.order_by_child('user_id').equal_to(user_id).get()

            if not all_notifications or not isinstance(all_notifications, dict):
                return 0

            # Count unread
            count = 0
            for _, data in all_notifications.items():
                if not isinstance(data, dict):
                    continue
                if not data.get('read', False):
                    count += 1

            return count

        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            raise

    async def get_by_type(
        self,
        user_id: str,
        notification_type: str,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications of a specific type for a user."""
        try:
            # Get all notifications for user
            all_notifications = self.ref.order_by_child('user_id').equal_to(user_id).get()

            if not all_notifications or not isinstance(all_notifications, dict):
                return []

            # Filter by type and convert to list
            notifications = []
            for key, data in all_notifications.items():
                if not isinstance(data, dict):
                    continue
                if data.get('type') == notification_type:
                    data['id'] = key
                    notifications.append(Notification.from_dict(data))

            # Sort by created_at descending
            notifications.sort(key=lambda n: n.created_at, reverse=True)

            # Apply limit
            return notifications[:limit]

        except Exception as e:
            logger.error(f"Error getting notifications by type for user {user_id}: {str(e)}")
            raise

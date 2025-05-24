"""Notification service using Expo Push Notifications."""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import requests
from utils.logging import setup_logger

logger = setup_logger("notification_service")


class NotificationService:
    """Service for handling push notifications using Expo."""

    def __init__(self):
        """Initialize notification service with Expo configuration."""
        self.expo_push_url = 'https://exp.host/--/api/v2/push/send'
        self.expo_receipt_url = 'https://exp.host/--/api/v2/push/getReceipts'
        # Expo Access Token is optional but recommended for higher rate limits
        self.expo_access_token = os.environ.get('EXPO_ACCESS_TOKEN')

    def send_push_notification(
        self,
        expo_push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = 'default',
        badge: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a push notification to a single device using Expo.

        Args:
            expo_push_token: The Expo push token for the device
            title: Notification title
            body: Notification body text
            data: Additional data to send with the notification
            sound: Sound to play (default, or null for no sound)
            badge: Badge count to set on app icon

        Returns:
            dict: Response from Expo push service
        """
        try:
            message: Dict[str, Any] = {
                'to': expo_push_token,
                'title': title,
                'body': body,
                'sound': sound,
                'channelId': 'default'
            }

            if data:
                message['data'] = data

            if badge is not None:
                message['badge'] = badge

            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/json'
            }

            # Add authorization header if access token is available
            if self.expo_access_token:
                headers['Authorization'] = f'Bearer {self.expo_access_token}'

            response = requests.post(
                self.expo_push_url,
                json={'to': expo_push_token, **message},
                headers=headers,
                timeout=30
            )

            result = response.json()

            if response.status_code == 200:
                logger.info("Push notification sent successfully to %s", expo_push_token)
                return result

            logger.error("Failed to send push notification: %s", result)
            return {'error': result}

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to send push notification: %s", str(e))
            return {'error': str(e)}

    def send_bulk_notifications(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send multiple push notifications in a single request.

        Args:
            messages: List of message dictionaries, each containing:
                - to: Expo push token
                - title: Notification title
                - body: Notification body
                - data: Optional additional data
                - sound: Optional sound setting
                - badge: Optional badge count

        Returns:
            dict: Response from Expo push service
        """
        try:
            # Expo accepts up to 100 notifications per request
            if len(messages) > 100:
                logger.warning("Attempting to send %s notifications. Expo limit is 100.",
                               len(messages))
                messages = messages[:100]

            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/json'
            }

            # Add authorization header if access token is available
            if self.expo_access_token:
                headers['Authorization'] = f'Bearer {self.expo_access_token}'

            response = requests.post(
                self.expo_push_url,
                json=messages,
                headers=headers,
                timeout=30
            )

            result = response.json()

            if response.status_code == 200:
                logger.info("Bulk notifications sent successfully: %s messages", len(messages))
                return result

            logger.error("Failed to send bulk notifications: %s", result)
            return {'error': result}

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to send bulk notifications: %s", str(e))
            return {'error': str(e)}

    def get_push_receipts(self, ticket_ids: List[str]) -> Dict[str, Any]:
        """
        Get receipts for previously sent push notifications.

        Args:
            ticket_ids: List of ticket IDs from previous push sends

        Returns:
            dict: Receipt information for the tickets
        """
        try:
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/json'
            }

            # Add authorization header if access token is available
            if self.expo_access_token:
                headers['Authorization'] = f'Bearer {self.expo_access_token}'

            response = requests.post(
                self.expo_receipt_url,
                json={'ids': ticket_ids},
                headers=headers,
                timeout=30
            )

            return response.json()

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get push receipts: %s", str(e))
            return {'error': str(e)}

    @staticmethod
    def create_notification_data(
        user_id: str,
        title: str,
        body: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a notification data structure.

        Args:
            user_id: ID of the user to receive the notification
            title: Notification title
            body: Notification body text
            notification_type: Type of notification
            data: Additional data for the notification
            action_url: URL to navigate to when notification is tapped

        Returns:
            dict: Notification data structure
        """
        notification = {
            'user_id': user_id,
            'title': title,
            'body': body,
            'type': notification_type,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'read': False,
            'read_at': None
        }

        if data:
            notification['data'] = data

        if action_url:
            notification['action_url'] = action_url

        return notification

    @staticmethod
    def format_notification_for_display(notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a notification for display in the app.

        Args:
            notification: Raw notification data

        Returns:
            dict: Formatted notification
        """
        return {
            'id': notification.get('id'),
            'title': notification.get('title'),
            'body': notification.get('body'),
            'type': notification.get('type'),
            'created_at': notification.get('created_at'),
            'read': notification.get('read', False),
            'read_at': notification.get('read_at'),
            'data': notification.get('data', {}),
            'action_url': notification.get('action_url')
        }

    @staticmethod
    def group_notifications_by_type(
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group notifications by their type.

        Args:
            notifications: List of notifications

        Returns:
            dict: Notifications grouped by type
        """
        grouped = {}

        for notification in notifications:
            notification_type = notification.get('type', 'other')
            if notification_type not in grouped:
                grouped[notification_type] = []
            grouped[notification_type].append(notification)

        return grouped

    @staticmethod
    def filter_unread_notifications(
        notifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out read notifications.

        Args:
            notifications: List of notifications

        Returns:
            list: List of unread notifications
        """
        return [n for n in notifications if not n.get('read', False)]

    @staticmethod
    def get_notification_summary(
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get a summary of notifications.

        Args:
            notifications: List of notifications

        Returns:
            dict: Summary with counts by type and read status
        """
        summary = {
            'total': len(notifications),
            'unread': 0,
            'by_type': {}
        }

        for notification in notifications:
            # Count unread
            if not notification.get('read', False):
                summary['unread'] += 1

            # Count by type
            notification_type = notification.get('type', 'other')
            if notification_type not in summary['by_type']:
                summary['by_type'][notification_type] = {
                    'total': 0,
                    'unread': 0
                }

            summary['by_type'][notification_type]['total'] += 1
            if not notification.get('read', False):
                summary['by_type'][notification_type]['unread'] += 1

        return summary

    @staticmethod
    def should_send_push_notification(
        notification_type: str,
        user_preferences: Dict[str, Any]
    ) -> bool:
        """
        Check if a push notification should be sent based on user preferences.

        Args:
            notification_type: Type of notification
            user_preferences: User's notification preferences

        Returns:
            bool: True if push notification should be sent
        """
        # Default to sending if no preferences are set
        if not user_preferences:
            return True

        # Check if push notifications are enabled globally
        if not user_preferences.get('push_notifications_enabled', True):
            return False

        # Check specific notification type preferences
        type_preferences = user_preferences.get('notification_types', {})

        # Default to True if type not in preferences
        return type_preferences.get(notification_type, True)

    @staticmethod
    def batch_notifications(
        notifications: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch notifications for bulk operations.

        Args:
            notifications: List of notifications
            batch_size: Maximum size of each batch

        Returns:
            list: List of notification batches
        """
        batches = []
        for i in range(0, len(notifications), batch_size):
            batches.append(notifications[i:i + batch_size])
        return batches

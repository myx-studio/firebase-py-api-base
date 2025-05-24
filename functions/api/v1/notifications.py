"""Notification API endpoints."""
from flask import Request
from firebase_admin.exceptions import FirebaseError

from repositories import get_notification_repository
from repositories.firestore.device_token_repo import FirestoreDeviceTokenRepository
from services.notification_service import NotificationService
from utils.helpers import create_response, get_user_id_from_request
from utils.logging import setup_logger

logger = setup_logger("api_notifications")

# Initialize services
notification_repo = get_notification_repository()
notification_service = NotificationService()
device_token_repo = FirestoreDeviceTokenRepository()


async def get_notifications(request: Request):
    """
    Get notifications for the authenticated user.

    Query parameters:
    - limit: Maximum number of notifications to return (default: 50)
    - offset: Number of notifications to skip (default: 0)
    - unread_only: If true, return only unread notifications
    """
    try:
        user_id = get_user_id_from_request(request)

        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        unread_only = request.args.get('unread_only', '').lower() == 'true'

        # Get notifications
        notifications = await notification_repo.get_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )

        # Convert to dict
        notifications_data = [n.to_dict() for n in notifications]

        return create_response(
            data={'notifications': notifications_data},
            message='Notifications retrieved successfully'
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Database error getting notifications: %s", str(e))
        return create_response(
            data=None,
            message='Failed to get notifications',
            error=str(e),
            status=500
        )


async def get_unread_count(request: Request):
    """Get count of unread notifications for the authenticated user."""
    try:
        user_id = get_user_id_from_request(request)

        # Get unread count
        count = await notification_repo.get_unread_count(user_id)

        return create_response(
            data={'unread_count': count},
            message='Unread count retrieved successfully'
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Database error getting unread count: %s", str(e))
        return create_response(
            data=None,
            message='Failed to get unread count',
            error=str(e),
            status=500
        )


async def mark_as_read(request: Request):
    """
    Mark a notification as read.

    URL parameter:
    - notification_id: ID of the notification to mark as read
    """
    try:
        user_id = get_user_id_from_request(request)
        notification_id = request.view_args.get('notification_id') if request.view_args else None

        if not notification_id:
            return create_response(
                data=None,
                message='Notification ID is required',
                error='Missing notification_id',
                status=400
            )

        # Get notification to verify ownership
        notification = await notification_repo.get_by_id(notification_id)

        if not notification:
            return create_response(
                data=None,
                message='Notification not found',
                error='Not found',
                status=404
            )

        if notification.user_id != user_id:
            return create_response(
                data=None,
                message='Unauthorized',
                error='Cannot mark notification for another user',
                status=403
            )

        # Mark as read
        success = await notification_repo.mark_as_read(notification_id)

        if success:
            return create_response(
                data={'notification_id': notification_id},
                message='Notification marked as read'
            )
        return create_response(
            data=None,
            message='Failed to mark notification as read',
            error='Update failed',
            status=500
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Database error marking notification as read: %s", str(e))
        return create_response(
            data=None,
            message='Failed to mark notification as read',
            error=str(e),
            status=500
        )


async def mark_all_as_read(request: Request):
    """Mark all notifications as read for the authenticated user."""
    try:
        user_id = get_user_id_from_request(request)

        # Mark all as read
        count = await notification_repo.mark_all_as_read(user_id)

        return create_response(
            data={'marked_count': count},
            message=f'Marked {count} notifications as read'
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Database error marking all notifications as read: %s", str(e))
        return create_response(
            data=None,
            message='Failed to mark all notifications as read',
            error=str(e),
            status=500
        )


async def delete_notification(request: Request):
    """
    Delete a notification.

    URL parameter:
    - notification_id: ID of the notification to delete
    """
    try:
        user_id = get_user_id_from_request(request)
        notification_id = request.view_args.get('notification_id') if request.view_args else None

        if not notification_id:
            return create_response(
                data=None,
                message='Notification ID is required',
                error='Missing notification_id',
                status=400
            )

        # Get notification to verify ownership
        notification = await notification_repo.get_by_id(notification_id)

        if not notification:
            return create_response(
                data=None,
                message='Notification not found',
                error='Not found',
                status=404
            )

        if notification.user_id != user_id:
            return create_response(
                data=None,
                message='Unauthorized',
                error='Cannot delete notification for another user',
                status=403
            )

        # Delete notification
        success = await notification_repo.delete(notification_id)

        if success:
            return create_response(
                data={'notification_id': notification_id},
                message='Notification deleted successfully'
            )
        return create_response(
            data=None,
            message='Failed to delete notification',
            error='Delete failed',
            status=500
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Database error deleting notification: %s", str(e))
        return create_response(
            data=None,
            message='Failed to delete notification',
            error=str(e),
            status=500
        )


async def register_device(request: Request):
    """
    Register a device for push notifications.

    Request body:
    - device_token: Expo push token
    - device_type: Type of device (ios, android)
    - device_name: Optional name for the device
    """
    try:
        user_id = get_user_id_from_request(request)  # Verify authentication
        data = request.get_json()

        device_token = data.get('device_token')
        device_type = data.get('device_type')
        device_name = data.get('device_name', 'Unknown Device')

        if not device_token:
            return create_response(
                data=None,
                message='Device token is required',
                error='Missing device_token',
                status=400
            )

        if not device_type or device_type not in ['ios', 'android']:
            return create_response(
                data=None,
                message='Valid device type is required (ios or android)',
                error='Invalid device_type',
                status=400
            )

        # Store device token in Firestore
        success = await device_token_repo.store_device_token(
            user_id=user_id,
            device_token=device_token,
            device_type=device_type,
            device_name=device_name
        )

        if not success:
            return create_response(
                data=None,
                message='Failed to register device token',
                error='Storage failed',
                status=500
            )

        return create_response(
            data={
                'device_token': device_token,
                'device_type': device_type,
                'device_name': device_name
            },
            message='Device registered successfully'
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )
    except (TypeError, KeyError) as e:
        logger.error("Invalid request data: %s", str(e))
        return create_response(
            data=None,
            message='Invalid request data',
            error=str(e),
            status=400
        )


async def unregister_device(request: Request):
    """
    Unregister a device from push notifications.

    URL parameter:
    - device_id: ID of the device to unregister
    """
    try:
        get_user_id_from_request(request)  # Verify authentication
        device_id = request.view_args.get('device_id') if request.view_args else None

        if not device_id:
            return create_response(
                data=None,
                message='Device ID is required',
                error='Missing device_id',
                status=400
            )

        # Remove device token from Firestore
        success = await device_token_repo.remove_device_token(device_id)

        if not success:
            return create_response(
                data=None,
                message='Failed to unregister device',
                error='Removal failed',
                status=500
            )

        return create_response(
            data={'device_id': device_id},
            message='Device unregistered successfully'
        )

    except (AttributeError, ValueError) as e:
        logger.error("Authentication or validation error: %s", str(e))
        return create_response(
            data=None,
            message='Authentication required',
            error=str(e),
            status=401
        )

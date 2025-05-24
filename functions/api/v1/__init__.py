"""Version 1 of the API."""
from flask import Flask, request
from config import CONFIG
from middlewares.auth_middleware import require_auth
from middlewares.logging_middleware import request_logger
# Import API endpoint functions
from .auth import login_with_email, register, get_user_profile, login_with_custom_token
from .users import get_users, get_user, create_user, update_user, delete_user, update_onboarding, update_user_photo
from .notifications import get_notifications, get_unread_count, mark_as_read, mark_all_as_read, delete_notification, register_device, unregister_device
from .password import request_reset, reset_password, change_password

# Get API prefix from config
API_PREFIX = CONFIG.get("api", {}).get("prefix", "/v1") if isinstance(CONFIG, dict) else "/v1"


def register_routes(flask_app: Flask):
    """
    Register all API routes with the Flask application.

    Args:
        flask_app: The Flask application instance
    """
    # Auth endpoints
    @flask_app.route(f"{API_PREFIX}/auth/login", methods=['POST'])
    @request_logger
    def flask_login_with_email():
        return login_with_email(request)

    @flask_app.route(f"{API_PREFIX}/auth/register", methods=['POST'])
    @request_logger
    def flask_register():
        return register(request)

    @flask_app.route(f"{API_PREFIX}/auth/me", methods=['GET'])
    @request_logger
    @require_auth
    def flask_get_user_profile():
        return get_user_profile(request)

    @flask_app.route(f"{API_PREFIX}/auth/token", methods=['POST'])
    @request_logger
    def flask_login_with_custom_token():
        return login_with_custom_token(request)

    # User endpoints
    @flask_app.route(f"{API_PREFIX}/users", methods=['GET'])
    @request_logger
    @require_auth
    def flask_get_users():
        return get_users(request)

    @flask_app.route(f"{API_PREFIX}/users/<user_id>", methods=['GET'])
    @request_logger
    @require_auth
    def flask_get_user():
        return get_user(request)

    @flask_app.route(f"{API_PREFIX}/users", methods=['POST'])
    @request_logger
    @require_auth
    def flask_create_user():
        return create_user(request)

    @flask_app.route(f"{API_PREFIX}/users/<user_id>", methods=['PUT'])
    @request_logger
    @require_auth
    def flask_update_user():
        return update_user(request)

    @flask_app.route(f"{API_PREFIX}/users", methods=['DELETE'])
    @request_logger
    @require_auth
    def flask_delete_current_user():
        return delete_user(request)

    @flask_app.route(f"{API_PREFIX}/users/<user_id>", methods=['DELETE'])
    @request_logger
    @require_auth
    def flask_delete_user():
        return delete_user(request)

    @flask_app.route(f"{API_PREFIX}/users/<user_id>/onboarding", methods=['POST'])
    @request_logger
    @require_auth
    def flask_update_onboarding():
        return update_onboarding(request)
        
    @flask_app.route(f"{API_PREFIX}/users/photo", methods=['POST'])
    @request_logger
    @require_auth
    def flask_update_user_photo():
        return update_user_photo(request)

    # Notification endpoints
    @flask_app.route(f"{API_PREFIX}/notifications", methods=['GET'])
    @request_logger
    @require_auth
    def flask_get_notifications():
        return get_notifications(request)

    @flask_app.route(f"{API_PREFIX}/notifications/unread", methods=['GET'])
    @request_logger
    @require_auth
    def flask_get_unread_count():
        return get_unread_count(request)

    @flask_app.route(f"{API_PREFIX}/notifications/<notification_id>/read", methods=['POST'])
    @request_logger
    @require_auth
    def flask_mark_as_read():
        return mark_as_read(request)

    @flask_app.route(f"{API_PREFIX}/notifications/read-all", methods=['POST'])
    @request_logger
    @require_auth
    def flask_mark_all_as_read():
        return mark_all_as_read(request)

    @flask_app.route(f"{API_PREFIX}/notifications/<notification_id>", methods=['DELETE'])
    @request_logger
    @require_auth
    def flask_delete_notification():
        return delete_notification(request)

    @flask_app.route(f"{API_PREFIX}/devices", methods=['POST'])
    @request_logger
    @require_auth
    def flask_register_device():
        return register_device(request)

    @flask_app.route(f"{API_PREFIX}/devices/<device_id>", methods=['DELETE'])
    @request_logger
    @require_auth
    def flask_unregister_device():
        return unregister_device(request)

    # Password management endpoints
    @flask_app.route(f"{API_PREFIX}/password/reset-request", methods=['POST'])
    @request_logger
    def flask_request_reset():
        return request_reset(request)
        
    @flask_app.route(f"{API_PREFIX}/password/reset", methods=['POST'])
    @request_logger
    def flask_reset_password():
        return reset_password(request)
        
    @flask_app.route(f"{API_PREFIX}/password/change", methods=['POST'])
    @request_logger
    @require_auth
    def flask_change_password():
        return change_password(request)

    # Error handling
    @flask_app.errorhandler(404)
    def page_not_found(e):
        from utils.helpers import create_response
        return create_response(
            data=None,
            message="Endpoint not found",
            error="Not Found",
            status=404
        )

    @flask_app.errorhandler(500)
    def server_error(e):
        from utils.helpers import create_response
        return create_response(
            data=None,
            message="Internal server error",
            error=str(e),
            status=500
        )
"""Password management API endpoints."""
from flask import Request
from firebase_admin.exceptions import FirebaseError

from services.password_service import PasswordService
from utils.helpers import create_response, get_user_id_from_request
from utils.logging import setup_logger

logger = setup_logger("api_password")

# Initialize password service
password_service = PasswordService()


async def request_reset(request: Request):
    """
    Request a password reset.

    Request body:
    - email: Email address to send reset link to
    - reset_base_url: Base URL for the password reset link (optional)
    """
    try:
        data = request.get_json()

        email = data.get('email')
        if not email:
            return create_response(
                data=None,
                message='Email is required',
                error='Missing email',
                status=400
            )

        # Get reset base URL from request or use default
        reset_base_url = data.get('reset_base_url', 'https://app.plek.com/reset-password')

        # Request password reset
        success, message = await password_service.request_password_reset(email, reset_base_url)

        if success:
            return create_response(
                data={'email': email},
                message=message
            )
        return create_response(
            data=None,
            message=message,
            error='Failed to process request',
            status=400
        )

    except (TypeError, KeyError) as e:
        logger.error("Invalid request data: %s", str(e))
        return create_response(
            data=None,
            message='Invalid request data',
            error=str(e),
            status=400
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Error requesting password reset: %s", str(e))
        return create_response(
            data=None,
            message='Failed to request password reset',
            error=str(e),
            status=500
        )


async def reset_password(request: Request):
    """
    Reset password using a reset token.

    Request body:
    - token: Password reset token
    - new_password: New password
    """
    try:
        data = request.get_json()

        token = data.get('token')
        new_password = data.get('new_password')

        if not token:
            return create_response(
                data=None,
                message='Reset token is required',
                error='Missing token',
                status=400
            )

        if not new_password:
            return create_response(
                data=None,
                message='New password is required',
                error='Missing new_password',
                status=400
            )

        # Validate password strength
        is_valid, error_msg = password_service.validate_password_strength(new_password)
        if not is_valid:
            return create_response(
                data=None,
                message=error_msg,
                error='Invalid password',
                status=400
            )

        # Reset password
        success, message = await password_service.reset_password(token, new_password)

        if success:
            return create_response(
                data={'success': True},
                message=message
            )
        return create_response(
            data=None,
            message=message,
            error='Failed to reset password',
            status=400
        )

    except (TypeError, KeyError) as e:
        logger.error("Invalid request data: %s", str(e))
        return create_response(
            data=None,
            message='Invalid request data',
            error=str(e),
            status=400
        )
    except (FirebaseError, ConnectionError) as e:
        logger.error("Error resetting password: %s", str(e))
        return create_response(
            data=None,
            message='Failed to reset password',
            error=str(e),
            status=500
        )


async def change_password(request: Request):
    """
    Change password for authenticated user.

    Request body:
    - current_password: Current password
    - new_password: New password
    """
    try:
        user_id = get_user_id_from_request(request)
        data = request.get_json()

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password:
            return create_response(
                data=None,
                message='Current password is required',
                error='Missing current_password',
                status=400
            )

        if not new_password:
            return create_response(
                data=None,
                message='New password is required',
                error='Missing new_password',
                status=400
            )

        # Validate password strength
        is_valid, error_msg = password_service.validate_password_strength(new_password)
        if not is_valid:
            return create_response(
                data=None,
                message=error_msg,
                error='Invalid password',
                status=400
            )

        # Change password
        success, message = await password_service.change_password(
            user_id,
            current_password,
            new_password
        )

        if success:
            return create_response(
                data={'success': True},
                message=message
            )
        return create_response(
            data=None,
            message=message,
            error='Failed to change password',
            status=400
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
    except (FirebaseError, ConnectionError) as e:
        logger.error("Error changing password: %s", str(e))
        return create_response(
            data=None,
            message='Failed to change password',
            error=str(e),
            status=500
        )

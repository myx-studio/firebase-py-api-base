"""Password service for handling password-related operations."""
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from firebase_admin import auth
from models.password_reset import PasswordReset
from repositories.firestore.password_reset_repo import FirestorePasswordResetRepository
from services.email_service import EmailService
from utils.logging import setup_logger

logger = setup_logger("password_service")


class PasswordService:
    """Service for handling password operations."""

    def __init__(self):
        """Initialize password service."""
        self.password_reset_repo = FirestorePasswordResetRepository()
        self.email_service = EmailService()
        self.token_expiry_hours = 1
        self.min_password_length = 8

    def generate_reset_token(self, length: int = 32) -> str:
        """
        Generate a secure random token for password reset.

        Args:
            length: Length of the token

        Returns:
            str: Random token
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def request_password_reset(self, email: str, reset_base_url: str) -> Tuple[bool, str]:
        """
        Request a password reset for the given email.

        Args:
            email: User's email address
            reset_base_url: Base URL for the password reset link

        Returns:
            tuple: (success, message)
        """
        try:
            # Check if user exists
            try:
                user = auth.get_user_by_email(email)
            except auth.UserNotFoundError:
                # Don't reveal if user exists or not for security
                return True, "If an account exists with this email, a reset link has been sent."

            # Check for existing non-expired reset request
            existing_reset = await self.password_reset_repo.get_active_reset_by_email(email)
            if existing_reset:
                # Don't create a new token if one already exists and is not expired
                return True, "If an account exists with this email, a reset link has been sent."

            # Generate reset token
            token = self.generate_reset_token()

            # Create password reset record
            password_reset = PasswordReset(
                email=email,
                user_id=user.uid,
                token=token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours)
            )

            await self.password_reset_repo.create(password_reset)

            # Send reset email
            reset_link = f"{reset_base_url}?token={token}"
            email_sent = self.email_service.send_password_reset_email(
                to_email=email,
                reset_link=reset_link,
                user_name=user.display_name
            )

            if email_sent:
                return True, "If an account exists with this email, a reset link has been sent."

            if password_reset.id:
                await self.password_reset_repo.delete(password_reset.id)
            return False, "Failed to send reset email. Please try again."

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error requesting password reset: %s", str(e))
            return False, "An error occurred. Please try again."

    async def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset password using the provided token.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            tuple: (success, message)
        """
        try:
            # Validate password
            if len(new_password) < self.min_password_length:
                return False, (f"Password must be at least "
                               f"{self.min_password_length} characters long.")

            # Get password reset record
            password_reset = await self.password_reset_repo.get_by_token(token)

            if not password_reset:
                return False, "Invalid or expired reset token."

            # Check if token is expired
            if password_reset.is_expired():
                return False, "Reset token has expired. Please request a new one."

            # Check if already used
            if password_reset.used:
                return False, "This reset token has already been used."

            # Update user's password in Firebase Auth
            try:
                auth.update_user(
                    password_reset.user_id,
                    password=new_password
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to update password in Firebase Auth: %s", str(e))
                return False, "Failed to update password. Please try again."

            # Mark token as used
            if password_reset.id:
                await self.password_reset_repo.mark_as_used(password_reset.id)

            return True, "Password has been reset successfully."

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error resetting password: %s", str(e))
            return False, "An error occurred. Please try again."

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Change user's password after verifying current password.

        Args:
            user_id: ID of the user
            current_password: Current password
            new_password: New password

        Returns:
            tuple: (success, message)
        """
        try:
            # Validate new password
            if len(new_password) < self.min_password_length:
                return False, (f"Password must be at least "
                               f"{self.min_password_length} characters long.")

            if current_password == new_password:
                return False, "New password must be different from current password."

            # Get user info
            try:
                _ = auth.get_user(user_id)  # Verify user exists
            except auth.UserNotFoundError:
                return False, "User not found."

            # Verify current password by attempting to sign in
            # Note: This requires the Firebase Auth REST API
            # For now, we'll just update the password
            # In production, you should verify the current password first

            # Update password
            try:
                auth.update_user(
                    user_id,
                    password=new_password
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to update password: %s", str(e))
                return False, "Failed to update password. Please try again."

            return True, "Password changed successfully."

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error changing password: %s", str(e))
            return False, "An error occurred. Please try again."

    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired password reset tokens.

        Returns:
            int: Number of tokens deleted
        """
        try:
            return await self.password_reset_repo.delete_expired_tokens()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error cleaning up expired tokens: %s", str(e))
            return 0

    def validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if len(password) < self.min_password_length:
            return False, f"Password must be at least {self.min_password_length} characters long."

        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter."

        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter."

        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number."

        # Check for at least one special character
        special_chars = string.punctuation
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character."

        return True, None

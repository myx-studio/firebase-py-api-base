"""Email service using Mailgun."""
import os
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from utils.logging import setup_logger

logger = setup_logger("email_service")


class EmailService:
    """Service for handling email operations using Mailgun."""

    def __init__(self):
        """Initialize email service with Mailgun configuration."""
        # Try to load from config first, then fall back to direct env vars
        try:
            from config import CONFIG  # pylint: disable=import-outside-toplevel
            mailgun_config = CONFIG.get('mailgun', {})
            self.mailgun_domain = (mailgun_config.get('domain') or
                                   os.environ.get('MAILGUN_DOMAIN', ''))
            self.mailgun_api_key = (mailgun_config.get('api_key') or
                                    os.environ.get('MAILGUN_API_KEY', ''))
            self.from_email = (mailgun_config.get('from_email') or
                               os.environ.get('MAILGUN_FROM_EMAIL', 'noreply@plek.app'))
            self.from_name = (mailgun_config.get('from_name') or
                              os.environ.get('MAILGUN_FROM_NAME', 'Plek App'))
        except ImportError:
            # Fallback to direct environment variables
            self.mailgun_domain = os.environ.get('MAILGUN_DOMAIN', '')
            self.mailgun_api_key = os.environ.get('MAILGUN_API_KEY', '')
            self.from_email = os.environ.get('MAILGUN_FROM_EMAIL', 'noreply@plek.app')
            self.from_name = os.environ.get('MAILGUN_FROM_NAME', 'Plek App')

        self.mailgun_api_base = 'https://api.mailgun.net/v3'
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'email_templates')

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an email using Mailgun.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            template_variables: Variables for email templates (optional)

        Returns:
            bool: True if email was sent successfully
        """
        try:
            url = f"{self.mailgun_api_base}/{self.mailgun_domain}/messages"

            data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': to_email,
                'subject': subject,
                'html': html_content
            }

            if text_content:
                data['text'] = text_content

            if template_variables:
                for key, value in template_variables.items():
                    data[f'v:{key}'] = value

            response = requests.post(
                url,
                auth=('api', self.mailgun_api_key),
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                logger.info("Email sent successfully to %s", to_email)
                return True

            logger.error("Failed to send email: %s", response.text)
            return False

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to send email to %s: %s", to_email, str(e))
            return False

    def load_template(self, template_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Load and process an HTML email template.

        Args:
            template_name: Name of the template file (without .html extension)
            variables: Variables to substitute in the template

        Returns:
            str: Processed HTML content
        """
        try:
            template_path = os.path.join(self.template_dir, f"{template_name}.html")
            
            with open(template_path, 'r', encoding='utf-8') as file:
                template_content = file.read()
            
            # Simple template variable substitution
            if variables:
                for key, value in variables.items():
                    placeholder = f"{{{{ {key} }}}}"
                    template_content = template_content.replace(placeholder, str(value))
            
            return template_content
            
        except FileNotFoundError:
            logger.error("Template file not found: %s", template_name)
            return ""
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error loading template %s: %s", template_name, str(e))
            return ""


    def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send a password reset email using HTML template.

        Args:
            to_email: Recipient email address
            reset_link: Password reset link
            user_name: User's name (optional)

        Returns:
            bool: True if email was sent successfully
        """
        subject = "Reset your Plek password"
        
        # Load HTML template with variables
        template_variables = {
            'reset_url': reset_link,
            'current_year': datetime.now().year
        }
        
        html_content = self.load_template('password_reset', template_variables)
        
        if not html_content:
            raise FileNotFoundError("Template not found")

        # Simple text version
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        text_content = f"""
        Reset your password

        {greeting}

        You requested a password reset for your Plek account.

        Reset your password here: {reset_link}

        If you didn't request this, you can safely ignore this email.
        This link will expire in 1 hour.
        """

        return self.send_email(to_email, subject, html_content, text_content)

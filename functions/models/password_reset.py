"""Password reset model."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PasswordReset:
    """Password reset data model."""

    email: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    used: bool = False
    used_at: Optional[datetime] = None
    id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert password reset to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': (
                self.expires_at.isoformat()
                if isinstance(self.expires_at, datetime)
                else self.expires_at
            ),
            'created_at': (
                self.created_at.isoformat()
                if isinstance(self.created_at, datetime)
                else self.created_at
            ),
            'used': self.used,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordReset':
        """Create password reset from dictionary."""
        # Parse datetime strings
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)

        expires_at = data.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        elif not isinstance(expires_at, datetime):
            expires_at = datetime.now(timezone.utc)

        used_at = data.get('used_at')
        if isinstance(used_at, str):
            used_at = datetime.fromisoformat(used_at.replace('Z', '+00:00'))

        return cls(
            id=data.get('id'),
            email=data.get('email') or '',
            user_id=data.get('user_id') or '',
            token=data.get('token') or '',
            expires_at=expires_at,
            created_at=created_at,
            used=data.get('used', False),
            used_at=used_at
        )

    def is_expired(self) -> bool:
        """Check if the reset token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def mark_as_used(self) -> None:
        """Mark the reset token as used."""
        self.used = True
        self.used_at = datetime.now(timezone.utc)

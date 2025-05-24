"""Notification model."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class Notification:
    """Notification data model."""

    user_id: str
    title: str
    body: str
    type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
    read_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    action_url: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'body': self.body,
            'type': self.type,
            'created_at': (
                self.created_at.isoformat()
                if isinstance(self.created_at, datetime)
                else self.created_at
            ),
            'read': self.read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'data': self.data,
            'action_url': self.action_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary."""
        # Parse datetime strings
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)

        read_at = data.get('read_at')
        if isinstance(read_at, str):
            read_at = datetime.fromisoformat(read_at.replace('Z', '+00:00'))

        return cls(
            id=data.get('id'),
            user_id=data.get('user_id') or '',
            title=data.get('title') or '',
            body=data.get('body') or '',
            type=data.get('type') or '',
            created_at=created_at,
            read=data.get('read', False),
            read_at=read_at,
            data=data.get('data', {}),
            action_url=data.get('action_url')
        )

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.read = True
        self.read_at = datetime.now(timezone.utc)

    def is_unread(self) -> bool:
        """Check if notification is unread."""
        return not self.read

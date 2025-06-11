from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """
    Represents a user in the system.
    
    Attributes:
        id (str): Unique identifier for the user
        email (str): User's email address
        role (str): User's role (admin, staff, etc.)
        name (str): User's full name
        created_at (datetime): When the user was created
        last_login (Optional[datetime]): Last login timestamp
        is_active (bool): Whether the user account is active
    """
    id: str
    email: str
    role: str
    name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create a User instance from a dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_login'):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert User instance to a dictionary for Firebase storage."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        } 
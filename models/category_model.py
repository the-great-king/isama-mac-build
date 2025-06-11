from dataclasses import dataclass
from datetime import datetime

@dataclass
class Category:
    """
    Represents a product category.
    
    Attributes:
        id (str): Unique identifier for the category
        name (str): Category name
        description (str): Optional description of the category
        created_at (datetime): When the category was created
        is_active (bool): Whether the category is active
    """
    id: str
    name: str
    description: str
    created_at: datetime
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert Category instance to a dictionary for Firebase storage."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Category':
        """Create a Category instance from a dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data) 
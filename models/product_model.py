from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

@dataclass
class StockUpdate:
    """
    Represents a stock update event.
    
    Attributes:
        quantity (int): Amount added or removed
        date (datetime): When the update occurred
        type (str): Type of update (initial, restock, adjustment)
        updated_by (str): User ID who made the update
        notes (Optional[str]): Additional notes about the update
    """
    quantity: int
    date: datetime
    type: str
    updated_by: str
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'quantity': self.quantity,
            'date': self.date.isoformat(),
            'type': self.type,
            'updated_by': self.updated_by,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StockUpdate':
        data['date'] = datetime.fromisoformat(data['date'])
        return cls(**data)

@dataclass
class Product:
    """
    Represents a product in the inventory.
    
    Attributes:
        id (str): Unique identifier for the product
        name (str): Product name
        category (str): Product category name shown to users
        category_id (Optional[str]): Firebase category ID used internally
        price (Decimal): Current selling price
        stock (int): Current stock level
        min_stock (int): Minimum stock level for alerts
        created_at (datetime): When the product was created
        stock_updates (List[StockUpdate]): History of stock updates
        is_active (bool): Whether the product is active in the system
    """
    id: str
    name: str
    category: str
    price: Decimal
    stock: int
    min_stock: int
    created_at: datetime
    stock_updates: List[StockUpdate]
    is_active: bool = True
    category_id: Optional[str] = None

    def add_stock_update(self, quantity: int, update_type: str, updated_by: str, notes: Optional[str] = None):
        """Add a new stock update record."""
        update = StockUpdate(
            quantity=quantity,
            date=datetime.now(),
            type=update_type,
            updated_by=updated_by,
            notes=notes
        )
        self.stock_updates.append(update)
        self.stock += quantity

    def to_dict(self) -> dict:
        """Convert Product instance to a dictionary for Firebase storage."""
        data = {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': str(self.price),  # Convert Decimal to string for Firebase
            'stock': self.stock,
            'min_stock': self.min_stock,
            'created_at': self.created_at.isoformat(),
            'stock_updates': [update.to_dict() for update in self.stock_updates],
            'is_active': self.is_active
        }
        if self.category_id is not None:
            data['category_id'] = self.category_id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """Create a Product instance from a dictionary."""
        data['price'] = Decimal(data['price'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['stock_updates'] = [
            StockUpdate.from_dict(update) for update in data['stock_updates']
        ]
        return cls(**data) 
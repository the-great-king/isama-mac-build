from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from .product_model import Product

@dataclass
class TransactionItem:
    """
    Represents an item in a transaction.
    
    Attributes:
        product_id (str): ID of the product sold
        quantity (int): Quantity sold
        price_per_unit (Decimal): Price per unit at time of sale
        total (Decimal): Total price for this item
    """
    product_id: str
    quantity: int
    price_per_unit: Decimal
    total: Decimal

    def to_dict(self) -> dict:
        return {
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price_per_unit': str(self.price_per_unit),
            'total': str(self.total)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TransactionItem':
        data['price_per_unit'] = Decimal(data['price_per_unit'])
        data['total'] = Decimal(data['total'])
        return cls(**data)

@dataclass
class Transaction:
    """
    Represents a sales transaction.
    
    Attributes:
        id (str): Unique identifier for the transaction
        items (List[TransactionItem]): Items sold in this transaction
        total_amount (Decimal): Total transaction amount
        transaction_date (datetime): When the transaction occurred
        transaction_type (str): Type of transaction (cash/loan)
        status (str): Transaction status (completed/pending/cancelled)
        created_by (str): User ID who created the transaction
        buyer_name (Optional[str]): Name of the buyer (required for loans)
        buyer_contact (Optional[str]): Contact info of the buyer
        due_date (Optional[datetime]): When the loan is due
        payment_status (Optional[str]): For loans: paid/unpaid/partial
        amount_paid (Optional[Decimal]): Amount paid so far (for loans)
        notes (Optional[str]): Additional transaction notes
    """
    id: str
    items: List[TransactionItem]
    total_amount: Decimal
    transaction_date: datetime
    transaction_type: str  # 'cash' or 'loan'
    status: str  # 'completed', 'pending', 'cancelled'
    created_by: str
    buyer_name: Optional[str] = None
    buyer_contact: Optional[str] = None
    due_date: Optional[datetime] = None
    payment_status: Optional[str] = None  # 'paid', 'unpaid', 'partial'
    amount_paid: Optional[Decimal] = None
    notes: Optional[str] = None

    def add_payment(self, amount: Decimal) -> None:
        """Add a payment to a loan transaction."""
        if self.transaction_type != 'loan':
            raise ValueError("Can only add payments to loan transactions")
        
        if self.amount_paid is None:
            self.amount_paid = Decimal('0')
        
        self.amount_paid += amount
        
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        else:
            self.payment_status = 'partial'

    def to_dict(self) -> dict:
        """Convert Transaction instance to a dictionary for Firebase storage."""
        data = {
            'id': self.id,
            'items': [item.to_dict() for item in self.items],
            'total_amount': str(self.total_amount),
            'transaction_date': self.transaction_date.isoformat(),
            'transaction_type': self.transaction_type,
            'status': self.status,
            'created_by': self.created_by,
        }
        
        # Add optional fields if they exist
        if self.buyer_name:
            data['buyer_name'] = self.buyer_name
        if self.buyer_contact:
            data['buyer_contact'] = self.buyer_contact
        if self.due_date:
            data['due_date'] = self.due_date.isoformat()
        if self.payment_status:
            data['payment_status'] = self.payment_status
        if self.amount_paid is not None:
            data['amount_paid'] = str(self.amount_paid)
        if self.notes:
            data['notes'] = self.notes
            
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create a Transaction instance from a dictionary."""
        # Convert string amounts to Decimal
        data['total_amount'] = Decimal(data['total_amount'])
        if data.get('amount_paid'):
            data['amount_paid'] = Decimal(data['amount_paid'])
            
        # Convert date strings to datetime
        data['transaction_date'] = datetime.fromisoformat(data['transaction_date'])
        if data.get('due_date'):
            data['due_date'] = datetime.fromisoformat(data['due_date'])
            
        # Convert items to TransactionItem objects
        data['items'] = [TransactionItem.from_dict(item) for item in data['items']]
        
        return cls(**data) 
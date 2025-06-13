from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any, Dict
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
class PaymentRecord:
    """
    Represents a payment record for a loan transaction.
    
    Attributes:
        amount (Decimal): Amount paid
        date (datetime): Date of payment
        created_by (str): User ID who recorded the payment
    """
    amount: Decimal
    date: datetime
    created_by: str

    def to_dict(self) -> dict:
        return {
            'amount': str(self.amount),
            'date': self.date.isoformat(),
            'created_by': self.created_by
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PaymentRecord':
        return cls(
            amount=Decimal(data['amount']),
            date=datetime.fromisoformat(data['date']),
            created_by=data['created_by']
        )

@dataclass
class Transaction:
    """Model representing a sales transaction."""
    
    id: str
    transaction_type: str  # 'cash' or 'loan'
    transaction_date: datetime
    total_amount: Decimal
    created_by: str
    items: List[TransactionItem]  # Now required again
    buyer_name: Optional[str] = None  # Optional - if None, it's a one-time client
    description: Optional[str] = None  # Optional - additional notes about the transaction
    buyer_contact: Optional[str] = None  # Required for loans only
    due_date: Optional[datetime] = None  # Required for loans only
    payment_status: Optional[str] = None  # Required for loans only: 'unpaid', 'partial', 'paid'
    amount_paid: Optional[Decimal] = None  # Required for loans only
    payment_history: Optional[List[PaymentRecord]] = None  # Payment history for loans
    status: Optional[str] = None  # For backward compatibility
    
    def to_dict(self) -> dict:
        """Convert the transaction to a dictionary."""
        data = {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat(),
            'total_amount': str(self.total_amount),
            'created_by': self.created_by,
            'items': [
                item.to_dict() if hasattr(item, 'to_dict') else item
                for item in self.items
            ]
        }
        
        # Add optional fields only if they have values
        if self.buyer_name is not None:
            data['buyer_name'] = self.buyer_name
            
        if self.description is not None:
            data['description'] = self.description
            
        if self.buyer_contact is not None:
            data['buyer_contact'] = self.buyer_contact
            
        if self.due_date is not None:
            data['due_date'] = self.due_date.isoformat()
            
        if self.payment_status is not None:
            data['payment_status'] = self.payment_status
            
        if self.amount_paid is not None:
            data['amount_paid'] = str(self.amount_paid)

        if self.payment_history:
            # Convert each payment record to dict, handling both PaymentRecord objects and dicts
            payment_records = []
            for payment in self.payment_history:
                if isinstance(payment, dict):
                    payment_records.append(payment)
                elif isinstance(payment, PaymentRecord):
                    payment_records.append(payment.to_dict())
                else:
                    print(f"Warning: Unknown payment record type: {type(payment)}")
            data['payment_history'] = payment_records
            
        # Add legacy status if it exists
        if self.status is not None:
            data['status'] = self.status
            
        return data
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create a Transaction instance from a dictionary."""
        try:
            # Handle required fields
            id = data['id']
            transaction_type = data['transaction_type']
            transaction_date = datetime.fromisoformat(data['transaction_date'])
            total_amount = Decimal(str(data['total_amount']))
            created_by = data['created_by']
            
            # Handle items - for backward compatibility and malformed data
            items_data = data.get('items', [])
            if not isinstance(items_data, list):
                items_data = []
                
            if not items_data and 'total_amount' in data:
                # Create a dummy item for old transactions
                items_data = [{
                    'product_id': 'legacy_transaction',
                    'quantity': 1,
                    'price_per_unit': str(data['total_amount']),
                    'total': str(data['total_amount'])
                }]
            
            # Convert items data to TransactionItem objects, skip malformed items
            items = []
            for item in items_data:
                try:
                    if isinstance(item, dict):
                        items.append(TransactionItem.from_dict(item))
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Error parsing item in transaction {id}: {e}")
                    continue
            
            # If no valid items were parsed, create a dummy item
            if not items:
                items = [TransactionItem(
                    product_id='legacy_transaction',
                    quantity=1,
                    price_per_unit=total_amount,
                    total=total_amount
                )]
            
            # Handle optional fields with defaults
            buyer_name = data.get('buyer_name')  # None means one-time client
            description = data.get('description')  # None means no description
            buyer_contact = data.get('buyer_contact')
            due_date = datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
            payment_status = data.get('payment_status')
            amount_paid = Decimal(str(data['amount_paid'])) if data.get('amount_paid') else None
            status = data.get('status')  # Keep status for backward compatibility

            # Handle payment history
            payment_history = None
            if data.get('payment_history'):
                try:
                    payment_history = [
                        PaymentRecord.from_dict(payment) 
                        for payment in data['payment_history']
                    ]
                except Exception as e:
                    print(f"Error parsing payment history for transaction {id}: {e}")
            
            # For loan transactions, buyer_name is required
            if transaction_type == 'loan' and not buyer_name:
                raise ValueError("Buyer name is required for loan transactions")
            
            return cls(
                id=id,
                transaction_type=transaction_type,
                transaction_date=transaction_date,
                total_amount=total_amount,
                created_by=created_by,
                items=items,
                buyer_name=buyer_name,
                description=description,
                buyer_contact=buyer_contact,
                due_date=due_date,
                payment_status=payment_status,
                amount_paid=amount_paid,
                payment_history=payment_history,
                status=status
            )
            
        except KeyError as e:
            print(f"Missing required field in transaction {data.get('id', 'unknown')}: {e}")
            raise
        except ValueError as e:
            print(f"Error parsing transaction {data.get('id', 'unknown')}: {e}")
            raise
            
    @property
    def display_name(self) -> str:
        """Get the display name for the buyer."""
        return self.buyer_name or "One-time Client"

    def add_payment(self, amount: Decimal, user_id: str) -> None:
        """Add a payment to a loan transaction."""
        if self.transaction_type != 'loan':
            raise ValueError("Can only add payments to loan transactions")
        
        if self.amount_paid is None:
            self.amount_paid = Decimal('0')
            self.payment_history = []
        
        # Add payment amount
        self.amount_paid += amount
        
        # Add payment record
        if self.payment_history is None:
            self.payment_history = []
        
        self.payment_history.append(PaymentRecord(
            amount=amount,
            date=datetime.now(),
            created_by=user_id
        ))
        
        # Update payment status
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        else:
            self.payment_status = 'partial'

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
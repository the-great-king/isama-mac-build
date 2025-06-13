from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from enum import Enum

class CashTransactionType(Enum):
    """Types of cash transactions"""
    SALE = "sale"
    LOAN_REPAYMENT_IN = "loan_repayment_in"  # When customer pays back
    LOAN_REPAYMENT_OUT = "loan_repayment_out"  # When business pays back
    DEPOSIT = "deposit"  # Cash injection into business
    EXPENSE = "expense"
    LOAN_IN = "loan_in"  # When business receives a loan
    LOAN_OUT = "loan_out"  # When business gives a loan

class ExpenseCategory(Enum):
    """Categories of business expenses"""
    SALARY = "salary"
    UTILITIES = "utilities"
    RENT = "rent"
    SUPPLIES = "supplies"
    TRANSPORT = "transport"
    MAINTENANCE = "maintenance"
    OTHER = "other"

@dataclass
class CashTransaction:
    """
    Represents a cash transaction in the business.
    
    Attributes:
        id (str): Unique identifier
        type (CashTransactionType): Type of transaction
        amount (Decimal): Transaction amount
        date (datetime): When the transaction occurred
        description (str): Transaction description
        created_by (str): User ID who created the transaction
        reference_id (Optional[str]): ID of related transaction (e.g., sale ID)
        category (Optional[str]): Category for expenses
        notes (Optional[str]): Additional notes
    """
    id: str
    type: CashTransactionType
    amount: Decimal
    date: datetime
    description: str
    created_by: str
    reference_id: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for Firebase storage."""
        data = {
            'id': self.id,
            'type': self.type.value,
            'amount': str(self.amount),
            'date': self.date.isoformat(),
            'description': self.description,
            'created_by': self.created_by
        }
        if self.reference_id:
            data['reference_id'] = self.reference_id
        if self.category:
            data['category'] = self.category
        if self.notes:
            data['notes'] = self.notes
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'CashTransaction':
        """Create instance from dictionary."""
        # Convert string amount to Decimal
        data['amount'] = Decimal(data['amount'])
        # Convert string date to datetime
        data['date'] = datetime.fromisoformat(data['date'])
        # Convert string type to enum
        data['type'] = CashTransactionType(data['type'])
        return cls(**data)

@dataclass
class BusinessLoan:
    """
    Represents a loan taken or given by the business.
    
    Attributes:
        id (str): Unique identifier
        is_cash_loan (bool): Whether it's a cash loan or item-based
        amount (Decimal): Loan amount (for cash loans)
        items (List[Dict]): List of items (for item-based loans)
        date_taken (datetime): When the loan was taken
        due_date (datetime): When the loan is due
        lender_name (str): Name of the lender
        lender_contact (str): Contact info of the lender
        is_business_borrower (bool): True if business took the loan, False if business gave the loan
        payment_status (str): paid/unpaid/partial
        amount_paid (Decimal): Amount paid so far
        created_by (str): User ID who created the record
        notes (Optional[str]): Additional notes
    """
    id: str
    is_cash_loan: bool
    date_taken: datetime
    due_date: datetime
    lender_name: str
    lender_contact: str
    is_business_borrower: bool
    payment_status: str
    created_by: str
    amount: Optional[Decimal] = None
    items: Optional[List[Dict]] = None
    amount_paid: Optional[Decimal] = None
    notes: Optional[str] = None

    def add_payment(self, amount: Decimal) -> None:
        """Add a payment to the loan."""
        if self.amount_paid is None:
            self.amount_paid = Decimal('0')
        
        self.amount_paid += amount
        
        if self.is_cash_loan:
            total_amount = self.amount
        else:
            total_amount = sum(Decimal(str(item['value'])) for item in self.items)
        
        if self.amount_paid >= total_amount:
            self.payment_status = 'paid'
        else:
            self.payment_status = 'partial'

    def to_dict(self) -> dict:
        """Convert to dictionary for Firebase storage."""
        data = {
            'id': self.id,
            'is_cash_loan': self.is_cash_loan,
            'date_taken': self.date_taken.isoformat(),
            'due_date': self.due_date.isoformat(),
            'lender_name': self.lender_name,
            'lender_contact': self.lender_contact,
            'is_business_borrower': self.is_business_borrower,
            'payment_status': self.payment_status,
            'created_by': self.created_by
        }
        
        if self.amount is not None:
            data['amount'] = str(self.amount)
        if self.items is not None:
            data['items'] = self.items
        if self.amount_paid is not None:
            data['amount_paid'] = str(self.amount_paid)
        if self.notes:
            data['notes'] = self.notes
            
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'BusinessLoan':
        """Create instance from dictionary."""
        # Convert string amounts to Decimal
        if data.get('amount'):
            data['amount'] = Decimal(data['amount'])
        if data.get('amount_paid'):
            data['amount_paid'] = Decimal(data['amount_paid'])
            
        # Convert date strings to datetime
        data['date_taken'] = datetime.fromisoformat(data['date_taken'])
        data['due_date'] = datetime.fromisoformat(data['due_date'])
        
        return cls(**data) 
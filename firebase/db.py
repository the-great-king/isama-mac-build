import os
import requests
import firebase_admin
from firebase_admin import credentials, db, auth
from dotenv import load_dotenv
from .web_config import SIGN_IN_URL
from models.transaction_model import Transaction
from models.cash_model import CashTransaction, BusinessLoan, CashTransactionType
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from google.cloud import firestore

# Load environment variables
load_dotenv()

class FirebaseManager:
    """
    Manages Firebase connections and operations for the Isama Management System.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize Firebase connection using service account credentials.
        
        IMPORTANT: Before running the application:
        1. Download your Firebase service account key JSON file
        2. Place it in the /firebase directory as 'service_Key.json'
        """
        try:
            # Initialize Firebase Admin SDK
            cred_path = os.path.join(os.path.dirname(__file__), 'service_key.json')
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
            })
            self.db = db
            self.auth = auth
            
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            raise

    def sign_in_with_email_password(self, email, password):
        """Sign in user with email and password using Firebase REST API."""
        try:
            # Prepare the request payload
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            # Make the REST API call
            response = requests.post(SIGN_IN_URL, json=payload)
            
            if response.status_code == 200:
                # Get the ID token and user data
                auth_data = response.json()
                id_token = auth_data["idToken"]
                
                # Get additional user info from Admin SDK
                user = self.auth.get_user_by_email(email)
                
                # Return both the token and user data
                return {
                    "id_token": id_token,
                    "user": user
                }
            else:
                error_message = response.json().get("error", {}).get("message", "Unknown error")
                raise ValueError(f"Authentication failed: {error_message}")
                
        except requests.RequestException as e:
            raise ValueError(f"Network error during authentication: {str(e)}")
        except Exception as e:
            raise ValueError(f"Authentication error: {str(e)}")

    def get_user_by_email(self, email):
        """Get user data from Firebase Auth by email."""
        try:
            return self.auth.get_user_by_email(email)
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def verify_id_token(self, id_token):
        """Verify Firebase ID token."""
        try:
            return self.auth.verify_id_token(id_token)
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None

    def get_database_reference(self, path):
        """Get a database reference for the specified path."""
        return self.db.reference(path)

    def get_transactions(self) -> List[Transaction]:
        """Get all transactions from Firebase."""
        try:
            transactions_ref = self.get_database_reference('transactions')
            transactions_data = transactions_ref.get() or {}
            
            transactions = []
            for tid, data in transactions_data.items():
                try:
                    if not isinstance(data, dict):
                        print(f"Invalid transaction data format for {tid}")
                        continue
                        
                    # Add ID to data
                    data['id'] = tid
                    
                    # Create transaction object
                    transaction = Transaction.from_dict(data)
                    transactions.append(transaction)
                    
                except Exception as e:
                    print(f"Error parsing transaction {tid}: {e}")
                    continue
                    
            return sorted(transactions, key=lambda t: t.transaction_date, reverse=True)
            
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []

    def get_cash_transactions(self):
        """Get all cash transactions from Firebase."""
        try:
            transactions_ref = self.get_database_reference('cash_transactions')
            transactions_data = transactions_ref.get() or {}
            
            transactions = []
            for transaction_id, data in transactions_data.items():
                if isinstance(data, dict):
                    try:
                        data['id'] = transaction_id
                        transaction = CashTransaction.from_dict(data)
                        transactions.append(transaction)
                    except Exception as e:
                        print(f"Error parsing cash transaction {transaction_id}: {e}")
                        continue
            
            return transactions
            
        except Exception as e:
            print(f"Error getting cash transactions: {e}")
            raise

    def get_business_loans(self):
        """Get all business loans from Firebase."""
        try:
            loans_ref = self.get_database_reference('business_loans')
            loans_data = loans_ref.get() or {}
            
            loans = []
            for loan_id, data in loans_data.items():
                if isinstance(data, dict):
                    try:
                        data['id'] = loan_id
                        loan = BusinessLoan.from_dict(data)
                        loans.append(loan)
                    except Exception as e:
                        print(f"Error parsing business loan {loan_id}: {e}")
                        continue
            
            return loans
        except Exception as e:
            print(f"Error getting business loans: {e}")
            raise

    def get_cash_balance(self):
        """Calculate total cash balance from all transactions."""
        try:
            transactions = self.get_cash_transactions()
            
            balance = Decimal('0')
            for transaction in transactions:
                if transaction.type.value in [
                    'sale', 'loan_repayment_in', 'deposit', 'loan_in'
                ]:
                    balance += transaction.amount
                elif transaction.type.value in [
                    'expense', 'loan_repayment_out', 'loan_out'
                ]:
                    balance -= transaction.amount
            
            return balance
        except Exception as e:
            print(f"Error calculating cash balance: {e}")
            raise

    def add_cash_transaction(self, transaction: CashTransaction):
        """Add a new cash transaction to Firebase."""
        try:
            ref = self.get_database_reference('cash_transactions')
            if not transaction.id:
                transaction.id = ref.push().key
            ref.child(transaction.id).set(transaction.to_dict())
            return transaction
        except Exception as e:
            print(f"Error adding cash transaction: {e}")
            raise

    def add_transaction(self, transaction: Transaction) -> None:
        """Add a new transaction to the database."""
        try:
            # Validate transaction data
            if not transaction.items:
                raise ValueError("Transaction must have at least one item")
                
            # Convert transaction to dict
            transaction_data = transaction.to_dict()
            
            # Add transaction to transactions collection
            transactions_ref = self.get_database_reference('transactions')
            transactions_ref.child(transaction.id).set(transaction_data)
            
            # Update product stock
            for item in transaction.items:
                try:
                    product_ref = self.get_database_reference(f'products/{item.product_id}')
                    product_data = product_ref.get()
                    if product_data:
                        new_stock = product_data.get('stock', 0) - item.quantity
                        product_ref.update({'stock': new_stock})
                except Exception as e:
                    print(f"Error updating stock for product {item.product_id}: {e}")
                    # Continue with other items even if one fails
                    continue
                    
            # Only add cash to business for cash sales, not loan sales
            if transaction.transaction_type == 'cash':
                # Create description based on available information
                description = "Cash sale"
                if transaction.buyer_name:
                    description += f" to {transaction.buyer_name}"
                if transaction.description:
                    description += f" - {transaction.description}"
                
                cash_transaction = CashTransaction(
                    id=self.get_database_reference('cash_transactions').push().key,
                    type=CashTransactionType.SALE,
                    amount=transaction.total_amount,
                    date=transaction.transaction_date,
                    description=description,
                    created_by=transaction.created_by,
                    category='sales'
                )
                self.add_cash_transaction(cash_transaction)
                
        except Exception as e:
            print(f"Error adding transaction: {e}")
            raise
            
    def get_transaction(self, transaction_id: str) -> Transaction:
        """Get a single transaction by ID."""
        try:
            transaction_ref = self.get_database_reference(f'transactions/{transaction_id}')
            data = transaction_ref.get()
            
            if not data:
                return None
                
            # Add ID to data
            data['id'] = transaction_id
            
            # Create transaction object
            return Transaction.from_dict(data)
            
        except Exception as e:
            print(f"Error getting transaction {transaction_id}: {e}")
            return None
            
    def update_transaction(self, transaction: Transaction) -> None:
        """Update an existing transaction."""
        try:
            # Get old transaction data
            old_transaction = self.get_transaction(transaction.id)
            if not old_transaction:
                raise ValueError(f"Transaction {transaction.id} not found")
                
            # Update transaction in database
            transaction_data = transaction.to_dict()
            transactions_ref = self.get_database_reference('transactions')
            transactions_ref.child(transaction.id).update(transaction_data)
            
            # If this is a loan payment, add the money to business cash
            if (old_transaction.transaction_type == 'loan' and 
                transaction.amount_paid > (old_transaction.amount_paid or 0)):
                
                # Calculate the payment amount (handle None values)
                old_amount_paid = old_transaction.amount_paid or Decimal('0')
                payment_amount = transaction.amount_paid - old_amount_paid
                
                if payment_amount > 0:
                    cash_transaction = CashTransaction(
                        id=self.get_database_reference('cash_transactions').push().key,
                        type=CashTransactionType.LOAN_REPAYMENT_IN,
                        amount=payment_amount,
                        date=datetime.now(),
                        description=f"Loan payment from {transaction.buyer_name}",
                        created_by=transaction.created_by,
                        category='loan_payment'
                    )
                    self.add_cash_transaction(cash_transaction)
                    
        except Exception as e:
            print(f"Error updating transaction: {e}")
            raise
            
    def get_business_loan(self, loan_id: str) -> Optional[BusinessLoan]:
        """Get a single business loan by ID."""
        try:
            loan_ref = self.get_database_reference('business_loans').child(loan_id)
            loan_data = loan_ref.get()
            
            if loan_data:
                loan_data['id'] = loan_id
                return BusinessLoan.from_dict(loan_data)
            return None
            
        except Exception as e:
            print(f"Error getting business loan: {e}")
            raise

    def add_business_loan(self, loan: BusinessLoan) -> None:
        """Add a new business loan (money we borrow from others)."""
        try:
            # Add loan to business_loans collection
            loans_ref = self.get_database_reference('business_loans')
            loans_ref.child(loan.id).set(loan.to_dict())
            
            # Note: We don't add to cash balance when taking a loan
            # The loan amount will only affect cash when we pay it back
            
        except Exception as e:
            print(f"Error adding business loan: {e}")
            raise
            
    def update_business_loan(self, loan: BusinessLoan) -> None:
        """Update a business loan."""
        try:
            # Get old loan data
            old_loan = self.get_business_loan(loan.id)
            if not old_loan:
                raise ValueError(f"Business loan {loan.id} not found")
                
            # Update loan in database
            loans_ref = self.get_database_reference('business_loans')
            loans_ref.child(loan.id).update(loan.to_dict())
            
            # If this is a loan payment and we are the borrower, deduct from cash
            if loan.is_business_borrower and loan.amount_paid > (old_loan.amount_paid or 0):
                payment_amount = loan.amount_paid - (old_loan.amount_paid or 0)
                
                # Create a cash transaction to deduct the payment amount
                cash_transaction = CashTransaction(
                    id=self.get_database_reference('cash_transactions').push().key,
                    type=CashTransactionType.LOAN_REPAYMENT_OUT,
                    amount=payment_amount,
                    date=datetime.now(),
                    description=f"Loan payment to {loan.lender_name}",
                    created_by=loan.created_by,
                    category='loan_payment'
                )
                self.add_cash_transaction(cash_transaction)
                
        except Exception as e:
            print(f"Error updating business loan: {e}")
            raise

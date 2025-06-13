from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QMessageBox,
    QComboBox, QDateEdit, QTabWidget, QGridLayout, QFrame,
    QSpinBox, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from decimal import Decimal
from datetime import datetime, timedelta
from models.user_model import User
from models.cash_model import CashTransaction, BusinessLoan, CashTransactionType, ExpenseCategory
from firebase.db import FirebaseManager
from utils.helpers import format_currency, format_date
from utils.window_manager import WindowManager

class AddExpenseDialog(QDialog):
    """Dialog for adding a new expense."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Expense")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1000000000)
        self.amount_input.setDecimals(2)
        layout.addRow("Amount:", self.amount_input)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems([c.value.title() for c in ExpenseCategory])
        layout.addRow("Category:", self.category_combo)
        
        # Description
        self.description_input = QLineEdit()
        layout.addRow("Description:", self.description_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
    def get_data(self) -> dict:
        """Get the expense data from the form."""
        return {
            'amount': Decimal(str(self.amount_input.value())),
            'category': self.category_combo.currentText().lower(),
            'description': self.description_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip() or None
        }

class AddDepositDialog(QDialog):
    """Dialog for adding a new deposit/investment."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Deposit")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1000000000)
        self.amount_input.setDecimals(2)
        layout.addRow("Amount:", self.amount_input)
        
        # Description
        self.description_input = QLineEdit()
        layout.addRow("Description:", self.description_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
    def get_data(self) -> dict:
        """Get the deposit data from the form."""
        return {
            'amount': Decimal(str(self.amount_input.value())),
            'description': self.description_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip() or None
        }

class AddBusinessLoanDialog(QDialog):
    """Dialog for adding a new business loan."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Business Loan")
        self.setMinimumWidth(500)
        
        layout = QFormLayout(self)
        
        # Loan Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Cash Loan", "Item-based Loan"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addRow("Loan Type:", self.type_combo)
        
        # Cash Amount (for cash loans)
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1000000000)
        self.amount_input.setDecimals(2)
        layout.addRow("Amount:", self.amount_input)
        
        # Items (for item-based loans)
        self.items_widget = QWidget()
        items_layout = QVBoxLayout(self.items_widget)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["Item", "Quantity", "Value"])
        items_layout.addWidget(self.items_table)
        
        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.add_item_row)
        items_layout.addWidget(add_item_btn)
        
        layout.addRow(self.items_widget)
        self.items_widget.hide()
        
        # Lender Info
        self.lender_name_input = QLineEdit()
        layout.addRow("Lender Name:", self.lender_name_input)
        
        self.lender_contact_input = QLineEdit()
        layout.addRow("Lender Contact:", self.lender_contact_input)
        
        # Due Date
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addMonths(1))
        layout.addRow("Due Date:", self.due_date_input)
        
        # Is Business Borrower
        self.is_borrower_combo = QComboBox()
        self.is_borrower_combo.addItems(["Business is borrowing", "Business is lending"])
        layout.addRow("Transaction Type:", self.is_borrower_combo)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
    def on_type_changed(self, text):
        """Handle loan type change."""
        is_cash = text == "Cash Loan"
        self.amount_input.setVisible(is_cash)
        self.layout().labelForField(self.amount_input).setVisible(is_cash)
        self.items_widget.setVisible(not is_cash)
        
    def add_item_row(self):
        """Add a new row to the items table."""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Add input widgets
        self.items_table.setCellWidget(row, 0, QLineEdit())
        
        quantity_input = QSpinBox()
        quantity_input.setMinimum(1)
        quantity_input.setMaximum(10000)
        self.items_table.setCellWidget(row, 1, quantity_input)
        
        value_input = QDoubleSpinBox()
        value_input.setMaximum(1000000000)
        value_input.setDecimals(2)
        self.items_table.setCellWidget(row, 2, value_input)
        
    def get_data(self) -> dict:
        """Get the loan data from the form."""
        is_cash_loan = self.type_combo.currentText() == "Cash Loan"
        
        data = {
            'is_cash_loan': is_cash_loan,
            'date_taken': datetime.now(),
            'due_date': self.due_date_input.date().toPython(),
            'lender_name': self.lender_name_input.text().strip(),
            'lender_contact': self.lender_contact_input.text().strip(),
            'is_business_borrower': self.is_borrower_combo.currentText() == "Business is borrowing",
            'payment_status': 'unpaid',
            'notes': self.notes_input.toPlainText().strip() or None
        }
        
        if is_cash_loan:
            data['amount'] = Decimal(str(self.amount_input.value()))
        else:
            items = []
            for row in range(self.items_table.rowCount()):
                item_name = self.items_table.cellWidget(row, 0).text().strip()
                if item_name:
                    items.append({
                        'name': item_name,
                        'quantity': self.items_table.cellWidget(row, 1).value(),
                        'value': str(self.items_table.cellWidget(row, 2).value())
                    })
            data['items'] = items
            
        return data

class CashWindow(QMainWindow):
    """Window for managing business cash and loans."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.window_manager = WindowManager()
        self.setup_ui()
        self.load_data()
        
        # Register with window manager
        self.window_manager.register_window('cash', self)
        
    def setup_ui(self):
        """Set up the cash management window UI."""
        self.setWindowTitle("Isama Management System - Cash Management")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header with cash overview
        header_layout = QHBoxLayout()
        
        # Cash balance card
        balance_card = QFrame()
        balance_card.setFrameStyle(QFrame.Box)
        balance_card.setStyleSheet("""
            QFrame {
                background-color: #1a73e8;
                border-radius: 8px;
                padding: 16px;
            }
            QLabel {
                color: white;
            }
        """)
        balance_layout = QVBoxLayout(balance_card)
        
        balance_title = QLabel("Total Cash Available")
        balance_title.setStyleSheet("font-size: 16px;")
        balance_layout.addWidget(balance_title)
        
        self.balance_amount = QLabel()
        self.balance_amount.setStyleSheet("font-size: 24px; font-weight: bold;")
        balance_layout.addWidget(self.balance_amount)
        
        header_layout.addWidget(balance_card)
        
        # Total debt card
        debt_card = QFrame()
        debt_card.setFrameStyle(QFrame.Box)
        debt_card.setStyleSheet("""
            QFrame {
                background-color: #dc3545;
                border-radius: 8px;
                padding: 16px;
            }
            QLabel {
                color: white;
            }
        """)
        debt_layout = QVBoxLayout(debt_card)
        
        debt_title = QLabel("Total Business Debt")
        debt_title.setStyleSheet("font-size: 16px;")
        debt_layout.addWidget(debt_title)
        
        self.debt_amount = QLabel()
        self.debt_amount.setStyleSheet("font-size: 24px; font-weight: bold;")
        debt_layout.addWidget(self.debt_amount)
        
        header_layout.addWidget(debt_card)
        header_layout.addStretch()
        
        # Action buttons
        actions_layout = QVBoxLayout()
        
        add_expense_btn = QPushButton("Add Expense")
        add_expense_btn.clicked.connect(self.show_add_expense_dialog)
        actions_layout.addWidget(add_expense_btn)
        
        add_deposit_btn = QPushButton("Add Deposit")
        add_deposit_btn.clicked.connect(self.show_add_deposit_dialog)
        actions_layout.addWidget(add_deposit_btn)
        
        add_loan_btn = QPushButton("Add Business Loan")
        add_loan_btn.clicked.connect(self.show_add_loan_dialog)
        actions_layout.addWidget(add_loan_btn)
        
        layout.addLayout(header_layout)
        layout.addLayout(actions_layout)
        
        # Add tabs
        tabs = QTabWidget()
        
        # Transactions tab
        transactions_tab = QWidget()
        transactions_layout = QVBoxLayout(transactions_tab)
        
        # Add filters
        filters_layout = QHBoxLayout()
        
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today", "This Week", "This Month"])
        self.date_filter.currentTextChanged.connect(self.load_data)
        filters_layout.addWidget(QLabel("Date Range:"))
        filters_layout.addWidget(self.date_filter)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types"] + [t.value.title() for t in CashTransactionType])
        self.type_filter.currentTextChanged.connect(self.load_data)
        filters_layout.addWidget(QLabel("Transaction Type:"))
        filters_layout.addWidget(self.type_filter)
        
        filters_layout.addStretch()
        transactions_layout.addLayout(filters_layout)
        
        # Add transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(6)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Type", "Amount", "Description", "Category", "Notes"
        ])
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        transactions_layout.addWidget(self.transactions_table)
        
        tabs.addTab(transactions_tab, "Transactions")
        
        # Business Loans tab
        loans_tab = QWidget()
        loans_layout = QVBoxLayout(loans_tab)
        
        # Add loans table
        self.loans_table = QTableWidget()
        self.loans_table.setColumnCount(8)
        self.loans_table.setHorizontalHeaderLabels([
            "Date Taken", "Type", "Amount/Items", "Due Date",
            "Lender", "Status", "Amount Paid", "Actions"
        ])
        self.loans_table.horizontalHeader().setStretchLastSection(True)
        loans_layout.addWidget(self.loans_table)
        
        tabs.addTab(loans_tab, "Business Loans")
        
        layout.addWidget(tabs)
        
    def load_data(self):
        """Load cash management data from Firebase."""
        try:
            # Update cash balance
            balance = self.firebase.get_cash_balance()
            self.balance_amount.setText(format_currency(balance))
            
            # Calculate total debt
            total_debt = Decimal('0')
            loans = self.firebase.get_business_loans()
            for loan in loans:
                if loan.is_business_borrower:  # Only count loans where business is the borrower
                    if loan.is_cash_loan:
                        total_amount = loan.amount
                    else:
                        total_amount = sum(Decimal(str(item['value'])) for item in loan.items)
                    amount_paid = loan.amount_paid or Decimal('0')
                    remaining = total_amount - amount_paid
                    if remaining > 0:
                        total_debt += remaining
            
            self.debt_amount.setText(format_currency(total_debt))
            
            # Load transactions
            self.load_transactions()
            
            # Load business loans
            self.load_business_loans()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
            
    def load_transactions(self):
        """Load and filter cash transactions."""
        try:
            # Get all transactions
            transactions = self.firebase.get_cash_transactions()
            
            # Apply date filter
            date_filter = self.date_filter.currentText()
            now = datetime.now()
            
            if date_filter == "Today":
                transactions = [t for t in transactions if t.date.date() == now.date()]
            elif date_filter == "This Week":
                week_start = now - timedelta(days=now.weekday())
                transactions = [t for t in transactions if t.date >= week_start]
            elif date_filter == "This Month":
                transactions = [t for t in transactions if t.date.month == now.month and t.date.year == now.year]
            
            # Apply type filter
            type_filter = self.type_filter.currentText()
            if type_filter != "All Types":
                transactions = [t for t in transactions if t.type.value.title() == type_filter]
            
            # Update table
            self.transactions_table.setRowCount(0)
            for transaction in sorted(transactions, key=lambda x: x.date, reverse=True):
                self.add_transaction_to_table(transaction)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load transactions: {str(e)}")
            
    def load_business_loans(self):
        """Load business loans."""
        try:
            loans = self.firebase.get_business_loans()
            
            # Update table
            self.loans_table.setRowCount(0)
            for loan in sorted(loans, key=lambda x: x.date_taken, reverse=True):
                self.add_loan_to_table(loan)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load loans: {str(e)}")
            
    def add_transaction_to_table(self, transaction: CashTransaction):
        """Add a transaction to the table."""
        row = self.transactions_table.rowCount()
        self.transactions_table.insertRow(row)
        
        # Date
        self.transactions_table.setItem(row, 0, QTableWidgetItem(format_date(transaction.date)))
        
        # Type
        self.transactions_table.setItem(row, 1, QTableWidgetItem(transaction.type.value.title()))
        
        # Amount
        amount_item = QTableWidgetItem(format_currency(transaction.amount))
        if transaction.type.value in ['expense', 'loan_repayment_out', 'loan_out']:
            amount_item.setForeground(Qt.red)
        else:
            amount_item.setForeground(Qt.darkGreen)
        self.transactions_table.setItem(row, 2, amount_item)
        
        # Description
        self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction.description))
        
        # Category
        self.transactions_table.setItem(row, 4, QTableWidgetItem(
            transaction.category.title() if transaction.category else "-"
        ))
        
        # Notes
        self.transactions_table.setItem(row, 5, QTableWidgetItem(transaction.notes or ""))
        
    def add_loan_to_table(self, loan: BusinessLoan):
        """Add a loan to the table."""
        row = self.loans_table.rowCount()
        self.loans_table.insertRow(row)
        
        # Date Taken
        self.loans_table.setItem(row, 0, QTableWidgetItem(format_date(loan.date_taken)))
        
        # Type
        loan_type = "Cash Loan" if loan.is_cash_loan else "Item-based Loan"
        self.loans_table.setItem(row, 1, QTableWidgetItem(loan_type))
        
        # Amount/Items
        if loan.is_cash_loan:
            amount_text = format_currency(loan.amount)
        else:
            items_text = ", ".join([
                f"{item['quantity']}x {item['name']} ({format_currency(Decimal(item['value']))})"
                for item in loan.items
            ])
            amount_text = items_text
        self.loans_table.setItem(row, 2, QTableWidgetItem(amount_text))
        
        # Due Date
        self.loans_table.setItem(row, 3, QTableWidgetItem(format_date(loan.due_date)))
        
        # Lender
        self.loans_table.setItem(row, 4, QTableWidgetItem(loan.lender_name))
        
        # Status
        self.loans_table.setItem(row, 5, QTableWidgetItem(loan.payment_status.title()))
        
        # Amount Paid
        amount_paid = loan.amount_paid or Decimal('0')
        self.loans_table.setItem(row, 6, QTableWidgetItem(format_currency(amount_paid)))
        
        # Actions
        if loan.payment_status != 'paid':
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            
            pay_btn = QPushButton("Pay")
            pay_btn.setMaximumWidth(60)
            pay_btn.clicked.connect(lambda: self.show_loan_payment_dialog(loan))
            actions_layout.addWidget(pay_btn)
            
            actions_layout.addStretch()
            self.loans_table.setCellWidget(row, 7, actions_widget)
        
    def show_add_expense_dialog(self):
        """Show dialog for adding a new expense."""
        dialog = AddExpenseDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
                
                # Create transaction
                transaction = CashTransaction(
                    id=self.firebase.get_database_reference('cash_transactions').push().key,
                    type=CashTransactionType.EXPENSE,
                    amount=data['amount'],
                    date=datetime.now(),
                    description=data['description'],
                    category=data['category'],
                    created_by=self.user.id,
                    notes=data['notes']
                )
                
                # Save to Firebase
                self.firebase.add_cash_transaction(transaction)
                
                # Reload data
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add expense: {str(e)}")
                
    def show_add_deposit_dialog(self):
        """Show dialog for adding a new deposit."""
        dialog = AddDepositDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
                
                # Create transaction
                transaction = CashTransaction(
                    id=self.firebase.get_database_reference('cash_transactions').push().key,
                    type=CashTransactionType.DEPOSIT,
                    amount=data['amount'],
                    date=datetime.now(),
                    description=data['description'],
                    created_by=self.user.id,
                    notes=data['notes']
                )
                
                # Save to Firebase
                self.firebase.add_cash_transaction(transaction)
                
                # Reload data
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add deposit: {str(e)}")
                
    def show_add_loan_dialog(self):
        """Show dialog for adding a new business loan."""
        dialog = AddBusinessLoanDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
                
                # Create loan
                loan = BusinessLoan(
                    id=self.firebase.get_database_reference('business_loans').push().key,
                    is_cash_loan=data['is_cash_loan'],
                    date_taken=data['date_taken'],
                    due_date=data['due_date'],
                    lender_name=data['lender_name'],
                    lender_contact=data['lender_contact'],
                    is_business_borrower=data['is_business_borrower'],
                    payment_status='unpaid',
                    created_by=self.user.id,
                    amount=data.get('amount'),
                    items=data.get('items'),
                    notes=data.get('notes')
                )
                
                # Save to Firebase
                self.firebase.add_business_loan(loan)
                
                # Reload data
                self.load_data()
                
                # Update dashboard if it exists
                self.update_dashboard()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add loan: {str(e)}")
                print(f"Detailed error adding loan: {str(e)}")
                
    def show_loan_payment_dialog(self, loan: BusinessLoan):
        """Show dialog for recording a loan payment."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Loan Payment")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Show current status
        if loan.is_cash_loan:
            total_amount = loan.amount
        else:
            total_amount = sum(Decimal(item['value']) for item in loan.items)
            
        layout.addRow(QLabel(f"<b>Total Amount:</b> {format_currency(total_amount)}"))
        layout.addRow(QLabel(f"<b>Amount Paid:</b> {format_currency(loan.amount_paid or 0)}"))
        layout.addRow(QLabel(f"<b>Remaining:</b> {format_currency(total_amount - (loan.amount_paid or 0))}"))
        
        # Add payment input
        payment_input = QDoubleSpinBox()
        payment_input.setMaximum(float(total_amount - (loan.amount_paid or 0)))
        payment_input.setDecimals(2)
        layout.addRow("Payment Amount:", payment_input)
        
        # Add buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
        if dialog.exec_():
            try:
                amount = Decimal(str(payment_input.value()))
                
                # Add payment to loan
                loan.add_payment(amount)
                
                # Save loan update to Firebase
                self.firebase.update_business_loan(loan)
                
                # Reload data
                self.load_data()
                
                # Update dashboard if it exists
                self.update_dashboard()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")
                print(f"Detailed error recording payment: {str(e)}")
                
    def update_dashboard(self):
        """Update the dashboard metrics if it's open."""
        try:
            dashboard = self.window_manager.get_window('dashboard')
            if dashboard:
                dashboard.load_data()
        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        self.window_manager.remove_window('cash')
        super().closeEvent(event) 
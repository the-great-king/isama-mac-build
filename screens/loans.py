from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QDoubleSpinBox, QMessageBox, QComboBox,
    QDateEdit, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from decimal import Decimal
from datetime import datetime, timedelta
from models.user_model import User
from models.transaction_model import Transaction, PaymentRecord
from firebase.db import FirebaseManager
from utils.helpers import format_currency, format_date
from utils.window_manager import WindowManager

class LoansWindow(QMainWindow):
    """Window for managing loan transactions."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.window_manager = WindowManager()
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Set up the loans window UI."""
        self.setWindowTitle("Isama Management System - Loans")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header
        header_layout = QHBoxLayout()
        title = QLabel("Loans Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a73e8;")
        header_layout.addWidget(title)
        
        # Add search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by buyer name...")
        self.search_input.textChanged.connect(self.load_data)
        self.search_input.setMaximumWidth(250)
        header_layout.addWidget(self.search_input)
        
        header_layout.addStretch()
        
        # Add filter controls
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Unpaid", "Partial", "Paid"])
        self.status_filter.currentTextChanged.connect(self.load_data)
        
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today", "This Week", "This Month", "Overdue"])
        self.date_filter.currentTextChanged.connect(self.load_data)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Date:"))
        filter_layout.addWidget(self.date_filter)
        header_layout.addLayout(filter_layout)
        
        layout.addLayout(header_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Date", "Due Date", "Buyer", "Contact",
            "Total Amount", "Amount Paid", "Status", "Actions"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # Add summary section
        summary_layout = QHBoxLayout()
        self.total_loans_label = QLabel()
        self.total_paid_label = QLabel()
        self.total_unpaid_label = QLabel()
        
        for label in [self.total_loans_label, self.total_paid_label, self.total_unpaid_label]:
            label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            summary_layout.addWidget(label)
            
        layout.addLayout(summary_layout)
        
    def load_data(self):
        """Load loans data from Firebase based on filters."""
        try:
            # Get transactions from Firebase
            db = self.firebase.get_database_reference('transactions')
            transactions_data = db.get() or {}
            
            # Filter loans
            loans = []
            total_amount = Decimal('0')
            total_paid = Decimal('0')
            
            # Get search text
            search_text = self.search_input.text().lower().strip()
            
            for transaction_id, data in transactions_data.items():
                try:
                    # Skip if not a loan or missing required data
                    if not isinstance(data, dict):
                        print(f"Invalid transaction data for {transaction_id}: {data}")
                        continue
                        
                    if data.get('transaction_type') != 'loan':
                        continue
                    
                    # Ensure required fields exist
                    required_fields = {
                        'total_amount': '0',
                        'transaction_date': datetime.now().isoformat(),
                        'status': 'pending',
                        'items': [],
                        'buyer_name': '',
                        'buyer_contact': '',
                        'payment_status': 'unpaid',
                        'amount_paid': '0'
                    }
                    
                    # Fill in missing fields with defaults
                    for field, default in required_fields.items():
                        if field not in data or data[field] is None:
                            print(f"Missing field {field} in transaction {transaction_id}, using default")
                            data[field] = default
                    
                    data['id'] = transaction_id
                    loan = Transaction.from_dict(data)
                    
                    # Apply search filter
                    if search_text and (not loan.buyer_name or search_text not in loan.buyer_name.lower()):
                        continue
                    
                    # Apply status filter
                    status_filter = self.status_filter.currentText().lower()
                    if status_filter != 'all' and loan.payment_status != status_filter:
                        continue
                        
                    # Apply date filter
                    date_filter = self.date_filter.currentText()
                    if date_filter != 'All Time':
                        if date_filter == 'Today':
                            if loan.transaction_date.date() != datetime.now().date():
                                continue
                        elif date_filter == 'This Week':
                            week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
                            if loan.transaction_date.date() < week_start:
                                continue
                        elif date_filter == 'This Month':
                            month_start = datetime.now().date().replace(day=1)
                            if loan.transaction_date.date() < month_start:
                                continue
                        elif date_filter == 'Overdue':
                            if loan.payment_status == 'paid' or loan.due_date > datetime.now():
                                continue
                                
                    loans.append(loan)
                    total_amount += loan.total_amount
                    total_paid += loan.amount_paid or Decimal('0')
                    
                except Exception as e:
                    print(f"Error processing loan {transaction_id}: {str(e)}")
                    print(f"Problematic data: {data}")
                    continue
                    
            # Update table
            self.table.setRowCount(len(loans))
            
            for row, loan in enumerate(loans):
                try:
                    self.table.setItem(row, 0, QTableWidgetItem(format_date(loan.transaction_date)))
                    self.table.setItem(row, 1, QTableWidgetItem(format_date(loan.due_date or datetime.now())))
                    self.table.setItem(row, 2, QTableWidgetItem(loan.buyer_name or "Unknown"))
                    self.table.setItem(row, 3, QTableWidgetItem(loan.buyer_contact or '-'))
                    self.table.setItem(row, 4, QTableWidgetItem(format_currency(loan.total_amount)))
                    self.table.setItem(row, 5, QTableWidgetItem(format_currency(loan.amount_paid or 0)))
                    
                    # Status with color
                    status_item = QTableWidgetItem(loan.payment_status.title())
                    if loan.payment_status == 'paid':
                        status_item.setForeground(Qt.darkGreen)
                    elif loan.payment_status == 'partial':
                        status_item.setForeground(Qt.darkYellow)
                    else:
                        status_item.setForeground(Qt.red)
                    self.table.setItem(row, 6, status_item)
                    
                    # Add action buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(4, 4, 4, 4)
                    
                    view_btn = QPushButton("View")
                    view_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #17a2b8;
                            color: white;
                            border: none;
                            padding: 4px 8px;
                            border-radius: 2px;
                        }
                        QPushButton:hover {
                            background-color: #138496;
                        }
                    """)
                    view_btn.clicked.connect(lambda checked, t=loan: self.show_loan_details(t))
                    actions_layout.addWidget(view_btn)
                    
                    if loan.payment_status != 'paid':
                        pay_btn = QPushButton("Record Payment")
                        pay_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #28a745;
                                color: white;
                                border: none;
                                padding: 4px 8px;
                                border-radius: 2px;
                            }
                            QPushButton:hover {
                                background-color: #218838;
                            }
                        """)
                        pay_btn.clicked.connect(lambda checked, t=loan: self.show_payment_dialog(t))
                        actions_layout.addWidget(pay_btn)
                        
                    actions_layout.addStretch()
                    self.table.setCellWidget(row, 7, actions_widget)
                    
                except Exception as e:
                    print(f"Error displaying loan in row {row}: {str(e)}")
                    print(f"Loan data: {loan.__dict__}")
                    continue
                    
            # Update summary
            self.total_loans_label.setText(f"Total Loans: {format_currency(total_amount)}")
            self.total_paid_label.setText(f"Total Paid: {format_currency(total_paid)}")
            self.total_unpaid_label.setText(f"Total Unpaid: {format_currency(total_amount - total_paid)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load loans data: {str(e)}")
            print(f"Detailed error: {str(e)}")  # For debugging
            
    def show_loan_details(self, loan: Transaction):
        """Show dialog with loan details."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Loan Details - {loan.id}")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Add loan info
        info_text = f"""
        <h3>Loan Information</h3>
        <p><b>Date:</b> {format_date(loan.transaction_date)}</p>
        <p><b>Due Date:</b> {format_date(loan.due_date)}</p>
        <p><b>Buyer:</b> {loan.buyer_name}</p>
        <p><b>Contact:</b> {loan.buyer_contact or 'N/A'}</p>
        <p><b>Total Amount:</b> {format_currency(loan.total_amount)}</p>
        <p><b>Amount Paid:</b> {format_currency(loan.amount_paid or 0)}</p>
        <p><b>Remaining:</b> {format_currency(loan.total_amount - (loan.amount_paid or 0))}</p>
        <p><b>Status:</b> {loan.payment_status.title()}</p>
        """
        
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        # Add items table
        items_group = QGroupBox("Items")
        items_layout = QVBoxLayout(items_group)
        
        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels([
            "Product ID", "Quantity", "Price", "Total"
        ])
        
        items_table.setRowCount(len(loan.items))
        for row, item in enumerate(loan.items):
            items_table.setItem(row, 0, QTableWidgetItem(item.product_id))
            items_table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
            items_table.setItem(row, 2, QTableWidgetItem(format_currency(item.price_per_unit)))
            items_table.setItem(row, 3, QTableWidgetItem(format_currency(item.total)))
            
        items_layout.addWidget(items_table)
        layout.addWidget(items_group)
        
        # Add payment history
        if loan.payment_history:
            history_group = QGroupBox("Payment History")
            history_layout = QVBoxLayout(history_group)
            
            history_table = QTableWidget()
            history_table.setColumnCount(2)
            history_table.setHorizontalHeaderLabels([
                "Date", "Amount"
            ])
            
            # Convert dictionary items to PaymentRecord objects if needed
            payment_records = []
            for payment in loan.payment_history:
                if isinstance(payment, dict):
                    payment_records.append(PaymentRecord.from_dict(payment))
                else:
                    payment_records.append(payment)
            
            history_table.setRowCount(len(payment_records))
            for row, payment in enumerate(sorted(payment_records, key=lambda x: x.date)):
                history_table.setItem(row, 0, QTableWidgetItem(format_date(payment.date)))
                history_table.setItem(row, 1, QTableWidgetItem(format_currency(payment.amount)))
                
            history_layout.addWidget(history_table)
            layout.addWidget(history_group)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
        
    def show_payment_dialog(self, loan: Transaction):
        """Show dialog for recording a payment."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Payment")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Show current status
        layout.addRow(QLabel(f"<b>Total Amount:</b> {format_currency(loan.total_amount)}"))
        layout.addRow(QLabel(f"<b>Amount Paid:</b> {format_currency(loan.amount_paid or 0)}"))
        layout.addRow(QLabel(f"<b>Remaining:</b> {format_currency(loan.total_amount - (loan.amount_paid or 0))}"))
        
        # Add payment input
        payment_input = QDoubleSpinBox()
        payment_input.setMaximum(float(loan.total_amount - (loan.amount_paid or 0)))
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
                
                # Add payment with user ID
                loan.add_payment(amount, self.user.id)
                
                # Save to Firebase using update_transaction to properly handle cash
                self.firebase.update_transaction(loan)
                
                # Reload data
                self.load_data()
                
                # Update dashboard if it exists
                self.update_dashboard()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")
                # Print detailed error for debugging
                print(f"Detailed error: {str(e)}")
                
    def update_dashboard(self):
        """Update the dashboard metrics if it's open."""
        try:
            dashboard = self.window_manager.get_window('dashboard')
            if dashboard:
                dashboard.load_data()
        except Exception as e:
            print(f"Error updating dashboard: {e}") 
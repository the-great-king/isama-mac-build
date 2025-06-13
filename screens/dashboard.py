from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGridLayout,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QTextEdit, QMessageBox, QComboBox, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt
from models.user_model import User
from models.cash_model import CashTransaction, CashTransactionType
from firebase.db import FirebaseManager
from utils.helpers import format_currency, format_date, get_date_range_filter
from utils.window_manager import WindowManager
from datetime import datetime
from decimal import Decimal

class AddCashWithdrawalDialog(QDialog):
    """Dialog for recording cash withdrawal from business."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Record Cash Withdrawal")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1000000000)
        self.amount_input.setDecimals(2)
        layout.addRow("Amount:", self.amount_input)
        
        # Reason
        self.reason_combo = QComboBox()
        self.reason_combo.addItems([
            "Wages/Salary",
            "Services",
            "Utilities",
            "Transport",
            "Maintenance",
            "Supplies",
            "Other"
        ])
        self.reason_combo.setEditable(True)
        layout.addRow("Reason:", self.reason_combo)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        layout.addRow("Details:", self.description_input)
        
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
        """Get the withdrawal data from the form."""
        return {
            'amount': Decimal(str(self.amount_input.value())),
            'reason': self.reason_combo.currentText().strip(),
            'description': self.description_input.toPlainText().strip()
        }

class DashboardWindow(QMainWindow):
    """Main dashboard window showing key metrics and navigation."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.window_manager = WindowManager()
        self.setup_ui()
        self.load_data()
        
        # Register with window manager
        self.window_manager.register_window('dashboard', self)
        
    def setup_ui(self):
        """Set up the dashboard UI."""
        self.setWindowTitle("Dashboard - Isama Management System")
        self.setMinimumSize(1200, 800)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        scroll.setWidget(central_widget)
        self.setCentralWidget(scroll)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Add header with custom styling
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a73e8;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        welcome = QLabel(f"Welcome, {self.user.name}!")
        welcome.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(welcome)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #1a73e8;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        logout_btn.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_btn)
        
        main_layout.addWidget(header_frame)
        
        # Add metrics section with custom styling
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 12px;
                padding: 24px;
            }
        """)
        metrics_layout = QGridLayout(metrics_frame)
        metrics_layout.setSpacing(24)
        metrics_layout.setContentsMargins(24, 24, 24, 24)
        
        # Create metric widgets in specific order
        metrics_order = [
            'total_stock',
            'loan_sales',
            'items_sold',
            'unpaid_loans',
            'cash_sales'
        ]
        
        self.metrics = {
            'total_stock': self.create_metric_widget("Total Stock Items", "0"),
            'cash_sales': self.create_metric_widget("Cash Sales Today", "TSHS 0.00"),
            'loan_sales': self.create_metric_widget("Loan Sales Today", "TSHS 0.00"),
            'unpaid_loans': self.create_metric_widget("Total Unpaid Loans", "TSHS 0.00"),
            'items_sold': self.create_metric_widget("Items Sold Today", "0")
        }
        
        # Add metrics to grid in 2 columns
        for i, key in enumerate(metrics_order):
            row = i // 2
            col = i % 2
            metrics_layout.addWidget(self.metrics[key], row, col)
        
        main_layout.addWidget(metrics_frame)
        
        # Add navigation buttons with improved styling
        nav_frame = QFrame()
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 24px;
            }
        """)
        nav_layout = QGridLayout(nav_frame)
        nav_layout.setSpacing(16)
        nav_layout.setContentsMargins(16, 16, 16, 16)
        
        nav_buttons = [
            ("Inventory", self.open_inventory),
            ("Categories", self.open_categories),
            ("Sales", self.open_sales),
            ("Loans", self.open_loans),
            ("Cash Management", self.open_cash),
            ("Business Debt", self.open_business_debt)
        ]
        
        # Add buttons in a 3x2 grid with smaller size
        for i, (text, slot) in enumerate(nav_buttons):
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a73e8;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 150px;
                    min-height: 45px;
                }
                QPushButton:hover {
                    background-color: #1557b0;
                }
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
            """)
            btn.clicked.connect(slot)
            row = i // 3
            col = i % 3
            nav_layout.addWidget(btn, row, col)
        
        main_layout.addWidget(nav_frame)
        
    def create_metric_widget(self, title: str, value: str) -> QFrame:
        """Create a metric widget with title and value."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
                min-width: 250px;
                min-height: 120px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)  # Reduced spacing between title and value
        
        # Title with custom styling
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 4px;
            }
        """)
        layout.addWidget(title_label)
        
        # Value with custom styling and red background
        value_frame = QFrame()
        value_frame.setStyleSheet("""
            QFrame {
                background-color: #e63946;  /* Business theme red color */
                border-radius: 8px;
                padding: 8px 12px;
            }
        """)
        value_layout = QHBoxLayout(value_frame)
        value_layout.setContentsMargins(8, 8, 8, 8)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                min-height: 40px;
            }
        """)
        value_label.setWordWrap(True)
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_layout.addWidget(value_label)
        
        layout.addWidget(value_frame)
        layout.addStretch()
        
        return frame
        
    def load_data(self):
        """Load and display dashboard data."""
        try:
            # Update metrics
            self.update_metrics()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load dashboard data: {str(e)}")
            
    def update_metrics(self):
        """Update the metrics display with new data."""
        try:
            # Get current date's start and end
            today = datetime.now()
            today_start = datetime.combine(today.date(), datetime.min.time())
            today_end = datetime.combine(today.date(), datetime.max.time())
            
            # Initialize metrics
            total_stock = 0
            cash_sales_today = Decimal('0')
            loan_sales_today = Decimal('0')
            items_sold_today = 0
            total_unpaid_loans = Decimal('0')
            
            # Get data from Firebase
            products_ref = self.firebase.get_database_reference('products')
            transactions_ref = self.firebase.get_database_reference('transactions')
            
            # Calculate total stock from products
            products_data = products_ref.get() or {}
            for product_data in products_data.values():
                if isinstance(product_data, dict):
                    total_stock += product_data.get('stock', 0)
            
            # Calculate sales and loans metrics from transactions
            transactions_data = transactions_ref.get() or {}
            for transaction_data in transactions_data.values():
                if not isinstance(transaction_data, dict):
                    continue
                    
                # Get transaction date
                try:
                    transaction_date = datetime.fromisoformat(transaction_data.get('transaction_date', ''))
                except (ValueError, TypeError):
                    continue
                
                # Calculate today's metrics
                if today_start <= transaction_date <= today_end:
                    transaction_amount = Decimal(str(transaction_data.get('total_amount', 0)))
                    if transaction_data.get('transaction_type') == 'cash':
                        cash_sales_today += transaction_amount
                    elif transaction_data.get('transaction_type') == 'loan':
                        loan_sales_today += transaction_amount
                    
                    # Count items sold today if items exist
                    items = transaction_data.get('items', [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                items_sold_today += item.get('quantity', 0)
                
                # Calculate total unpaid loans
                if transaction_data.get('transaction_type') == 'loan':
                    payment_status = transaction_data.get('payment_status', 'unpaid')
                    if payment_status in ['unpaid', 'partial']:
                        total_amount = Decimal(str(transaction_data.get('total_amount', 0)))
                        amount_paid = Decimal(str(transaction_data.get('amount_paid', 0)))
                        total_unpaid_loans += (total_amount - amount_paid)
            
            # Update metrics with exact numbers
            self.metrics['total_stock'].findChildren(QLabel)[-1].setText(f"{total_stock:,}")
            self.metrics['cash_sales'].findChildren(QLabel)[-1].setText(format_currency(cash_sales_today))
            self.metrics['loan_sales'].findChildren(QLabel)[-1].setText(format_currency(loan_sales_today))
            self.metrics['unpaid_loans'].findChildren(QLabel)[-1].setText(format_currency(total_unpaid_loans))
            self.metrics['items_sold'].findChildren(QLabel)[-1].setText(f"{items_sold_today:,}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update metrics: {str(e)}")
            
    def show_cash_withdrawal_dialog(self):
        """Show dialog for recording cash withdrawal."""
        dialog = AddCashWithdrawalDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
                
                # Create transaction
                transaction = CashTransaction(
                    id=self.firebase.get_database_reference('cash_transactions').push().key,
                    type=CashTransactionType.EXPENSE,
                    amount=data['amount'],
                    date=datetime.now(),
                    description=f"{data['reason']}: {data['description']}",
                    created_by=self.user.id,
                    category=data['reason'].lower()
                )
                
                # Save to Firebase
                self.firebase.add_cash_transaction(transaction)
                
                # Reload data
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record withdrawal: {str(e)}")
                
    def show_business_loans(self):
        """Show business loans window."""
        window = self.window_manager.get_window('cash')
        if not window:
            from .cash import CashWindow
            window = CashWindow(self.user)
        window.show()
        window.activateWindow()
        # Switch to loans tab
        window.findChild(QTabWidget).setCurrentIndex(1)
        
    def show_cash_history(self):
        """Show cash history window."""
        window = self.window_manager.get_window('cash')
        if not window:
            from .cash import CashWindow
            window = CashWindow(self.user)
        window.show()
        window.activateWindow()
        # Switch to transactions tab
        window.findChild(QTabWidget).setCurrentIndex(0)
        
    def handle_logout(self):
        """Handle user logout."""
        from screens.login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()
        
    def open_inventory(self):
        """Open the inventory management window."""
        from screens.inventory import InventoryWindow
        self.inventory = InventoryWindow(self.user)
        self.inventory.show()
        
    def open_sales(self):
        """Open the sales management window."""
        from screens.sales import SalesWindow
        self.sales = SalesWindow(self.user)
        self.sales.show()
        
    def open_loans(self):
        """Open the loans management window."""
        from screens.loans import LoansWindow
        self.loans = LoansWindow(self.user)
        self.loans.show()
        
    def open_categories(self):
        """Open the category management window."""
        from screens.categories import CategoryWindow
        self.categories = CategoryWindow(self.user)
        self.categories.show()
        
    def open_cash(self):
        """Open the cash management window."""
        from screens.cash import CashWindow
        window = self.window_manager.get_window('cash')
        if not window:
            window = CashWindow(self.user)
        window.show()
        window.activateWindow()
        
    def open_business_debt(self):
        """Open the business debt management window."""
        from screens.cash import CashWindow
        window = self.window_manager.get_window('cash')
        if not window:
            window = CashWindow(self.user)
        window.show()
        window.activateWindow()
        # Switch to business loans tab
        window.findChild(QTabWidget).setCurrentIndex(1)
        
    def closeEvent(self, event):
        """Handle window close event."""
        self.window_manager.remove_window('dashboard')
        super().closeEvent(event) 
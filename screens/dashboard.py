from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from models.user_model import User
from firebase.db import FirebaseManager
from utils.helpers import format_currency, format_date, get_date_range_filter
from utils.window_manager import WindowManager
from datetime import datetime
from decimal import Decimal

class DashboardWindow(QMainWindow):
    """
    Main dashboard window showing key metrics and navigation.
    """
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.window_manager = WindowManager()
        self.setup_ui()
        self.load_data()
        
        # Register with window manager
        self.window_manager.register_window('dashboard', self)
        
    def closeEvent(self, event):
        """Handle window close event."""
        self.window_manager.remove_window('dashboard')
        super().closeEvent(event)
        
    def setup_ui(self):
        """Set up the dashboard UI."""
        self.setWindowTitle("Isama Management System - Dashboard")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add header
        header_layout = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a73e8;")
        header_layout.addWidget(title)
        
        # Add user info and logout button
        user_info = QLabel(f"Welcome, {self.user.name}")
        user_info.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(user_info)
        header_layout.addStretch()
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        logout_btn.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_btn)
        main_layout.addLayout(header_layout)
        
        # Add metrics grid
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        metrics_layout = QGridLayout(metrics_frame)
        
        # Create metric widgets
        self.metrics = {
            'total_stock': self.create_metric_widget("Total Stock Items", "0"),
            'cash_sales': self.create_metric_widget("Cash Sales Today", "TSHS 0.00"),
            'loan_sales': self.create_metric_widget("Loan Sales Today", "TSHS 0.00"),
            'unpaid_loans': self.create_metric_widget("Total Unpaid Loans", "TSHS 0.00"),
            'items_sold': self.create_metric_widget("Items Sold Today", "0")
        }
        
        # Add metrics to grid
        for i, (key, widget) in enumerate(self.metrics.items()):
            row = i // 3
            col = i % 3
            metrics_layout.addWidget(widget, row, col)
            
        main_layout.addWidget(metrics_frame)
        
        # Add navigation buttons
        nav_layout = QHBoxLayout()
        nav_buttons = [
            ("Inventory", self.open_inventory),
            ("Categories", self.open_categories),
            ("Sales", self.open_sales),
            ("Loans", self.open_loans)
        ]
        
        for text, slot in nav_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a73e8;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1557b0;
                }
            """)
            btn.clicked.connect(slot)
            nav_layout.addWidget(btn)
            
        main_layout.addLayout(nav_layout)
        main_layout.addStretch()
        
    def create_metric_widget(self, label: str, value: str) -> QFrame:
        """Create a widget to display a metric."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 16px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #6c757d; font-size: 14px;")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("color: #212529; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_widget)
        
        return frame
        
    def load_data(self):
        """Load and display dashboard data."""
        try:
            # Update metrics
            self.update_metrics()
            
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            
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
                    
                    # Count items sold today
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
            
            # Update the UI
            self.metrics['total_stock'].findChildren(QLabel)[-1].setText(str(total_stock))
            self.metrics['cash_sales'].findChildren(QLabel)[-1].setText(format_currency(cash_sales_today))
            self.metrics['loan_sales'].findChildren(QLabel)[-1].setText(format_currency(loan_sales_today))
            self.metrics['unpaid_loans'].findChildren(QLabel)[-1].setText(format_currency(total_unpaid_loans))
            self.metrics['items_sold'].findChildren(QLabel)[-1].setText(str(items_sold_today))
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
            
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
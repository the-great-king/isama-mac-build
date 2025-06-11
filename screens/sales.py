from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict
from models.user_model import User
from models.product_model import Product
from models.transaction_model import Transaction, TransactionItem
from firebase.db import FirebaseManager
from utils.helpers import format_currency, format_date
from utils.window_manager import WindowManager

class AddSaleDialog(QDialog):
    """Dialog for creating a new sale."""
    
    def __init__(self, parent=None, products: List[Product] = None):
        super().__init__(parent)
        self.products = products or []
        self.items: List[Dict] = []
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the sale dialog UI."""
        self.setWindowTitle("New Sale")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Add items section
        items_group = QWidget()
        items_layout = QHBoxLayout(items_group)
        
        # Product selection
        self.product_combo = QComboBox()
        for product in self.products:
            if product.stock > 0:  # Only show products with stock
                self.product_combo.addItem(product.name, product)
                
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.valueChanged.connect(self.update_item_total)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(1000000)
        self.price_spin.setDecimals(2)
        self.price_spin.valueChanged.connect(self.update_item_total)
        
        self.total_label = QLabel("TSHS 0.00")
        
        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.add_item)
        
        items_layout.addWidget(QLabel("Product:"))
        items_layout.addWidget(self.product_combo)
        items_layout.addWidget(QLabel("Quantity:"))
        items_layout.addWidget(self.quantity_spin)
        items_layout.addWidget(QLabel("Price:"))
        items_layout.addWidget(self.price_spin)
        items_layout.addWidget(QLabel("Total:"))
        items_layout.addWidget(self.total_label)
        items_layout.addWidget(add_item_btn)
        
        layout.addWidget(items_group)
        
        # Items table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Product", "Quantity", "Price", "Total", "Action"
        ])
        layout.addWidget(self.table)
        
        # Sale type and buyer info
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        
        self.sale_type_combo = QComboBox()
        self.sale_type_combo.addItems(["Cash", "Loan"])
        self.sale_type_combo.currentTextChanged.connect(self.toggle_buyer_fields)
        
        self.buyer_name_input = QLineEdit()
        self.buyer_contact_input = QLineEdit()
        self.due_date_input = QDateEdit()
        self.due_date_input.setMinimumDate(QDate.currentDate())
        
        # Add form fields with labels stored as class attributes
        self.form_layout.addRow("Sale Type:", self.sale_type_combo)
        self.buyer_name_label = QLabel("Buyer Name:")
        self.form_layout.addRow(self.buyer_name_label, self.buyer_name_input)
        self.buyer_contact_label = QLabel("Buyer Contact:")
        self.form_layout.addRow(self.buyer_contact_label, self.buyer_contact_input)
        self.due_date_label = QLabel("Due Date:")
        self.form_layout.addRow(self.due_date_label, self.due_date_input)
        
        layout.addWidget(form_widget)
        
        # Initially hide buyer fields
        self.toggle_buyer_fields("Cash")
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Sale")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Update price when product changes
        self.product_combo.currentIndexChanged.connect(self.update_price)
        self.update_price()
        
    def update_price(self):
        """Update price when product selection changes."""
        product = self.product_combo.currentData()
        if product:
            self.price_spin.setValue(float(product.price))
            self.quantity_spin.setMaximum(product.stock)
            
    def update_item_total(self):
        """Update total amount for current item."""
        quantity = self.quantity_spin.value()
        price = Decimal(str(self.price_spin.value()))
        total = quantity * price
        self.total_label.setText(format_currency(total))
        
    def add_item(self):
        """Add item to the sale."""
        product = self.product_combo.currentData()
        if not product:
            return
            
        quantity = self.quantity_spin.value()
        price = Decimal(str(self.price_spin.value()))
        total = quantity * price
        
        # Add to items list
        item = {
            'product': product,
            'quantity': quantity,
            'price': price,
            'total': total
        }
        self.items.append(item)
        
        # Update table
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(product.name))
        self.table.setItem(row, 1, QTableWidgetItem(str(quantity)))
        self.table.setItem(row, 2, QTableWidgetItem(format_currency(price)))
        self.table.setItem(row, 3, QTableWidgetItem(format_currency(total)))
        
        # Add remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_item(row))
        self.table.setCellWidget(row, 4, remove_btn)
        
    def remove_item(self, row: int):
        """Remove item from the sale."""
        self.items.pop(row)
        self.table.removeRow(row)
        
    def toggle_buyer_fields(self, sale_type: str):
        """Show/hide buyer fields based on sale type."""
        show = sale_type == "Loan"
        self.buyer_name_input.setVisible(show)
        self.buyer_contact_input.setVisible(show)
        self.due_date_input.setVisible(show)
        self.buyer_name_label.setVisible(show)
        self.buyer_contact_label.setVisible(show)
        self.due_date_label.setVisible(show)
        
    def get_sale_data(self) -> dict:
        """Get the sale data from the form."""
        total_amount = sum(item['total'] for item in self.items)
        transaction_type = self.sale_type_combo.currentText().lower()
        
        data = {
            'items': [
                {
                    'product_id': item['product'].id,
                    'quantity': item['quantity'],
                    'price_per_unit': item['price'],
                    'total': item['total']
                }
                for item in self.items
            ],
            'total_amount': total_amount,
            'transaction_type': transaction_type,
            'transaction_date': datetime.now(),
        }
        
        if transaction_type == 'loan':
            data.update({
                'buyer_name': self.buyer_name_input.text().strip(),
                'buyer_contact': self.buyer_contact_input.text().strip(),
                'due_date': datetime.combine(
                    self.due_date_input.date().toPython(),
                    datetime.now().time()
                ),
                'payment_status': 'unpaid',
                'amount_paid': Decimal('0')
            })
            
        return data

class SalesWindow(QMainWindow):
    """Window for managing sales."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.window_manager = WindowManager()
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Set up the sales window UI."""
        self.setWindowTitle("Isama Management System - Sales")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header
        header_layout = QHBoxLayout()
        title = QLabel("Sales Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a73e8;")
        header_layout.addWidget(title)
        
        # Add filters section
        filters_layout = QHBoxLayout()
        
        # Date filter
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today", "This Week", "This Month"])
        self.date_filter.currentTextChanged.connect(self.load_data)
        
        # Month filter
        self.month_filter = QComboBox()
        self.month_filter.addItem("All Months")
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        self.month_filter.addItems(months)
        self.month_filter.currentTextChanged.connect(self.load_data)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Cash", "Loan"])
        self.type_filter.currentTextChanged.connect(self.load_data)
        
        filters_layout.addWidget(QLabel("Date Range:"))
        filters_layout.addWidget(self.date_filter)
        filters_layout.addWidget(QLabel("Month:"))
        filters_layout.addWidget(self.month_filter)
        filters_layout.addWidget(QLabel("Type:"))
        filters_layout.addWidget(self.type_filter)
        
        # Add new sale button
        new_sale_btn = QPushButton("New Sale")
        new_sale_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        new_sale_btn.clicked.connect(self.show_new_sale_dialog)
        
        header_layout.addStretch()
        header_layout.addWidget(new_sale_btn)
        
        layout.addLayout(header_layout)
        layout.addLayout(filters_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Type", "Items", "Total", "Status",
            "Buyer", "Actions"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # Add summary section
        summary_layout = QHBoxLayout()
        self.total_sales_label = QLabel()
        self.cash_sales_label = QLabel()
        self.loan_sales_label = QLabel()
        
        for label in [self.total_sales_label, self.cash_sales_label, self.loan_sales_label]:
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
        """Load sales data from Firebase based on filters."""
        try:
            # Get transactions from Firebase
            db = self.firebase.get_database_reference('transactions')
            transactions_data = db.get() or {}
            
            # Initialize summary metrics
            total_amount = Decimal('0')
            cash_sales = Decimal('0')
            loan_sales = Decimal('0')
            
            # Filter and sort transactions
            filtered_transactions = []
            
            for transaction_id, data in transactions_data.items():
                try:
                    # Skip if not a valid transaction data
                    if not isinstance(data, dict):
                        print(f"Invalid transaction data for {transaction_id}: {data}")
                        continue
                    
                    # Ensure required fields exist
                    required_fields = {
                        'total_amount': '0',
                        'transaction_date': datetime.now().isoformat(),
                        'status': 'pending',
                        'items': [],
                        'transaction_type': 'cash',
                        'buyer_name': '',
                        'buyer_contact': '',
                        'payment_status': 'unpaid',
                        'amount_paid': '0'
                    }
                    
                    # Fill in missing fields with defaults
                    for field, default in required_fields.items():
                        if field not in data or data[field] is None:
                            data[field] = default
                    
                    data['id'] = transaction_id
                    transaction = Transaction.from_dict(data)
                    
                    # Apply type filter
                    type_filter = self.type_filter.currentText()
                    if type_filter != "All Types" and transaction.transaction_type.title() != type_filter:
                        continue
                    
                    # Apply date filters
                    date_filter = self.date_filter.currentText()
                    month_filter = self.month_filter.currentText()
                    
                    # Get transaction date
                    transaction_date = transaction.transaction_date
                    
                    # Apply date range filter
                    if date_filter != "All Time":
                        today = datetime.now()
                        if date_filter == "Today":
                            if transaction_date.date() != today.date():
                                continue
                        elif date_filter == "This Week":
                            week_start = today.date() - timedelta(days=today.weekday())
                            if transaction_date.date() < week_start:
                                continue
                        elif date_filter == "This Month":
                            month_start = today.date().replace(day=1)
                            if transaction_date.date() < month_start:
                                continue
                    
                    # Apply month filter
                    if month_filter != "All Months":
                        month_num = datetime.strptime(month_filter, "%B").month
                        if transaction_date.month != month_num:
                            continue
                    
                    filtered_transactions.append(transaction)
                    
                    # Update summary metrics
                    total_amount += transaction.total_amount
                    if transaction.transaction_type == 'cash':
                        cash_sales += transaction.total_amount
                    else:
                        loan_sales += transaction.total_amount
                    
                except Exception as e:
                    print(f"Error processing transaction {transaction_id}: {e}")
                    continue
            
            # Sort transactions by date (newest first)
            filtered_transactions.sort(key=lambda x: x.transaction_date, reverse=True)
            
            # Update table
            self.table.setRowCount(len(filtered_transactions))
            
            for row, transaction in enumerate(filtered_transactions):
                try:
                    self.table.setItem(row, 0, QTableWidgetItem(format_date(transaction.transaction_date)))
                    self.table.setItem(row, 1, QTableWidgetItem(transaction.transaction_type.title()))
                    self.table.setItem(row, 2, QTableWidgetItem(str(len(transaction.items))))
                    self.table.setItem(row, 3, QTableWidgetItem(format_currency(transaction.total_amount)))
                    
                    # Status with color
                    status_item = QTableWidgetItem(transaction.status.title())
                    if transaction.status == 'completed':
                        status_item.setForeground(Qt.darkGreen)
                    elif transaction.status == 'pending':
                        status_item.setForeground(Qt.darkYellow)
                    self.table.setItem(row, 4, status_item)
                    
                    # Buyer info
                    buyer_text = f"{transaction.buyer_name}\n{transaction.buyer_contact}" if transaction.buyer_name else "-"
                    self.table.setItem(row, 5, QTableWidgetItem(buyer_text))
                    
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
                    view_btn.clicked.connect(lambda checked, t=transaction: self.show_transaction_details(t))
                    actions_layout.addWidget(view_btn)
                    
                    if transaction.transaction_type == 'loan' and transaction.payment_status != 'paid':
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
                        pay_btn.clicked.connect(lambda checked, t=transaction: self.show_payment_dialog(t))
                        actions_layout.addWidget(pay_btn)
                        
                    actions_layout.addStretch()
                    self.table.setCellWidget(row, 6, actions_widget)
                    
                except Exception as e:
                    print(f"Error displaying transaction in row {row}: {e}")
                    continue
            
            # Update summary labels
            self.total_sales_label.setText(f"Total Sales: {format_currency(total_amount)}")
            self.cash_sales_label.setText(f"Cash Sales: {format_currency(cash_sales)}")
            self.loan_sales_label.setText(f"Loan Sales: {format_currency(loan_sales)}")
            
            # Update dashboard if it exists
            self.update_dashboard()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sales data: {str(e)}")
            print(f"Detailed error: {e}")
            
    def update_dashboard(self):
        """Update the dashboard metrics if it's open."""
        try:
            dashboard = self.window_manager.get_window('dashboard')
            if dashboard:
                dashboard.load_data()
        except Exception as e:
            print(f"Error updating dashboard: {e}")
        
    def show_new_sale_dialog(self):
        """Show dialog for creating a new sale."""
        try:
            # Get products from Firebase
            products_data = self.firebase.get_database_reference('products').get() or {}
            products = [
                Product.from_dict({**data, 'id': pid})
                for pid, data in products_data.items()
            ]
            
            dialog = AddSaleDialog(self, products)
            if dialog.exec_():
                try:
                    data = dialog.get_sale_data()
                    
                    # Create new transaction
                    transaction = Transaction(
                        id=self.firebase.db.reference('transactions').push().key,
                        items=[TransactionItem(**item) for item in data['items']],
                        total_amount=data['total_amount'],
                        transaction_date=data['transaction_date'],
                        transaction_type=data['transaction_type'],
                        status='completed',
                        created_by=self.user.id,
                        buyer_name=data.get('buyer_name'),
                        buyer_contact=data.get('buyer_contact'),
                        due_date=data.get('due_date'),
                        payment_status=data.get('payment_status'),
                        amount_paid=data.get('amount_paid')
                    )
                    
                    # Update product stock
                    for item in dialog.items:
                        product = item['product']
                        product.add_stock_update(
                            quantity=-item['quantity'],
                            update_type='sale',
                            updated_by=self.user.id,
                            notes=f"Sold in transaction {transaction.id}"
                        )
                        self.firebase.db.reference(f'products/{product.id}').update(product.to_dict())
                    
                    # Save transaction
                    self.firebase.db.reference(f'transactions/{transaction.id}').set(transaction.to_dict())
                    
                    # Reload data
                    self.load_data()
                    
                    # Update dashboard
                    self.update_dashboard()
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create sale: {str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
            
    def show_transaction_details(self, transaction: Transaction):
        """Show dialog with transaction details."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Transaction Details - {transaction.id}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Add transaction info
        info_text = f"""
        <h3>Transaction Information</h3>
        <p><b>Date:</b> {format_date(transaction.transaction_date)}</p>
        <p><b>Type:</b> {transaction.transaction_type.title()}</p>
        <p><b>Total Amount:</b> {format_currency(transaction.total_amount)}</p>
        <p><b>Status:</b> {transaction.status.title()}</p>
        """
        
        if transaction.transaction_type == 'loan':
            info_text += f"""
            <p><b>Buyer:</b> {transaction.buyer_name}</p>
            <p><b>Contact:</b> {transaction.buyer_contact or 'N/A'}</p>
            <p><b>Due Date:</b> {format_date(transaction.due_date)}</p>
            <p><b>Payment Status:</b> {transaction.payment_status.title()}</p>
            <p><b>Amount Paid:</b> {format_currency(transaction.amount_paid or 0)}</p>
            """
            
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        # Add items table
        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels([
            "Product ID", "Quantity", "Price", "Total"
        ])
        
        items_table.setRowCount(len(transaction.items))
        for row, item in enumerate(transaction.items):
            items_table.setItem(row, 0, QTableWidgetItem(item.product_id))
            items_table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
            items_table.setItem(row, 2, QTableWidgetItem(format_currency(item.price_per_unit)))
            items_table.setItem(row, 3, QTableWidgetItem(format_currency(item.total)))
            
        layout.addWidget(items_table)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
        
    def show_payment_dialog(self, transaction: Transaction):
        """Show dialog for recording a payment."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Payment")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Show current status
        layout.addRow(QLabel(f"<b>Total Amount:</b> {format_currency(transaction.total_amount)}"))
        layout.addRow(QLabel(f"<b>Amount Paid:</b> {format_currency(transaction.amount_paid or 0)}"))
        layout.addRow(QLabel(f"<b>Remaining:</b> {format_currency(transaction.total_amount - (transaction.amount_paid or 0))}"))
        
        # Add payment input
        payment_input = QDoubleSpinBox()
        payment_input.setMaximum(float(transaction.total_amount - (transaction.amount_paid or 0)))
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
                
                # Add payment
                transaction.add_payment(amount)
                
                # Save to Firebase
                self.firebase.db.reference(f'transactions/{transaction.id}').update(transaction.to_dict())
                
                # Reload data
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}") 
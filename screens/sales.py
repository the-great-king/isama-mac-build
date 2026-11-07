from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QComboBox, QDateEdit, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict
from models.user_model import User
from models.product_model import Product
from models.transaction_model import Transaction, TransactionItem, PaymentRecord
from models.cash_model import CashTransaction, CashTransactionType
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
        """Set up the dialog UI."""
        self.setWindowTitle("New Sale")
        self.setMinimumWidth(800)
        
        layout = QVBoxLayout(self)
        
        # Add form layout for sale details
        form_layout = QFormLayout()
        
        # Sale type
        self.sale_type_combo = QComboBox()
        self.sale_type_combo.addItems(["Cash", "Loan"])
        self.sale_type_combo.currentTextChanged.connect(self.on_sale_type_changed)
        form_layout.addRow("Sale Type:", self.sale_type_combo)
        
        # Buyer name (required for loans, optional for cash)
        self.buyer_name_input = QLineEdit()
        self.buyer_name_label = QLabel("Buyer Name:")
        form_layout.addRow(self.buyer_name_label, self.buyer_name_input)
        
        # Buyer contact (required for loans)
        self.buyer_contact_input = QLineEdit()
        self.buyer_contact_label = QLabel("Buyer Contact:")
        form_layout.addRow(self.buyer_contact_label, self.buyer_contact_input)
        
        # Due date (for loans)
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addMonths(1))
        self.due_date_label = QLabel("Due Date:")
        form_layout.addRow(self.due_date_label, self.due_date_input)
        
        layout.addLayout(form_layout)
        
        # Add items section
        items_group = QGroupBox("Items")
        items_layout = QVBoxLayout(items_group)
        
        # Add items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Product", "Price", "Quantity", "Total", "Actions"
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        items_layout.addWidget(self.items_table)
        
        # Add item button and product count label
        button_layout = QHBoxLayout()
        
        self.product_count_label = QLabel()
        self.update_product_count_label()
        button_layout.addWidget(self.product_count_label)
        
        button_layout.addStretch()
        
        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.show_add_item_dialog)
        button_layout.addWidget(add_item_btn)
        
        items_layout.addLayout(button_layout)
        
        layout.addWidget(items_group)
        
        # Add total amount display
        self.total_label = QLabel("Total Amount: TSHS 0.00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.total_label)
        
        # Description/Notes
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Optional: Add any notes about this sale")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        
        # Add buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
        
        # Initialize UI state
        self.on_sale_type_changed(self.sale_type_combo.currentText())
        
    def update_product_count_label(self):
        """Update the product count label."""
        available_products = sum(1 for p in self.products if p.stock > 0)
        total_products = len(self.products)
        self.product_count_label.setText(
            f"Available Products: {available_products} of {total_products}"
        )
        
    def on_sale_type_changed(self, sale_type: str):
        """Handle sale type change."""
        is_loan = sale_type.lower() == 'loan'
        
        # Buyer name is required for loans, optional for cash
        self.buyer_name_label.setText("Buyer Name:" + (" *" if is_loan else ""))
        
        # Contact and due date only for loans
        self.buyer_contact_input.setVisible(is_loan)
        self.buyer_contact_label.setVisible(is_loan)
        self.due_date_input.setVisible(is_loan)
        self.due_date_label.setVisible(is_loan)
        
    def show_add_item_dialog(self):
        """Show dialog for adding an item to the sale."""
        # Check if there are products with stock
        available_products = [p for p in self.products if p.stock > 0]
        if not available_products:
            QMessageBox.warning(
                self,
                "No Products Available",
                "There are no products with available stock. Please add stock to products first."
            )
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Item")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Product selection
        product_combo = QComboBox()
        for product in available_products:
            product_combo.addItem(f"{product.name} (Stock: {product.stock})", product)
        layout.addRow("Product:", product_combo)
        
        # Quantity input
        quantity_input = QSpinBox()
        quantity_input.setMinimum(1)
        quantity_input.setMaximum(
            product_combo.currentData().stock if product_combo.currentData() else 0
        )
        layout.addRow("Quantity:", quantity_input)
        
        # Price display
        price_label = QLabel()
        def update_price_label():
            product = product_combo.currentData()
            if product:
                price_label.setText(f"Price: {format_currency(product.price)}")
        update_price_label()
        product_combo.currentIndexChanged.connect(update_price_label)
        layout.addRow("", price_label)
        
        # Update quantity max when product changes
        def update_quantity_max():
            product = product_combo.currentData()
            if product:
                quantity_input.setMaximum(product.stock)
                quantity_input.setValue(min(quantity_input.value(), product.stock))
        
        product_combo.currentIndexChanged.connect(update_quantity_max)
        
        # Total display
        total_label = QLabel()
        def update_total():
            product = product_combo.currentData()
            if product:
                total = product.price * quantity_input.value()
                total_label.setText(f"Total: {format_currency(total)}")
        update_total()
        quantity_input.valueChanged.connect(update_total)
        product_combo.currentIndexChanged.connect(update_total)
        layout.addRow("", total_label)
        
        # Buttons
        button_box = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_box.addWidget(add_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
        if dialog.exec_():
            product = product_combo.currentData()
            quantity = quantity_input.value()
            
            # Add item to sale
            self.add_item(product, quantity)
            
    def add_item(self, product: Product, quantity: int):
        """Add an item to the sale."""
        # Calculate total
        total = product.price * quantity
        
        # Add to items list
        self.items.append({
            'product': product,
            'quantity': quantity,
            'price': product.price,
            'total': total
        })
        
        # Update table
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        self.items_table.setItem(row, 0, QTableWidgetItem(product.name))
        self.items_table.setItem(row, 1, QTableWidgetItem(format_currency(product.price)))
        self.items_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
        self.items_table.setItem(row, 3, QTableWidgetItem(format_currency(total)))
        
        # Add remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_item(row))
        self.items_table.setCellWidget(row, 4, remove_btn)
        
        # Update total
        self.update_total()
        
    def remove_item(self, row: int):
        """Remove an item from the sale."""
        self.items.pop(row)
        self.items_table.removeRow(row)
        self.update_total()
        
    def update_total(self):
        """Update the total amount display."""
        total = sum(item['total'] for item in self.items)
        self.total_label.setText(f"Total Amount: {format_currency(total)}")
        
    def get_sale_data(self) -> dict:
        """Get the sale data from the form."""
        if not self.items:
            raise ValueError("Please add at least one item to the sale")
            
        total_amount = sum(item['total'] for item in self.items)
        transaction_type = self.sale_type_combo.currentText().lower()
        buyer_name = self.buyer_name_input.text().strip() or None  # None for one-time clients
        description = self.description_input.toPlainText().strip() or None  # None if empty
        
        data = {
            'total_amount': total_amount,
            'transaction_type': transaction_type,
            'transaction_date': datetime.now(),
            'items': [
                {
                    'product_id': item['product'].id,
                    'quantity': item['quantity'],
                    'price_per_unit': item['price'],
                    'total': item['total']
                }
                for item in self.items
            ]
        }
        
        # Only add optional fields if they have values
        if buyer_name:
            data['buyer_name'] = buyer_name
            
        if description:
            data['description'] = description
        
        if transaction_type == 'loan':
            if not buyer_name:
                raise ValueError("Buyer name is required for loan sales")
                
            data.update({
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
        self.window_manager = WindowManager()  # Add window manager
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Set up the sales window UI."""
        self.setWindowTitle("Sales Management")
        self.setMinimumSize(900, 650)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        header = QLabel("Sales Management")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        button_layout = QHBoxLayout()
        add_sale_btn = QPushButton("New Sale")
        add_sale_btn.clicked.connect(self.show_add_sale_dialog)
        button_layout.addWidget(add_sale_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        filter_layout = QHBoxLayout()

        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today", "This Week", "This Month", "Custom Range"])
        self.date_filter.currentTextChanged.connect(self.update_date_filters_visibility)
        self.date_filter.currentTextChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Date:"))
        filter_layout.addWidget(self.date_filter)

        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_label = QLabel("From:")
        filter_layout.addWidget(self.start_date_label)
        filter_layout.addWidget(self.start_date_input)

        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_label = QLabel("To:")
        filter_layout.addWidget(self.end_date_label)
        filter_layout.addWidget(self.end_date_input)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Cash", "Loan"])
        self.type_filter.currentTextChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Paid", "Partial Paid", "Unpaid"])
        self.status_filter.currentTextChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)

        self.sort_filter = QComboBox()
        self.sort_filter.addItems(["Newest First", "Oldest First"])
        self.sort_filter.currentTextChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Sort:"))
        filter_layout.addWidget(self.sort_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.update_date_filters_visibility()
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Type", "Buyer", "Amount", "Status", "Description", "Actions"
        ])
        layout.addWidget(self.table)

    def update_date_filters_visibility(self):
        """Show or hide custom date range inputs."""
        custom_range = self.date_filter.currentText() == "Custom Range"
        self.start_date_label.setVisible(custom_range)
        self.start_date_input.setVisible(custom_range)
        self.end_date_label.setVisible(custom_range)
        self.end_date_input.setVisible(custom_range)
        
    def load_data(self):
        """Load sales data from Firebase with date, type, status, and sorting filters."""
        try:
            self.table.setRowCount(0)
            transactions = self.firebase.get_transactions()

            date_filter = self.date_filter.currentText()
            type_filter = self.type_filter.currentText().lower()
            status_filter = self.status_filter.currentText().lower()
            sort_desc = self.sort_filter.currentText() == "Newest First"

            filtered_transactions = []
            for transaction in transactions:
                if type_filter != "all types" and transaction.transaction_type.lower() != type_filter:
                    continue

                if transaction.transaction_type == 'loan':
                    payment_status = (transaction.payment_status or 'unpaid').lower()
                    if status_filter == 'paid' and payment_status != 'paid':
                        continue
                    if status_filter == 'partial paid' and payment_status != 'partial':
                        continue
                    if status_filter == 'unpaid' and payment_status != 'unpaid':
                        continue
                elif status_filter in ['paid', 'partial paid', 'unpaid']:
                    continue

                if date_filter != "All Time":
                    transaction_date = transaction.transaction_date.date()
                    today = datetime.now().date()

                    if date_filter == "Today":
                        if transaction_date != today:
                            continue
                    elif date_filter == "This Week":
                        week_start = today - timedelta(days=today.weekday())
                        week_end = week_start + timedelta(days=6)
                        if not (week_start <= transaction_date <= week_end):
                            continue
                    elif date_filter == "This Month":
                        month_start = today.replace(day=1)
                        if transaction_date < month_start:
                            continue
                    elif date_filter == "Custom Range":
                        start_date = self.start_date_input.date().toPython()
                        end_date = self.end_date_input.date().toPython()
                        if not (start_date <= transaction_date <= end_date):
                            continue

                filtered_transactions.append(transaction)

            filtered_transactions.sort(
                key=lambda t: t.transaction_date,
                reverse=sort_desc
            )

            for transaction in filtered_transactions:
                row = self.table.rowCount()
                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(format_date(transaction.transaction_date)))
                self.table.setItem(row, 1, QTableWidgetItem(transaction.transaction_type.title()))
                self.table.setItem(row, 2, QTableWidgetItem(transaction.display_name))
                self.table.setItem(row, 3, QTableWidgetItem(format_currency(transaction.total_amount)))

                if transaction.transaction_type == 'loan':
                    status = (transaction.payment_status or 'unpaid').title()
                    if status == 'Partial':
                        status = 'Partial Paid'
                    if transaction.amount_paid is not None:
                        status = f"{status} ({format_currency(transaction.amount_paid)})"
                else:
                    status = "Paid"

                self.table.setItem(row, 4, QTableWidgetItem(status))
                self.table.setItem(row, 5, QTableWidgetItem(transaction.description or ""))

                if transaction.transaction_type == 'loan' and (transaction.payment_status or 'unpaid') != 'paid':
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(0, 0, 0, 0)

                    pay_btn = QPushButton("Pay")
                    pay_btn.clicked.connect(lambda checked, t=transaction: self.show_payment_dialog(t))
                    action_layout.addWidget(pay_btn)

                    self.table.setCellWidget(row, 6, action_widget)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sales data: {str(e)}")
            
    def show_add_sale_dialog(self):
        """Show dialog for adding a new sale."""
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
                    # Get sale data
                    data = dialog.get_sale_data()
                    
                    # Create transaction
                    transaction = Transaction(
                        id=self.firebase.get_database_reference('transactions').push().key,
                        transaction_type=data['transaction_type'],
                        transaction_date=data['transaction_date'],
                        total_amount=data['total_amount'],
                        items=[TransactionItem(**item) for item in data['items']],
                        created_by=self.user.id,
                        buyer_name=data.get('buyer_name'),
                        description=data.get('description'),
                        buyer_contact=data.get('buyer_contact'),
                        due_date=data.get('due_date'),
                        payment_status=data.get('payment_status'),
                        amount_paid=data.get('amount_paid')
                    )
                    
                    # Save to Firebase - this will handle stock updates
                    self.firebase.add_transaction(transaction)
                    
                    # Reload data
                    self.load_data()
                    
                    # Update dashboard if it exists
                    self.update_dashboard()
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add sale: {str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
            
    def show_payment_dialog(self, transaction: Transaction):
        """Show dialog for recording a loan payment."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Payment")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Show current status
        layout.addRow(QLabel(f"<b>Total Amount:</b> {format_currency(transaction.total_amount)}"))
        layout.addRow(QLabel(f"<b>Amount Paid:</b> {format_currency(transaction.amount_paid or 0)}"))
        layout.addRow(QLabel(f"<b>Remaining:</b> {format_currency(transaction.total_amount - (transaction.amount_paid or 0))}"))
        
        # Show payment history if exists
        if transaction.payment_history:
            history_group = QGroupBox("Payment History")
            history_layout = QVBoxLayout(history_group)
            
            history_table = QTableWidget()
            history_table.setColumnCount(2)
            history_table.setHorizontalHeaderLabels([
                "Date", "Amount"
            ])
            
            # Convert dictionary items to PaymentRecord objects if needed
            payment_records = []
            for payment in transaction.payment_history:
                if isinstance(payment, dict):
                    payment_records.append(PaymentRecord.from_dict(payment))
                else:
                    payment_records.append(payment)
            
            history_table.setRowCount(len(payment_records))
            for row, payment in enumerate(sorted(payment_records, key=lambda x: x.date)):
                history_table.setItem(row, 0, QTableWidgetItem(format_date(payment.date)))
                history_table.setItem(row, 1, QTableWidgetItem(format_currency(payment.amount)))
                
            history_layout.addWidget(history_table)
            layout.addRow(history_group)
        
        # Amount input
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(float(transaction.total_amount - (transaction.amount_paid or 0)))
        amount_input.setValue(amount_input.maximum())
        amount_input.setDecimals(2)
        layout.addRow("Payment Amount:", amount_input)
        
        # Buttons
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
                # Update transaction
                payment_amount = Decimal(str(amount_input.value()))
                
                # Add payment with history
                transaction.add_payment(payment_amount, self.user.id)
                
                # Save to Firebase - this will handle the cash transaction
                self.firebase.update_transaction(transaction)
                
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
                
    def closeEvent(self, event):
        """Handle window close event."""
        self.deleteLater()
        super().closeEvent(event) 
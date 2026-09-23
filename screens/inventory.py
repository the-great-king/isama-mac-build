from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Slot
from decimal import Decimal
from datetime import datetime
from models.user_model import User
from models.product_model import Product, StockUpdate
from models.category_model import Category
from firebase.db import FirebaseManager
from utils.helpers import format_currency, format_date, format_stock_status
from utils.window_manager import WindowManager

class AddProductDialog(QDialog):
    """Dialog for adding/editing a product."""
    
    def __init__(self, parent=None, product: Product = None):
        super().__init__(parent)
        self.product = product
        self.firebase = FirebaseManager()
        self.setup_ui()
        self.load_categories()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Product" if not self.product else "Edit Product")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Name input
        self.name_input = QLineEdit()
        if self.product:
            self.name_input.setText(self.product.name)
        layout.addRow("Name:", self.name_input)
        
        # Category input
        self.category_combo = QComboBox()
        if self.product:
            self.category_combo.addItem(self.product.category)
        layout.addRow("Category:", self.category_combo)
        
        # Price input
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(1000000)
        self.price_input.setDecimals(2)
        if self.product:
            self.price_input.setValue(float(self.product.price))
        layout.addRow("Price:", self.price_input)
        
        # Stock inputs
        if not self.product:  # Only show stock input for new products
            self.stock_input = QSpinBox()
            self.stock_input.setMaximum(1000000)
            layout.addRow("Initial Stock:", self.stock_input)
            
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setMaximum(1000000)
        if self.product:
            self.min_stock_input.setValue(self.product.min_stock)
        layout.addRow("Minimum Stock:", self.min_stock_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow("", button_layout)
        
    def load_categories(self):
        """Load categories from Firebase and store each category's ID in the combo box data."""
        try:
            self.category_combo.clear()

            db = self.firebase.get_database_reference('categories')
            categories_data = db.get() or {}

            for category_id, data in categories_data.items():
                try:
                    data['id'] = category_id
                    category = Category.from_dict(data)
                    if category.is_active:
                        self.category_combo.addItem(category.name, category.id)
                except Exception as e:
                    print(f"Error loading category {category_id}: {e}")
                    continue

            if self.product:
                if getattr(self.product, 'category_id', None):
                    index = self.category_combo.findData(self.product.category_id)
                else:
                    index = self.category_combo.findText(self.product.category)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load categories: {str(e)}")

    def get_product_data(self) -> dict:
        """Get the product data from the form."""
        selected_category_id = self.category_combo.currentData()
        data = {
            'name': self.name_input.text().strip(),
            'category': self.category_combo.currentText(),
            'category_id': selected_category_id,
            'price': Decimal(str(self.price_input.value())),
            'min_stock': self.min_stock_input.value()
        }

        if not self.product:
            data['stock'] = self.stock_input.value()

        return data

class InventoryWindow(QMainWindow):
    """Window for managing product inventory."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.window_manager = WindowManager()  # Add window manager
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Set up the inventory window UI."""
        self.setWindowTitle("Isama Management System - Inventory")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header
        header_layout = QHBoxLayout()
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a73e8;")
        header_layout.addWidget(title)
        
        # Add search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by product name...")
        self.search_input.textChanged.connect(self.load_data)
        self.search_input.setMaximumWidth(250)
        header_layout.addWidget(self.search_input)
        
        header_layout.addStretch()
        
        # Add product button
        add_btn = QPushButton("Add Product")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Category", "Price", "Stock", "Min Stock",
            "Status", "Actions"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
    def load_data(self):
        """Load inventory data from Firebase."""
        try:
            # Get products from Firebase
            db = self.firebase.get_database_reference('products')
            products_data = db.get() or {}
            
            # Filter products by search text
            search_text = self.search_input.text().lower().strip()
            filtered_products = []
            
            for product_id, data in products_data.items():
                try:
                    data['id'] = product_id
                    product = Product.from_dict(data)

                    if not getattr(product, 'is_active', True):
                        continue
                    
                    # Apply search filter
                    if search_text and search_text not in product.name.lower():
                        continue
                        
                    filtered_products.append(product)
                except Exception as e:
                    print(f"Error loading product {product_id}: {e}")
                    continue
            
            # Update table
            self.table.setRowCount(len(filtered_products))
            
            for row, product in enumerate(filtered_products):
                try:
                    # Add product data to table
                    self.table.setItem(row, 0, QTableWidgetItem(product.name))
                    self.table.setItem(row, 1, QTableWidgetItem(product.category))
                    self.table.setItem(row, 2, QTableWidgetItem(format_currency(product.price)))
                    self.table.setItem(row, 3, QTableWidgetItem(str(product.stock)))
                    self.table.setItem(row, 4, QTableWidgetItem(str(product.min_stock)))
                    
                    # Add status with color
                    status_text, color_class = format_stock_status(product.stock, product.min_stock)
                    status_item = QTableWidgetItem(status_text)
                    status_item.setForeground(Qt.red if color_class == 'text-red-600'
                                            else Qt.darkYellow if color_class == 'text-yellow-600'
                                            else Qt.darkGreen)
                    self.table.setItem(row, 5, status_item)
                    
                    # Add action buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(4, 4, 4, 4)
                    
                    edit_btn = QPushButton("Edit")
                    edit_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ffc107;
                            color: black;
                            border: none;
                            padding: 4px 8px;
                            border-radius: 2px;
                        }
                        QPushButton:hover {
                            background-color: #e0a800;
                        }
                    """)
                    edit_btn.clicked.connect(lambda checked, p=product: self.show_edit_dialog(p))
                    
                    update_stock_btn = QPushButton("Update Stock")
                    update_stock_btn.setStyleSheet("""
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
                    update_stock_btn.clicked.connect(lambda checked, p=product: self.show_stock_update_dialog(p))

                    delete_btn = QPushButton("Delete")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #dc3545;
                            color: white;
                            border: none;
                            padding: 4px 8px;
                            border-radius: 2px;
                        }
                        QPushButton:hover {
                            background-color: #c82333;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, p=product: self.delete_product(p))
                    
                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(update_stock_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_layout.addStretch()
                    
                    self.table.setCellWidget(row, 6, actions_widget)
                    
                except Exception as e:
                    print(f"Error displaying product in row {row}: {e}")
                    continue
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load inventory data: {str(e)}")
            print(f"Detailed error: {e}")  # For debugging
            
    def update_dashboard(self):
        """Update the dashboard metrics if it's open."""
        try:
            dashboard = self.window_manager.get_window('dashboard')
            if dashboard:
                dashboard.load_data()
        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def show_add_dialog(self):
        """Show dialog for adding a new product."""
        dialog = AddProductDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_product_data()

                product = Product(
                    id=self.firebase.db.reference('products').push().key,
                    name=data['name'],
                    category=data['category'],
                    category_id=data.get('category_id'),
                    price=data['price'],
                    stock=data['stock'],
                    min_stock=data['min_stock'],
                    created_at=datetime.now(),
                    stock_updates=[
                        StockUpdate(
                            quantity=data['stock'],
                            date=datetime.now(),
                            type='initial',
                            updated_by=self.user.id,
                            notes="Initial stock"
                        )
                    ]
                )

                self.firebase.db.reference(f'products/{product.id}').set(product.to_dict())
                
                # Reload data
                self.load_data()
                
                # Update dashboard if it exists
                self.update_dashboard()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add product: {str(e)}")
                
    def show_edit_dialog(self, product: Product):
        """Show dialog for editing a product."""
        dialog = AddProductDialog(self, product)
        if dialog.exec_():
            try:
                data = dialog.get_product_data()

                product.name = data['name']
                product.category = data['category']
                product.category_id = data.get('category_id')
                product.price = data['price']
                product.min_stock = data['min_stock']

                self.firebase.db.reference(f'products/{product.id}').update(product.to_dict())
                
                # Reload data
                self.load_data()
                
                # Update dashboard if it exists
                self.update_dashboard()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update product: {str(e)}")
                
    def delete_product(self, product: Product):
        """Permanently delete a product after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{product.name}'?\n\nThis action cannot be undone and the product cannot be retrieved after deletion.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.firebase.db.reference(f'products/{product.id}').delete()
            self.load_data()
            self.update_dashboard()
            QMessageBox.information(self, "Deleted", f"'{product.name}' has been deleted successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete product: {str(e)}")

    def show_stock_update_dialog(self, product: Product):
        """Show dialog for updating stock quantity."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Update Stock")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        quantity_input = QSpinBox()
        quantity_input.setMinimum(-product.stock)  # Don't allow reducing below 0
        quantity_input.setMaximum(1000000)
        
        notes_input = QLineEdit()
        
        layout.addRow("Quantity Change:", quantity_input)
        layout.addRow("Notes:", notes_input)
        
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
                quantity = quantity_input.value()
                notes = notes_input.text().strip()
                
                # Add stock update
                product.add_stock_update(
                    quantity=quantity,
                    update_type='adjustment',
                    updated_by=self.user.id,
                    notes=notes
                )
                
                # Save to Firebase
                self.firebase.db.reference(f'products/{product.id}').update(product.to_dict())
                
                # Reload data
                self.load_data()
                
                # Update dashboard if it exists
                self.update_dashboard()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update stock: {str(e)}") 
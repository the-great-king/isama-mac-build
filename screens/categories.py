from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QLineEdit, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from datetime import datetime
from models.user_model import User
from models.category_model import Category
from firebase.db import FirebaseManager
from utils.helpers import format_date

class AddCategoryDialog(QDialog):
    """Dialog for adding/editing a category."""
    
    def __init__(self, parent=None, category: Category = None):
        super().__init__(parent)
        self.category = category
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Category" if not self.category else "Edit Category")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Name input
        self.name_input = QLineEdit()
        if self.category:
            self.name_input.setText(self.category.name)
        layout.addRow("Name:", self.name_input)
        
        # Description input
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if self.category:
            self.description_input.setText(self.category.description)
        layout.addRow("Description:", self.description_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow("", button_layout)
        
    def get_category_data(self) -> dict:
        """Get the category data from the form."""
        return {
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText().strip()
        }

class CategoryWindow(QMainWindow):
    """Window for managing product categories."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.firebase = FirebaseManager()
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Set up the categories window UI."""
        self.setWindowTitle("Isama Management System - Categories")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header
        header_layout = QHBoxLayout()
        title = QLabel("Category Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a73e8;")
        header_layout.addWidget(title)
        
        # Add new category button
        new_category_btn = QPushButton("New Category")
        new_category_btn.setStyleSheet("""
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
        new_category_btn.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(new_category_btn)
        layout.addLayout(header_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Name", "Description", "Created", "Actions"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
    def load_data(self):
        """Load categories from Firebase."""
        try:
            # Get categories from Firebase
            db = self.firebase.get_database_reference('categories')
            categories_data = db.get() or {}
            
            # Update table
            self.table.setRowCount(len(categories_data))
            
            for row, (category_id, data) in enumerate(categories_data.items()):
                try:
                    # Add ID to data for category creation
                    data['id'] = category_id
                    category = Category.from_dict(data)
                    
                    if not category.is_active:
                        continue
                    
                    # Add category data to table
                    self.table.setItem(row, 0, QTableWidgetItem(category.name))
                    self.table.setItem(row, 1, QTableWidgetItem(category.description))
                    self.table.setItem(row, 2, QTableWidgetItem(format_date(category.created_at)))
                    
                    # Add action buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(4, 4, 4, 4)
                    
                    edit_btn = QPushButton("Edit")
                    edit_btn.setStyleSheet("""
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
                    edit_btn.clicked.connect(lambda checked, c=category: self.show_edit_dialog(c))
                    actions_layout.addWidget(edit_btn)
                    
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
                    delete_btn.clicked.connect(lambda checked, c=category: self.delete_category(c))
                    actions_layout.addWidget(delete_btn)
                    
                    actions_layout.addStretch()
                    self.table.setCellWidget(row, 3, actions_widget)
                    
                except Exception as e:
                    print(f"Error loading category {category_id}: {e}")
                    continue
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load categories: {str(e)}")
            
    def show_add_dialog(self):
        """Show dialog for adding a new category."""
        dialog = AddCategoryDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_category_data()
                
                # Create new category
                category = Category(
                    id=self.firebase.db.reference('categories').push().key,
                    name=data['name'],
                    description=data['description'],
                    created_at=datetime.now()
                )
                
                # Save to Firebase
                self.firebase.db.reference(f'categories/{category.id}').set(category.to_dict())
                
                # Reload data
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add category: {str(e)}")
                
    def show_edit_dialog(self, category: Category):
        """Show dialog for editing a category."""
        dialog = AddCategoryDialog(self, category)
        if dialog.exec_():
            try:
                data = dialog.get_category_data()
                
                # Update category data
                category.name = data['name']
                category.description = data['description']
                
                # Save to Firebase
                self.firebase.db.reference(f'categories/{category.id}').update(category.to_dict())
                
                # Reload data
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update category: {str(e)}")
                
    def delete_category(self, category: Category):
        """Delete (deactivate) a category after checking linked inventory."""
        try:
            products_data = self.firebase.get_database_reference('products').get() or {}
            linked_products = []

            for product_id, data in products_data.items():
                if not isinstance(data, dict):
                    continue
                is_linked = (
                    (data.get('category_id') == category.id)
                    or (
                        data.get('category_id') is None
                        and data.get('category') == category.name
                    )
                )
                if is_linked and data.get('is_active', True) is not False:
                    linked_products.append(data.get('name', product_id))

            if linked_products:
                QMessageBox.warning(
                    self,
                    "Cannot Delete Category",
                    f"This category is linked to inventory items: {', '.join(linked_products)}.\n\nPlease delete the inventory first, then delete the category."
                )
                return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check category usage: {str(e)}")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the category '{category.name}'?\n\nThis action cannot be undone and the category cannot be retrieved after deletion.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.firebase.db.reference(f'categories/{category.id}').delete()
                self.load_data()
                QMessageBox.information(self, "Deleted", f"'{category.name}' has been deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete category: {str(e)}") 
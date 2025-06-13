from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from models.user_model import User
from .inventory import InventoryWindow
from .sales import SalesWindow
from .loans import LoansWindow
from .cash import CashWindow
from .dashboard import DashboardWindow
from utils.window_manager import WindowManager

class MainWindow(QMainWindow):
    """Main window of the Isama Management System."""
    
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.window_manager = WindowManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("Isama Management System")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add welcome message
        welcome = QLabel(f"Welcome, {self.user.name}!")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("font-size: 24px; margin: 20px;")
        layout.addWidget(welcome)
        
        # Add navigation buttons
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.clicked.connect(self.show_dashboard)
        layout.addWidget(dashboard_btn)
        
        inventory_btn = QPushButton("Inventory")
        inventory_btn.clicked.connect(self.show_inventory)
        layout.addWidget(inventory_btn)
        
        sales_btn = QPushButton("Sales")
        sales_btn.clicked.connect(self.show_sales)
        layout.addWidget(sales_btn)
        
        loans_btn = QPushButton("Loans")
        loans_btn.clicked.connect(self.show_loans)
        layout.addWidget(loans_btn)
        
        cash_btn = QPushButton("Cash Management")
        cash_btn.clicked.connect(self.show_cash)
        layout.addWidget(cash_btn)
        
        # Add stretch to push buttons to the top
        layout.addStretch()
        
    def show_dashboard(self):
        """Show the dashboard window."""
        window = self.window_manager.get_window('dashboard')
        if not window:
            window = DashboardWindow(self.user)
        window.show()
        window.activateWindow()
        
    def show_inventory(self):
        """Show the inventory window."""
        window = self.window_manager.get_window('inventory')
        if not window:
            window = InventoryWindow(self.user)
        window.show()
        window.activateWindow()
        
    def show_sales(self):
        """Show the sales window."""
        window = self.window_manager.get_window('sales')
        if not window:
            window = SalesWindow(self.user)
        window.show()
        window.activateWindow()
        
    def show_loans(self):
        """Show the loans window."""
        window = self.window_manager.get_window('loans')
        if not window:
            window = LoansWindow(self.user)
        window.show()
        window.activateWindow()
        
    def show_cash(self):
        """Show the cash management window."""
        window = self.window_manager.get_window('cash')
        if not window:
            window = CashWindow(self.user)
        window.show()
        window.activateWindow() 
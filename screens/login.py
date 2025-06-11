import os
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from firebase_admin import auth
from firebase.db import FirebaseManager
from models.user_model import User
from screens.dashboard import DashboardWindow
from utils.helpers import validate_email

class LoginWindow(QMainWindow):
    """
    Login window for the Isama Management System.
    Handles user authentication using Firebase Auth.
    """
    
    def __init__(self):
        super().__init__()
        self.firebase = FirebaseManager()
        self.load_ui()
        self.setup_connections()
        self.setup_logo()
        
    def load_ui(self):
        """Load the UI from the .ui file."""
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'login.ui')
        self.ui = loader.load(ui_file_path)
        
        # Set window properties
        self.setCentralWidget(self.ui.centralwidget)
        self.setWindowTitle("Isama Management System - Login")
        self.setFixedSize(400, 600)  # Made taller to accommodate logo
        
        # Store references to UI elements we'll need
        self.logo_label = self.ui.logoLabel
        self.email_input = self.ui.emailInput
        self.password_input = self.ui.passwordInput
        self.login_button = self.ui.loginButton
        self.error_label = self.ui.errorLabel
        
        # Set focus to email input
        self.email_input.setFocus()
        
    def setup_logo(self):
        """Set up the logo image."""
        try:
            # Load and scale the logo
            logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'isama_logo.jpg')
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
    def setup_connections(self):
        """Connect UI signals to slots."""
        self.login_button.clicked.connect(self.handle_login)
        self.email_input.returnPressed.connect(self.focus_password)
        self.password_input.returnPressed.connect(self.handle_login)
        
    @Slot()
    def focus_password(self):
        """Move focus to password field when Enter is pressed in email field."""
        self.password_input.setFocus()
        
    @Slot()
    def handle_login(self):
        """Handle the login button click or Enter key press."""
        # Clear any previous error message
        self.error_label.setText("")
        
        # Get input values
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not email or not password:
            self.show_error("Please enter both email and password.")
            return
            
        if not validate_email(email):
            self.show_error("Please enter a valid email address.")
            return
            
        # Attempt to sign in with Firebase
        try:
            # Sign in with email/password using REST API
            auth_result = self.firebase.sign_in_with_email_password(email, password)
            
            # Get the user details
            user = auth_result['user']
            
            # Create User model instance
            user_model = User(
                id=user.uid,
                email=user.email,
                role=user.custom_claims.get('role', 'staff') if user.custom_claims else 'staff',
                name=user.display_name or email.split('@')[0],
                created_at=user.user_metadata.creation_timestamp,
                last_login=user.user_metadata.last_sign_in_timestamp
            )
            
            # Show the dashboard
            self.show_dashboard(user_model)
            
        except ValueError as e:
            self.show_error(str(e))
            print(f"Login error: {e}")  # Log the actual error for debugging
            
    def show_error(self, message: str):
        """Display an error message in the UI."""
        self.error_label.setText(message)
        
    def show_dashboard(self, user: User):
        """
        Create and show the dashboard window.
        
        Args:
            user (User): The authenticated user model
        """
        self.dashboard = DashboardWindow(user)
        self.dashboard.show()
        self.close() 
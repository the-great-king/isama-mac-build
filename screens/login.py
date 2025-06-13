import os
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
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
        self.rotation_angle = 0
        self.setup_loading_indicator()
        
    def setup_loading_indicator(self):
        """Create the loading indicator pixmap."""
        size = 40
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the black circle
        pen = QPen(QColor("#000000"))  # Black color
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw the red arc
        pen = QPen(QColor("#e63946"))  # Red color
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawArc(4, 4, size-8, size-8, 0, 90 * 16)
        
        painter.end()
        self.loading_label.setPixmap(pixmap)
        
    def load_ui(self):
        """Load the UI from the .ui file."""
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'login.ui')
        self.ui = loader.load(ui_file_path)
        
        # Set window properties
        self.setCentralWidget(self.ui.centralwidget)
        self.setWindowTitle("Isama Management System - Login")
        self.setFixedSize(400, 600)
        
        # Store references to UI elements we'll need
        self.logo_label = self.ui.logoLabel
        self.email_input = self.ui.emailInput
        self.password_input = self.ui.passwordInput
        self.login_button = self.ui.loginButton
        self.error_label = self.ui.errorLabel
        self.loading_label = self.ui.loadingLabel
        
        # Hide loading indicator initially
        self.loading_label.hide()
        
        # Set focus to email input
        self.email_input.setFocus()
        
    def setup_logo(self):
        """Set up the logo image."""
        try:
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
        
    def start_loading(self):
        """Start the loading animation."""
        # Clear error message BEFORE starting loading
        self.error_label.clear()
        self.error_label.repaint()
        
        # Disable inputs
        self.login_button.setEnabled(False)
        self.email_input.setEnabled(False)
        self.password_input.setEnabled(False)
        
        # Show and start loading animation
        self.loading_label.raise_()  # Bring to front
        self.loading_label.show()
        self.loading_label.repaint()  # Force immediate update
        print("Loading indicator shown")  # Debug print
        
        self.rotation_angle = 0
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_loading)
        self.rotation_timer.start(50)
        
    def rotate_loading(self):
        """Rotate the loading indicator."""
        self.rotation_angle = (self.rotation_angle + 15) % 360  # Faster rotation
        
        # Create new pixmap for rotation
        size = 40
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the black circle
        pen = QPen(QColor("#000000"))  # Black color
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw the rotating red arc
        pen = QPen(QColor("#e63946"))  # Red color
        pen.setWidth(4)
        painter.setPen(pen)
        # Calculate the arc angles based on rotation
        start_angle = self.rotation_angle * 16
        span_angle = 90 * 16
        painter.drawArc(4, 4, size-8, size-8, start_angle, span_angle)
        
        painter.end()
        self.loading_label.setPixmap(pixmap)
        self.loading_label.repaint()
        
    def stop_loading(self, success: bool = True):
        """Stop the loading animation."""
        if hasattr(self, 'rotation_timer'):
            self.rotation_timer.stop()
        
        self.loading_label.hide()
        self.login_button.setEnabled(True)
        self.email_input.setEnabled(True)
        self.password_input.setEnabled(True)
        
        if success:
            # Small delay before showing dashboard
            QTimer.singleShot(200, lambda: self.show_dashboard(self.current_user))
        
    @Slot()
    def handle_login(self):
        """Handle the login button click or Enter key press."""
        # Start loading animation immediately
        self.start_loading()
        
        # Get input values
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not email or not password:
            self.stop_loading(False)
            self.show_error("Please enter both email and password.")
            return
            
        if not validate_email(email):
            self.stop_loading(False)
            self.show_error("Please enter a valid email address.")
            return
            
        # Attempt to sign in with Firebase
        try:
            # Sign in with email/password using REST API
            auth_result = self.firebase.sign_in_with_email_password(email, password)
            
            # Get the user details
            user = auth_result['user']
            
            # Create User model instance
            self.current_user = User(
                id=user.uid,
                email=user.email,
                role=user.custom_claims.get('role', 'staff') if user.custom_claims else 'staff',
                name=user.display_name or email.split('@')[0],
                created_at=user.user_metadata.creation_timestamp,
                last_login=user.user_metadata.last_sign_in_timestamp
            )
            
            # Complete loading animation and show dashboard
            self.stop_loading(True)
            
        except ValueError as e:
            self.stop_loading(False)
            self.show_error(str(e))
            print(f"Login error: {e}")
            
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
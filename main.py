import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from screens.login import LoginWindow

def main():
    """
    Main entry point of the Isama Management System.
    Initializes the application and displays the login window.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Isama Management System")
    
    # Set application icons
    if sys.platform == "win32":
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "isama_icon.ico")
        app.setWindowIcon(QIcon(icon_path))
    elif sys.platform == "darwin":  # macOS
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "isama_icon.icns")
        app.setWindowIcon(QIcon(icon_path))
    
    # Show the login window
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 

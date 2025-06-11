import os
import requests
import firebase_admin
from firebase_admin import credentials, db, auth
from dotenv import load_dotenv
from .web_config import SIGN_IN_URL

# Load environment variables
load_dotenv()

class FirebaseManager:
    """
    Manages Firebase connections and operations for the Isama Management System.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize Firebase connection using service account credentials.
        
        IMPORTANT: Before running the application:
        1. Download your Firebase service account key JSON file
        2. Place it in the /firebase directory as 'khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json'
        3. DO NOT commit this file to version control!
        4. Add 'firebase/khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json' to your .gitignore file
        """
        try:
            # Initialize Firebase Admin SDK
            cred_path = os.path.join(os.path.dirname(__file__), 'khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json')
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
            })
            self.db = db
            self.auth = auth
            
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            print("Please ensure you have placed the khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json file in the firebase directory")
            raise

    def sign_in_with_email_password(self, email, password):
        """Sign in user with email and password using Firebase REST API."""
        try:
            # Prepare the request payload
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            # Make the REST API call
            response = requests.post(SIGN_IN_URL, json=payload)
            
            if response.status_code == 200:
                # Get the ID token and user data
                auth_data = response.json()
                id_token = auth_data["idToken"]
                
                # Get additional user info from Admin SDK
                user = self.auth.get_user_by_email(email)
                
                # Return both the token and user data
                return {
                    "id_token": id_token,
                    "user": user
                }
            else:
                error_message = response.json().get("error", {}).get("message", "Unknown error")
                raise ValueError(f"Authentication failed: {error_message}")
                
        except requests.RequestException as e:
            raise ValueError(f"Network error during authentication: {str(e)}")
        except Exception as e:
            raise ValueError(f"Authentication error: {str(e)}")

    def get_user_by_email(self, email):
        """Get user data from Firebase Auth by email."""
        try:
            return self.auth.get_user_by_email(email)
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def verify_id_token(self, id_token):
        """Verify Firebase ID token."""
        try:
            return self.auth.verify_id_token(id_token)
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None

    def get_database_reference(self, path):
        """Get a database reference for the specified path."""
        return self.db.reference(path)

# Create a .gitignore file to prevent committing sensitive data
with open(os.path.join(os.path.dirname(__file__), '..', '.gitignore'), 'a') as f:
    f.write('\nfirebase/khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json\n.env\n') 
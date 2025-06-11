"""Firebase Web API configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Firebase Web API Key from environment variable
FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')
if not FIREBASE_WEB_API_KEY:
    raise ValueError("FIREBASE_WEB_API_KEY not found in environment variables. Please add it to your .env file.")

# Firebase Auth REST API endpoints
AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1"
SIGN_IN_URL = f"{AUTH_BASE_URL}/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
SIGN_UP_URL = f"{AUTH_BASE_URL}/accounts:signUp?key={FIREBASE_WEB_API_KEY}" 
import os
from dotenv import load_dotenv

# Load environment variables (especially API Key)
load_dotenv()

# --- App Configuration ---
SECRET_KEY = os.urandom(24)

# MySQL Configuration - Using environment variables for security
DB_USERNAME = os.getenv('DB_USERNAME', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'capa_ai_system')
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
UPLOAD_FOLDER = 'uploads'  # Folder to store uploaded images
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limit file upload size (e.g., 16MB)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- Gemini AI Configuration ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

from flask import Flask
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_login import LoginManager # Added import for LoginManager
from weasyprint import HTML  # Import WeasyPrint for PDF generation
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from models import db, User
# Removed: from routes import register_routes
from flask_bootstrap import Bootstrap
from utils import from_json_filter, nl2br_filter

# Initialize the Flask application
app = Flask(__name__)

# Mail configuration (hardcoded for testing)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'printecci@gmail.com'
app.config['MAIL_PASSWORD'] = 'tqod dylm vrir jduh'  # App Password with spaces as Google provides it
app.config['MAIL_DEFAULT_SENDER'] = 'printecci@gmail.com'
app.config['MAIL_DEBUG'] = True  # Enable mail debugging

mail = Mail() # Initialize without app

# Configure the app from our settings
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Register custom Jinja filters
app.jinja_env.filters['fromjson'] = from_json_filter
app.jinja_env.filters['nl2br'] = nl2br_filter

# Initialize the database with the app
db.init_app(app)

# Initialize Bootstrap
bootstrap = Bootstrap(app)

# Initialize Mail with app
mail.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # The name of the view to redirect to when login is required

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import and register routes after all core app objects are initialized
from routes import register_routes
register_routes(app)

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)  # Run in debug mode for development

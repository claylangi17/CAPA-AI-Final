from flask import Flask
from weasyprint import HTML  # Import WeasyPrint for PDF generation
import os

from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from models import db
from routes import register_routes
from utils import from_json_filter, nl2br_filter

# Initialize the Flask application
app = Flask(__name__)

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

# Register all routes from routes.py
register_routes(app)

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)  # Run in debug mode for development

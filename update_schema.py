from flask import Flask
from models import db
import os
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, UPLOAD_FOLDER, MAX_CONTENT_LENGTH

# Initialize the Flask application
app = Flask(__name__)

# Configure the app from our settings
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize the database with the app
db.init_app(app)


def add_column_to_root_cause():
    """Add the user_adjusted_whys_json column to the root_causes table"""
    with app.app_context():
        # Check if the column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('root_causes')]

        if 'user_adjusted_whys_json' not in columns:
            print("Adding user_adjusted_whys_json column to root_causes table...")
            db.engine.execute(
                'ALTER TABLE root_causes ADD COLUMN user_adjusted_whys_json TEXT')
            print("Column added successfully!")
        else:
            print("Column user_adjusted_whys_json already exists in root_causes table.")


if __name__ == '__main__':
    add_column_to_root_cause()

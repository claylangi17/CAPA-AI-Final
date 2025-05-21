from flask import Flask
from models import db
from sqlalchemy import text
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
            with db.engine.connect() as connection:
                connection.execute(
                    text('ALTER TABLE root_causes ADD COLUMN user_adjusted_whys_json TEXT')
                )
                connection.commit()  # DDL statements often need a commit
            print("Column user_adjusted_whys_json added successfully to root_causes table!")
        else:
            print("Column user_adjusted_whys_json already exists in root_causes table.")


def add_initial_photos_column_to_capa_issues():
    """Add the initial_photos_json column to the capa_issues table"""
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('capa_issues')]

        if 'initial_photos_json' not in columns:
            print("Adding initial_photos_json column to capa_issues table...")
            with db.engine.connect() as connection:
                connection.execute(
                    text('ALTER TABLE capa_issues ADD COLUMN initial_photos_json TEXT')
                )
                connection.commit()
            print("Column initial_photos_json added successfully to capa_issues table!")
        else:
            print("Column initial_photos_json already exists in capa_issues table.")

if __name__ == '__main__':
    add_column_to_root_cause()
    add_initial_photos_column_to_capa_issues()

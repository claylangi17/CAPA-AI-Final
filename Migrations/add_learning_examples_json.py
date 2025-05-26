import sys
import os

# Ensure the parent directory is in the path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from sqlalchemy import Column, Text, text
from app import app, db
from models import RootCause

def migrate():
    """
    Adds the learning_examples_json field to the RootCause table.
    """
    print("Starting migration to add learning_examples_json field to RootCause table...")
    
    with app.app_context():
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('root_causes')]
        
        if 'learning_examples_json' not in columns:
            print("Column 'learning_examples_json' not found. Adding it...")
            try:
                # Add the column using raw SQL to ensure compatibility
                db.session.execute(text('ALTER TABLE root_causes ADD COLUMN learning_examples_json TEXT'))
                db.session.commit()
                print("Column 'learning_examples_json' added successfully.")
            except Exception as e:
                print(f"Error adding column: {e}")
                db.session.rollback()
                return False
        else:
            print("Column 'learning_examples_json' already exists. No changes needed.")
        
        print("Migration completed successfully.")
        return True

if __name__ == '__main__':
    migrate()

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import app, db
from models import CapaIssue, User

def run_migration():
    with app.app_context():
        print("Starting migration to add 'created_by_user_id' to 'capa_issues' table...")
        
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('capa_issues')
        column_exists = any(c['name'] == 'created_by_user_id' for c in columns)

        if column_exists:
            print("'created_by_user_id' column already exists in 'capa_issues'. Migration not needed.")
            return

        try:
            # Add the column. SQLite does not fully support ALTER TABLE ADD COLUMN with FOREIGN KEY directly in older versions.
            # For SQLite, it's often easier to recreate table or use Alembic for complex migrations.
            # However, for adding a nullable column, this might work or might need specific SQLite pragmas.
            # For PostgreSQL/MySQL, this should be fine.
            db.session.execute(db.text('ALTER TABLE capa_issues ADD COLUMN created_by_user_id INTEGER REFERENCES users(id)'))
            db.session.commit()
            print("Successfully added 'created_by_user_id' column to 'capa_issues' table.")
            
            # Optional: Populate existing CAPAs with a default user ID (e.g., first super_admin or a specific user)
            # This is a placeholder. You should decide on a strategy for existing data.
            first_super_admin = User.query.filter_by(role='super_admin').first()
            if first_super_admin:
                print(f"Attempting to assign existing CAPAs to user ID: {first_super_admin.id} ({first_super_admin.username})...")
                result = CapaIssue.query.filter(CapaIssue.created_by_user_id.is_(None)).update({'created_by_user_id': first_super_admin.id})
                db.session.commit()
                print(f"{result} existing CAPA issues (without a creator) were updated to be created by user ID {first_super_admin.id}.")
            else:
                print("No super_admin found to assign as default creator for existing CAPAs. Existing CAPAs will have NULL created_by_user_id.")

        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {e}")
            print("If you are using SQLite, you might need to use a more robust migration tool like Alembic (Flask-Migrate) or manually manage schema changes.")

if __name__ == '__main__':
    run_migration()

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import app, db

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))


def add_columns():
    with app.app_context():
        print("Starting process to add new columns for multi-company setup...")
        engine = db.engine
        with engine.connect() as connection:
            try:
                # Add columns to 'users' table
                print("Attempting to add 'role' column to 'users' table...")
                connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) NULL"))
                print("'role' column added to 'users' table.")
            except Exception as e:
                if 'Duplicate column name' in str(e) or '1060' in str(e):
                    print("'role' column likely already exists in 'users' table.")
                else:
                    print(f"Error adding 'role' column to 'users': {e}")
                    # raise # Optionally re-raise if you want the script to stop

            try:
                print("Attempting to add 'company_id' column to 'users' table...")
                connection.execute(text("ALTER TABLE users ADD COLUMN company_id INTEGER NULL"))
                print("'company_id' column added to 'users' table.")
                print("Attempting to add foreign key for 'users.company_id'...")
                connection.execute(text("ALTER TABLE users ADD CONSTRAINT fk_users_company_id FOREIGN KEY (company_id) REFERENCES companies(id)"))
                print("Foreign key 'fk_users_company_id' added.")
            except Exception as e:
                if 'Duplicate column name' in str(e) or '1060' in str(e):
                    print("'company_id' column likely already exists in 'users' table.")
                elif 'fk_users_company_id' in str(e) and ('1022' in str(e) or '1826' in str(e) or 'already exists' in str(e).lower()): # MySQL 1022, MariaDB 1826 for duplicate FK name
                    print("Foreign key 'fk_users_company_id' likely already exists.")
                elif 'Cannot add foreign key constraint' in str(e) or '1215' in str(e):
                     print(f"Error adding foreign key 'fk_users_company_id' (companies table or id column might not exist yet, or types mismatch): {e}")
                else:
                    print(f"Error adding 'company_id' column or FK to 'users': {e}")

            # Add columns to 'capa_issues' table
            try:
                print("Attempting to add 'company_id' column to 'capa_issues' table...")
                connection.execute(text("ALTER TABLE capa_issues ADD COLUMN company_id INTEGER NULL"))
                print("'company_id' column added to 'capa_issues' table.")
                print("Attempting to add foreign key for 'capa_issues.company_id'...")
                connection.execute(text("ALTER TABLE capa_issues ADD CONSTRAINT fk_capa_issues_company_id FOREIGN KEY (company_id) REFERENCES companies(id)"))
                print("Foreign key 'fk_capa_issues_company_id' added.")
            except Exception as e:
                if 'Duplicate column name' in str(e) or '1060' in str(e):
                    print("'company_id' column likely already exists in 'capa_issues' table.")
                elif 'fk_capa_issues_company_id' in str(e) and ('1022' in str(e) or '1826' in str(e) or 'already exists' in str(e).lower()):
                    print("Foreign key 'fk_capa_issues_company_id' likely already exists.")
                elif 'Cannot add foreign key constraint' in str(e) or '1215' in str(e):
                     print(f"Error adding foreign key 'fk_capa_issues_company_id' (companies table or id column might not exist yet, or types mismatch): {e}")
                else:
                    print(f"Error adding 'company_id' column or FK to 'capa_issues': {e}")

            # Add columns to 'ai_knowledge_base' table
            try:
                print("Attempting to add 'company_id' column to 'ai_knowledge_base' table...")
                connection.execute(text("ALTER TABLE ai_knowledge_base ADD COLUMN company_id INTEGER NULL"))
                print("'company_id' column added to 'ai_knowledge_base' table.")
                print("Attempting to add foreign key for 'ai_knowledge_base.company_id'...")
                connection.execute(text("ALTER TABLE ai_knowledge_base ADD CONSTRAINT fk_ai_knowledge_base_company_id FOREIGN KEY (company_id) REFERENCES companies(id)"))
                print("Foreign key 'fk_ai_knowledge_base_company_id' added.")
            except Exception as e:
                if 'Duplicate column name' in str(e) or '1060' in str(e):
                    print("'company_id' column likely already exists in 'ai_knowledge_base' table.")
                elif 'fk_ai_knowledge_base_company_id' in str(e) and ('1022' in str(e) or '1826' in str(e) or 'already exists' in str(e).lower()):
                    print("Foreign key 'fk_ai_knowledge_base_company_id' likely already exists.")
                elif 'Cannot add foreign key constraint' in str(e) or '1215' in str(e):
                     print(f"Error adding foreign key 'fk_ai_knowledge_base_company_id' (companies table or id column might not exist yet, or types mismatch): {e}")
                else:
                    print(f"Error adding 'company_id' column or FK to 'ai_knowledge_base': {e}")
            
            # Important: Commit changes if your connection/engine is not in autocommit mode by default
            # For SQLAlchemy's connection.execute(text(...)) with DDL, it's often autocommitted for some backends (like MySQL with default settings for DDL)
            # but explicit commit can be added if needed, though DDL in transactions varies by DB.
            # For instance, connection.commit() if it were a transaction block.
            # However, ALTER TABLE is usually its own transaction.
            print("Column and foreign key addition process completed.")

if __name__ == '__main__':
    add_columns()

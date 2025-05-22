import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import app, db
from sqlalchemy import text

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

def alter_tables():
    with app.app_context():
        print("Starting schema alteration to enforce NOT NULL constraints...")
        try:
            # Ensure your company_id is indeed INTEGER. If it's another type like BIGINT,
            # adjust the SQL accordingly. The migration script should have populated NULLs,
            # so these operations should be safe from violating NOT NULL constraints immediately.

            # For CapaIssue table
            # First, check if the column is already NOT NULL
            inspector = db.inspect(db.engine)
            columns_capa_issue = inspector.get_columns('capa_issues')
            company_id_col_capa = next((col for col in columns_capa_issue if col['name'] == 'company_id'), None)

            if company_id_col_capa and company_id_col_capa['nullable']:
                print("Altering capa_issues table to make company_id NOT NULL...")
                # Note: The exact syntax for ALTER might slightly vary if default values or other constraints are involved.
                # For MySQL, MODIFY is common. For PostgreSQL, it's ALTER COLUMN ... SET NOT NULL.
                # Assuming MySQL based on pymysql driver.
                sql_alter_capa_issues = text("ALTER TABLE capa_issues MODIFY COLUMN company_id INTEGER NOT NULL;")
                db.session.execute(sql_alter_capa_issues)
                db.session.commit()
                print("capa_issues.company_id altered successfully.")
            elif company_id_col_capa:
                print("capa_issues.company_id is already NOT NULL.")
            else:
                print("Could not find company_id column in capa_issues table.")

            # For AIKnowledgeBase table
            columns_ai_kb = inspector.get_columns('ai_knowledge_base')
            company_id_col_kb = next((col for col in columns_ai_kb if col['name'] == 'company_id'), None)

            if company_id_col_kb and company_id_col_kb['nullable']:
                print("Altering ai_knowledge_base table to make company_id NOT NULL...")
                sql_alter_ai_knowledge_base = text("ALTER TABLE ai_knowledge_base MODIFY COLUMN company_id INTEGER NOT NULL;")
                db.session.execute(sql_alter_ai_knowledge_base)
                db.session.commit()
                print("ai_knowledge_base.company_id altered successfully.")
            elif company_id_col_kb:
                print("ai_knowledge_base.company_id is already NOT NULL.")
            else:
                print("Could not find company_id column in ai_knowledge_base table.")

            print("Schema alteration finished.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred during schema alteration: {e}")
            print("Changes have been rolled back.")

if __name__ == '__main__':
    alter_tables()

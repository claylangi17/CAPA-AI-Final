import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import app, db
from models import User, Company, CapaIssue, AIKnowledgeBase

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

USER_DEFAULT_COMPANY_NAME = "Unassigned"
USER_DEFAULT_COMPANY_CODE = "UNASSIGNED"
PRIMARY_DEFAULT_COMPANY_NAME = "Sansico Group"
PRIMARY_DEFAULT_COMPANY_CODE = "SGC" # Assuming SGC, user to confirm
DEFAULT_USER_ROLE = "user"

def migrate_data():
    with app.app_context():
        print("Starting data migration for multi-company setup...")

        # 1. Ensure Default Companies exist
        # For Users
        user_default_company = Company.query.filter_by(company_code=USER_DEFAULT_COMPANY_CODE).first()
        if not user_default_company:
            print(f"Creating user default company: {USER_DEFAULT_COMPANY_NAME} ({USER_DEFAULT_COMPANY_CODE})")
            user_default_company = Company(name=USER_DEFAULT_COMPANY_NAME, company_code=USER_DEFAULT_COMPANY_CODE)
            db.session.add(user_default_company)
            # Commit separately to ensure it exists before potentially creating the next one
            db.session.commit()
            print(f"User default company created with ID: {user_default_company.id}")
        else:
            print(f"User default company '{user_default_company.name}' already exists with ID: {user_default_company.id}")

        # For CapaIssue and AIKnowledgeBase (Primary Default)
        primary_default_company = Company.query.filter_by(company_code=PRIMARY_DEFAULT_COMPANY_CODE).first()
        if not primary_default_company:
            # Attempt to find by name if code not found (e.g. if ID=1 is Sansico Group but code is different)
            primary_default_company = Company.query.filter_by(name=PRIMARY_DEFAULT_COMPANY_NAME).first()
            if not primary_default_company:
                print(f"Creating primary default company: {PRIMARY_DEFAULT_COMPANY_NAME} ({PRIMARY_DEFAULT_COMPANY_CODE})")
                primary_default_company = Company(name=PRIMARY_DEFAULT_COMPANY_NAME, company_code=PRIMARY_DEFAULT_COMPANY_CODE)
                db.session.add(primary_default_company)
                db.session.commit()
                print(f"Primary default company created with ID: {primary_default_company.id}")
            else:
                print(f"Primary default company '{primary_default_company.name}' found by name with ID: {primary_default_company.id}. Consider standardizing code to {PRIMARY_DEFAULT_COMPANY_CODE}.")
        else:
            print(f"Primary default company '{primary_default_company.name}' already exists with ID: {primary_default_company.id}")

        # Fallback if primary_default_company is still None (e.g. DB error or unexpected state)
        if not primary_default_company:
            print(f"CRITICAL: Could not find or create primary default company '{PRIMARY_DEFAULT_COMPANY_NAME}'. Assigning to user default as a last resort.")
            primary_default_company = user_default_company
            if not primary_default_company: # Should not happen if user_default_company logic is sound
                print("CRITICAL: User default company also not found. Aborting migration for CapaIssue/AIKnowledgeBase.")
                # Optionally, raise an error here
                return # Or sys.exit(1)


        # 2. Update existing Users
        users_to_update = User.query.filter((User.company_id == None) | (User.role == None)).all()
        if users_to_update:
            print(f"Found {len(users_to_update)} user(s) needing migration.")
            for user in users_to_update:
                updated = False
                if user.company_id is None:
                    user.company_id = user_default_company.id
                    print(f"  Updating user '{user.username}' (ID: {user.id}) to company ID: {user_default_company.id} ({user_default_company.name})")
                    updated = True
                if user.role is None:
                    user.role = DEFAULT_USER_ROLE
                    print(f"  Updating user '{user.username}' (ID: {user.id}) to role: {DEFAULT_USER_ROLE}")
                    updated = True
            db.session.commit()
            print("User migration completed.")
        else:
            print("No users found needing company/role migration.")

        # 3. Update existing CapaIssue records
        capa_issues_to_update = CapaIssue.query.filter(CapaIssue.company_id == None).all()
        if capa_issues_to_update:
            print(f"Found {len(capa_issues_to_update)} CAPA issue(s) needing migration.")
            for issue in capa_issues_to_update:
                issue.company_id = primary_default_company.id
                # print(f"  Updating CAPA issue ID {issue.capa_id} to company ID: {primary_default_company.id} ({primary_default_company.name})")
            db.session.commit()
            print(f"CAPA issue migration completed. {len(capa_issues_to_update)} issues updated.")
        else:
            print("No CAPA issues found needing company migration.")

        # 4. Update existing AIKnowledgeBase records
        knowledge_entries_to_update = AIKnowledgeBase.query.filter(AIKnowledgeBase.company_id == None).all()
        if knowledge_entries_to_update:
            print(f"Found {len(knowledge_entries_to_update)} AI knowledge base entr(y/ies) needing migration.")
            for entry in knowledge_entries_to_update:
                entry.company_id = primary_default_company.id
                # print(f"  Updating AI Knowledge Base entry ID {entry.knowledge_id} to company ID: {primary_default_company.id} ({primary_default_company.name})")
            db.session.commit()
            print(f"AI knowledge base migration completed. {len(knowledge_entries_to_update)} entries updated.")
        else:
            print("No AI knowledge base entries found needing company migration.")

        print("Data migration finished.")

if __name__ == '__main__':
    migrate_data()

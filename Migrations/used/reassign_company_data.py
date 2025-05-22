from app import app, db
from models import CapaIssue, AIKnowledgeBase, Company

TARGET_COMPANY_NAME = "PT. Printec Perkasa II"

def run_data_reassignment():
    with app.app_context():
        # Get the target company ID
        target_company = Company.query.filter_by(name=TARGET_COMPANY_NAME).first()
        if not target_company:
            print(f"Error: Target company '{TARGET_COMPANY_NAME}' not found in the database.")
            return

        target_company_id = target_company.id
        print(f"Target company: '{TARGET_COMPANY_NAME}' (ID: {target_company_id})")

        # Reassign CapaIssue records
        try:
            capa_issues_updated_count = CapaIssue.query.update({CapaIssue.company_id: target_company_id})
            print(f"Reassigned {capa_issues_updated_count} records in 'CapaIssue' table.")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating CapaIssue table: {e}")
            return

        # Reassign AIKnowledgeBase records
        try:
            ai_knowledge_updated_count = AIKnowledgeBase.query.update({AIKnowledgeBase.company_id: target_company_id})
            print(f"Reassigned {ai_knowledge_updated_count} records in 'AIKnowledgeBase' table.")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating AIKnowledgeBase table: {e}")
            return

        # Commit changes if both updates were successful
        try:
            db.session.commit()
            print("Data reassignment successful. All changes have been committed.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes to the database: {e}")

if __name__ == '__main__':
    print("Starting data reassignment script...")
    print("IMPORTANT: Ensure you have a backup of your database before proceeding.")
    confirmation = input("Do you want to proceed with reassigning all CapaIssue and AIKnowledgeBase records to PT. Printec Perkasa II? (yes/no): ")
    if confirmation.lower() == 'yes':
        run_data_reassignment()
    else:
        print("Data reassignment cancelled by user.")

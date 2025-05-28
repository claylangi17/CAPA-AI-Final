# WARNING: THIS SCRIPT PERMANENTLY DELETES DATA FROM THE DATABASE.
# MAKE SURE YOU HAVE A BACKUP BEFORE RUNNING THIS SCRIPT.

import os
import sys

# Add the project root to the Python path to allow importing app modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from app import app, db  # Import your Flask app and SQLAlchemy instance
from models import CapaIssue, AIKnowledgeBase # Import necessary models

MIN_CAPA_ID = 0
MAX_CAPA_ID = 999

def delete_capas_in_range():
    """Deletes CAPA issues and their related data within the specified ID range."""
    with app.app_context(): # Essential for SQLAlchemy operations outside of a Flask request
        try:
            capas_to_delete = CapaIssue.query.filter(
                CapaIssue.capa_id >= MIN_CAPA_ID,
                CapaIssue.capa_id <= MAX_CAPA_ID
            ).all()

            if not capas_to_delete:
                print(f"No CAPA issues found with capa_id between {MIN_CAPA_ID} and {MAX_CAPA_ID}.")
                return

            print(f"Found {len(capas_to_delete)} CAPA issues to delete (IDs from {MIN_CAPA_ID} to {MAX_CAPA_ID}).")
            print("This will also delete related data in GembaInvestigation, RootCause, ActionPlan, Evidence, and AIKnowledgeBase due to cascades or explicit deletion.")
            
            # Double confirmation
            confirm = input("Are you absolutely sure you want to proceed with deleting these records? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Deletion cancelled by user.")
                return

            count_deleted_capas = 0
            count_deleted_knowledge_entries = 0

            for capa in capas_to_delete:
                print(f"Processing CAPA ID: {capa.capa_id}...")
                
                # 1. Explicitly delete related AIKnowledgeBase entries
                # (as it doesn't have cascade delete-orphan from CapaIssue's perspective in the model for 'knowledge_entries' backref)
                # However, AIKnowledgeBase.capa_issue relationship *might* handle it if CapaIssue is deleted.
                # To be safe, let's query and delete explicitly if the database doesn't have ON DELETE CASCADE.
                # A better approach for AIKnowledgeBase would be to ensure its 'capa_issue' relationship has cascade options,
                # or the DB foreign key has ON DELETE CASCADE.
                # For now, let's assume we need to manually delete for AIKnowledgeBase if not cascaded by DB.

                # Alternative: if AIKnowledgeBase.capa_issue relationship was defined with cascade="all, delete-orphan"
                # this manual step for AIKnowledgeBase wouldn't be needed.
                # Let's check if the 'knowledge_entries' backref on CapaIssue has cascade.
                # The model shows: capa_issue = db.relationship('CapaIssue', backref=db.backref('knowledge_entries', lazy='dynamic'))
                # This doesn't specify cascade from CapaIssue to AIKnowledgeBase via 'knowledge_entries'.
                # So, we should manually delete AIKnowledgeBase entries related to this capa_id.

                related_knowledge_entries = AIKnowledgeBase.query.filter_by(capa_id=capa.capa_id).all()
                if related_knowledge_entries:
                    print(f"  Deleting {len(related_knowledge_entries)} AIKnowledgeBase entries for CAPA ID {capa.capa_id}...")
                    for entry in related_knowledge_entries:
                        db.session.delete(entry)
                        count_deleted_knowledge_entries += 1
                
                # 2. Delete the CapaIssue itself.
                # SQLAlchemy should handle cascades for GembaInvestigation, RootCause, ActionPlan, Evidence.
                db.session.delete(capa)
                count_deleted_capas += 1
                print(f"  Marked CAPA ID {capa.capa_id} for deletion.")

            # Commit the transaction
            db.session.commit()
            print(f"\nSuccessfully deleted {count_deleted_capas} CAPA issues and {count_deleted_knowledge_entries} related AIKnowledgeBase entries.")
            print("Related Gemba, RCA, Action Plan, and Evidence records should also be deleted due to model cascades.")

        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {e}")
            print("Transaction rolled back. No data was deleted in this attempt.")

if __name__ == '__main__':
    print("--- SCRIPT TO DELETE CAPA ISSUES BY ID RANGE ---")
    print("WARNING: THIS SCRIPT PERMANENTLY DELETES DATA FROM THE DATABASE.")
    print("IT IS STRONGLY RECOMMENDED TO BACK UP YOUR DATABASE BEFORE RUNNING THIS.")
    print(f"This script will target CAPA issues with capa_id from {MIN_CAPA_ID} to {MAX_CAPA_ID}.")
    
    proceed = input("Do you understand the risk and wish to continue? (yes/no): ")
    if proceed.lower() == 'yes':
        delete_capas_in_range()
    else:
        print("Operation cancelled.")

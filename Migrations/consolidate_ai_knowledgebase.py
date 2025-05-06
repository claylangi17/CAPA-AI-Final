import json
# Removed: from models import AIKnowledgeBase # This was causing the issue
from app import app, db  # db object is needed
import os
import sys
from dotenv import load_dotenv
# For temp model
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, text  # Added text
from datetime import datetime  # For temp model

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv(os.path.join(project_root, '.env'))


def run_migration():
    """
    Migration script to consolidate AIKnowledgeBase entries:
    1. For CAPAs with both 'rca_adjustment' and 'action_plan_adjustment' entries,
       it ensures the 'action_plan_adjustment' entry has the 'adjusted_whys_json'
       from the 'rca_adjustment' entry, then deletes the 'rca_adjustment' entry.
    2. Drops the 'source_type' column from the 'ai_knowledge_base' table.
    """
    with app.app_context():
        # Define a temporary model class that reflects the OLD structure (with source_type)
        # This is necessary because the main models.py has already been updated.
        class _OldAIKnowledgeBase(db.Model):
            __tablename__ = 'ai_knowledge_base'
            # Important for redefinition in same session context
            __table_args__ = {'extend_existing': True}

            knowledge_id = Column(Integer, primary_key=True)
            # Assuming FK constraint
            capa_id = Column(Integer, ForeignKey(
                'capa_issues.capa_id'), nullable=False)
            # The column we are dealing with
            source_type = Column(String(50), nullable=False)
            machine_name = Column(String(200), nullable=True)
            issue_description = Column(Text, nullable=True)
            adjusted_whys_json = Column(Text, nullable=True)
            adjusted_temporary_actions_json = Column(Text, nullable=True)
            adjusted_preventive_actions_json = Column(Text, nullable=True)
            created_at = Column(DateTime, default=datetime.utcnow)
            is_active = Column(Boolean, default=True)

        print("Starting AIKnowledgeBase consolidation migration...")

        # Get all unique capa_ids from AIKnowledgeBase using the temporary old model
        capa_ids_with_entries = db.session.query(
            _OldAIKnowledgeBase.capa_id).distinct().all()
        capa_ids_with_entries = [c[0] for c in capa_ids_with_entries]

        processed_capa_ids = set()

        for capa_id in capa_ids_with_entries:
            if capa_id in processed_capa_ids:
                continue

            # Query using the temporary _OldAIKnowledgeBase model
            rca_entry = _OldAIKnowledgeBase.query.filter_by(
                capa_id=capa_id, source_type='rca_adjustment').first()
            action_plan_entry = _OldAIKnowledgeBase.query.filter_by(
                capa_id=capa_id, source_type='action_plan_adjustment').first()

            if rca_entry and action_plan_entry:
                print(
                    f"Processing CAPA ID {capa_id}: Found both RCA and Action Plan entries.")
                # If action plan entry is missing whys, try to populate from RCA entry
                if action_plan_entry.adjusted_whys_json is None and rca_entry.adjusted_whys_json is not None:
                    action_plan_entry.adjusted_whys_json = rca_entry.adjusted_whys_json
                    print(
                        f"  Updated adjusted_whys_json for action plan entry of CAPA ID {capa_id} from RCA entry.")

                # Delete the rca_adjustment entry
                db.session.delete(rca_entry)
                print(f"  Deleted rca_adjustment entry for CAPA ID {capa_id}.")
                processed_capa_ids.add(capa_id)

            elif rca_entry and not action_plan_entry:
                print(
                    f"Processing CAPA ID {capa_id}: Found only RCA entry. It will be kept.")
                # This entry will remain, and source_type column will be dropped.
                # The application logic will treat it as a consolidated entry with only RCA data.
                processed_capa_ids.add(capa_id)

            elif action_plan_entry and not rca_entry:
                print(
                    f"Processing CAPA ID {capa_id}: Found only Action Plan entry. It will be kept.")
                # This entry will remain.
                processed_capa_ids.add(capa_id)

        try:
            db.session.commit()
            print("Committed deletions of redundant rca_adjustment entries and updates to action_plan_adjustment entries.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes during data consolidation: {e}")
            return

        # Drop the source_type column
        print("Attempting to drop 'source_type' column from 'ai_knowledge_base' table...")
        try:
            # Use raw SQL for dropping column as SQLAlchemy might not directly support it
            # in a way that's easy for migrations without Alembic.
            # Ensure this SQL is correct for your database (MySQL in this case).
            db.session.execute(
                text("ALTER TABLE ai_knowledge_base DROP COLUMN source_type;"))
            db.session.commit()  # Commit DDL change
            print("'source_type' column dropped successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error dropping 'source_type' column: {e}")
            print(
                "Please ensure the column is dropped manually if the script fails here.")

        print("Migration finished.")


if __name__ == '__main__':
    confirmation = input(
        "This script will modify the 'ai_knowledge_base' table by deleting some rows and dropping the 'source_type' column. This is a destructive operation. Are you sure you want to continue? (yes/no): ")
    if confirmation.lower() == 'yes':
        run_migration()
    else:
        print("Migration cancelled by user.")

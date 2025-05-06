from models import db, CapaIssue, AIKnowledgeBase
from config import SQLALCHEMY_DATABASE_URI  # Import the variable directly
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
import os
import sys
import json
from datetime import datetime

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


# Import models AFTER path is set
# Note: AIKnowledgeBase model imported is the NEW definition

load_dotenv(os.path.join(project_root, '.env'))


def run_migration():
    # Use the imported variable
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    inspector = inspect(engine)
    table_name = AIKnowledgeBase.__tablename__  # Should be 'ai_knowledge_base'

    print(f"Starting migration for table: {table_name}")

    # 1. Define new columns and check/add them
    columns_to_add = {
        'capa_id': 'INTEGER',  # FK will be handled by SQLAlchemy model later
        'customer_name': 'VARCHAR(200)',
        'item_involved': 'VARCHAR(200)',
        'machine_name': 'VARCHAR(200)',
        'issue_description': 'TEXT',
        'gemba_findings': 'TEXT',
        'learned_data_json': 'TEXT',
        'original_ai_suggestion_json': 'TEXT'
    }

    existing_columns = [col['name']
                        for col in inspector.get_columns(table_name)]

    with engine.connect() as connection:
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    print(f"Added column: {col_name}")
                except SQLAlchemyError as e:
                    print(
                        f"Could not add column {col_name}. It might already exist or other DB error: {e}")
            else:
                print(f"Column {col_name} already exists.")
        connection.commit()

    # 2. Add a temporary migration flag column if it doesn't exist
    migration_flag_col = 'migration_temp_flag_v1'
    if migration_flag_col not in existing_columns:
        with engine.connect() as connection:
            try:
                connection.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN {migration_flag_col} BOOLEAN DEFAULT FALSE"))
                connection.commit()
                print(
                    f"Added temporary migration flag column: {migration_flag_col}")
            except SQLAlchemyError as e:
                print(
                    f"Error adding migration flag column '{migration_flag_col}': {e}")
                # If this fails, re-run safety is compromised.

    # 3. Fetch records that haven't been migrated
    # Ensure 'source_id' and 'knowledge_data' (old columns) are selected.
    # If these columns were dropped, this query would fail.
    # This script assumes they still exist for reading.
    try:
        old_records_query_str = f"SELECT knowledge_id, source_id, source_type, knowledge_data FROM {table_name} WHERE {migration_flag_col} IS FALSE OR {migration_flag_col} IS NULL"
        old_records_result = session.execute(
            text(old_records_query_str)).fetchall()
    except SQLAlchemyError as e:
        # Check if old columns are missing (e.g. if script is run after they are dropped)
        if "source_id" in str(e).lower() or "knowledge_data" in str(e).lower():
            print(
                f"Error: Old columns 'source_id' or 'knowledge_data' may be missing. Migration might have been partially run or columns dropped. {e}")
        else:
            print(f"Error fetching old records: {e}")
        session.close()
        return

    print(f"Found {len(old_records_result)} records to migrate.")
    migrated_count = 0

    for row_proxy in old_records_result:
        record = dict(row_proxy._mapping)  # Convert RowProxy to dict

        knowledge_id = record['knowledge_id']
        # This is the capa_id for the CapaIssue
        old_capa_id = record['source_id']
        # source_type_val = record['source_type'] # Not directly used for new columns, but good for context
        knowledge_data_json_str = record['knowledge_data']

        print(
            f"Processing knowledge_id: {knowledge_id} (old_capa_id: {old_capa_id})")

        try:
            knowledge_data_dict = json.loads(knowledge_data_json_str)

            issue_context = knowledge_data_dict.get("issue_context", {})
            ai_suggestion_dict = knowledge_data_dict.get("ai_suggestion", {})
            user_adjustment_dict = knowledge_data_dict.get(
                "user_adjustment", {})

            # Fetch CapaIssue to get machine_name and other details if needed
            capa_issue_obj = session.query(CapaIssue).filter_by(
                capa_id=old_capa_id).first()

            machine_name_val = None
            customer_name_val = issue_context.get("customer_name")
            item_involved_val = issue_context.get("item_involved")
            issue_description_val = issue_context.get("issue_description")
            # Will be null if not in RCA context
            gemba_findings_val = issue_context.get("gemba_findings")

            if capa_issue_obj:
                machine_name_val = capa_issue_obj.machine_name
                # Potentially override/enrich from CapaIssue if more reliable
                customer_name_val = capa_issue_obj.customer_name or customer_name_val
                item_involved_val = capa_issue_obj.item_involved or item_involved_val
                issue_description_val = capa_issue_obj.issue_description or issue_description_val
                if capa_issue_obj.gemba_investigation:
                    gemba_findings_val = capa_issue_obj.gemba_investigation.findings or gemba_findings_val
            else:
                print(
                    f"  Warning: CapaIssue with id {old_capa_id} not found. machine_name will be null.")

            # Prepare update dictionary for the AIKnowledgeBase record
            update_data = {
                "capa_id": old_capa_id,  # This is the FK to CapaIssue
                "customer_name": customer_name_val,
                "item_involved": item_involved_val,
                "machine_name": machine_name_val,
                "issue_description": issue_description_val,
                "gemba_findings": gemba_findings_val,
                "learned_data_json": json.dumps(user_adjustment_dict),
                "original_ai_suggestion_json": json.dumps(ai_suggestion_dict),
                migration_flag_col: True
            }

            # Update the record using ORM by fetching it first
            db_record_to_update = session.query(AIKnowledgeBase).filter_by(
                knowledge_id=knowledge_id).first()
            if db_record_to_update:
                for key, value in update_data.items():
                    setattr(db_record_to_update, key, value)
                migrated_count += 1
            else:
                print(
                    f"  Record with knowledge_id {knowledge_id} not found via ORM during update. Skipping.")
                continue

        except json.JSONDecodeError:
            print(
                f"  Error decoding JSON for knowledge_id: {knowledge_id}. Skipping.")
            # Mark as failed/skipped if necessary, e.g., by setting flag to a different value
            session.query(AIKnowledgeBase).filter_by(knowledge_id=knowledge_id).update(
                # Mark as processed to avoid re-attempt
                {migration_flag_col: True})
            continue
        except Exception as e:
            print(
                f"  An error occurred processing knowledge_id {knowledge_id}: {e}. Skipping.")
            session.query(AIKnowledgeBase).filter_by(knowledge_id=knowledge_id).update(
                {migration_flag_col: True})  # Mark as processed
            continue

    try:
        session.commit()
        print(
            f"Successfully processed {migrated_count} records for migration.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error committing changes: {e}")
    finally:
        session.close()
        print("Migration process finished.")


if __name__ == "__main__":
    print("Running AIKnowledgeBase migration script...")
    # Ensure this script is run from the project root or that paths are correctly handled.
    # Example: python migrations/migrate_ai_knowledgebase.py
    run_migration()

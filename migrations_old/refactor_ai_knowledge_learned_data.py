import os
import sys
import json
# Ensure this import is present and early
from dotenv import load_dotenv, dotenv_values
from sqlalchemy import create_engine, text, inspect, Column, Text


# --- Global Configuration ---
config = {}


def load_configuration():
    """Loads .env file into the global config dictionary."""
    global config
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    dotenv_path = os.path.join(project_root, '.env')

    # Use dotenv_values to load into dict directly
    if os.path.exists(dotenv_path):
        config = dotenv_values(dotenv_path)
        if not config:
            print(
                f"Warning: .env file at {dotenv_path} was found but `dotenv_values` returned empty.")
    else:
        print(f"Warning: .env file not found at {dotenv_path}")


# Load configuration when the module is imported/run
load_configuration()

# --- Database Functions ---


def get_db_uri():
    """Constructs the database URI from the loaded config dictionary."""
    global config
    db_user = config.get('DB_USERNAME')
    db_password = config.get('DB_PASSWORD')
    db_host = config.get('DB_HOST')
    db_name = config.get('DB_NAME')

    if db_user is None or db_password is None or db_host is None or db_name is None:
        missing = [k for k, v in {"USER": db_user, "PASS": db_password,
                                  "HOST": db_host, "NAME": db_name}.items() if v is None]
        raise ValueError(
            f"DB connection details missing in .env. Missing: {', '.join(missing)}")

    # Handle empty password case correctly in connection string
    password_part = f":{db_password}" if db_password else ""
    return f"mysql+pymysql://{db_user}{password_part}@{db_host}/{db_name}"


def simplify_action_list(actions):
    """Extracts only the action text from a list of action dictionaries."""
    simplified_list = []
    if not isinstance(actions, list):
        return []
    for action in actions:
        if isinstance(action, dict):
            # Get text or empty string
            simplified_list.append(action.get('action_text', ''))
        elif isinstance(action, str):
            simplified_list.append(action)  # If it's already just a string
    # Filter out any potentially empty strings if desired, or keep them
    return [text for text in simplified_list if text]


def migrate_data(connection):
    """Migrates data from learned_data_json to new columns."""
    print("Starting data migration from learned_data_json...")

    # Select existing data
    select_sql = text(
        "SELECT knowledge_id, source_type, learned_data_json FROM ai_knowledge_base")
    rows = connection.execute(select_sql).fetchall()

    update_count = 0
    error_count = 0

    for row in rows:
        knowledge_id, source_type, learned_data_json_str = row

        if not learned_data_json_str:
            continue  # Skip if no data to migrate

        try:
            learned_data = json.loads(learned_data_json_str)

            if source_type == 'rca_adjustment':
                whys_list = learned_data.get('whys', [])
                if isinstance(whys_list, list):
                    update_sql = text("""
                        UPDATE ai_knowledge_base 
                        SET adjusted_whys_json = :whys 
                        WHERE knowledge_id = :id
                    """)
                    connection.execute(
                        update_sql, {"whys": json.dumps(whys_list), "id": knowledge_id})
                    update_count += 1
                else:
                    print(
                        f"Warning: Invalid 'whys' format for ID {knowledge_id}. Skipping.")
                    error_count += 1

            elif source_type == 'action_plan_adjustment':
                temp_actions = learned_data.get('temp_actions', [])
                prev_actions = learned_data.get('prev_actions', [])

                simplified_temp = simplify_action_list(temp_actions)
                simplified_prev = simplify_action_list(prev_actions)

                update_sql = text("""
                    UPDATE ai_knowledge_base 
                    SET adjusted_temporary_actions_json = :temp, 
                        adjusted_preventive_actions_json = :prev 
                    WHERE knowledge_id = :id
                """)
                connection.execute(update_sql, {
                    "temp": json.dumps(simplified_temp),
                    "prev": json.dumps(simplified_prev),
                    "id": knowledge_id
                })
                update_count += 1

        except json.JSONDecodeError:
            print(
                f"Warning: Could not parse learned_data_json for ID {knowledge_id}. Skipping.")
            error_count += 1
        except Exception as e:
            print(f"Error processing row ID {knowledge_id}: {e}")
            error_count += 1

    print(
        f"Data migration finished. Updated rows: {update_count}, Errors/Skipped: {error_count}")
    if error_count > 0:
        print("WARNING: Some rows encountered errors during migration. Review logs.")
        # Decide whether to proceed with dropping the column if errors occurred
        # For now, we'll proceed cautiously and NOT drop if errors happened.
        return False
    return True


def run_migration():
    """Adds new columns, migrates data, and drops the old column."""
    try:
        db_uri = get_db_uri()
    except ValueError as e:
        print(f"Error getting DB URI: {e}")
        sys.exit(1)

    engine = create_engine(db_uri)

    new_columns = {
        "adjusted_whys_json": Text,
        "adjusted_temporary_actions_json": Text,
        "adjusted_preventive_actions_json": Text
    }

    with engine.connect() as connection:
        inspector = inspect(engine)
        existing_columns = [col['name']
                            for col in inspector.get_columns('ai_knowledge_base')]

        transaction = connection.begin()
        try:
            # Add new columns if they don't exist
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    # Convert SQLAlchemy type to SQL type string (basic example)
                    sql_type = "TEXT"  # Default for MySQL TEXT
                    add_col_sql = text(
                        f"ALTER TABLE ai_knowledge_base ADD COLUMN {col_name} {sql_type} NULL")
                    connection.execute(add_col_sql)
                    print(f"Added column: {col_name}")
                else:
                    print(f"Column {col_name} already exists. Skipping add.")

            # Migrate data
            migration_successful = migrate_data(connection)

            # Drop old column only if migration was successful and column exists
            if migration_successful and 'learned_data_json' in existing_columns:
                drop_col_sql = text(
                    "ALTER TABLE ai_knowledge_base DROP COLUMN learned_data_json")
                connection.execute(drop_col_sql)
                print("Dropped column: learned_data_json")
            elif not migration_successful:
                print("Skipping drop of learned_data_json due to migration errors.")
            elif 'learned_data_json' not in existing_columns:
                print("Column learned_data_json does not exist. Skipping drop.")

            transaction.commit()
            print("Migration completed successfully.")

        except Exception as e:
            print(f"An error occurred during migration: {e}")
            transaction.rollback()
            print("Transaction rolled back.")


# --- Main Execution ---
if __name__ == '__main__':
    print("Starting migration: Refactor ai_knowledge_base learned data...")
    run_migration()
    print("Migration script finished.")

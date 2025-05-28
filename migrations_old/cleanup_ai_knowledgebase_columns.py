import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, dotenv_values

# --- Global Configuration ---
config = {}


def load_configuration():
    """Loads .env file into the global config dictionary."""
    global config
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))

    # Add project root to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    dotenv_path = os.path.join(project_root, '.env')

    if os.path.exists(dotenv_path):
        # For os.getenv if used elsewhere or by libraries
        load_dotenv(dotenv_path)
        config = dotenv_values(dotenv_path)
        if not config:
            print(
                f"Warning: .env file at {dotenv_path} was found but `dotenv_values` returned empty. Check file content.")
    else:
        print(f"Warning: .env file not found at {dotenv_path}")


# Load configuration when the module is imported/run
load_configuration()

# --- Application Import (Optional for this script) ---
try:
    from app import app, db as app_db
except ImportError:
    print("Error: Could not import app or db. Continuing with direct SQL execution.")
    # sys.exit(1) # Not exiting to allow script to run

# --- Database Functions ---


def get_db_uri():
    """Constructs the database URI from the loaded config dictionary."""
    global config  # Ensure we're using the global config
    db_user = config.get('DB_USERNAME')
    db_password = config.get('DB_PASSWORD')
    db_host = config.get('DB_HOST')
    db_name = config.get('DB_NAME')

    # Print loaded values for debugging
    # print(f"DEBUG: DB_USERNAME: {db_user}, DB_PASSWORD: {'******' if db_password else 'EMPTY'}, DB_HOST: {db_host}, DB_NAME: {db_name}")

    # Check if essential components are missing. Allow empty string for password.
    if db_user is None or db_password is None or db_host is None or db_name is None:
        missing_details = []
        if db_user is None:
            missing_details.append("DB_USERNAME")
        if db_password is None:
            # This means the key itself is missing, not an empty string value
            missing_details.append("DB_PASSWORD")
        if db_host is None:
            missing_details.append("DB_HOST")
        if db_name is None:
            missing_details.append("DB_NAME")

        # Further check: if any of the required (non-password) fields are empty strings
        if not db_user:
            missing_details.append("DB_USERNAME (empty value)")
        # db_password can be an empty string, so we don't check `if not db_password` here
        if not db_host:
            missing_details.append("DB_HOST (empty value)")
        if not db_name:
            missing_details.append("DB_NAME (empty value)")

        # Remove duplicates if any field was both None and then checked as empty
        unique_missing_details = sorted(list(set(missing_details)))

        if unique_missing_details:
            raise ValueError(
                f"Database connection details missing or incomplete in .env file or config dictionary. Missing/Incomplete: {', '.join(unique_missing_details)}")

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"


def drop_columns():
    """Drops specified columns from the ai_knowledge_base table."""
    try:
        db_uri = get_db_uri()
    except ValueError as e:
        print(f"Error getting DB URI: {e}")
        sys.exit(1)

    engine = create_engine(db_uri)

    final_columns_to_drop = [
        'customer_name', 'item_involved', 'gemba_findings',
        'original_ai_suggestion_json', 'knowledge_data',
        'source_id', 'migration_temp_flag_1'
    ]

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            for column_name in final_columns_to_drop:
                check_column_sql = text(f"""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'ai_knowledge_base' AND COLUMN_NAME = '{column_name}';
                """)
                result = connection.execute(check_column_sql).scalar_one()

                if result > 0:
                    sql = text(
                        f"ALTER TABLE ai_knowledge_base DROP COLUMN {column_name};")
                    connection.execute(sql)
                    print(f"Successfully dropped column: {column_name}")
                else:
                    print(f"Column {column_name} does not exist. Skipping.")
            transaction.commit()
            print("Successfully dropped columns from ai_knowledge_base.")
        except Exception as e:
            transaction.rollback()
            print(f"An error occurred during DB operation: {e}")
            print("Transaction rolled back.")


# --- Main Execution ---
if __name__ == '__main__':
    print("Starting column cleanup for ai_knowledge_base table...")
    drop_columns()
    print("Column cleanup script finished.")

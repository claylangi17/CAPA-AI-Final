import os
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from app import app, db, CapaIssue, RootCause, ActionPlan, Evidence

# Load environment variables
load_dotenv()

# Database configuration
DB_USERNAME = os.getenv('DB_USERNAME', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'capa_ai_system')

# SQLite database path
SQLITE_DB_PATH = 'instance/capa_db.sqlite3'


def create_mysql_database():
    """Create the MySQL database if it doesn't exist."""
    # Connect to MySQL server without specifying a database
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        charset='utf8mb4',
        cursorclass=DictCursor
    )

    try:
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"Database '{DB_NAME}' created or already exists.")
    finally:
        connection.close()


def create_tables():
    """Create tables in MySQL using SQLAlchemy models."""
    with app.app_context():
        db.create_all()
        print("Tables created successfully in MySQL database.")


def check_sqlite_data_exists():
    """Check if SQLite database exists and has data."""
    if not os.path.exists(SQLITE_DB_PATH):
        print("SQLite database file not found. No data to migrate.")
        return False

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Check if capa_issues table has data
        cursor.execute("SELECT COUNT(*) FROM capa_issues")
        count = cursor.fetchone()[0]

        conn.close()

        if count > 0:
            print(f"Found {count} records in SQLite database to migrate.")
            return True
        else:
            print("SQLite database exists but has no data.")
            return False
    except sqlite3.Error as e:
        print(f"Error checking SQLite database: {e}")
        return False


def migrate_data():
    """Migrate data from SQLite to MySQL."""
    if not check_sqlite_data_exists():
        return

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    with app.app_context():
        # Clear existing data in MySQL tables
        db.session.query(Evidence).delete()
        db.session.query(ActionPlan).delete()
        db.session.query(RootCause).delete()
        db.session.query(CapaIssue).delete()
        db.session.commit()

        # Migrate CAPA Issues
        sqlite_cursor.execute("SELECT * FROM capa_issues")
        issues = sqlite_cursor.fetchall()

        for issue in issues:
            # Check which columns exist in the SQLite table
            issue_data = {
                'capa_id': issue['capa_id'],
                'customer_name': issue['customer_name'],
                'issue_date': issue['issue_date'],
                'issue_description': issue['issue_description'],
                'item_involved': issue['item_involved'],
                'machine_name': None,
                'batch_number': None,
                'initial_photo_path': issue['initial_photo_path'],
                'submission_timestamp': issue['submission_timestamp'],
                'status': issue['status']
            }
            
            # Update with actual values if columns exist
            if 'machine_name' in issue:
                issue_data['machine_name'] = issue['machine_name']
            if 'batch_number' in issue:
                issue_data['batch_number'] = issue['batch_number']
                
            new_issue = CapaIssue(
                capa_id=issue_data['capa_id'],
                customer_name=issue_data['customer_name'],
                issue_date=issue_data['issue_date'],
                issue_description=issue_data['issue_description'],
                item_involved=issue_data['item_involved'],
                machine_name=issue_data['machine_name'],
                batch_number=issue_data['batch_number'],
                initial_photo_path=issue_data['initial_photo_path'],
                submission_timestamp=issue_data['submission_timestamp'],
                status=issue_data['status']
            )
            db.session.add(new_issue)

        db.session.commit()
        print(f"Migrated {len(issues)} CAPA issues")

        # Migrate Root Causes
        sqlite_cursor.execute("SELECT * FROM root_causes")
        root_causes = sqlite_cursor.fetchall()

        # Check columns in root_causes table
        sqlite_cursor.execute("PRAGMA table_info(root_causes)")
        rc_columns = [column[1] for column in sqlite_cursor.fetchall()]
        print(f"Root Causes columns: {rc_columns}")

        for rc in root_causes:
            # Create dictionary with default values
            rc_data = {
                'rc_id': rc['rc_id'],
                'capa_id': rc['capa_id'],
                'ai_suggested_rc_json': rc['ai_suggested_rc_json'],
                'user_adjusted_why1': None,
                'user_adjusted_why2': None,
                'user_adjusted_why3': None,
                'user_adjusted_why4': None,
                'user_adjusted_root_cause': None,
                'rc_submission_timestamp': rc['rc_submission_timestamp']
            }

            # Update with actual values if columns exist
            for col in rc_columns:
                if col in rc and col != 'rc_id' and col != 'capa_id' and col != 'ai_suggested_rc_json' and col != 'rc_submission_timestamp':
                    rc_data[col] = rc[col]

            new_rc = RootCause(
                rc_id=rc_data['rc_id'],
                capa_id=rc_data['capa_id'],
                ai_suggested_rc_json=rc_data['ai_suggested_rc_json'],
                user_adjusted_why1=rc_data['user_adjusted_why1'],
                user_adjusted_why2=rc_data['user_adjusted_why2'],
                user_adjusted_why3=rc_data['user_adjusted_why3'],
                user_adjusted_why4=rc_data['user_adjusted_why4'],
                user_adjusted_root_cause=rc_data['user_adjusted_root_cause'],
                rc_submission_timestamp=rc_data['rc_submission_timestamp']
            )
            db.session.add(new_rc)

        db.session.commit()
        print(f"Migrated {len(root_causes)} root causes")

        # Migrate Action Plans
        sqlite_cursor.execute("SELECT * FROM action_plans")
        action_plans = sqlite_cursor.fetchall()

        # Check columns in action_plans table
        sqlite_cursor.execute("PRAGMA table_info(action_plans)")
        ap_columns = [column[1] for column in sqlite_cursor.fetchall()]
        print(f"Action Plans columns: {ap_columns}")

        for ap in action_plans:
            # Create dictionary with default values
            ap_data = {
                'ap_id': ap['ap_id'],
                'capa_id': ap['capa_id'],
                'ai_suggested_actions_json': ap['ai_suggested_actions_json'],
                'user_adjusted_temp_action': None,
                'user_adjusted_prev_action': None,
                'pic_name': None,
                'due_date': None,
                'action_submission_timestamp': ap['action_submission_timestamp'],
                'user_adjusted_actions_json': None
            }

            # Update with actual values if columns exist
            for col in ap_columns:
                if col in ap and col != 'ap_id' and col != 'capa_id' and col != 'ai_suggested_actions_json' and col != 'action_submission_timestamp':
                    ap_data[col] = ap[col]

            new_ap = ActionPlan(
                ap_id=ap_data['ap_id'],
                capa_id=ap_data['capa_id'],
                ai_suggested_actions_json=ap_data['ai_suggested_actions_json'],
                user_adjusted_actions_json=ap_data['user_adjusted_actions_json'],
                user_adjusted_temp_action=ap_data['user_adjusted_temp_action'],
                user_adjusted_prev_action=ap_data['user_adjusted_prev_action'],
                pic_name=ap_data['pic_name'],
                due_date=ap_data['due_date'],
                action_submission_timestamp=ap_data['action_submission_timestamp']
            )
            db.session.add(new_ap)

        db.session.commit()
        print(f"Migrated {len(action_plans)} action plans")

        # Migrate Evidence
        sqlite_cursor.execute("SELECT * FROM evidence")
        evidences = sqlite_cursor.fetchall()

        # Check columns in evidence table
        sqlite_cursor.execute("PRAGMA table_info(evidence)")
        ev_columns = [column[1] for column in sqlite_cursor.fetchall()]
        print(f"Evidence columns: {ev_columns}")

        for ev in evidences:
            # Create dictionary with default values
            ev_data = {
                'evidence_id': ev['evidence_id'],
                'capa_id': ev['capa_id'],
                'evidence_photo_path': ev['evidence_photo_path'],
                'evidence_description': None,
                'evidence_submission_timestamp': ev['evidence_submission_timestamp']
            }

            # Update with actual values if columns exist
            for col in ev_columns:
                if col in ev and col != 'evidence_id' and col != 'capa_id' and col != 'evidence_photo_path' and col != 'evidence_submission_timestamp':
                    ev_data[col] = ev[col]

            new_ev = Evidence(
                evidence_id=ev_data['evidence_id'],
                capa_id=ev_data['capa_id'],
                evidence_photo_path=ev_data['evidence_photo_path'],
                evidence_description=ev_data['evidence_description'],
                evidence_submission_timestamp=ev_data['evidence_submission_timestamp']
            )
            db.session.add(new_ev)

        db.session.commit()
        print(f"Migrated {len(evidences)} evidence items")

    sqlite_conn.close()
    print("Data migration completed successfully")


def main():
    # Steps for migration
    print("Starting migration from SQLite to MySQL...")

    # Step 1: Create MySQL database
    create_mysql_database()

    # Step 2: Create tables in MySQL
    create_tables()

    # Step 3: Migrate data from SQLite to MySQL
    migrate_data()

    print("Migration completed successfully!")
    print(
        f"Your application is now configured to use MySQL database: {DB_NAME}")
    print("You can now start your application with 'flask run' or 'python app.py'")


if __name__ == "__main__":
    main()

from app import app
from models import db
from sqlalchemy import text

def update_gemba_table():
    """
    Updates the gemba_investigations table to match the simplified model structure
    - Adds gemba_photo_path column
    - Removes unused columns from the previous structure
    """
    with app.app_context():
        # Add new column first
        db.session.execute(text("ALTER TABLE gemba_investigations ADD COLUMN gemba_photo_path VARCHAR(300);"))
        
        # We'll keep the findings column as it exists
        
        # Remove columns that are no longer needed
        # Check if these columns exist before trying to drop them
        result = db.session.execute(text("SHOW COLUMNS FROM gemba_investigations LIKE 'suspected_root_cause';"))
        if result.rowcount > 0:
            db.session.execute(text("ALTER TABLE gemba_investigations DROP COLUMN suspected_root_cause;"))
            
        result = db.session.execute(text("SHOW COLUMNS FROM gemba_investigations LIKE 'contributing_factors';"))
        if result.rowcount > 0:
            db.session.execute(text("ALTER TABLE gemba_investigations DROP COLUMN contributing_factors;"))
            
        result = db.session.execute(text("SHOW COLUMNS FROM gemba_investigations LIKE 'gemba_photos_json';"))
        if result.rowcount > 0:
            db.session.execute(text("ALTER TABLE gemba_investigations DROP COLUMN gemba_photos_json;"))
            
        db.session.commit()
        print("Successfully updated gemba_investigations table schema.")

if __name__ == "__main__":
    try:
        update_gemba_table()
    except Exception as e:
        print(f"Error updating schema: {e}")

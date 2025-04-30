from app import app
from models import db
from sqlalchemy import text

def update_gemba_table():
    """
    Updates the gemba_investigations table schema to support multiple photos
    - Adds gemba_photos_json column
    - Removes gemba_photo_path column
    """
    with app.app_context():
        try:
            # Check if gemba_photo_path exists
            result = db.session.execute(text("SHOW COLUMNS FROM gemba_investigations LIKE 'gemba_photo_path';"))
            if result.rowcount > 0:
                # Add new column first to avoid data loss
                db.session.execute(text("ALTER TABLE gemba_investigations ADD COLUMN gemba_photos_json TEXT;"))
                
                # Copy existing single photo to the new JSON array format
                db.session.execute(text("""
                    UPDATE gemba_investigations 
                    SET gemba_photos_json = CONCAT('["', gemba_photo_path, '"]') 
                    WHERE gemba_photo_path IS NOT NULL AND gemba_photo_path != '';
                """))
                
                # Drop old column
                db.session.execute(text("ALTER TABLE gemba_investigations DROP COLUMN gemba_photo_path;"))
                
                db.session.commit()
                print("Successfully updated gemba_investigations table schema to support multiple photos.")
            else:
                # Check if gemba_photos_json exists
                result = db.session.execute(text("SHOW COLUMNS FROM gemba_investigations LIKE 'gemba_photos_json';"))
                if result.rowcount > 0:
                    print("Schema is already updated with gemba_photos_json column.")
                else:
                    # Add the new column
                    db.session.execute(text("ALTER TABLE gemba_investigations ADD COLUMN gemba_photos_json TEXT;"))
                    db.session.commit()
                    print("Added gemba_photos_json column to gemba_investigations table.")
                    
        except Exception as e:
            db.session.rollback()
            print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_gemba_table()

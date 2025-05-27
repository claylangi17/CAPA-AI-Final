from app import app
from sqlalchemy import text
from models import db

def update_evidence_schema():
    """
    Menambahkan kolom action_type dan action_index ke tabel evidence
    """
    try:
        with app.app_context():
            # Cek apakah kolom action_type sudah ada
            result = db.session.execute(text("SHOW COLUMNS FROM evidence LIKE 'action_type'"))
            if not result.fetchone():
                # Tambahkan kolom action_type jika belum ada
                db.session.execute(text("ALTER TABLE evidence ADD COLUMN action_type VARCHAR(20)"))
                print("Kolom action_type berhasil ditambahkan ke tabel evidence")
            else:
                print("Kolom action_type sudah ada di tabel evidence")
                
            # Cek apakah kolom action_index sudah ada
            result = db.session.execute(text("SHOW COLUMNS FROM evidence LIKE 'action_index'"))
            if not result.fetchone():
                # Tambahkan kolom action_index jika belum ada
                db.session.execute(text("ALTER TABLE evidence ADD COLUMN action_index INT"))
                print("Kolom action_index berhasil ditambahkan ke tabel evidence")
            else:
                print("Kolom action_index sudah ada di tabel evidence")
                
            db.session.commit()
            print("Schema evidence berhasil diupdate")
            
    except Exception as e:
        print(f"Error saat update schema: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    update_evidence_schema()

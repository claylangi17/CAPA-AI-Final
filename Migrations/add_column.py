from app import app, db
import sqlite3

# Path ke file database SQLite
db_path = 'instance/capa_db.sqlite3'  # File database yang aktif digunakan

# Jalankan dalam konteks aplikasi
with app.app_context():
    try:
        # Buat koneksi langsung ke SQLite untuk mengubah struktur tabel
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Periksa apakah kolom sudah ada (untuk menghindari error jika kolom sudah ada)
        cursor.execute("PRAGMA table_info(action_plans)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_adjusted_actions_json' not in columns:
            # Tambahkan kolom baru ke tabel yang sudah ada
            cursor.execute("ALTER TABLE action_plans ADD COLUMN user_adjusted_actions_json TEXT")
            print("Kolom user_adjusted_actions_json berhasil ditambahkan ke tabel action_plans")
        else:
            print("Kolom user_adjusted_actions_json sudah ada di tabel action_plans")
        
        conn.commit()
        conn.close()
        
        print("Migrasi database selesai dengan sukses")
        
    except Exception as e:
        print(f"Error saat melakukan migrasi database: {str(e)}")

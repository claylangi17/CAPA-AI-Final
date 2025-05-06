import json
import os
import datetime
import pandas as pd
from flask import Flask
from models import db, AIKnowledgeBase, CapaIssue
from config import SQLALCHEMY_DATABASE_URI



# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def import_excel_data(excel_path):
    """Import data from Excel file to the ai_knowledge_base table"""
    # Validasi file Excel
    if not os.path.exists(excel_path):
        print(f"Error: File Excel tidak ditemukan di {excel_path}")
        return False
    
    # Baca file Excel
    try:
        df = pd.read_excel(excel_path)
        print(f"Berhasil membaca file Excel: {excel_path}")
        print(f"Total baris: {len(df)}")
    except Exception as e:
        print(f"Error saat membaca file Excel: {e}")
        return False
    
    # Cek kolom yang dibutuhkan
    required_columns = ['created_at', 'machine_name', 'issue_description', 'adjusted_whys_json', 'adjusted_temporary_actions_json', 'adjusted_preventive_actions_json']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        # Coba pemetaan alternatif dari nama kolom yang terlihat di Excel
        column_mapping = {
            'created_at': 'created_at',
            'machine_name': 'machine_name',
            'issue_description': 'issue_description',
            'adjusted_whys_json': 'adjusted_whys_item',  # berdasarkan gambar
            'adjusted_temporary_actions_json': 'adjusted_temporary_actions_item',  # berdasarkan gambar
            'adjusted_preventive_actions_json': 'adjusted_preventive_actions_item'  # berdasarkan gambar
        }
        
        # Periksa apakah ada kolom yang sesuai dengan pemetaan alternatif
        for missing_col in missing_columns.copy():
            alt_col = column_mapping[missing_col]
            if alt_col in df.columns:
                # Ganti nama kolom
                df = df.rename(columns={alt_col: missing_col})
                missing_columns.remove(missing_col)
        
        # Jika masih ada kolom yang hilang, coba gunakan nama kolom dari gambar Excel
        if missing_columns:
            excel_columns = list(df.columns)
            print(f"Kolom dalam Excel: {excel_columns}")
            
            # Berdasarkan gambar Excel, coba tebak kolom yang sesuai
            if 'adjusted_whys_json' in missing_columns and 'adjusted_whys_item' not in df.columns:
                # Cari kolom yang mungkin berisi data Why
                for col in df.columns:
                    if 'why' in col.lower() or 'root' in col.lower() or 'akar' in col.lower():
                        df['adjusted_whys_json'] = df[col].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                        missing_columns.remove('adjusted_whys_json')
                        break
            
            if 'adjusted_temporary_actions_json' in missing_columns:
                # Cari kolom yang mungkin berisi tindakan sementara
                for col in df.columns:
                    if 'temp' in col.lower() or 'sement' in col.lower() or 'action' in col.lower():
                        df['adjusted_temporary_actions_json'] = df[col].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                        missing_columns.remove('adjusted_temporary_actions_json')
                        break
            
            if 'adjusted_preventive_actions_json' in missing_columns:
                # Cari kolom yang mungkin berisi tindakan pencegahan
                for col in df.columns:
                    if 'prev' in col.lower() or 'cegah' in col.lower() or 'prevent' in col.lower():
                        df['adjusted_preventive_actions_json'] = df[col].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                        missing_columns.remove('adjusted_preventive_actions_json')
                        break
    
    # Jika masih ada kolom yang hilang, coba tebak berdasarkan screenshot
    if missing_columns and 'adjusted_whys_json' in missing_columns:
        print("Mencoba memetakan kolom berdasarkan screenshot...")
        if 'adjusted_whys_item' not in df.columns:
            # Dari gambar Excel, kolom ini mungkin adalah adjusted_whys_json
            if 'adjusted_whys_item' in missing_columns and 'adjusted_whys_json' in missing_columns:
                if 'adjusted_whys_item' in df.columns:
                    df['adjusted_whys_json'] = df['adjusted_whys_item'].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                    missing_columns.remove('adjusted_whys_json')
    
    # Berdasarkan screenshot, ini adalah kolom yang terlihat di Excel
    expected_cols = ['created_at', 'machine_name', 'issue_description']  # kolom dasar
    col_mappings = {
        'adjusted_whys_json': ['adjusted_whys_item', 'root_cause', 'why'],
        'adjusted_temporary_actions_json': ['adjusted_temporary_actions_item', 'temp_action', 'action'],
        'adjusted_preventive_actions_json': ['adjusted_preventive_actions_item', 'prev_action', 'preventive']
    }
    
    # Coba memetakan kolom Excel ke format yang dibutuhkan
    for target_col, possible_cols in col_mappings.items():
        if target_col in missing_columns:
            for col in possible_cols:
                if col in df.columns:
                    df[target_col] = df[col].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                    missing_columns.remove(target_col)
                    break
    
    # Jika masih ada kolom yang hilang, gunakan kolom dari gambar Excel yang kita lihat
    # Berdasarkan screenshot di gambar 1, kita tahu ada kolom:
    # 'created_at', 'machine_name', 'issue_description', dan kolom-kolom tindakan
    if 'adjusted_whys_json' in missing_columns and 'adjusted_whys_item' not in df.columns:
        print("Menggunakan metadata dari gambar Excel...")
        if 'adjusted_whys_json' in missing_columns:
            df['adjusted_whys_json'] = df.apply(lambda row: json.dumps([str(row.get('issue_description', ''))]), axis=1)
            missing_columns.remove('adjusted_whys_json')
        
        if 'adjusted_temporary_actions_json' in missing_columns:
            col_name = None
            for col in df.columns:
                if 'temp' in col.lower() or 'action' in col.lower() or 'tindakan' in col.lower():
                    col_name = col
                    break
            if col_name:
                df['adjusted_temporary_actions_json'] = df[col_name].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                missing_columns.remove('adjusted_temporary_actions_json')
            else:
                df['adjusted_temporary_actions_json'] = df.apply(lambda _: json.dumps([]), axis=1)
                missing_columns.remove('adjusted_temporary_actions_json')
        
        if 'adjusted_preventive_actions_json' in missing_columns:
            col_name = None
            for col in df.columns:
                if 'prev' in col.lower() or 'cegah' in col.lower() or 'prevent' in col.lower():
                    col_name = col
                    break
            if col_name:
                df['adjusted_preventive_actions_json'] = df[col_name].apply(lambda x: json.dumps([str(x)]) if pd.notna(x) else json.dumps([]))
                missing_columns.remove('adjusted_preventive_actions_json')
            else:
                df['adjusted_preventive_actions_json'] = df.apply(lambda _: json.dumps([]), axis=1)
                missing_columns.remove('adjusted_preventive_actions_json')
    
    # Jika masih ada kolom yang hilang, beri tahu user
    if missing_columns:
        print(f"Error: Kolom yang dibutuhkan tidak ditemukan dalam file Excel: {missing_columns}")
        print(f"Kolom yang tersedia di Excel: {list(df.columns)}")
        return False
    
    # Impor data ke database
    with app.app_context():
        # Counter untuk membuat ID unik jika diperlukan
        fake_capa_id_counter = 9000
        import_count = 0
        
        # Iterasi melalui data
        for _, row in df.iterrows():
            # Pastikan data yang diperlukan ada dan valid
            if pd.isna(row['machine_name']) or pd.isna(row['issue_description']):
                print(f"Melewati baris dengan machine_name atau issue_description kosong")
                continue
            
            # Konversi created_at ke string jika itu datetime
            created_at = row['created_at']
            if isinstance(created_at, pd.Timestamp):
                created_at = created_at.strftime("%Y-%m-%d")
            elif pd.isna(created_at):
                created_at = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Buat item data
            item = {
                'created_at': created_at,
                'machine_name': str(row['machine_name']),
                'issue_description': str(row['issue_description']),
                'adjusted_whys_json': row['adjusted_whys_json'] if isinstance(row['adjusted_whys_json'], str) else 
                                      json.dumps([str(row['adjusted_whys_json'])]) if pd.notna(row['adjusted_whys_json']) else json.dumps([]),
                'adjusted_temporary_actions_json': row['adjusted_temporary_actions_json'] if isinstance(row['adjusted_temporary_actions_json'], str) else 
                                                 json.dumps([str(row['adjusted_temporary_actions_json'])]) if pd.notna(row['adjusted_temporary_actions_json']) else json.dumps([]),
                'adjusted_preventive_actions_json': row['adjusted_preventive_actions_json'] if isinstance(row['adjusted_preventive_actions_json'], str) else 
                                                  json.dumps([str(row['adjusted_preventive_actions_json'])]) if pd.notna(row['adjusted_preventive_actions_json']) else json.dumps([])
            }
            # Tidak perlu memeriksa duplikasi - impor semua data
            # Komentar: Kode untuk memeriksa duplikasi dihapus agar semua data tetap diimpor, sesuai permintaan user
            
            # Coba temukan CAPA issue yang cocok (opsional)
            capa_issue = CapaIssue.query.filter_by(
                machine_name=item["machine_name"],
                issue_description=item["issue_description"]
            ).first()
            
            # Jika tidak ditemukan, kita akan membuat entri baru dengan fake_capa_id
            capa_id = capa_issue.capa_id if capa_issue else fake_capa_id_counter
            
            # Konversi string date ke datetime
            try:
                if isinstance(item["created_at"], str):
                    created_at = datetime.datetime.strptime(item["created_at"], "%Y-%m-%d")
                else:
                    created_at = item["created_at"]
            except Exception as e:
                print(f"Error konversi tanggal: {e}. Menggunakan tanggal saat ini.")
                created_at = datetime.datetime.now()
            
            # Buat objek AIKnowledgeBase
            # Gunakan 'rca_adjustment' atau 'action_plan_adjustment' sebagai source_type
            # tergantung data mana yang tersedia
            source_type = 'action_plan_adjustment'
            try:
                whys_data = json.loads(item["adjusted_whys_json"])
                if whys_data and len(whys_data) > 0:
                    source_type = 'rca_adjustment'
            except:
                pass
            
            new_knowledge = AIKnowledgeBase(
                capa_id=capa_id,
                source_type=source_type,
                machine_name=item["machine_name"],
                issue_description=item["issue_description"],
                adjusted_whys_json=item["adjusted_whys_json"],
                adjusted_temporary_actions_json=item["adjusted_temporary_actions_json"],
                adjusted_preventive_actions_json=item["adjusted_preventive_actions_json"],
                created_at=created_at,
                is_active=True
            )
            
            # Tambahkan ke database
            db.session.add(new_knowledge)
            import_count += 1
            
            # Increment counter jika menggunakan fake_capa_id
            if not capa_issue:
                fake_capa_id_counter += 1
        
        # Commit semua perubahan
        try:
            db.session.commit()
            print(f"Berhasil mengimport {import_count} data ke tabel ai_knowledge_base")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saat import data: {e}")
            return False

def import_initial_data():
    """Function for backward compatibility"""
    print("PERHATIAN: Fungsi ini sekarang memerlukan file Excel. Gunakan import_excel_data(excel_path) sebagai gantinya.")
    print("Contoh: import_excel_data('data_perusahaan.xlsx')")
    return False

def prompt_for_excel_file():
    """Meminta user untuk menentukan lokasi file Excel yang akan diimpor"""
    print("\nScript untuk Mengimpor Data Excel ke AI Knowledge Base")
    print("==================================================")
    
    # Cari file Excel di direktori saat ini atau uploads
    excel_files = []
    directories_to_check = ['.', 'uploads', 'Docs', 'example']
    
    for directory in directories_to_check:
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith(('.xlsx', '.xls')):
                    excel_files.append(os.path.join(directory, file))
    
    if excel_files:
        print("\nFile Excel yang ditemukan:")
        for i, file in enumerate(excel_files, 1):
            print(f"{i}. {file}")
        
        try:
            choice = int(input("\nPilih nomor file Excel yang ingin diimpor (atau 0 untuk memasukkan path lain): "))
            if 1 <= choice <= len(excel_files):
                excel_path = excel_files[choice-1]
                print(f"Anda memilih: {excel_path}")
                return excel_path
        except:
            pass
    
    # Jika tidak ada pilihan yang valid atau tidak ada file yang ditemukan
    excel_path = input("\nMasukkan path lengkap ke file Excel: ")
    return excel_path

if __name__ == "__main__":
    # Coba cari file excel di direktori
    excel_path = prompt_for_excel_file()
    if excel_path and os.path.exists(excel_path):
        import_excel_data(excel_path)
    else:
        print(f"File tidak ditemukan: {excel_path}")

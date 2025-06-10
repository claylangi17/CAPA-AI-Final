# Detailed Prompt: Pengembangan Aplikasi Web CAPA AI Assistant untuk Manufaktur Packaging

## 1. Tujuan Utama:

Membuat aplikasi web berbasis Flask bernama "CAPA AI Assistant" untuk mengelola proses CAPA di perusahaan manufaktur packaging. Aplikasi ini bertujuan menyederhanakan input data, memanfaatkan AI (Google Gemini API) untuk analisis akar masalah (Root Cause Analysis - 5 Why) dan rekomendasi rencana tindakan (Action Plan), serta menyimpan histori data untuk pembelajaran AI dan pelaporan.

## 2. Target Pengguna:

Staf Quality Assurance (QA), Staf Produksi, Manajer terkait, dan personel lain yang terlibat dalam proses penanganan keluhan pelanggan dan tindakan perbaikan/pencegahan di lingkungan manufaktur packaging.

## 3. Teknologi yang Digunakan:

- Backend Framework: Flask (Python)
- Frontend: HTML, CSS, JavaScript (bisa menggunakan framework seperti Bootstrap atau Tailwind CSS untuk tampilan menarik)
- Database: Pilih salah satu relational database (misalnya PostgreSQL, MySQL, atau SQLite untuk development awal) - *Spesifikasikan pilihan jika ada preferensi.*
- AI Model: Google Gemini API (via library Python google-generativeai)
- PDF Generation: Library Python seperti WeasyPrint, ReportLab, atau FPDF2.
- Deployment (Contoh): Gunicorn + Nginx (atau platform hosting lain seperti Heroku, PythonAnywhere, dll.)

## 4. Fitur Utama:

- Input data CAPA melalui form web yang intuitif.
- Integrasi AI untuk rekomendasi Root Cause (5 Why).
- Integrasi AI untuk rekomendasi Action Plan (Temporary & Preventive).
- Kemampuan bagi user untuk mengedit/menyesuaikan rekomendasi AI.
- Penyimpanan data CAPA secara terstruktur dalam database.
- Kemampuan AI untuk "belajar" dari histori data CAPA di database untuk memberikan rekomendasi yang lebih relevan di masa depan.
- Upload bukti foto (sebelum dan sesudah tindakan).
- Generate laporan CAPA dalam format PDF dengan desain profesional.
- Manajemen status CAPA (Open, Action Pending, Pending Review, Closed).

## 5. Struktur Database (Contoh Skema):

### Tabel capa_issues:
- capa_id (Primary Key, Auto Increment)
- customer_name (VARCHAR)
- issue_date (DATE)
- issue_description (TEXT)
- item_involved (VARCHAR)
- initial_photo_path (VARCHAR) - *Path ke file foto isu awal*
- submission_timestamp (DATETIME)
- status (VARCHAR - e.g., 'Open', 'RCA Pending', 'Action Pending', 'Evidence Pending', 'Closed')

### Tabel root_causes:
- rc_id (Primary Key, Auto Increment)
- capa_id (Foreign Key -> capa_issues.capa_id)
- ai_suggested_rc_json (TEXT/JSON) - *Menyimpan 5 Why dari AI*
- user_adjusted_why1 (TEXT)
- user_adjusted_why2 (TEXT)
- user_adjusted_why3 (TEXT)
- user_adjusted_why4 (TEXT)
- user_adjusted_root_cause (TEXT) - *Why ke-5 atau akar masalah final*
- rc_submission_timestamp (DATETIME)

### Tabel action_plans:
- ap_id (Primary Key, Auto Increment)
- capa_id (Foreign Key -> capa_issues.capa_id)
- ai_suggested_actions_json (TEXT/JSON) - *Menyimpan rekomendasi AI*
- user_adjusted_temp_action (TEXT)
- user_adjusted_prev_action (TEXT)
- pic_name (VARCHAR) - *Person in Charge*
- due_date (DATE)
- action_submission_timestamp (DATETIME)

### Tabel evidence:
- evidence_id (Primary Key, Auto Increment)
- capa_id (Foreign Key -> capa_issues.capa_id)
- evidence_photo_path (VARCHAR) - *Path ke file foto bukti*
- evidence_description (TEXT, optional)
- evidence_submission_timestamp (DATETIME)

## 6. User Flow & Interaksi AI:

### 1. Input Isu Awal:
- User membuka form "New CAPA".
- User mengisi: Customer, CAPA Issue Date, Issue Description, Part Number.
- User mengunggah Photo issue (foto awal).
- User Submit -> Data disimpan ke tabel capa_issues dengan status 'Open' atau 'RCA Pending'.

### 2. AI Rekomendasi Root Cause (5 Why):
- Setelah form awal disubmit, aplikasi memicu panggilan ke Gemini API.
- Input ke AI: Deskripsi isu, item, mungkin konteks dari isu serupa sebelumnya (ambil dari DB).
- Prompt Contoh (untuk AI): "Anda adalah asisten QA di pabrik packaging. Berdasarkan deskripsi isu berikut: '[Issue Description]', item: '[Part Number]', dan mempertimbangkan histori CAPA sebelumnya [opsional: ringkasan N kasus serupa dari DB], lakukan analisis 5 Why untuk menemukan akar masalahnya. Sajikan dalam format terstruktur (Why 1, Why 2, ..., Why 5/Root Cause)."
- Aplikasi menampilkan hasil 5 Why dari AI kepada user.

### 3. User Adjustment & Submit Root Cause:
- User melihat rekomendasi 5 Why dari AI.
- User dapat mengedit setiap tingkatan "Why" jika dirasa kurang sesuai dengan kondisi lapangan.
- User Submit Root Cause yang sudah final -> Data 5 Why (baik asli AI maupun yang di-adjust user) disimpan ke tabel root_causes. Status CAPA di capa_issues diupdate (misal ke 'Action Pending').

### 4. AI Rekomendasi Action Plan (Temporary & Preventive):
- Setelah Root Cause disubmit, aplikasi memicu panggilan *kedua* ke Gemini API.
- Input ke AI: Deskripsi isu awal, *Root Cause final* yang sudah di-adjust user, mungkin konteks action plan efektif dari kasus serupa sebelumnya (ambil dari DB).
- Prompt Contoh (untuk AI): "Berdasarkan isu '[Issue Description]' dengan akar masalah '[User Final Root Cause]', dan mempertimbangkan histori tindakan efektif sebelumnya [opsional: ringkasan N tindakan berhasil dari DB], berikan rekomendasi Rencana Tindakan Sementara (Temporary Action) dan Rencana Tindakan Pencegahan (Preventive Action) yang spesifik dan dapat diukur."
- Aplikasi menampilkan rekomendasi Temporary & Preventive Action dari AI.

### 5. User Adjustment & Input Detail Action Plan:
- User melihat rekomendasi action plan dari AI.
- User dapat mengedit teks Temporary Action dan Preventive Action.
- User *wajib* mengisi PIC (Person in Charge) untuk action plan tersebut.
- User *wajib* mengisi Due Date penyelesaian action plan.
- User Submit Action Plan -> Data action plan (asli AI dan adjusted), PIC, Due Date disimpan ke tabel action_plans. Status CAPA di capa_issues diupdate (misal ke 'Evidence Pending').

### 6. Submit Evidence:
- Setelah PIC melaksanakan action plan, user (atau PIC) kembali ke detail CAPA tersebut di aplikasi.
- User mengunggah Evidence photo (foto bukti setelah tindakan).
- User dapat menambahkan deskripsi singkat untuk bukti (optional).
- User Submit Evidence -> Path foto bukti disimpan ke tabel evidence. Status CAPA di capa_issues diupdate menjadi 'Closed' atau 'Pending Review' (jika perlu approval).

## 7. AI "Learning" Mekanisme:

- AI (Gemini) sendiri bersifat stateless pada setiap panggilan API. "Pembelajaran" terjadi di sisi *aplikasi* dengan cara:
  - Saat meminta rekomendasi (Root Cause atau Action Plan), aplikasi *mengquery* database untuk mencari N record CAPA historis yang paling relevan (berdasarkan kemiripan deskripsi isu, item, atau root cause).
  - Ringkasan atau contoh data historis ini (misal: "Untuk isu serupa X, root cause nya adalah Y dan tindakan efektifnya adalah Z") disertakan dalam *prompt* yang dikirim ke Gemini API.
  - Ini memberikan konteks spesifik perusahaan kepada AI, memungkinkannya menghasilkan output yang lebih relevan dibandingkan hanya berdasarkan pengetahuan umumnya.

## 8. Laporan PDF:

- Harus ada fitur untuk men-generate laporan PDF per CAPA atau rangkuman beberapa CAPA (misal berdasarkan periode, status, atau customer).
- Konten Laporan: Harus mencakup semua detail CAPA: Info Isu Awal (termasuk foto awal jika memungkinkan), Analisis 5 Why (final user), Action Plan (Temporary & Preventive, PIC, Due Date), Bukti Foto (jika memungkinkan), Status Final.
- Tampilan: Desain menarik dan profesional. Sertakan logo perusahaan, format tabel yang rapi, header/footer yang jelas.

## 9. Aspek Tambahan:

- Autentikasi & Otorisasi: Implementasikan login user. Pertimbangkan level akses berbeda jika diperlukan (misal: Staf input, Manager approval).
- Keamanan: Lindungi API Key Gemini, validasi input user, cegah SQL Injection, amankan upload file.
- Notifikasi: Pertimbangkan sistem notifikasi (misal: email) saat due date mendekat atau saat status CAPA berubah.
- User Interface (UI): Desain UI/UX yang bersih, mudah digunakan, dan responsif (tampil baik di desktop maupun mobile browser). *Meskipun disebut "APK", Flask secara native membuat web app. Jika perlu seperti aplikasi mobile native, perlu dibungkus menggunakan tool seperti WebView atau framework cross-platform.*

## 10. Deliverables:

- Source code aplikasi Flask (Python).
- Skrip setup database (SQL).
- Dokumentasi cara setup, konfigurasi (termasuk API Key), dan menjalankan aplikasi.
- Contoh file PDF report yang dihasilkan.

Prompt ini memberikan kerangka kerja yang sangat detail. Anda bisa menyesuaikannya lebih lanjut jika ada detail spesifik lain atau perubahan alur yang diinginkan. Semoga berhasil!

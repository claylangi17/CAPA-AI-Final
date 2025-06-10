[x] Inject knowledge ke ainya
[x] Flow process harus jelas dulu, biar toolsnya gk disalahkan gunakan (gemba dulu -> Baru pakai ke website ->)
[x] AInya bisa baca history dan ada pilihan root cause dulu.
[ ] konek ke data baan untuk nyari lotnya/ batch mana yang harusnya di tarik (karna harus lapor ke danon, wajib tau batch) tracebility (optional)
[ ] Simulasi biaya ainya per satu bulan kira kira bisa berapa
[x] Table beda untuk dibaca ai agar future usenya
[x] Revise table ai knowledgenya
[x] Masukan batch 
[x] Revise Status
[x] Kecilkan photo hasil buktinya 
[x] Bedakan tiap pt dalam websitenya
[x] Tambahkan informasi process (Machine/line) Routingnya done
[x] Buat ainya bisa belajar dari history
[x] Upgrade uinya jadi lebih bagus dari web dan juga hasil pdfnya
[x] Foto evidence bisa ditambah agar bisa lebih banyak
[x] Hapus column indikator keberhasilan pada hasil laporan CAPA (pdf)
[x] Ubah databasenya ke MySQL (tanya mana lebih baik)
[x] Bug: list tidak terhapus untuk action plan
[x] Bug: CAPA action plan belum ada buktinya tapi statusnya success
[x] Bug: Pesan warning "Tindakan ini sudah ditandai selesai, tetapi belum ada bukti foto yang diunggah" masih muncul meskipun sudah ada foto
[x] Ketika kirim bukti, buat jangan dia scroll ulang ke bawah lagi
[x] Bagian 5 why bisa di hapus jika tidak sampai 5 whynya
[x] Di pdf pada bagian action plan, masih memakai action plan yang dari AI, bukan hasil revise 
[x] Batch number/ SPK diganti textnya 
[x] Ganti kata status di report pdf jadi "Closed" and "Open" 
[x] Issue jika status masih gemba pending itu harusnya dia bisa pergi ke page untuk input gembanya terlebih dahulu 
[x] perbaiki loading screen pada halaman action plan (ketika submit)
[x] Perbaiki UI loading screen
[x] Ketika kirim bukti, jangan pergi ke page paling atas, tapi dia stay di bagian Pengajuan Bukti
[x] Fix sematic search di action plan 
[x] Ganti API key tiap project (CAPA and GEMBA)
[x] Ganti semantic search pakai yang free
[x] Animasi loading pada saat upload file 
[x] Dashboard capa (repeted issue)
[x] show to user rekomendasi dari ainya 
[x] Foto di bagian initial issue bisa lebih dari satu 
[x]update waktu di pdf report
[ ]summary sebelum pengajuan bukti (need to be consern again) 
[ ]auto save draft 
[x]fitur role:
    - Super role: Dsiplay all PT
    - User: Display only their own PT
[x] filter by weekending
[ ] AI baca by process
[ ] Masuk ai knowledge based ketika status sudah evidence pending, gaperlu tunggu close (need to be consern again) 
[x] Create dev branch
[x] add to main Branch
[x] Fitur Delete CAPA only on super admin role
[X] Hasil ainya buat tidak ada mengapa lagi 
[x] Fitur liat password
[x] Fitur register hanya bisa dipakai oleh master admin
[X] Companynya ganti printec perkasa tanggerang dan Cikarang (bukan 1&2) - Ask Ignaz update db 
[x] Buat script untuk hapus database CAPA yang idnya dari 0 - 3 digit (dari semua table di database)
[x] Fix bug di view contoh pembelajaran dan add tombol close
[ ] Buat exportnya to customer and to internal (internal dalam bentuk link dan ada kasih tau ini issuenya sudah repeat atau gk, lalu untuk external pdf biasa)
[ ] User isi register form > admin get notify (request register list user) > admin approve > sent email to user kalau sudah di approve untuk data diri yang diisi di register form, lalu ada link untuk create password for user > user login pakai username yang diisi di register form dan password yang sudah dibuat tadi
[x] Buat yang bisa close CAPAnya adalah orang yang buka CAPAnya
[x] Buat table cutomer bisa di choose by dropdown
[x] Fix evidance pending photo not displayed in the pdf report
[ ] Ubah admin passwords
[ ] Buat dashboard untuk kasih tampil CAPA overdue
[x] Kasih fitur diplay setiap image yang di upload, dan juga edit photo gemba  



Flow:
masukin case (Batch, Jumlah reject) -> required untuk gemba (Foto, deskripsi real issue) -> RCA -> Action plan -> evidence
Nice

prompt untuk revise table ai knowledge:
"""
disini saya melihat database ai knowledge based saya itu semua di store dalam satu column yaitu knowledge data, dimana di dalam situ ada terlalu banyak informasi, sehingga saya takutkan ai akan banyak sekali membaca informasi disana sehingga memakai banyak token. saya mau kita bisa query berdasrkan maachine name. 
"""
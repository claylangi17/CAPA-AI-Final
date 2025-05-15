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
[ ] Bedakan tiap pt dalam websitenya
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
[ ] show to user rekomendasi dari ainya 


Flow:
masukin case (Batch, Jumlah reject) -> required untuk gemba (Foto, deskripsi real issue) -> RCA -> Action plan -> evidence
Nice

prompt untuk revise table ai knowledge:
"""
disini saya melihat database ai knowledge based saya itu semua di store dalam satu column yaitu knowledge data, dimana di dalam situ ada terlalu banyak informasi, sehingga saya takutkan ai akan banyak sekali membaca informasi disana sehingga memakai banyak token. saya mau kita bisa query berdasrkan maachine name. 
"""
# Active Context

*This file tracks the current state of work, recent decisions, immediate next steps, and important patterns or learnings relevant to the ongoing development.*

**Key Sections:**

*   **Current Focus:** Meningkatkan kualitas rekomendasi AI untuk RCA dan Action Plan dengan memperbaiki fungsi embedding dan memodifikasi prompt agar tidak menyertakan frasa "Mengadaptasi dari contoh".

*   **Recent Changes (AI Recommendation Improvement):**
    *   **Embedding Model Fix (`ai_learning.py`):**
        *   Memperbaiki fungsi `get_embedding` untuk menggunakan metode yang benar dari Google Generative AI library.
        *   Mengubah pemanggilan dari `embedding_model.embed_content(text)` menjadi `genai.embed_content(model="models/embedding-001", content=text, task_type="retrieval_document")`.
        *   Perubahan ini memperbaiki error: "Error getting embedding: 'Model' object has no attribute 'embed_content'"
    *   **AI Prompt Enhancement (`ai_service.py`):**
        *   Memodifikasi prompt untuk `trigger_rca_analysis` dan `trigger_action_plan_recommendation` agar AI tidak menyertakan frasa "Mengadaptasi dari contoh 1 & 2" dalam responsnya.
        *   Menambahkan instruksi eksplisit: "PENTING: JANGAN PERNAH menyebutkan frasa seperti 'Mengadaptasi dari contoh 1 & 2' atau sejenisnya dalam jawaban Anda. Gunakan bahasa Anda sendiri dan integrasikan solusi dari contoh-contoh ini secara alami tanpa mereferensikan nomor contoh."
    *   **Code Formatting:**
        *   Memperbaiki formatting kode di beberapa file untuk meningkatkan keterbacaan, terutama pada fungsi `_parse_action_list` di `ai_service.py` dan beberapa bagian di `ai_learning.py`.

*   **Next Steps:**
    1.  **Crucial:** Uji kualitas rekomendasi AI untuk RCA dan Action Plan dengan model embedding yang sudah diperbaiki. Verifikasi apakah AI sekarang menghasilkan saran yang lebih relevan berdasarkan semantic search.
    2.  Verifikasi bahwa AI tidak lagi menyertakan frasa "Mengadaptasi dari contoh" dalam responsnya.
    3.  Monitor log aplikasi untuk memastikan tidak ada error terkait embedding.
    4.  Pertimbangkan untuk meningkatkan threshold similarity jika recall terlalu tinggi (saat ini diatur ke 0.3).
    5.  Evaluasi keseimbangan antara precision dan recall dalam hasil semantic search.

*   **Active Decisions/Considerations:**
    *   Memperbaiki fungsi embedding untuk menggunakan metode yang benar dari Google Generative AI library.
    *   Menurunkan threshold similarity dari 0.5 menjadi 0.3 untuk meningkatkan recall dalam pencarian semantic.
    *   Memodifikasi prompt AI untuk mencegah penggunaan frasa "Mengadaptasi dari contoh".
    *   Mempertahankan bobot yang lebih tinggi (70%) untuk kemiripan WHYs dibandingkan kemiripan issue description (30%) dalam menghitung skor relevansi action plan.

*   **Important Patterns/Preferences:**
    *   Menggunakan semantic search untuk menemukan action plan dan RCA yang relevan berdasarkan kemiripan makna, bukan hanya kecocokan kata kunci.
    *   Memberikan instruksi eksplisit dalam prompt AI untuk menghasilkan respons yang lebih alami dan tidak mereferensikan contoh secara langsung.
    *   Menambahkan logging yang ekstensif untuk memudahkan debugging dan pemahaman alur kerja sistem.

*   **Learnings/Insights:**
    *   Semantic search menghasilkan rekomendasi yang jauh lebih relevan dibandingkan pencarian berbasis kata kunci, terutama ketika kata-kata yang digunakan berbeda tetapi maknanya serupa.
    *   Kualitas prompt sangat memengaruhi kualitas output AI. Instruksi yang jelas dan spesifik menghasilkan output yang lebih sesuai dengan kebutuhan.
    *   Embedding model dari Google Generative AI memerlukan parameter yang tepat (`model`, `content`, dan `task_type`) untuk berfungsi dengan baik.
    *   Bobot yang lebih tinggi untuk kemiripan WHYs (70%) dibandingkan kemiripan issue description (30%) menghasilkan rekomendasi action plan yang lebih relevan.

*(This file should be updated frequently to reflect the current development pulse.)*

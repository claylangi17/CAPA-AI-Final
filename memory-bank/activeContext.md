# Active Context

*This file tracks the current state of work, recent decisions, immediate next steps, and important patterns or learnings relevant to the ongoing development.*

**Key Sections:**

*   **Current Focus:** Explaining the basis of semantic similarity for action plan recommendations now that the feature is operational. Discussing potential tuning of similarity thresholds or weights.

*   **Recent Changes (UI/UX Enhancements and Semantic Search Model Update):**
    *   **UI Enhancements (`new_capa.html`, `view_capa.html`, and `gemba_investigation.html`):**
        *   Implemented file upload animation on 'Submit New CAPA Issue' form: Added a spinner and 'uploading' message for the 'Initial Issue Photo' field.
        *   Enhanced 'Machine Name' input on `new_capa.html`: Replaced free text input with a searchable dropdown using Choices.js.
        *   Created a new API endpoint `/api/machine_names` in `routes.py` to provide existing machine names. **Source of machine names for this API is now the `AiKnowledgeBase` table (previously `CapaIssue` table).**
        *   Included Choices.js CDN in `base.html`.
        *   Implemented file upload animation for 'Edit Bukti' form in `view_capa.html` (previous session).
        *   Added file upload animation to the 'Foto Bukti' section in `gemba_investigation.html` for consistency with other forms.
    *   **Embedding Model Change (`ai_learning.py`):**
        *   Mengganti model embedding dari `google.generativeai` (`models/embedding-001`) ke `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
        *   Mengimpor `SentenceTransformer` dari `sentence_transformers`.
        *   Menginisialisasi model `SentenceTransformer` di tingkat modul.
        *   Memperbarui fungsi `get_embedding` (sekarang `get_embedding_st` dan `get_embedding_st_rca`) untuk menggunakan metode `model.encode()` dari `sentence-transformers`.
        *   Menghapus ketergantungan pada `GOOGLE_API_KEY` untuk proses embedding.
        *   **Route Update (`routes.py`):**
            *   Modified `generate_pdf_report` to eagerly load `CapaIssue.gemba_investigation` using `db.joinedload()` for PDF report generation, ensuring all related data (including timestamps) is efficiently fetched.
        *   **Dependency Update (`requirements.txt`):**
        *   Menambahkan `sentence-transformers` ke `requirements.txt`.
    *   **AI Prompt Enhancement (`ai_service.py`):** (Perubahan sebelumnya, masih relevan)
        *   Memodifikasi prompt untuk `trigger_rca_analysis` dan `trigger_action_plan_recommendation` agar AI tidak menyertakan frasa "Mengadaptasi dari contoh 1 & 2" dalam responsnya.
    *   **Code Formatting:** (Perubahan sebelumnya, masih relevan)
        *   Memperbaiki formatting kode di beberapa file.
    *   **Logging Enhancement (`ai_learning.py`):**
        *   Enhanced logging in `cosine_similarity_rca` function.
        *   Added debug log for the calculated similarity score.
        *   Added debug log for invalid input cases, detailing input types.
    *   **Debugging Attempt for Action Plan Search (`ai_learning.py`):**
        *   Modified conditional assignment for `current_issue_embedding` and replaced `cosine_similarity` with `cosine_similarity_rca` in `get_relevant_action_plan_knowledge`.
        *   This, along with subsequent robust NumPy array handling, resolved the "truth value of an array is ambiguous" error.
    *   **NameError Fix (`ai_learning.py`):**
        *   Resolved `NameError: name 'cosine_similarity_rca' is not defined` by moving the definitions of `cosine_similarity_rca` and `get_embedding_st_rca` to appear before `get_relevant_action_plan_knowledge` function which calls them.
    *   **Semantic Search for Action Plans Now Operational:** The combination of fixes has successfully enabled the semantic search functionality for action plans.
    *   **Refactored Action Plan Semantic Search (`ai_learning.py`):** Changed `get_relevant_action_plan_knowledge` to a two-stage process as per USER request:
        1.  **Stage 1:** Select Top 5 historical action plans based on similarity of *issue description*.
        2.  **Stage 2:** From these Top 5, select Top 3 based on similarity of *5 Whys analysis*.
        *   The final score is now based on the 5 Whys similarity from Stage 2.
        *   Removed local `get_embedding_st` and `cosine_similarity` functions, now consistently using global `_rca` suffixed versions.
        *   Added `_extract_text_from_whys_json_str` helper function.
    *   **Further Refined Action Plan Search (`ai_learning.py`):** Added an initial **Stage 0** to `get_relevant_action_plan_knowledge`:
        *   **Stage 0:** Filter potential action plans by exact `current_capa_machine_name` *before* semantic search stages.
        *   Stages 1 (Issue Sim.) and 2 (Whys Sim.) now operate on this machine-filtered list.

*   **Next Steps:**
    1.  **Thoroughly test the new *three-stage* semantic search for action plan recommendations (Machine Filter -> Issue Sim. -> Whys Sim.).**
        *   Verify correct filtering at each stage.
        *   Check logging for clarity.
        *   Evaluate the relevance of the final recommendations under this new logic.
    2.  Discuss with the USER if the new three-stage approach and its results (Machine Filter -> Top 5 Issue -> Top 3 Whys) are satisfactory, or if further tuning of N/M values is desired.
    3.  **Explain the basis of similarity calculation for action plans to the USER.** (Currently doing)
    4.  Discuss with the USER if the current similarity threshold (0.3) and weighting (30% issue, 70% Whys) provide good results, or if tuning is desired.
    5.  **Crucial:** Uji kualitas rekomendasi AI untuk RCA dan Action Plan dengan model embedding `paraphrase-multilingual-MiniLM-L12-v2`. Verifikasi apakah AI sekarang menghasilkan saran yang lebih relevan (Action plan part seems to be working, RCA needs checking too).
    6.  Pastikan dependensi `sentence-transformers` terinstal dengan benar di lingkungan deployment (`pip install -r requirements.txt`).
    7.  Monitor log aplikasi untuk memastikan tidak ada error terkait model embedding baru.
    8.  Run the application to verify the enhanced logging in `cosine_similarity_rca` and overall cosine similarity functionality.
    9.  Verifikasi bahwa AI tidak lagi menyertakan frasa "Mengadaptasi dari contoh" dalam responsnya (tugas berkelanjutan).
    10. Pertimbangkan untuk menyesuaikan threshold similarity (saat ini 0.3) jika diperlukan setelah pengujian dengan model baru.
    11. Evaluasi keseimbangan antara precision dan recall dalam hasil semantic search dengan model baru.
    12. Await user feedback on the new upload animation and form enhancements.
    13. Continue addressing items from the `todo.md` or new user requests.
    14. Verify the functionality of all recent UI enhancements:
        *   File upload animation on `new_capa.html` (Initial Issue Photo).
        *   Searchable dropdown for 'Machine Name' on `new_capa.html` (ensure data now comes from `AiKnowledgeBase`).
        *   File upload animation on `view_capa.html` (Edit Bukti).
        *   File upload animation on `gemba_investigation.html` (Foto Bukti).
    15. Test the submission process for forms with these new animations to ensure data is correctly submitted and animations behave as expected.
    16. Address any further UI/UX feedback or issues that arise from testing.
    17. **Created `HOW_TO_RUN.md` to document application setup and execution.**

*   **Active Decisions/Considerations:**
    *   Mengganti model embedding ke `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` untuk potensi peningkatan kualitas semantic search, terutama untuk teks multilingual.
    *   Menurunkan threshold similarity dari 0.5 menjadi 0.3 untuk meningkatkan recall dalam pencarian semantic (keputusan sebelumnya, mungkin perlu ditinjau ulang dengan model baru).
    *   Memodifikasi prompt AI untuk mencegah penggunaan frasa "Mengadaptasi dari contoh" (keputusan sebelumnya).
    *   Mempertahankan bobot yang lebih tinggi (70%) untuk kemiripan WHYs dibandingkan kemiripan issue description (30%) dalam menghitung skor relevansi action plan (keputusan sebelumnya, mungkin perlu ditinjau ulang dengan model baru).
    *   Used Bootstrap spinner for animations for consistency with existing UI elements.
    *   Chose Choices.js for the searchable dropdown due to its flexibility and ease of integration.
    *   Ensured new machine names can still be added via the 'Other' option in the dropdown.
    *   Decided to implement consistent file upload animations across all relevant forms (`new_capa.html`, `view_capa.html`, `gemba_investigation.html`) to improve user experience.
    *   JavaScript logic for Choices.js dropdown on `new_capa.html` was refined to correctly combine API-fetched machine names with a static 'Other (manual input)' option before rendering.
    *   The `gemba_investigation.html` already had an AI processing overlay; the new file upload animation was integrated to appear before this overlay if files are being uploaded.
    *   **The `/api/machine_names` endpoint in `routes.py` now queries the `AiKnowledgeBase` table for machine names instead of `CapaIssue`.**

*   **Open Questions/Decisions:**
    *   Are the Top 5 (issue sim) / Top 3 (Whys sim) counts optimal for action plan recommendations after machine name filtering?
    *   Should the RCA recommendation logic (`get_relevant_rca_knowledge`) be updated to a similar multi-stage process?
    *   What is the next major feature or improvement focus after validating current AI functionalities?

*   **Important Patterns/Preferences:**
    *   Menggunakan semantic search (sekarang dengan `sentence-transformers`) untuk menemukan action plan dan RCA yang relevan.
    *   Menginisialisasi model embedding sekali di tingkat modul untuk efisiensi.
    *   Memberikan instruksi eksplisit dalam prompt AI untuk menghasilkan respons yang lebih alami.
    *   Menambahkan logging yang ekstensif untuk debugging.
    *   Standard form submission reloads the page, so the animation is visible during the upload process until the new page loads.
    *   Combining backend API endpoints (Flask) with frontend JavaScript libraries (Choices.js) to create dynamic and user-friendly form elements.
    *   Importance of providing visual feedback (animations) during time-consuming operations like file uploads.

*   **Learnings/Insights:**
    *   `sentence-transformers` menyediakan cara yang mudah untuk menggunakan berbagai model embedding pre-trained.
    *   Model `paraphrase-multilingual-MiniLM-L12-v2` diharapkan memberikan hasil yang baik untuk teks dalam berbagai bahasa.
    *   Perubahan model embedding memerlukan pembaruan pada cara embedding dihasilkan dan dependensi proyek.
    *   Semantic search (umumnya) menghasilkan rekomendasi yang jauh lebih relevan dibandingkan pencarian berbasis kata kunci.
    *   Kualitas prompt sangat memengaruhi kualitas output AI.

*(This file should be updated frequently to reflect the current development pulse.)*

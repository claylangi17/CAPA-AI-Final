# Active Context

*This file tracks the current state of work, recent decisions, immediate next steps, and important patterns or learnings relevant to the ongoing development.*

**Key Sections:**

*   **Current Work Focus**
    *   **New Feature: Soft Delete for CAPA Issues**
        - Implemented soft delete functionality for CAPA issues to allow marking items as deleted without permanent removal.
        - **Model Changes (`models.py`):** Added `is_deleted` (Boolean, default `False`) and `deleted_at` (DateTime, nullable) fields to the `CapaIssue` model.
        - **New Route (`routes.py`):** Created `/capa/<int:capa_id>/soft_delete` (POST) for `super_admin` users to mark a CAPA as deleted. This route updates `is_deleted` to `True` and sets `deleted_at`.
        - **Route Modifications (`routes.py`):** Updated the `index` and `dashboard_data` routes to filter out CAPA issues where `is_deleted` is `True`, ensuring they are not displayed or included in analytics.
    *   **New Feature: AI Learning Examples Dropdown**

*   **Current Work Focus**
    - **New Feature: AI Learning Examples Dropdown**
        - Implemented a transparency feature showing examples of historical CAPA data used by the AI to generate RCA suggestions.
        - Added `learning_examples_json` field to the `RootCause` model and created migration script.
        - Enhanced `trigger_rca_analysis()` to store structured learning examples data.
        - Added UI dropdown below AI RCA suggestions with accordion display of learning examples.
        - Fixed parameter error in `get_relevant_rca_knowledge()` function call that was causing runtime errors.
    - **Enhancing Dashboard Date Filters (Testing Phase):**
        - `dashboard.html`: 
            - UI for tiered date filters (Predefined, Year/Month/Week, Custom Range) and JS logic to send parameters to backend.
            - **Recent JS Updates (Current Session):** Implemented default year selection for YMW filter, ensured year parameter is consistently sent, and improved fallback query. Minor UI aesthetic improvements to filter bar spacing and alignment.
        - `routes.py` (`dashboard_data` function):
            - Added logic to parse new filter parameters: `filter_type`, `year`, `month`, `week`, `start_date`, `end_date`.
            - Calculates `from_date_obj` and `to_date_obj` based on these parameters.
            - Applies these date objects to filter `capa_issue_query` to create `query_after_date_filter`.
            - All subsequent chart aggregations now use `query_after_date_filter`.
            - Imported `date` from `datetime` and `calendar`.
            - Fixed indentation errors introduced during the modification of filter logic.
    - **New Feature: Forgot Password by Email**
        - User requested a 'Forgot Password' feature.
        - Implementation includes:
            1. Adding `Flask-Mail` to `requirements.txt` and configuring mail settings in `app.py`
            2. Adding token generation/verification methods to the `User` model in `models.py`
            3. Creating routes: `/request_reset_token` and `/reset_token/<token>` in `routes.py`
            4. Building templates: `request_reset_token.html`, `reset_token.html`, and `reset_email.html`
        - **Recent Fixes (Current Session):**
            1. Fixed template imports in password reset templates: Changed from `bootstrap5/form.html` to `bootstrap/form.html` to match the installed `bootstrap-flask` package
            2. Updated Gmail authentication: Added App Password in `.env` for secure SMTP authentication
            3. Added `python-dotenv` integration to properly load environment variables from `.env` file
            4. Formatted App Password correctly (without spaces) to avoid authentication issues
    *   **Dashboard Bug Fix:** User reported discrepancy in 'Status Distribution' chart on Dashboard Analytic page (showed 2 'Action Pending' vs 1 'Closed' CAPA for the selected company on main dashboard). Investigated `dashboard_data` route and found that the company filter was being lost during status calculation due to query re-initialization. Applied a fix to ensure company filter persists for status distribution.
    *   **Dashboard Verification:** Verified backend logic for 'Repeated Issues' and 'Issue Trends' charts in `dashboard_data`. Confirmed they correctly handle and display data for a single CAPA scenario within the selected company context.

**Recent Changes (New Feature Initiation, Startup Issue Resolution, etc.):**
    *   **Dashboard Date Filter Backend (`routes.py`):**
        *   Implemented backend logic in `dashboard_data` to receive and process new date filter parameters (`filter_type`, `year`, `month`, `week`, `start_date`, `end_date`).
        *   Ensured date filters are applied correctly to the base query for all chart data aggregations.
            *   Corrected Python indentation errors that arose during the implementation of the new filter logic.
    *   **Soft Delete Implementation (`routes.py`):**
        *   Modified `index` and `dashboard_data` routes to filter `CapaIssue` queries by `is_deleted == False`.
    *   **New Feature Initiation: Multi-Company Support**
        *   Received user request for multi-company functionality with role-based access (Super User vs. User) and data filtering, including a specific list of companies.
        *   Updated `projectbrief.md` and `productContext.md` to reflect this new major requirement.
    *   **User Query about CAPA ID Generation:**
        *   User inquired about CAPA ID generation, specifically why a new CAPA for a new company did not start with ID 1.
        *   Clarified that `CapaIssue.capa_id` is a global auto-incrementing primary key, not reset or sequenced per company. This is standard database behavior for ensuring unique record identifiers across the entire table.
    *   **Startup Module Error Resolution (`flask_login`, `flask_wtf`):
    *   **Startup Module Error Resolution (`flask_login`, `flask_wtf`):
        *   Encountered `ModuleNotFoundError` for `flask_login` and subsequently `flask_wtf` despite being listed in `requirements.txt`.
        *   Troubleshooting steps included:
            *   Verifying `requirements.txt`.
            *   Attempting to run `app.py` with the explicit virtual environment Python interpreter (`.\.venv\Scripts\python.exe app.py`).
            *   Forcing reinstallation of packages using `.\.venv\Scripts\pip.exe install --force-reinstall ...`.
            *   Checking `sys.path` for the venv Python interpreter to confirm `site-packages` was included.
            *   Listing `site-packages` directory contents to confirm missing packages.
        *   Identified that `pip.exe` might be resolving to an incorrect venv due to how the project copy was made or PowerShell path resolution.
        *   **Successfully resolved by installing packages using the command: `& "d:\Coding\CAPA AI Final - Copy\CAPA AI Assistant\.venv\Scripts\python.exe" -m pip install <package_name>==<version>`. This ensures `pip` is run as a module of the correct Python interpreter within the correct virtual environment.**
        *   The application (`app.py`) now starts successfully without module errors.
    *   **User Registration Refinement & Testing:**
        *   Successfully resolved `ModuleNotFoundError: No module named 'email_validator'` by ensuring `pip install -r requirements.txt` was run in the correct virtual environment (`D:\Coding\CAPA AI Final - Copy\CAPA AI Assistant\venv\`).
        *   Modified `routes.py` in the `/register` route to filter the company selection dropdown, excluding "Sansico Group (all company combine)" and "Unassigned" for new regular user registrations.
        *   Confirmed that new users can register, select an appropriate company, and log in. Post-login, regular users do not see a company selection dropdown and are scoped to their registered company.
    *   **User Authentication Flow Verification:**
        *   Successfully tested and confirmed the entire authentication flow:
            *   Unauthorized access to protected routes redirects to login.
            *   Successful login with valid credentials.
            *   Authorized access to protected routes post-login.
            *   Successful logout.
            *   Unauthorized access to protected routes post-logout (redirects to login).
    *   **UI Enhancements (`new_capa.html`, `view_capa.html`, and `gemba_investigation.html`):**
        *   Implemented file upload animation on 'Submit New CAPA Issue' form: Added a spinner and 'uploading' message for the 'Initial Issue Photo' field.
        *   Enhanced 'Machine Name' input on `new_capa.html`: Replaced free text input with a searchable dropdown using Choices.js.
        *   Created a new API endpoint `/api/machine_names` in `routes.py` to provide existing machine names. **Source of machine names for this API is now the `AiKnowledgeBase` table (previously `CapaIssue` table).**
        *   Included Choices.js CDN in `base.html`.
        *   Implemented file upload animation for 'Edit Bukti' form in `view_capa.html` (previous session).
        *   Added file upload animation to the 'Foto Bukti' section in `gemba_investigation.html` for consistency with other forms.
        *   **CSRF Token Fix (`new_capa.html`):** Added `{{ form.hidden_tag() }}` to the form in `new_capa.html` to resolve CSRF token missing errors on submission.
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

*   **Next Steps (Immediate):**
    *   **Testing CSRF Protection (High Priority):**
        *   Thoroughly test all forms where CSRF tokens were recently added (`new_capa.html`, `gemba_investigation.html`, `view_capa.html`) to ensure CSRF tokens are functioning correctly and form submissions are processed without errors.
    *   **Soft Delete - Database Migration:**
        *   Run `flask db migrate -m "Add soft delete fields to CapaIssue"`.
        *   Run `flask db upgrade`.
        *   Address potential `ModuleNotFoundError` with `update_schema.py` by verifying script content and virtual environment activation.
    *   **Soft Delete - Testing:**
        *   Test the `/capa/<int:capa_id>/soft_delete` route functionality.
        *   Verify that soft-deleted CAPAs are correctly filtered from the `index` page and `dashboard_data` aggregations.
    *   **Soft Delete - UI Updates:**
        *   Implement a "Delete" button in the UI for CAPA issues (e.g., on `view_capa.html` or `index.html`).
        *   Ensure the button triggers the soft delete route.
        *   Add a confirmation dialog before soft deletion.

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
    *   **UI Navbar Enhancements (`templates/base.html`):**
        *   Added vertical padding (`py-2`) to the main navbar element.
        *   Added an offset (`data-bs-offset="0,10"`) to company selector and user dropdown toggles.
        *   Applied rounded corners (`rounded-3`) to dropdown menus.
        *   Adjusted `top` style of `#sticky-flash-container` to `78px`.
        *   Fixed alignment issue for regular users by changing company display from `<span class="navbar-text me-3">` to `<a class="nav-link" href="#">` within a `<li class="nav-item dropdown">` element for consistent styling with super_admin view.
    *   **Navbar Alignment Fix for Regular Users:** Fixed the alignment issue for regular users by modifying the company display in the navbar to ensure consistent styling with the super admin view.
    *   **Security Enhancements:**
        *   **CSRF Protection (All Forms):** 
            *   Added `{{ form.hidden_tag() }}` to all identified forms requiring it across the application (`new_capa.html`, `gemba_investigation.html`, `view_capa.html`) to enhance security against CSRF attacks. This includes:
                *   `new_capa.html`: New CAPA submission form.
                *   `gemba_investigation.html`: Gemba investigation form.
                *   `view_capa.html`: RCA Edit, Action Plan Edit, Temporary/Preventive Evidence Submission, Close CAPA, Edit Evidence Modal forms.
            *   **Resolved `jinja2.exceptions.UndefinedError: 'form' is undefined`:** Fixed this error for `new_capa.html`, `view_capa.html`, and `gemba_investigation.html` by defining a minimal `CSRFOnlyForm(FlaskForm)` in `routes.py` and ensuring an instance of it is passed to these templates during GET requests. Authentication routes (`login`, `register`, etc.) were confirmed to correctly pass their specific WTForms.

*   **Next Steps & Action Items:**
    1.  **Review Navbar UI Changes:**
        - User to review the recent navbar UI enhancements in `templates/base.html`.
        - Provide feedback for any further adjustments.
    2.  **Test Dashboard Date Filters (USER ACTION REQUIRED):**
        - User to thoroughly test the recent JavaScript and UI changes in `dashboard.html` for date filtering (Predefined, Year/Month/Week, Custom Range).
        - Verify data is filtered and displayed correctly, especially the YMW filter's default year behavior.
        - Provide feedback on UI aesthetic changes to the filter bar.
    3.  **Review `routes.py` for Lint Errors:**
        - Address any remaining lint errors in `routes.py` after recent backend fixes.
    4.  **Finalize Forgot Password Feature:**
        - User to configure actual email sending credentials in `.env` for the 'Forgot Password' feature.
        - Test the end-to-end 'Forgot Password' flow.
    5.  **Continue Multi-Company Feature Development:**
        - User to run the `reassign_company_data.py` script (after backing up the database) to migrate existing data.
        - User to verify that the excluded companies no longer appear in UI dropdowns.
        - User to manually delete the excluded companies (IDs 1, 11, 12) from the `companies` table via phpMyAdmin after successful data migration and verification.
        - Continue with the implementation of multi-company data handling for other routes (e.g., `edit_capa`, `view_capa`).
        - Thoroughly test the application, especially company selection and data association.
        - Update all relevant Memory Bank files based on testing outcomes and further development.
    6.  **Database Migration (Multi-Company):**
        - Plan and execute database migration for multi-company model changes if not already fully completed (associating existing records, ensuring constraints).
    7.  **Memory Bank Update:**
        - Comprehensively update all relevant Memory Bank files (`progress.md`, `systemPatterns.md`, `techContext.md`, etc.) to reflect the current project state, including multi-company architecture and recent UI changes.

*   **Active Decisions/Considerations:**
    *   The week calculation logic in `routes.py` for the 'Year/Month/Week' dashboard filter is a simple implementation (e.g., week 1 is days 1-7). This may need refinement based on user feedback or specific business requirements (e.g., ISO week standards).
    *   **Decision to prioritize multi-company feature development based on user request.**
    *   **Initial data model design for multi-company:**
        *   A new `Company` table will be created (attributes: `id`, `name`, `code`).
        *   The `User` table will be modified to include a `role` field (e.g., string values 'super_user', 'user') and a `company_id` (ForeignKey to `Company.id`).
        *   A `company_id` (ForeignKey to `Company.id`) will be added to all primary data tables that need to be company-specific (e.g., `CapaIssue`, `AIKnowledgeBase`, and their related tables like `GembaInvestigation`, `RootCause`, `ActionPlan`).
    *   User roles defined as 'Super Role' (can access all company data and an aggregated view) and 'User' (access only their own company's data).
    *   The company selection will likely be stored in the user's session.
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
    *   Ensured Python packages are installed into the correct virtual environment by invoking `pip` as a module of the venv's Python interpreter (`python.exe -m pip install ...`).
    *   Utilized PowerShell's call operator `&` and quoted executable paths for robust command execution when paths contain spaces.

*   **Open Questions/Decisions (Multi-Company Feature):**
    *   How will existing user and CAPA data be migrated/associated with the new company structure? (e.g., default company, script for assignment, manual update?)
    *   What is the exact behavior for the "Sansico Group (all company combine)" option in the dropdown? Is it a true data aggregation across tables, or does it imply 'no company filter' for super users (showing all records)? True aggregation can be complex.
    *   Where precisely in the UI header (as requested by user image) should the company dropdown be placed, and how will it interact with existing navigation elements for optimal UX?
    *   How will the 'company code' (e.g., 191, 180) be used? Is it just for display, or for linking/filtering as well?
    *   Will there be an admin interface to manage companies and user-company assignments?

*   **Open Questions/Decisions (Existing Features):**
    *   Are the Top 5 (issue sim) / Top 3 (Whys sim) counts optimal for action plan recommendations after machine name filtering?
    *   Should the RCA recommendation logic (`get_relevant_rca_knowledge`) be updated to a similar multi-stage process?
    *   What is the next major feature or improvement focus after validating current AI functionalities (now superseded by multi-company feature)?

*   **Important Patterns/Preferences:**
    *   Menggunakan semantic search (sekarang dengan `sentence-transformers`) untuk menemukan action plan dan RCA yang relevan.
    *   Menginisialisasi model embedding sekali di tingkat modul untuk efisiensi.
    *   Memberikan instruksi eksplisit dalam prompt AI untuk menghasilkan respons yang lebih alami.
    *   Menambahkan logging yang ekstensif untuk debugging.
    *   Standard form submission reloads the page, so the animation is visible during the upload process until the new page loads.
    *   Combining backend API endpoints (Flask) with frontend JavaScript libraries (Choices.js) to create dynamic and user-friendly form elements.
    *   Importance of providing visual feedback (animations) during time-consuming operations like file uploads.

*   **Learnings/Insights:**
    *   PowerShell requires careful handling of commands with paths containing spaces and arguments. Using the call operator (`&`) and quoting the executable path (`& "path\to\exe" args`) is more reliable.
    *   Invoking `pip` as a module of a specific Python interpreter (`python.exe -m pip ...`) is the most robust way to ensure packages are installed into that interpreter's environment, especially when multiple virtual environments or complex project setups are involved.
    *   Copying virtual environment folders directly can sometimes lead to `pip` or other scripts retaining incorrect path associations.
    *   `sentence-transformers` menyediakan cara yang mudah untuk menggunakan berbagai model embedding pre-trained.
    *   Model `paraphrase-multilingual-MiniLM-L12-v2` diharapkan memberikan hasil yang baik untuk teks dalam berbagai bahasa.
    *   Perubahan model embedding memerlukan pembaruan pada cara embedding dihasilkan dan dependensi proyek.
    *   Semantic search (umumnya) menghasilkan rekomendasi yang jauh lebih relevan dibandingkan pencarian berbasis kata kunci.
    *   Kualitas prompt sangat memengaruhi kualitas output AI.

*(This file should be updated frequently to reflect the current development pulse.)*

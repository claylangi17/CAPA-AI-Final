# Project Progress

*This document tracks the overall status of the project, what's completed, what remains, known issues, and the evolution of key decisions.*

**Status Overview:**

*   **Current State:** The application implements the core CAPA workflow with AI integration. Startup module errors (`flask_login`, `flask_wtf`) have been resolved. The semantic search functionality uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. User registration has been refined: `email-validator` dependency issues are fixed, and the company selection list for new users is correctly filtered. Development continues on the multi-company support feature.
*   **What Works (Inferred & Recently Enhanced):**
    *   Core CAPA workflow (issue creation, Gemba, RCA, Action Plan, Evidence, Closure).
    *   AI-powered suggestions for RCA and Action Plans (using Google Generative AI for text generation).
    *   Script `import_initial_data.py` for initial data import.
    *   Modified prompt system in `ai_service.py` for AI suggestions.
    *   **Semantic Search Enhancement (Model Change):**
        *   Switched embedding model from Google's `embedding-001` to `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` in `ai_learning.py`.
        *   Integrated `sentence-transformers` library for generating embeddings.
        *   Model is initialized at the module level in `ai_learning.py`.
        *   Removed dependency on `GOOGLE_API_KEY` for embeddings.
        *   Added `sentence-transformers` to `requirements.txt`.
        *   Maintained similarity threshold at 0.3 (may need review with new model).
        *   Maintained extensive logging for similarity scores.
    *   **AI Prompt Improvement:** (Previous enhancement, still active)
        *   Modified prompts in `trigger_rca_analysis` and `trigger_action_plan_recommendation` to prevent AI from using phrases like "Mengadaptasi dari contoh 1 & 2".
        *   Added explicit instructions for AI to integrate solutions naturally without referencing example numbers.
    *   **Code Formatting:**
        *   Improved code formatting in `ai_service.py` and `ai_learning.py` for better readability.
    *   PDF report generation.
    *   File uploads and serving with animation for 'Edit Bukti' form.
    *   Basic status tracking.
    *   **File upload animation for 'Initial Issue Photo' on 'Submit New CAPA Issue' form (`new_capa.html`)**.
    *   **Searchable dropdown for 'Machine Name' on 'Submit New CAPA Issue' form (`new_capa.html`)**: 
        *   Populated from database via `/api/machine_names`.
        *   Uses Choices.js for search functionality.
        *   Allows manual input for new machine names.
    *   **File upload animation for 'Foto Bukti' on 'Gemba Investigation' form (`gemba_investigation.html`)**.
    *   **Navbar UI Enhancements (`templates/base.html`):**
        *   Added vertical padding (`py-2`) to the main navbar element.
        *   Added an offset (`data-bs-offset="0,10"`) to company selector and user dropdown toggles.
        *   Applied rounded corners (`rounded-3`) to dropdown menus.
        *   Adjusted the `top` style of `#sticky-flash-container` to `78px`.
    *   **Application Startup:** Successfully starts without `ModuleNotFoundError` issues for `flask_login` and `flask_wtf` after correct `pip` installation within the virtual environment.
    *   **Dashboard Date Filters:**
        *   **`routes.py` (Backend):** Logic in `dashboard_data` function successfully parses new date filter parameters (`filter_type`, `year`, `month`, `week`, `start_date`, `end_date`), calculates date objects, and applies them to a base query for consistent chart filtering. Indentation errors resolved.
        *   **`dashboard.html` (Frontend - Current Session):** JavaScript updated to improve 'Year/Month/Week' (YMW) filter functionality by implementing default year selection, ensuring the 'year' parameter is consistently sent, and correcting fallback query logic. Minor UI aesthetic improvements made to the filter bar (spacing, alignment).
    *   **User Registration & Authentication:**
        *   New users can register successfully.
        *   The company selection dropdown on the registration form correctly excludes "Sansico Group (all company combine)" and "Unassigned".
        *   Email validation (`email-validator`) is working due to correct installation in the virtual environment.
        *   The overall user authentication flow (login, logout, protected routes) is fully functional. Tested and confirmed:
        *   Unauthorized access to protected routes redirects to login.
        *   Successful login with valid credentials.
        *   Authorized access to protected routes post-login.
        *   Successful logout.
        *   Unauthorized access to protected routes post-logout (redirects to login).
    *   **Logging Enhancements (`ai_learning.py`):**
        *   Improved logging in `cosine_similarity_rca` to include calculated similarity scores.
        *   Added detailed logging for invalid input scenarios in `cosine_similarity_rca`.
    *   **PDF Report Generation (`routes.py`):**
        *   Enhanced `generate_pdf_report` to eagerly load `CapaIssue.gemba_investigation` for improved data fetching efficiency and to ensure all timestamp-related data is available.
    *   **Three-Stage Semantic Search for Action Plans:**
        *   Refactored `get_relevant_action_plan_knowledge` to a three-stage process:
            0.  **Stage 0:** Filter by exact `current_capa_machine_name` if provided.
            1.  **Stage 1:** From machine-filtered (or all if no machine name) entries, identifies Top 5 based purely on *issue description similarity*.
            2.  **Stage 2:** From these Top 5, identifies the Top 3 based purely on *5 Whys similarity*.
        *   The final reported score for a recommendation is its 5 Whys similarity score from Stage 2.
        *   Added a helper function `_extract_text_from_whys_json_str` for consistent text extraction from 5 Whys JSON data.
*   **What's Left to Build / Refine
- **Test Dashboard Date Filters (USER ACTION - High Priority):**
    - User to conduct thorough end-to-end testing of the recent JavaScript and UI changes in `dashboard.html` for the date filtering system (Predefined, Year/Month/Week, Custom Range).
    - Verify data accuracy for all filter combinations, especially YMW default year behavior.
    - Provide feedback on UI aesthetic changes to the filter bar.
    - Identify and report any bugs or unexpected behavior.
    - After user testing, potentially refine week calculation logic in `routes.py` or address further JS issues based on feedback.
- **Implement 'Forgot Password' Feature (In Progress):**
    - Add email sending capability (`Flask-Mail`). (Added to `requirements.txt`, config in `app.py`)
    - Implement secure token generation and verification for password reset links. (Methods added to `User` model)
    - Create forms for requesting reset and setting new password.
    - Develop routes to handle reset requests and password updates. (DONE - `request_reset_token`, `reset_token/<token>` routes, `send_reset_email` helper, and supporting HTML templates created)
    - Create email template. (DONE - `templates/reset_email.html`)
    - Add UI elements (e.g., link on login page).
    *   **Testing AI Effectiveness:** Thoroughly test the AI suggestion quality with the new `paraphrase-multilingual-MiniLM-L12-v2` embedding model.
    *   **Semantic Search Fine-tuning:** Evaluate and adjust the similarity threshold (currently 0.3) with the new model to balance precision and recall.
    *   **Dependency Management:** Ensure `sentence-transformers` and its dependencies are correctly handled in deployment.
    *   **Advanced Text Matching:** The new semantic search model is a significant step; further NLP techniques could be explored later.
    *   **User Interface/Experience (UI/UX):** General review and refinement.
    *   **Error Handling:** Continued focus on robust error handling.
    *   **Security, Formal Testing (Unit/Integration), Deployment Prep:** Standard ongoing concerns.
    *   **Database Migrations:** Consider adopting a formal migration tool like Alembic for future schema changes.
    *   **Documentation:** Create `HOW_TO_RUN.md` (Completed).
    *   **Company Management & Data Migration:**
        - Modified `routes.py` to hide specific companies (IDs 1, 11, 12) from UI selection.
        - Created `reassign_company_data.py` script to reassign existing `CapaIssue` and `AIKnowledgeBase` data to a single target company (PT. Printec Perkasa II - ID 3).
        - User to execute `reassign_company_data.py` script.
        - User to verify UI changes and data migration.
        - User to manually delete unused company entries from the database.
        - Implement company-based data handling for `edit_capa`, `view_capa`, and related entities.

*   **Known Issues/Bugs (Resolved):**
    *   **Startup Errors (Resolved):** `ModuleNotFoundError: No module named 'flask_login'` and `ModuleNotFoundError: No module named 'flask_wtf'`. Resolved by ensuring `pip install` commands were executed correctly within the project's virtual environment.
    *   **Email Validation Error (Resolved):** `ModuleNotFoundError: No module named 'email_validator'` during registration. Resolved by running `pip install -r requirements.txt` within the active virtual environment (`D:\Coding\CAPA AI Final - Copy\CAPA AI Assistant\venv\`).
    *   The similarity threshold of 0.3, chosen for the previous model, needs to be re-evaluated for `paraphrase-multilingual-MiniLM-L12-v2`.
    *   **Persistent Error (Resolved):** "The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()" error occurs in `ai_learning.py` during semantic search for action plans. A more robust check for NumPy array handling has been implemented.
    *   **NameError (Resolved):** `NameError: name 'cosine_similarity_rca' is not defined` in `ai_learning.py` was resolved by moving function definitions earlier in the file.
*   **Decision Log (Recent Additions):**
    *   **Dashboard Date Filters (`routes.py`):**
        *   Implemented backend logic to parse and apply tiered date filters (Predefined, Year/Month/Week, Custom Range) in the `dashboard_data` function.
        *   Ensured all chart data aggregations use a common base query (`query_after_date_filter`) that has the date filters applied for consistency.
        *   Corrected Python indentation errors in `routes.py` that occurred during the filter logic implementation.
    *   **Decision to enhance logging in `cosine_similarity_rca` (`ai_learning.py`) to include calculated similarity scores and details for invalid input cases for better debugging.**
    *   **Decision to modify `edit_rca` route logic (`routes.py`) to save the last provided "Why" answer into the `user_adjusted_root_cause` field, allowing action plan generation even if fewer than 5 Whys are submitted.**
    *   Decision to fix the embedding function to use the correct method from Google Generative AI library (previous decision, now superseded by model change).
    *   Decision to lower the similarity threshold from 0.5 to 0.3 to increase recall in semantic search (may need review with new model).
    *   Decision to modify AI prompts to prevent phrases like "Mengadaptasi dari contoh" in responses.
    *   Decision to maintain higher weight (70%) for WHYs similarity compared to issue description similarity (30%) in calculating action plan relevance score.
    *   Decision to add extensive logging for similarity scores and matched action plans to aid debugging and understanding.
    *   Decision to modify AI prompt system to prioritize references from AI knowledge base rather than generating new recommendations from scratch.
    *   Decision to increase the number of retrieved references from 3 to 10 to provide more historical data to the AI.
    *   Decision to import company's historical data from Excel directly into the existing `ai_knowledge_base` table without creating new tables.
    *   Decision to refactor `AIKnowledgeBase` to use dedicated columns for learned data (`adjusted_..._json`) instead of a single JSON blob (previous refactor).
    *   Decision to store the associated 5 Whys (`adjusted_whys_json`) within `action_plan_adjustment` entries to enable direct filtering (previous refactor).
    *   Decision to simplify stored action plan data to only include lists of action text strings (previous refactor).
    *   Revised logic for `get_relevant_action_plan_knowledge` to directly filter action plan entries based on context and 5 Whys match (previous refactor).
    *   **Decision to consolidate `AIKnowledgeBase` to a single entry per CAPA, stored upon closure, removing the `source_type` column.**
    *   **Decision to move all AI knowledge storage logic to the CAPA closure step (`close_capa` route).**
    *   **Decision to modify `ai_service.py` to handle plain strings in historical JSON columns (`adjusted_whys_json`, `adjusted_temporary_actions_json`, `adjusted_preventive_actions_json`) instead of requiring a data fixing script.**
    *   **Decision to implement client-side animation for file uploads in `view_capa.html` using JavaScript and Bootstrap spinner.**
    *   **Decision to implement upload animation and searchable 'Machine Name' dropdown (using Choices.js and a new API endpoint) on `new_capa.html`.**
    *   **Decision to implement file upload animation for 'Foto Bukti' on 'Gemba Investigation' form (`gemba_investigation.html`).**
    *   **Decision to modify the `/api/machine_names` endpoint in `routes.py` to fetch distinct machine names from the `AiKnowledgeBase` table instead of `CapaIssue` table.**
    *   **Decision to refactor `get_relevant_action_plan_knowledge` to a three-stage semantic search process for action plans.**
    *   **Decision to eagerly load `CapaIssue.gemba_investigation` in `generate_pdf_report` (`routes.py`) for PDF timestamp accuracy and performance.**
    *   Continued use of custom Python scripts for database migrations.
    *   **Decision to use `& "path\to\python.exe" -m pip install ...` for installing Python packages to ensure correct virtual environment targeting, especially with PowerShell and paths containing spaces.**
    *   **Decision to filter the company selection dropdown on the registration page (`/register`) to exclude 'Sansico Group (all company combine)' and 'Unassigned' for new user sign-ups, implemented in `routes.py`.**
    *   **Ensured `email-validator` (and all other dependencies from `requirements.txt`) is installed in the correct project virtual environment (`D:\Coding\CAPA AI Final - Copy\CAPA AI Assistant\venv\`) to resolve `ModuleNotFoundError` during registration.**

*(This progress assessment reflects the latest enhancements to the AI recommendation system.)*

## What's Left / Next Steps

- **Testing & Verification (Immediate Priority):**
    - **Verify overall application stability and basic functionality:** Perform a quick run-through of key non-authentication features to ensure no regressions or unexpected issues have arisen.
- **Testing & Verification (Following Stability Check):**
    - **Thoroughly test the new *three-stage* semantic search for action plan recommendations (Machine Filter -> Issue Sim. -> Whys Sim.).**
    - **Test UI Enhancements:**
        - File upload animations on `new_capa.html`, `view_capa.html` (Edit Bukti), and `gemba_investigation.html`.
        - Searchable 'Machine Name' dropdown on `new_capa.html` (data population, search, 'Other' option).
    - Thoroughly test the file upload animations on `new_capa.html`, `view_capa.html`, and `gemba_investigation.html`.
    - Verify the searchable 'Machine Name' dropdown on `new_capa.html` (data population from `AiKnowledgeBase`, search functionality, 'Other' option).
    - Test end-to-end submission for forms with these new features.
    - Run the application to observe and verify the enhanced logging output from `cosine_similarity_rca`.
    - **Test the new three-stage semantic search logic for action plans.**
- **User Feedback:** Gather user feedback on these enhancements.
- **Documentation:** Update any necessary project documentation regarding these UI changes if applicable. (`HOW_TO_RUN.md` created).
- Address items from `todo.md` or other pending tasks.
- **Multi-Company Feature Implementation:**
    - Finalize data model changes:
        - Implement the `Company` model.
        - Update the `User` model with `role` and `company_id`.
        - Add `company_id` to all relevant data tables (e.g., `CapaIssue`, `AIKnowledgeBase`).
    - Plan and execute database migration strategy for existing data to associate with companies.
    - Develop backend logic for storing and retrieving the selected company in user sessions.
    - `api_machine_names` route: Provides a list of distinct `CapaIssue.machine_name` values filtered by the selected company.
    - **Bug Fix:** Corrected company filtering in `dashboard_data` route for the 'Status Distribution' chart. It previously showed data for all companies instead of the selected one. 
    - Design and implement the company selection dropdown in `base.html` for logged-in super_users and ensure it's functional (Note: company selection for *new user registration* is complete).

## Known Issues / Bugs

- Previously, the machine name dropdown in `new_capa.html` was not populating due to incorrect JavaScript logic with Choices.js `setChoices` method. This has been resolved.
- **Persistent Error (Action Plan Search - Resolved):** "The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()" error occurs in `ai_learning.py` during semantic search for action plans. A more robust conditional check for `current_issue_embedding_list` (handling it as a NumPy array or list of arrays) has been implemented. 
- **NameError (Action Plan Search - Resolved):** `NameError: name 'cosine_similarity_rca' is not defined` in `get_relevant_action_plan_knowledge` was resolved by moving the function definition of `cosine_similarity_rca` (and its helper `get_embedding_st_rca`) to appear before its call site.

## Decision Log

- **2025-05-07:** Decided to use Choices.js for the searchable dropdown for 'Machine Name' to improve UX.
- **2025-05-07:** Decided to implement file upload animations using Bootstrap spinners for better user feedback during uploads.
- **2025-05-08:** Corrected Choices.js population logic by consolidating API results and static options before a single `setChoices` call.
- **2025-05-08:** Ensured file upload animation on `gemba_investigation.html` is shown distinctly before the more general AI processing overlay if files are part of the submission.
- **2025-05-08:** Changed the data source for the `/api/machine_names` endpoint to `AiKnowledgeBase` table for populating the machine name dropdown.
- **2025-05-08:** Decided to refactor `get_relevant_action_plan_knowledge` to a three-stage semantic search process for action plans.
- **Multi-Company Feature Design Decisions:**
    - Decision to implement a `Company` model (`id`, `name`, `code`) to manage company information.
    - Decision to modify the `User` model to include `role` (e.g., 'super_user', 'user') and `company_id` (ForeignKey to `Company.id`).
    - **Data Model:** `Company` model exists. `User` model refined (duplicates removed, `role` defaults to 'user', `company_id` `nullable=True`). `CapaIssue.company_id` and `AIKnowledgeBase.company_id` set to `nullable=False`. Database migration pending.
    - Decision that 'super_user' roles can select and view data for any company or an aggregated view, while 'user' roles are restricted to their own company's data.
    - Decision to implement a company selection dropdown in the UI, visible to 'super_user' roles.

## Overall Status
### Action Plan Recommendation (`get_relevant_action_plan_knowledge` in `ai_learning.py`)
-   **Status:** Significantly refactored.
-   **Previous Logic:** Single-stage semantic search combining issue description similarity (30% weight) and 5 Whys similarity (70% weight), filtered by a threshold of 0.3.
-   **Current Logic (New - Needs Testing):** Three-stage semantic search.
    0.  **Stage 0:** Filter by exact `current_capa_machine_name` if provided.
    1.  **Stage 1:** From machine-filtered (or all if no machine name) entries, identifies Top 5 based purely on *issue description similarity*.
    2.  **Stage 2:** From these Top 5, identifies the Top 3 based purely on *5 Whys similarity*.
    *   The final score is the 5 Whys similarity from Stage 2.
    *   This was implemented based on user request for a sequential filtering approach.
-   **Error Status:** All known critical errors (ambiguous truth value, NameError) have been **resolved**.
-   **Next Steps:** Thoroughly test the new three-stage logic (machine filter -> issue sim -> whys sim) for relevance and correctness. Evaluate if the Top 5 / Top 3 counts are optimal.

### RCA Recommendation (`get_relevant_rca_knowledge` in `ai_learning.py`)
-   **Status:** No recent changes.
-   **Logic:** Single-stage semantic search combining issue description similarity (30% weight) and 5 Whys similarity (70% weight), filtered by a threshold of 0.3.
-   **Error Status:** No known errors.
-   **Next Steps:** Review and potentially refactor to align with the new three-stage approach for action plans.

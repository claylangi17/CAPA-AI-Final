# Project Progress

*This document tracks the overall status of the project, what's completed, what remains, known issues, and the evolution of key decisions.*

**Status Overview:**

*   **Current State:** The application implements the core CAPA workflow with AI integration. The semantic search functionality has been updated to use the `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` model. File upload animation has been implemented for the 'Edit Bukti' form. Upload animation and searchable dropdown for machine name have been added to the 'Submit New CAPA Issue' form. File upload animation has been added to the 'Gemba Investigation' form. Logging in `cosine_similarity_rca` has been enhanced.
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
    *   **Logging Enhancements (`ai_learning.py`):**
        *   Improved logging in `cosine_similarity_rca` to include calculated similarity scores.
        *   Added detailed logging for invalid input scenarios in `cosine_similarity_rca`.
    *   **Three-Stage Semantic Search for Action Plans:**
        *   Refactored `get_relevant_action_plan_knowledge` to a three-stage process:
            0.  **Stage 0:** Filter by exact `current_capa_machine_name` if provided.
            1.  **Stage 1:** From machine-filtered (or all if no machine name) entries, identifies Top 5 based purely on *issue description similarity*.
            2.  **Stage 2:** From these Top 5, identifies the Top 3 based purely on *5 Whys similarity*.
        *   The final reported score for a recommendation is its 5 Whys similarity score from Stage 2.
        *   Added a helper function `_extract_text_from_whys_json_str` for consistent text extraction from 5 Whys JSON data.
*   **What's Left to Build (Potential Areas):**
    *   **Testing AI Effectiveness:** Thoroughly test the AI suggestion quality with the new `paraphrase-multilingual-MiniLM-L12-v2` embedding model.
    *   **Semantic Search Fine-tuning:** Evaluate and adjust the similarity threshold (currently 0.3) with the new model to balance precision and recall.
    *   **Dependency Management:** Ensure `sentence-transformers` and its dependencies are correctly handled in deployment.
    *   **Advanced Text Matching:** The new semantic search model is a significant step; further NLP techniques could be explored later.
    *   **User Interface/Experience (UI/UX):** General review and refinement.
    *   **Error Handling:** Continued focus on robust error handling.
    *   **Security, Formal Testing (Unit/Integration), Deployment Prep:** Standard ongoing concerns.
    *   **Database Migrations:** Consider adopting a formal migration tool like Alembic for future schema changes.
    *   **Documentation:** Create `HOW_TO_RUN.md` (Completed).

*   **Known Issues/Bugs (Resolved):**
    *   The similarity threshold of 0.3, chosen for the previous model, needs to be re-evaluated for `paraphrase-multilingual-MiniLM-L12-v2`.
    *   **Persistent Error (Resolved):** "The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()" error occurs in `ai_learning.py` during semantic search for action plans. A more robust check for NumPy array handling has been implemented.
    *   **NameError (Resolved):** `NameError: name 'cosine_similarity_rca' is not defined` in `ai_learning.py` was resolved by moving function definitions earlier in the file.
*   **Decision Log (Recent Additions):**
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
    *   Continued use of custom Python scripts for database migrations.

*(This progress assessment reflects the latest enhancements to the AI recommendation system.)*

## What's Left / Next Steps

- **Testing & Verification:**
    - Thoroughly test the file upload animations on `new_capa.html`, `view_capa.html`, and `gemba_investigation.html`.
    - Verify the searchable 'Machine Name' dropdown on `new_capa.html` (data population from `AiKnowledgeBase`, search functionality, 'Other' option).
    - Test end-to-end submission for forms with these new features.
    - Run the application to observe and verify the enhanced logging output from `cosine_similarity_rca`.
    - **Test the new three-stage semantic search logic for action plans.**
- **User Feedback:** Gather user feedback on these enhancements.
- **Documentation:** Update any necessary project documentation regarding these UI changes if applicable. (`HOW_TO_RUN.md` created).
- Address items from `todo.md` or other pending tasks.

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

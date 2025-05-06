# Project Progress

*This document tracks the overall status of the project, what's completed, what remains, known issues, and the evolution of key decisions.*

**Status Overview:**

*   **Current State:** The application implements the core CAPA workflow with AI integration. A significant refactoring of the `ai_knowledge_base` system has been implemented to consolidate knowledge into a single entry per CAPA, stored upon closure, and to remove the `source_type` differentiation. This aims to improve data quality for AI learning and simplify the data model.
*   **What Works (Inferred & Recently Enhanced):**
    *   Core CAPA workflow (issue creation, Gemba, RCA, Action Plan, Evidence, Closure).
    *   AI-powered suggestions for RCA and Action Plans.
    *   Script `import_initial_data.py` for initial data import.
    *   Modified prompt system in `ai_service.py` for AI suggestions.
    *   **Consolidated AI Knowledge System:**
        *   `AIKnowledgeBase` table schema updated in `models.py` (removed `source_type`).
        *   `ai_learning.py` updated:
            *   `store_rca_learning` function removed.
            *   `store_action_plan_learning` renamed to `store_knowledge_on_capa_close`. This function now creates/updates a single `AIKnowledgeBase` entry per `capa_id` upon CAPA closure, storing final `adjusted_whys_json`, `adjusted_temporary_actions_json`, and `adjusted_preventive_actions_json`.
            *   `get_relevant_rca_knowledge` and `get_relevant_action_plan_knowledge` updated to work with the consolidated structure (no `source_type` filter).
        *   `routes.py` updated:
            *   Calls to `store_rca_learning` and old `store_action_plan_learning` removed from `edit_rca` and `edit_action_plan` routes.
            *   Call to `store_knowledge_on_capa_close` added to the `close_capa` route.
        *   New migration script `migrations/consolidate_ai_knowledgebase.py` created and successfully executed to handle existing data and drop the `source_type` column.
        *   `ai_service.py` updated in `trigger_rca_analysis` and `trigger_action_plan_recommendation` to handle plain strings in historical JSON columns (`adjusted_whys_json`, `adjusted_temporary_actions_json`, `adjusted_preventive_actions_json`) by treating them as single-item lists.
    *   PDF report generation.
    *   File uploads and serving.
    *   Basic status tracking.
*   **What's Left to Build (Potential Areas):**
    *   **Testing AI Effectiveness:** Thoroughly test the AI suggestion quality for both RCA and Action Plans, especially for cases where historical data was plain text, to confirm the `ai_service.py` modifications work as intended.
    *   **Testing:** Critical end-to-end testing of the entire CAPA workflow, focusing on knowledge storage on closure and retrieval logic.
    *   **Advanced Text Matching:** The current "matching issue description" uses substring matching (`LIKE %...%`). More advanced NLP techniques could be explored.
    *   **5 Whys Matching Refinement:** The current 5 Whys matching uses sorted list comparison. String similarity metrics could provide more flexibility.
    *   **User Interface/Experience (UI/UX):** General review and refinement.
    *   **Error Handling:** Continued focus on robust error handling.
    *   **Security, Formal Testing (Unit/Integration), Deployment Prep:** Standard ongoing concerns.
    *   **Database Migrations:** Consider adopting a formal migration tool like Alembic for future schema changes.
*   **Known Issues/Bugs (Potential):**
    *   The effectiveness and accuracy of the AI suggestions using the modified `ai_service.py` logic (handling plain strings) need validation through testing.
*   **Decision Log (Recent Additions):**
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
    *   Continued use of custom Python scripts for database migrations.

*(This progress assessment reflects the latest refactoring. Please review and update.)*

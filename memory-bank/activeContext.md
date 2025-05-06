# Active Context

*This file tracks the current state of work, recent decisions, immediate next steps, and important patterns or learnings relevant to the ongoing development.*

**Key Sections:**

*   **Current Focus:** Refactoring the `ai_knowledge_base` to store a single, consolidated entry per CAPA upon its closure, removing the `source_type` differentiation. This aims to reduce data duplication and improve AI learning from final, complete CAPA data.
*   **Recent Changes (AI Knowledge Base Consolidation):**
    *   **Database Schema (`models.py`):**
        *   Removed the `source_type` column from the `AIKnowledgeBase` model.
    *   **Data Storage Logic (`ai_learning.py`):**
        *   Removed the `store_rca_learning` function.
        *   Renamed `store_action_plan_learning` to `store_knowledge_on_capa_close`.
        *   The new `store_knowledge_on_capa_close` function now creates or updates a single `AIKnowledgeBase` entry for a given `capa_id` when the CAPA is closed. It stores the final `adjusted_whys_json`, `adjusted_temporary_actions_json`, and `adjusted_preventive_actions_json`.
    *   **Data Retrieval Logic (`ai_learning.py`):**
        *   Updated `get_relevant_rca_knowledge` and `get_relevant_action_plan_knowledge` to query the `AIKnowledgeBase` table without considering `source_type`. They now expect a single, consolidated entry per CAPA.
    *   **Routing Logic (`routes.py`):**
        *   Removed calls to `store_rca_learning` from the `edit_rca` route.
        *   Removed calls to `store_action_plan_learning` (the old name) from the `edit_action_plan` route.
        *   Added a call to the new `store_knowledge_on_capa_close` function in the `close_capa` route, ensuring knowledge is stored only when a CAPA is finalized.
    *   **Database Migration (`migrations/consolidate_ai_knowledgebase.py`):**
        *   Created a new migration script to:
            *   Consolidate existing data: For `capa_id`s with both `rca_adjustment` and `action_plan_adjustment` entries, it attempts to merge `adjusted_whys_json` into the action plan entry and then deletes the redundant RCA entry.
            *   Drop the `source_type` column from the `ai_knowledge_base` table.
        *   Successfully ran the migration script.
    *   **AI Service Logic (`ai_service.py`):**
        *   Updated `trigger_rca_analysis` to handle cases where `adjusted_whys_json` from the knowledge base contains a plain string instead of a valid JSON array. It now attempts to treat such strings as a single-item list `["plain string"]` to include them in the AI prompt.
        *   Updated `trigger_action_plan_recommendation` similarly to handle plain strings in `adjusted_temporary_actions_json` and `adjusted_preventive_actions_json`, treating them as single-item action lists.
*   **Next Steps:**
    1.  **Crucial:** Thoroughly test the AI suggestion quality for both RCA and Action Plans, specifically for cases where historical data was previously plain text. Verify if the AI now generates more relevant suggestions based on this historical data.
    2.  Continue testing the entire CAPA workflow, including knowledge saving on closure and retrieval.
    3.  Monitor application logs for any errors or warnings related to data parsing in `ai_service.py`.
    4.  Update `systemPatterns.md` and `progress.md` in the Memory Bank to reflect the latest `ai_service.py` changes.
    5.  Await user confirmation and next task.
*   **Active Decisions/Considerations:**
    *   Adopted a single-entry-per-CAPA model for `AIKnowledgeBase`, stored upon CAPA closure.
    *   Removed `source_type`.
    *   Learning occurs only at CAPA closure.
    *   **Modified `ai_service.py` (both RCA and Action Plan functions) to be tolerant of plain strings in historical JSON columns (`adjusted_whys_json`, `adjusted_temporary_actions_json`, `adjusted_preventive_actions_json`), treating them as single-item lists for the AI prompt.** (Chosen over fixing data via script for now).
*   **Important Patterns/Preferences:**
    *   Database schema evolution continues to be managed via custom Python migration scripts.
    *   Centralizing knowledge storage to a single point (CAPA closure) simplifies logic flow.
*   **Learnings/Insights:**
    *   Consolidating data storage can simplify retrieval and learning logic.
    *   Timing of data capture for learning is critical.
    *   There's a trade-off between enforcing strict data formats (requiring data cleaning) and making application logic more robust to handle variations (potentially hiding underlying data quality issues). The decision was made to prioritize robustness in `ai_service.py` for this specific case.

*(This file should be updated frequently to reflect the current development pulse.)*

# Active Context

*This file tracks the current state of work, recent decisions, immediate next steps, and important patterns or learnings relevant to the ongoing development.*

**Key Sections:**

*   **Current Focus:** Completed major refactoring of the AI knowledge base system based on user feedback for improved relevance, token optimization, and data structure clarity.
*   **Recent Changes (AI Knowledge Base Refactoring - Flattened Structure):**
    *   **Database Schema (`models.py`):**
        *   Modified `AIKnowledgeBase` model again:
            *   Removed `learned_data_json`.
            *   Added `adjusted_whys_json` (Text, nullable=True) for RCA adjustments.
            *   Added `adjusted_temporary_actions_json` (Text, nullable=True) for Action Plan adjustments (stores list of action strings).
            *   Added `adjusted_preventive_actions_json` (Text, nullable=True) for Action Plan adjustments (stores list of action strings).
    *   **Database Migration (`migrations/refactor_ai_knowledge_learned_data.py`):**
        *   Created and successfully executed a new migration script to:
            *   Add the three new `adjusted_..._json` columns.
            *   Migrate data from the old `learned_data_json` into the appropriate new columns, simplifying action plan data to lists of strings.
            *   Drop the `learned_data_json` column.
        *   Troubleshot and resolved `NameError` related to `dotenv_values` import in the migration script.
    *   **Data Storage Logic (`ai_learning.py`):**
        *   Updated `store_rca_learning` to save the user-adjusted 5 Whys list into `adjusted_whys_json`.
        *   Updated `store_action_plan_learning` to extract simplified lists of action text strings and save them into `adjusted_temporary_actions_json` and `adjusted_preventive_actions_json`. **Crucially, it now also saves the associated `adjusted_whys_json` (from the CAPA's RootCause) into the action plan knowledge entry.**
    *   **Data Retrieval Logic (`ai_learning.py`):**
        *   Modified `get_relevant_rca_knowledge` to retrieve `adjusted_whys_json`.
        *   **Corrected `get_relevant_action_plan_knowledge`:** It now directly filters `action_plan_adjustment` entries based on machine name, issue description, and matching `adjusted_whys_json` against the current CAPA's 5 Whys. It returns the `adjusted_temporary_actions_json` and `adjusted_preventive_actions_json` from matching entries. (The previous two-step logic was incorrect).
        *   Fixed bugs related to JSON parsing, variable names, and `try...except` block structure in retrieval functions.
    *   **AI Service Prompts (`ai_service.py`):**
        *   Updated `trigger_rca_analysis` prompt generation to use `adjusted_whys_json` from retrieved knowledge.
        *   Updated `trigger_action_plan_recommendation` prompt generation to use `adjusted_temporary_actions_json` and `adjusted_preventive_actions_json` from retrieved knowledge (which is now correctly filtered based on 5 Whys).
*   **Next Steps:**
    1.  **Crucial:** Thorough user testing of the entire AI suggestion workflow (RCA and Action Plan) to verify the refactoring works correctly.
    2.  Update `systemPatterns.md` and `progress.md` in the Memory Bank to reflect this final logic.
    3.  Await user confirmation and next task.
*   **Active Decisions/Considerations:**
    *   Adopted a flattened structure for `AIKnowledgeBase`.
    *   Action plan knowledge entries now store the associated 5 Whys (`adjusted_whys_json`) to enable direct filtering for relevant past action plans.
    *   Action plan learning data stores simplified lists of action text strings.
*   **Important Patterns/Preferences:**
    *   Database schema evolution managed via custom migration scripts. Need for careful testing after migrations.
*   **Learnings/Insights:**
    *   Refactoring data models can significantly impact multiple parts of the system (storage, retrieval, service layer).
    *   Clear separation of concerns (e.g., dedicated columns vs. complex JSON blobs) can improve code clarity and potentially performance/token usage, but requires careful migration.

*(This file should be updated frequently to reflect the current development pulse.)*

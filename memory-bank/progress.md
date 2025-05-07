# Project Progress

*This document tracks the overall status of the project, what's completed, what remains, known issues, and the evolution of key decisions.*

**Status Overview:**

*   **Current State:** The application implements the core CAPA workflow with AI integration. Baru-baru ini, kita telah memperbaiki fungsi embedding untuk semantic search dan meningkatkan kualitas prompt AI agar tidak menyertakan frasa "Mengadaptasi dari contoh" dalam responsnya.
*   **What Works (Inferred & Recently Enhanced):**
    *   Core CAPA workflow (issue creation, Gemba, RCA, Action Plan, Evidence, Closure).
    *   AI-powered suggestions for RCA and Action Plans.
    *   Script `import_initial_data.py` for initial data import.
    *   Modified prompt system in `ai_service.py` for AI suggestions.
    *   **Semantic Search Enhancement:**
        *   Fixed embedding function in `ai_learning.py` to use the correct method from Google Generative AI library.
        *   Updated from `embedding_model.embed_content(text)` to `genai.embed_content(model="models/embedding-001", content=text, task_type="retrieval_document")`.
        *   Lowered similarity threshold from 0.5 to 0.3 for better recall.
        *   Added extensive logging for similarity scores and matched action plans.
    *   **AI Prompt Improvement:**
        *   Modified prompts in `trigger_rca_analysis` and `trigger_action_plan_recommendation` to prevent AI from using phrases like "Mengadaptasi dari contoh 1 & 2".
        *   Added explicit instructions for AI to integrate solutions naturally without referencing example numbers.
    *   **Code Formatting:**
        *   Improved code formatting in `ai_service.py` and `ai_learning.py` for better readability.
    *   PDF report generation.
    *   File uploads and serving.
    *   Basic status tracking.
*   **What's Left to Build (Potential Areas):**
    *   **Testing AI Effectiveness:** Thoroughly test the AI suggestion quality with the fixed embedding model and improved prompts.
    *   **Semantic Search Fine-tuning:** Evaluate and adjust the similarity threshold (currently 0.3) to balance precision and recall.
    *   **Advanced Text Matching:** The current semantic search is a significant improvement, but could be further enhanced with more sophisticated NLP techniques.
    *   **User Interface/Experience (UI/UX):** General review and refinement.
    *   **Error Handling:** Continued focus on robust error handling.
    *   **Security, Formal Testing (Unit/Integration), Deployment Prep:** Standard ongoing concerns.
    *   **Database Migrations:** Consider adopting a formal migration tool like Alembic for future schema changes.
*   **Known Issues/Bugs (Potential):**
    *   The similarity threshold of 0.3 might be too low in some cases, potentially returning less relevant results. This needs monitoring and possible adjustment.
*   **Decision Log (Recent Additions):**
    *   Decision to fix the embedding function to use the correct method from Google Generative AI library.
    *   Decision to lower the similarity threshold from 0.5 to 0.3 to increase recall in semantic search.
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
    *   Continued use of custom Python scripts for database migrations.

*(This progress assessment reflects the latest enhancements to the AI recommendation system.)*

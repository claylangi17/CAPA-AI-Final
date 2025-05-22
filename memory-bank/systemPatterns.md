# System Patterns

*This document outlines the architectural design, key technical decisions, and established patterns used throughout the system.*

**Key Elements:**

*   **Architecture Overview:**
    *   Standard **Flask Web Application** structure.
    *   Follows a **Model-View-Controller (MVC)**-like pattern, although not strictly enforced:
        *   **Models:** Defined in `models.py` using Flask-SQLAlchemy. Key models include:
            *   `CapaIssue`: Core entity for tracking corrective and preventive actions.
            *   `User`: Manages user accounts and authentication.
            *   `AIKnowledgeBase`: Stores learned data from closed CAPAs for AI recommendations.
            *   `Company`: Manages company information for multi-company support.
            *   Supporting models: `RootCause`, `ActionPlan`, `Evidence`, `GembaInvestigation`.
            *   **Multi-Company Enhancements:**
                *   The `Company` model (`id`, `name`, `code`) stores company details.
                *   The `User` model is extended with `role` (e.g., 'super_admin', 'user', `nullable=False`, default 'user') and a `company_id` (ForeignKey to `Company.id`, `nullable=True`) to associate users with companies and define their access levels.
                *   `CapaIssue`, `AIKnowledgeBase`, and other relevant data models are extended with `company_id` (ForeignKey to `Company.id`, `nullable=False`) to ensure all records are associated with a company and to segregate data by company.
        *   **Views:** Handled by Jinja2 templates in the `templates/` directory (renders HTML).
        *   **Controllers:** Logic resides within route functions defined in `routes.py`.
    *   Configuration is centralized in `config.py` and utilizes environment variables (`.env`) via `python-dotenv`.
    *   Application initialization and setup occur in `app.py`.
    *   Utility functions are separated into `utils.py`.
    *   AI-related logic is encapsulated in `ai_service.py` and `ai_learning.py`.

*   **Key Technical Decisions:**
    *   Framework Choice: **Flask** (lightweight Python web framework).
    *   Database ORM: **Flask-SQLAlchemy** (provides abstraction over SQL).
    *   Database: **MySQL** (chosen relational database).
    *   AI Integration: **Google Generative AI** (for RCA and Action Plan suggestions).
    *   Semantic Search: **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** (via `sentence-transformers` library for finding relevant historical data).
    *   PDF Generation: **WeasyPrint** (for creating PDF reports from HTML).
    *   Configuration Management: **`.env` file** with `python-dotenv`.
    *   File Uploads: Handled directly within routes, saving to the `uploads/` folder.
    *   **Multi-Company Architecture:** Decision to implement multi-company support by:
        *   Introducing a `Company` model (`id`, `name`, `code`).
        *   Adding `role` (`nullable=False`, default 'user') and `company_id` (`nullable=True`) to the `User` model for role-based access control (RBAC) and company association.
        *   Adding `company_id` (now `nullable=False`) to data-bearing models like `CapaIssue` and `AIKnowledgeBase` to enforce company association and enable data partitioning/filtering per company.

*   **Design Patterns:**
    *   **Repository Pattern (Implicit):** SQLAlchemy models act somewhat like repositories for database interaction.
    *   **Dependency Injection (via Flask):** Flask handles injecting the `app` context where needed. Routes are registered onto the `app` object.
    *   **Helper/Utility Module:** `utils.py` for common functions (e.g., `allowed_file`, Jinja filters).
    *   **Service Layer (Implicit):** `ai_service.py` acts as a service layer for interacting with the external AI API. `ai_learning.py` handles semantic search and knowledge retrieval.
    *   **Semantic Search Pattern:** Using embeddings to find semantically similar content rather than exact keyword matches.

*   **Component Relationships:**
    *   `app.py`: Initializes Flask app, DB, registers routes, and runs the server.
    *   `config.py`: Provides settings (DB URI, API keys, upload paths).
    *   `models.py`: Defines DB schema and relationships. Used by routes for data operations.
    *   `routes.py`: Defines URL endpoints, handles requests, interacts with models, calls AI services, and renders templates.
    *   `templates/`: Contains Jinja2 HTML templates rendered by routes.
    *   `static/`: Holds CSS, JS, and images served directly.
    *   `ai_service.py`: Called by routes to get AI suggestions. Interacts with `google-generativeai` for text generation. Retrieves relevant past knowledge via `ai_learning.py` to inform prompts. Contains explicit instructions in prompts to prevent AI from using phrases like "Mengadaptasi dari contoh".
    *   `ai_learning.py`:
        *   Initializes `SentenceTransformer` with `paraphrase-multilingual-MiniLM-L12-v2` model at module level.
        *   `get_embedding_st` / `get_embedding_st_rca`: Converts text to vector embeddings using the initialized `sentence-transformers` model for semantic search.
        *   `get_relevant_rca_knowledge`: Uses semantic search to find relevant RCA knowledge based on issue description and machine name.
        *   `get_relevant_action_plan_knowledge`: Uses semantic search with weighted similarity (70% WHYs, 30% issue) to find relevant action plans.
        *   `store_knowledge_on_capa_close`: Called when a CAPA is closed. Creates or updates a single `AIKnowledgeBase` entry for the `capa_id`.
    *   `utils.py`: Provides helper functions used across the application, especially in routes.
    *   `migrations/`: Contains custom Python scripts for database schema changes.
    *   `update_embedding.py`: Script created to update the embedding function to use the correct method from Google Generative AI library.

*   **Data Model - AIKnowledgeBase:**
    *   Stores a single, consolidated entry per `capa_id`.
    *   Associated with a specific company via `company_id` (ForeignKey to `Company.id`).
    *   This entry is created or updated when the CAPA is closed.
    *   Contains the final user-adjusted data: `adjusted_whys_json`, `adjusted_temporary_actions_json`, and `adjusted_preventive_actions_json`.
    *   The `source_type` column has been removed.
    *   Contextual fields (`machine_name`, `issue_description`) are retained for filtering.
    *   Raw AI suggestions are not stored.

*   **Semantic Search Implementation:**
    *   Uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` model (via `sentence-transformers` library) to convert text to vector embeddings.
    *   The `SentenceTransformer` model is initialized once at the module level in `ai_learning.py`.
    *   Calculates cosine similarity between current issue/WHYs and historical data.
    *   Applies higher weight (70%) to WHYs similarity for action plan relevance.
    *   Uses a similarity threshold (0.3) to filter results.
    *   Includes fallback to keyword-based search if semantic search fails.
    *   Provides extensive logging of similarity scores for debugging.

*   **AI Prompt Enhancements:**
    *   Explicit instructions to prevent phrases like "Mengadaptasi dari contoh" in AI responses.
    *   Instructions to integrate solutions naturally without referencing example numbers.
    *   Consistent format for all 5 WHYs, using placeholders for missing ones.
    *   Clear JSON output format specification for action plans.

*   **Critical Implementation Paths:**
    *   **CAPA Creation:** `new_capa` route -> Saves `CapaIssue` -> Redirects to `gemba_investigation`.
    *   **Gemba Investigation:** `gemba_investigation` route -> Saves `GembaInvestigation` -> Updates `CapaIssue` status -> Triggers `trigger_rca_analysis` (`ai_service.py`).
    *   **Root Cause Analysis (RCA):** `view_capa` displays AI suggestions (from `RootCause` model) -> `edit_rca` route saves user adjustments (saves all provided Whys to `user_adjusted_whys_json` and the *last* provided Why to `user_adjusted_root_cause`) -> Updates `CapaIssue` status -> Triggers `trigger_action_plan_recommendation` (`ai_service.py`).
    *   **Action Planning:** `view_capa` displays AI suggestions (from `ActionPlan` model) -> `edit_action_plan` route saves user adjustments -> Updates `CapaIssue` status.
    *   **Evidence Submission:** `submit_evidence` route saves `Evidence` -> Updates `ActionPlan` item status -> `edit_evidence` allows modification.
    *   **CAPA Closure:** `close_capa` route updates `CapaIssue` status -> Calls `store_knowledge_on_capa_close` (`ai_learning.py`) to save the final consolidated knowledge.
    *   **Report Generation:** `generate_pdf_report` route renders `report_template.html` -> Uses WeasyPrint to create PDF.
    *   **User Registration:** `register` route (`routes.py`) -> `RegistrationForm` populates company choices, filtering out 'Sansico Group (all company combine)' and 'Unassigned' -> Validates unique username/email and other fields -> Creates new `User` with selected `company_id` and default 'user' role -> Redirects to login.

*(This document provides a technical blueprint of the system.)*

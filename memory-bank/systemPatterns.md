# System Patterns

*This document outlines the architectural design, key technical decisions, and established patterns used throughout the system.*

**Key Elements:**

*   **Architecture Overview:**
    *   Standard **Flask Web Application** structure.
    *   Follows a **Model-View-Controller (MVC)**-like pattern, although not strictly enforced:
        *   **Models:** Defined in `models.py` using Flask-SQLAlchemy (handles data and database interaction).
        *   **Views:** Handled by Jinja2 templates in the `templates/` directory (renders HTML).
        *   **Controllers:** Logic resides within route functions defined in `routes.py`.
    *   Configuration is centralized in `config.py` and utilizes environment variables (`.env`) via `python-dotenv`.
    *   Application initialization and setup occur in `app.py`.
    *   Utility functions are separated into `utils.py`.
    *   AI-related logic is likely encapsulated in `ai_service.py` and `ai_learning.py`.

*   **Key Technical Decisions:**
    *   Framework Choice: **Flask** (lightweight Python web framework).
    *   Database ORM: **Flask-SQLAlchemy** (provides abstraction over SQL).
    *   Database: **MySQL** (chosen relational database).
    *   AI Integration: **Google Generative AI** (for RCA and Action Plan suggestions).
    *   PDF Generation: **WeasyPrint** (for creating PDF reports from HTML).
    *   Configuration Management: **`.env` file** with `python-dotenv`.
    *   File Uploads: Handled directly within routes, saving to the `uploads/` folder.

*   **Design Patterns:**
    *   **Repository Pattern (Implicit):** SQLAlchemy models act somewhat like repositories for database interaction.
    *   **Dependency Injection (via Flask):** Flask handles injecting the `app` context where needed. Routes are registered onto the `app` object.
    *   **Helper/Utility Module:** `utils.py` for common functions (e.g., `allowed_file`, Jinja filters).
    *   **Service Layer (Implicit):** `ai_service.py` likely acts as a service layer for interacting with the external AI API. `ai_learning.py` handles feedback loops.

*   **Component Relationships:**
    *   `app.py`: Initializes Flask app, DB, registers routes, and runs the server.
    *   `config.py`: Provides settings (DB URI, API keys, upload paths).
    *   `models.py`: Defines DB schema and relationships. Used by routes for data operations.
    *   `routes.py`: Defines URL endpoints, handles requests, interacts with models, calls AI services, and renders templates.
    *   `templates/`: Contains Jinja2 HTML templates rendered by routes.
    *   `static/`: Holds CSS, JS, and images served directly.
    *   `ai_service.py`: Called by routes to get AI suggestions. Interacts with `google-generativeai`. Retrieves relevant past knowledge via `ai_learning.py` to inform prompts. Includes logic to handle potentially non-JSON plain strings in historical data columns (`adjusted_whys_json`, `adjusted_temporary_actions_json`, `adjusted_preventive_actions_json`), treating them as single-item lists when building the prompt.
    *   `ai_learning.py`:
        *   `store_knowledge_on_capa_close`: Called when a CAPA is closed. Creates or updates a single `AIKnowledgeBase` entry for the `capa_id`, storing the final `adjusted_whys_json` (from `RootCause`), `adjusted_temporary_actions_json`, and `adjusted_preventive_actions_json` (from `ActionPlan`).
        *   `get_relevant_rca_knowledge`: Retrieves `adjusted_whys_json` from `AIKnowledgeBase` based on machine name and issue description match. Does not filter by `source_type` anymore.
        *   `get_relevant_action_plan_knowledge`: Retrieves `adjusted_temporary_actions_json` and `adjusted_preventive_actions_json` from `AIKnowledgeBase`. Filters by machine name, issue description, and matching `adjusted_whys_json` against the current CAPA's 5 Whys. Does not filter by `source_type` anymore.
    *   `utils.py`: Provides helper functions used across the application, especially in routes.
    *   `migrations/`: Contains custom Python scripts for database schema changes (e.g., `cleanup_ai_knowledgebase_columns.py`, `refactor_ai_knowledge_learned_data.py`, `consolidate_ai_knowledgebase.py`).

*   **Data Model - AIKnowledgeBase:**
    *   Stores a single, consolidated entry per `capa_id`.
    *   This entry is created or updated when the CAPA is closed.
    *   Contains the final user-adjusted data: `adjusted_whys_json`, `adjusted_temporary_actions_json`, and `adjusted_preventive_actions_json`.
    *   The `source_type` column has been removed.
    *   Contextual fields (`machine_name`, `issue_description`) are retained for filtering.
    *   Raw AI suggestions are not stored.

*   **Critical Implementation Paths:**
    *   **CAPA Creation:** `new_capa` route -> Saves `CapaIssue` -> Redirects to `gemba_investigation`.
    *   **Gemba Investigation:** `gemba_investigation` route -> Saves `GembaInvestigation` -> Updates `CapaIssue` status -> Triggers `trigger_rca_analysis` (`ai_service.py`).
    *   **Root Cause Analysis (RCA):** `view_capa` displays AI suggestions (from `RootCause` model) -> `edit_rca` route saves user adjustments -> Updates `CapaIssue` status -> Triggers `trigger_action_plan_recommendation` (`ai_service.py`). (No direct learning storage here anymore).
    *   **Action Planning:** `view_capa` displays AI suggestions (from `ActionPlan` model) -> `edit_action_plan` route saves user adjustments -> Updates `CapaIssue` status. (No direct learning storage here anymore).
    *   **Evidence Submission:** `submit_evidence` route saves `Evidence` -> Updates `ActionPlan` item status -> `edit_evidence` allows modification.
    *   **CAPA Closure:** `close_capa` route updates `CapaIssue` status -> Calls `store_knowledge_on_capa_close` (`ai_learning.py`) to save the final consolidated knowledge.
    *   **Report Generation:** `generate_pdf_report` route renders `report_template.html` -> Uses WeasyPrint to create PDF.

*(This document provides a technical blueprint of the system.)*

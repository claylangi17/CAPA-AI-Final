# Technical Context

*This document details the specific technologies, tools, setup, and constraints relevant to the project's development environment.*

**Key Information:**

*   **Core Technologies:**
    *   Programming Language: Python (Version needs confirmation, likely 3.x)
    *   Web Framework: Flask
    *   Runtime Environment: Standard Python environment

*   **Database(s):**
    *   System: MySQL (using `mysql+pymysql` driver)
    *   ORM: Flask-SQLAlchemy
    *   Default DB Name: `capa_ai_system` (Configurable via environment variables)
    *   **Data Model Enhancements (Multi-Company):**
        *   New `Company` model (`id`, `name`, `code`).
        *   `User` model modified to include `role` (e.g., 'super_user', 'user') and `company_id` (ForeignKey to `Company.id`).
        *   `company_id` field to be added to relevant data tables (e.g., `CapaIssue`, `AIKnowledgeBase`) to associate records with specific companies.

*   **Key Libraries/Dependencies:** (from `requirements.txt`)
    *   `Flask`: Web framework core
    *   `Flask-SQLAlchemy`: Database ORM integration
    *   `google-generativeai`: Integration with Google's Generative AI (likely Gemini) for text generation suggestions.
    *   `sentence-transformers`: For using `paraphrase-multilingual-MiniLM-L12-v2` embedding model.
    *   `WeasyPrint`: PDF generation from HTML/CSS (for reports).
    *   `python-dotenv`: Loading environment variables from a `.env` file.
    *   `PyMySQL`: MySQL database driver (implied by connection string).
    *   `email-validator`: For validating email address formats in WTForms.

*   **Development Setup:**
    1.  Ensure Python 3.x and `pip` are installed.
    2.  Set up a MySQL database server.
    3.  Create a `.env` file in the project root with the following variables:
        *   `DB_USERNAME`: Your MySQL username
        *   `DB_PASSWORD`: Your MySQL password
        *   `DB_HOST`: Database host (e.g., `localhost`)
        *   `DB_NAME`: Database name (e.g., `capa_ai_system`)
        *   `GOOGLE_API_KEY`: Your API key for Google Generative AI (used for text generation, not for the new sentence-transformer embeddings).
    4.  Create a Python virtual environment (recommended): `python -m venv .venv` and activate it.
    5.  Install dependencies: `pip install -r requirements.txt`
    6.  Run the application: `python app.py`. The database tables should be created automatically on the first run.
    *   **User Registration (Multi-Company):** New user registration (`/register`) assigns users to a specific company (selected from a filtered list excluding 'Sansico Group' and 'Unassigned') and assigns a default 'user' role. Email validation is active.

*   **Tooling:**
    *   Virtual Environments (`.venv` folder suggests usage)
    *   Likely standard Python development tools (linters/formatters not specified but recommended).

*   **Technical Constraints:**
    *   Requires a running MySQL instance.
    *   Requires a valid Google Generative AI API key for AI text generation features. (The new embedding model does not require this key).
    *   File uploads are limited by `MAX_CONTENT_LENGTH` (16MB default) and `ALLOWED_EXTENSIONS` (`png`, `jpg`, `jpeg`, `gif`).

*   **API Integrations:**
    *   Google Generative AI API (via `google-generativeai` library for text generation).
    *   Hugging Face models (via `sentence-transformers` library for embeddings).

*(This provides essential information for developers working on the project.)*

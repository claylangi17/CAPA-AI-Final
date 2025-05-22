# Project Brief

*This is the foundational document for the project. Please provide the core requirements, goals, and overall scope.*

**Inferred Project Brief (Based on Code Analysis):**

*   **Primary Objective:** To create a web application for managing the Corrective and Preventive Action (CAPA) process, enhanced with AI capabilities to assist users in root cause analysis and action planning.
*   **High-Level Requirements:**
    *   Allow users to log new CAPA issues, including details like customer, item, date, description, machine, batch number, and an initial photo.
    *   Guide users through a structured CAPA workflow:
        *   User authentication and authorization (protecting routes).
    *   **Multi-company data management:** Implement a system allowing data to be associated with specific companies.
    *   **Company Selection & Data Segregation:**
        *   Provide a global company selection mechanism (e.g., a dropdown in the header).
        *   Implement role-based access control (RBAC) for company data:
            *   **Super Role:** Can select and view data for any individual company, or an aggregated view of all companies ("Sansico Group").
            *   **User Role:** Restricted to viewing and interacting with data only for their own registered company.
        *   Ensure all relevant data displayed throughout the application (dashboards, CAPA lists, reports, AI knowledge, etc.) is filtered based on the currently selected company and the user's role and permissions.
        1.  Gemba Investigation (on-site findings and photos).
        2.  Root Cause Analysis (RCA), potentially using the 5 Whys method, with AI suggestions.
        3.  Action Planning (Temporary and Preventive actions), with AI suggestions, including assigning PIC and due dates.
        4.  Evidence Submission (photos and descriptions linked to specific actions).
        5.  CAPA Closure.
    *   Provide AI-powered suggestions for Root Cause Analysis (RCA) and Action Plans, potentially leveraging company-specific historical data where appropriate.
    *   Store user adjustments to AI suggestions for potential future learning/improvement (`AIKnowledgeBase`).
    *   Allow viewing the status and details of CAPA issues.
    *   Generate PDF reports summarizing a completed CAPA.
    *   Manage file uploads for photos (initial issue, Gemba, evidence).
*   **Target Audience/User:** Likely quality assurance personnel, engineers, production staff, or managers involved in identifying, investigating, and resolving quality issues or incidents within an organization (possibly manufacturing, given terms like 'Gemba', 'machine', 'batch').
*   **Key Deliverables:** A functional Flask web application implementing the described CAPA workflow with AI assistance and PDF reporting.
*   **Major Constraints (Inferred):**
    *   Requires a MySQL database.
    *   Requires a Google Generative AI API key.
    *   Relies on specific Python libraries (Flask, SQLAlchemy, WeasyPrint, etc.).

*(This brief is inferred from the code. Please review and update with accurate project details.)*

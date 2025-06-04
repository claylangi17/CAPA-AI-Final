---
description: Get the AI to understand the existing codebase and document it.
---

Act as a senior software architect, a lead developer, and a product manager simultaneously. Your primary goal is to create a comprehensive "Mental Model" document for the [Your Project Name] application by thoroughly exploring its entire repository.

This document, to be named '[project_name]_architecture_analysis.md' and saved in the root of the repository, will serve as a persistent knowledge base for future development tasks and AI interactions.

Please structure your analysis to include, but not be limited to, the following sections:

1.  **Overall Application Overview:**
    * Purpose of the application.
    * Target users/personas (if discernible).
    * Core existing features and functionalities.
2.  **Software Architecture Analysis (Architect's View):**
    * High-level architecture (e.g., monolith, microservices, client-server).
    * Key technology stack (languages, frameworks, databases, major libraries).
    * Directory structure overview and conventions.
    * Main components/modules and their responsibilities.
    * Data flow diagrams (using Mermaid.js syntax) for critical processes (e.g., authentication, main data processing).
    * API endpoints and their general purpose (if applicable).
3.  **Software Developer Analysis (Developer's View):**
    * Common coding patterns and conventions observed.
    * Setup and build process (if identifiable from package.json, Dockerfile, etc.).
    * Database schema overview (key tables/collections and relationships, represent with Mermaid.js ERD if possible).
    * Error handling strategies in place.
    * Testing setup and frameworks used (if any).
4.  **Product Management Analysis (Product Manager's View):**
    * Key user journeys currently supported.
    * Potential areas for future development or improvement based on the current structure.
    * Any apparent business logic or rules embedded in the code.

**Instructions for Mermaid Diagrams:**
* Ensure diagrams are clearly labeled and accurately represent the relevant aspects.
* Use appropriate Mermaid diagram types (e.g., `graph LR` for flowcharts, `erDiagram` for ERDs, `sequenceDiagram` for interactions).

Compile your findings into a well-organized, extensive markdown document. The more detailed and accurate this document is, the better our subsequent interactions will be. Do not make assumptions if information is unclear; note it as an area requiring clarification.
---
description: Evolve the static MVP by integrating it with the backend and database.
---

We've successfully created a front-end MVP for the '[feature_name]' using static data, as documented in '[feature_name]_PRD.md' under the 'Implementation Status'.

The next critical step is to connect this front-end to our actual database and implement the necessary backend logic. Please act as a full-stack developer.

Referring to both the '[project_name]_architecture_analysis.md' (for our existing tech stack, database type like [e.g., PostgreSQL with Prisma ORM], API patterns, etc.) and the '[feature_name]_PRD.md' (for full feature requirements), your tasks are to:

1.  **Identify Data Points:** Review the current front-end components for '[feature_name]' and identify all areas where static/mock data is currently used.
2.  **Database Schema Design/Update (if necessary):**
    * Based on the data requirements for '[feature_name]' from the PRD, define any new database tables/collections or modifications to existing ones.
    * If using an ORM like Prisma, this will involve updating the `schema.prisma` file and generating new migrations. Please detail these changes.
3.  **Backend API Endpoint Development:**
    * Create the necessary backend API endpoints to support all CRUD (Create, Read, Update, Delete) operations or other relevant actions for the '[feature_name]' as defined in the PRD.
    * Ensure these endpoints follow RESTful principles (or your project's established API style, e.g., GraphQL).
    * Implement appropriate validation and error handling for these endpoints.
    * Use the established backend framework (e.g., [Express.js, NestJS, Django, Spring Boot]) as per our architecture document.
4.  **Frontend Integration:**
    * Modify the existing front-end components of '[feature_name]' to:
        * Fetch data from the newly created backend API endpoints instead of using static data.
        * Send data to these endpoints for creation, updates, or deletions.
        * Implement proper state management for handling asynchronous data (loading states, error states, success states).
        * Include user feedback mechanisms for these operations (e.g., loading spinners, success/error messages).
5.  **Data Seeding/Dummy Data (Optional but Recommended for Development):**
    * If appropriate, create a small script or method to populate the new database tables/collections with some realistic dummy data to facilitate testing.
6.  **Adherence to Standards:**
    * All new code (backend and frontend) must align with the coding patterns, security best practices, and architectural principles outlined in '[project_name]_architecture_analysis.md'.
7.  **Outline Your Plan (Before Coding):** Before writing the code, please provide a brief outline of:
    * The proposed database schema changes/additions.
    * The API endpoints you will create (method, path, purpose).
    * The main front-end files/components you will modify and how.
    Wait for my approval before proceeding with the actual implementation.

## Brief overview
These rules define the **Memory Bank** workflow, a mandatory process for AI to manage project context due to memory resets between sessions. It involves maintaining a specific set of Markdown files in the `memory-bank/` directory. Adherence to this workflow is critical for AI's effectiveness.

## Memory Bank Structure
- **Core Files (Required):** MUST create and maintain the following files within the `memory-bank/` directory:
    - `projectbrief.md`: Project goals, requirements, scope.
    - `productContext.md`: The "why" - problems solved, user goals, UX.
    - `activeContext.md`: Current focus, recent changes, next steps, active decisions, recent patterns/learnings. *Updated frequently.*
    *   `systemPatterns.md`: Architecture, key technical decisions, design patterns, component interactions.
    *   `techContext.md`: Technologies, dependencies, setup, constraints, APIs.
    *   `progress.md`: Overall status, what works, what's left, known issues, decision log.
- **Hierarchy:** Files build upon each other, starting with `projectbrief.md`. `activeContext.md` and `progress.md` are most dynamic.
- **Additional Context:** AI may create additional files/folders within `memory-bank/` for complex features, APIs, etc., if needed for organization.

## Core Workflows
- **Session Start / Task Initiation:**
    - MUST check for the `memory-bank/` directory.
    - If it exists, MUST read ALL core files to load context before proceeding.
    - If it doesn't exist, MUST create the directory and all core files with placeholder content, then request the user to populate them or attempt to infer context from the project if requested.
- **During Development (Act Mode):**
    - Before executing tasks, consult the relevant Memory Bank files.
    - After significant changes (e.g., implementing features, refactoring, key decisions), update the relevant Memory Bank files, especially `activeContext.md` and `progress.md`.
- **Plan Mode:**
    - MUST read the Memory Bank first.
    - If files are incomplete, the plan should include steps to gather information and populate them.
    - If files are complete, verifies context and develops a strategy based on the Memory Bank.
- **Explicit Update Request:**
    - If the user requests "**update memory bank**", MUST review ALL core Memory Bank files and update them comprehensively to reflect the current project state, even if some files seem unchanged. Focus on `activeContext.md` and `progress.md`.

## Documentation Updates
- **Triggers:** Updates occur when discovering new patterns, after significant changes, upon user request ("update memory bank"), or when context needs clarification.
- **Process:** Review ALL files, document the current state, clarify next steps, and document new insights or patterns.
- **MCP:** Please always use all the MCP server like brave search (access web search) and context7 (get all library documentation)

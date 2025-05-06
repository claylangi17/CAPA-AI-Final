# Product Context

*This document describes the "why" behind the project. Focus on the problems it solves, the intended user experience, and how it should function from a user's perspective.*

**Inferred Product Context (Based on Code Analysis):**

*   **Problem Statement:** Managing the Corrective and Preventive Action (CAPA) process can be complex, time-consuming, and prone to inconsistencies. Identifying true root causes and formulating effective action plans requires expertise and can be challenging. Tracking the status and evidence for multiple CAPAs manually or with disconnected tools is inefficient.
*   **User Goals:**
    *   Easily log and track quality issues or incidents requiring CAPA.
    *   Be guided through a standardized CAPA workflow (Gemba, RCA, Action Plan, Evidence, Closure).
    *   Receive assistance (AI suggestions) in identifying potential root causes (e.g., via 5 Whys) and formulating relevant temporary and preventive actions.
    *   Efficiently manage and document findings, photos, action items (with PIC/due dates), and evidence.
    *   Quickly view the status and history of any CAPA issue.
    *   Generate standardized PDF reports for completed CAPAs.
    *   Improve the quality and consistency of CAPA investigations and resolutions.
*   **Functional Overview:** The system provides a web interface for managing CAPAs. Users create new issues, upload initial details/photos, perform Gemba investigations (findings/photos), review AI-suggested root causes, adjust them, review AI-suggested action plans, adjust them (assigning PICs/due dates), upload evidence for actions, mark actions as complete, and finally close the CAPA. The system tracks the status throughout this workflow and allows generating a final PDF report. It also includes a mechanism to store user adjustments to AI suggestions, potentially for future learning.
*   **User Experience (UX) Goals:**
    *   **Guided:** The system should clearly guide users through the distinct steps of the CAPA process.
    *   **Efficient:** Reduce the manual effort involved in documentation, tracking, and reporting.
    *   **Assisted:** Provide helpful AI suggestions to augment the user's expertise during RCA and action planning.
    *   **Clear:** Present CAPA information and status in an easily understandable format.
    *   **Consistent:** Ensure a standardized approach to managing CAPAs.
*   **Assumptions:**
    *   Users have a basic understanding of the CAPA process and terms like Gemba, RCA, 5 Whys.
    *   Users have access to a web browser and potentially mobile devices for uploading photos.
    *   The organization has access to and is willing to use Google's Generative AI services.

*(This context is inferred from the code. Please review and update with accurate product details.)*

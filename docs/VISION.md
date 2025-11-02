# Project: Enterprise Code Archaeologist

**Tagline:** *Mapping the blast radius of change in complex enterprise systems.*

---

## 1. The Vision

We are building an AI-powered investigation assistant that visualizes the hidden connections within a complex, heterogeneous software ecosystem. It answers the critical developer question: "If I change this, what else breaks?" Unlike standard code assistants that generate code in isolation, the Archaeologist maps impact across multiple repositories, databases, and disconnected artifacts, explicitly identifying knowledge gaps and suggesting concrete next steps for investigation.

---

## 2. The Problem

In large organizations, software systems evolve over years, becoming a tangled web of applications (web, desktop), databases, and non-traditional code (Excel macros, stored procedures). When a change is needed, senior engineers spend countless hours on "archaeology"—manually tracing data flows and dependencies across disconnected parts of the system. This process is:
- **Time-Consuming:** Digging through documentation (or lack thereof) is a major drag on productivity.
- **Error-Prone:** Missing a single dependency can cause catastrophic production issues.
- **Knowledge-Silos:** Critical information is often locked away in the minds of a few individuals or in inaccessible systems.

Current AI code assistants fail here because they lack a holistic view and, critically, they never admit when they don't have enough information.

---

## 3. The Solution: Enterprise Code Archaeologist

A local, distributed AI system that acts as a principal engineer's co-pilot. A user provides a proposed change in natural language, and the Archaeologist:
1.  **Maps the Impact:** Visually displays all connected components on an interactive graph.
2.  **Quantifies Confidence:** Shows which connections are certain (direct code matches) versus probable (semantic links).
3.  **Identifies Knowledge Gaps:** Explicitly calls out missing information (e.g., "This API is maintained by another team; you need to request payload samples from them.").

---

## 4. Development Philosophy: Visual & Test-First

Our core development principle is **Visual & Test-First**. We will not write a single line of implementation logic until we have:
1.  **A Visual Shell:** A beautiful, non-functional UI that shows exactly what the end product will look like. This is our North Star.
2.  **A Failing Test Suite:** A comprehensive set of automated tests (user stories) that define the required functionality. All tests will fail initially.

Implementation will then be an iterative process of making the tests pass, one by one, bringing the visual shell to life.

---

## 5. The Target UI: The System Impact Explorer

The dashboard is the centerpiece of the project. It will be a single-page application with the following key components:

-   **Header:** A clean title "Enterprise Code Archaeologist" and a prominent search bar for the change request (e.g., "Change `term_sheet_id` from string to UUID").
-   **The Dependency Graph (Main View):**
    -   An interactive, force-directed graph (using `react-flow`).
    -   **Nodes:** Represent system components (Git repos, DB tables, Excel files, etc.). Each node has a unique icon and color based on its type (e.g., cylinder for DB, folder for repo).
    -   **Edges:** Represent dependencies. Thickness and color indicate confidence:
        -   **Thick, Solid Red:** High-confidence, direct dependency (found by literal search).
        -   **Medium, Dashed Yellow:** Probable, semantic dependency (found by RAG).
        -   **Thin, Dotted Gray:** Potential dependency requiring manual verification.
-   **The Investigation Panel (Sidebar):**
    -   Appears when a node is clicked.
    -   Shows the file/component name, path, and type (Live/Snapshot).
    -   Displays the relevant code snippet that triggered the dependency.
    -   Shows the last updated timestamp for snapshot sources.
-   **The Knowledge Gaps Banner:**
    -   A non-intrusive but clear banner at the top of the page that appears if the system identifies missing information.
    -   Example: "⚠️ **Knowledge Gap Identified:** The connection to `external-payment-api` is inferred. Action: Request API schema from the 'Payments Team'."
-   **The Test Status Bar:**
    -   A small footer bar for development purposes, showing the status of our test suite (e.g., "5 / 15 Tests Passing").

> UI must be **multilingual-ready** (i18n), starting with English (default) and Japanese, and **accessible** (WCAG compliant).

---

## 6. High-Level Architecture

+----------------+ +------------------------+ +---------------------+
| | | | | |
| React UI |<---->| FastAPI Orchestrator |<---->| LLM Endpoint (OpenAI-compatible API) |
| | | | | |
+----------------+ +-----------+------------+ +---------------------+
|
| (Orchestrates Calls)
|
+--------------------+--------------------+
| | |
v v v
+---------------------+ +-----------------------+ +-------------------+
| | | | | |
| Tool 1: Code | | Tool 2: RAG Engine | | Guardrail |
| Scanner (ripgrep) | | (VectorDB + BM25) | | (Pydantic) |
| | | | | |
+---------------------+ +-----------+-----------+ +-------------------+
|
v
+-----------------+
| |
| VectorDB Store |
| |
+-----------------+

---

## 7. UI Technology Stack & Architecture

The frontend is built with modern tooling for optimal development experience and performance:

- **Build Tool**: Vite - Fast development server and optimized builds
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom theme and build-time pruning
- **Visualization**: React Flow for the interactive dependency graph
- **Icons**: Lucide React for consistent iconography (the sole icon library used across all components)
- **Testing**: Vitest with React Testing Library

**Architecture Notes**:
- **Development**: UI runs on Vite dev server (localhost:3000) with API proxy to backend
- **Production**: UI is built as static assets and served by the FastAPI backend
- **No separate container**: Frontend is not deployed as independent container service
- **Static asset serving**: FastAPI serves the built UI from `/static` mount point
- **Style Consistency**: All UI components use a consistent styling approach with lucide-react for icons and Tailwind CSS for styling. No mixing of UI libraries like MUI with other styling approaches.

**Vite Configuration**:
- Development server on port 3000 with API proxy to localhost:8000
- TypeScript compilation with type checking
- Optimized production builds with chunk splitting

**Tailwind CSS Configuration**:
- Custom color palette with primary blues and neutral grays
- Content scanning for automatic class pruning
- PostCSS integration with Autoprefixer

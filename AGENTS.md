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

> Use RHEL public images as base images for containers to ensure compatibility with enterprise environments. Dockerfile and docker-compose.yml must also be compatible with podman.

> Don't use .bat files for Windows; instead, use shell scripts that can run in Git Bash or WSL environments on Windows.

> Centralize configuration in .env.dev and .env.prod files for development and production settings, respectively.

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

## 6. The Test Suite: Our Guiding User Stories

These user stories will be implemented as automated tests. They are our definition of "done".

**Backend Tests (using `pytest`):**

-   `test_api_health_check`: Can the API server receive a heartbeat?
-   `test_investigate_endpoint_exists`: Does the `/investigate` endpoint exist and accept a POST request?
-   `test_simple_literal_search`: When querying for a known string (`term_sheet_id`), the system returns the correct file (`schema.sql`) with high confidence.
-   `test_semantic_search`: When querying for a concept (`client identifier`), the system returns semantically related files (`user-service/models.py`, `reporting-service/report_generator.js`).
-   `test_knowledge_gap_reporting`: When a dependency points to a non-existent component, the system's final report includes a `knowledge_gaps` entry with a required action.
-   `test_source_type_differentiation`: The system correctly identifies and tags sources as `live_repo` or `snapshot`.
-   `test_guardrail_validation`: If the LLM hallucinates a file not found by the tools, the guardrail adds it to the report with a "verification needed" flag.

**Frontend Tests (using `Vitest` and `React Testing Library`):**

-   `test_renders_header`: The header with the search bar is rendered.
-   `test_renders_empty_graph`: On initial load, the graph area is empty.
-   `test_submit_query_calls_api`: Submitting a query triggers a `fetch` call to the `/investigate` endpoint.
-   `test_renders_graph_from_api_response`: When the API returns a mock impact report, the UI renders the correct nodes and edges.
-   `test_node_click_opens_sidebar`: Clicking on a node in the graph displays its details in the sidebar.
-   `test_knowledge_gap_banner_appears`: If the API response includes `knowledge_gaps`, the banner is rendered with the correct text.

---

## 7. High-Level Architecture

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
| Scanner (ripgrep) | | (ChromaDB + BM25) | | (Pydantic) |
| | | | | |
+---------------------+ +-----------+-----------+ +-------------------+
|
v
+-----------------+
| |
| ChromaDB Store |
| |
+-----------------+


---

## 8. UI Technology Stack & Architecture

The frontend is built with modern tooling for optimal development experience and performance:

- **Build Tool**: Vite - Fast development server and optimized builds
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom theme and build-time pruning
- **Visualization**: React Flow for the interactive dependency graph
- **Icons**: Lucide React for consistent iconography
- **Testing**: Vitest with React Testing Library

**Architecture Notes**:
- **Development**: UI runs on Vite dev server (localhost:3000) with API proxy to backend
- **Production**: UI is built as static assets and served by the FastAPI backend
- **No separate container**: Frontend is not deployed as independent container service
- **Static asset serving**: FastAPI serves the built UI from `/static` mount point

**Vite Configuration**:
- Development server on port 3000 with API proxy to localhost:8000
- TypeScript compilation with type checking
- Optimized production builds with chunk splitting

**Tailwind CSS Configuration**:
- Custom color palette with primary blues and neutral grays
- Content scanning for automatic class pruning
- PostCSS integration with Autoprefixer

---

## 9. Implementation Roadmap

**Phase 0: Setup (1 hour)**
- Create project root `enterprise-archaeologist`.
- Initialize Git repo.
- Set up `docker-compose.yml` for `api`, `ui`, and `chromadb` services.

**Phase 1: The Visual Shell & Failing Tests (3 hours)**
- **UI:** Create the basic React components for the Header, Graph area, and Sidebar. Use `react-flow` to render an empty graph. Style with Tailwind CSS classes to achieve the final design without writing custom CSS.
- **Frontend Tests:** Write the Vitest tests for the UI components. They will run against the static shell.
- **Backend:** Create the FastAPI app with a placeholder `/investigate` endpoint that returns static, dummy data and serves the built UI as static assets.
- **Backend Tests:** Write the `pytest` tests. All tests will fail because the logic is not implemented.

**Phase 2: The Deterministic Core (Tool 1 & Data Ingestion)**
- Implement the `mock_enterprise` system.
- Build the Code Scanner microservice.
- Implement the data ingestion script for ChromaDB.
- Make the first set of backend tests pass (`test_simple_literal_search`, `test_source_type_differentiation`).

**Phase 3: The Semantic Brain (Tool 2 & Orchestrator)**
- Implement the Hybrid Search in the RAG engine.
- Set up the LLM API (first local, later cloud) and the function-calling logic for the Planner/Orchestrator.
- Wire the Orchestrator to call the tools.
- Make more backend tests pass (`test_semantic_search`, `test_knowledge_gap_reporting`).

**Phase 4: The Trust Layer (Guardrail & Full Integration)**
- Implement the Guardrail component.
- Integrate it into the `/investigate` endpoint.
- Make the final backend tests pass (`test_guardrail_validation`).
- Configure FastAPI to serve the built UI as static assets.
- Connect the real API to the React UI. Make the final frontend tests pass.

**Phase 5: Polish & Showcase**
- Refine UI animations and transitions using Tailwind CSS classes.
- Add more detail to the graph nodes and sidebar.
- Write the final `README.md`.
- Prepare the demo script.

---

## 10. Initial File Structure

enterprise-archaeologist/
├── docker-compose.yml
├── README.md
├── CRUSH.md
├── mock_enterprise/
│ ├── live_repos/
│ │ ├── user-service.git/
│ │ └── reporting-service.git/
│ └── data_lake/
│ ├── finance_macros/
│ │ └── 2023-10-27/
│ │ └── term_sheet_generator.vba
│ └── db_schemas/
│ └── schema.sql
│
├── api/
│ ├── Dockerfile
pyproject.toml
│ ├── app/
│ │ ├── init.py
│ │ ├── main.py # FastAPI app and endpoints
│ │ ├── orchestrator.py # LLM agent logic
│ │ ├── tools/
│ │ │ ├── init.py
│ │ │ ├── scanner.py # Tool 1
│ │ │ └── rag_engine.py # Tool 2
│ │ ├── guardrail.py # Validation component
│ │ └── data_ingestion.py # Script to populate ChromaDB
│ └── tests/
│ └── test_archaeologist.py
│
├── ui/
│ ├── package.json
│ ├── vite.config.ts
│ ├── tailwind.config.js
│ ├── postcss.config.js
│ ├── public/
│ │ └── index.html
│ ├── src/
│ │ ├── main.tsx
│ │ ├── App.tsx
│ │ ├── components/
│ │ │ ├── Header.tsx
│ │ │ ├── DependencyGraph.tsx
│ │ │ └── InvestigationPanel.tsx
│ │ └── ...
│ └── tests/
│ └── components/
│ └── Header.test.tsx
│
└── scanner/
├── Dockerfile
├── requirements.txt
└── main.py # FastAPI microservice
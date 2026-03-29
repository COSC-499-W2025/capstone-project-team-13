# Tech Stack

This documents the actual technology stack used in the final implementation of the Digital Artifact Mining Software.

---

## Frontend

**React 19 + Vite**
React for building the interactive UI (project cards, resume builder, portfolio views, skills visualizations). Vite as the build tool for fast development and optimized production builds.

**Key libraries:**
- `react-router-dom` v7 — client-side routing
- `axios` / `fetch` — API communication via a centralized `apiClient.js` wrapper
- `lucide-react` — iconography

**Styling:** Plain CSS with CSS custom properties for theming (dark/light mode via `data-theme` on `<body>`, persisted in localStorage)

---

## Backend

**FastAPI (Python)**
RESTful API framework. All business logic is separated into service files; routers handle HTTP concerns only.

**Key libraries:**
- sqlalchemy — ORM for database access
- python-jose[cryptography] — JWT token generation and validation
- passlib[bcrypt] + bcrypt==4.0.1 — password hashing
- pydantic — request/response validation
- uvicorn — ASGI server
- python-multipart — file upload handling
- httpx — async HTTP client
- python-docx — DOCX export generation
- PyPDF2 / Pillow — PDF handling and image processing
- google-generativeai — Gemini AI integration
- GitPython==3.1.43 — Git repository analysis (contributor extraction, project dates)
- nltk + rake-nltk — keyword extraction from text artifacts
- pandas — data processing
- tqdm — progress tracking during scans

**AI integration:** Google Gemini API (via `ai_service.py`) for bullet generation, AI project descriptions, and interview answer generation. All AI features require explicit user consent.

---

## Database

**SQLite** (via `projects.db`)

Chosen for simplicity given the local/single-user nature of the application. SQLAlchemy ORM handles all queries. Schema changes are applied via direct `ALTER TABLE` commands rather than migration scripts.

---

## Authentication

JWT-based authentication with 30-day token expiry. Two dependency patterns used throughout the API:
- `require_auth` — hard-requires a logged-in user (raises 401 otherwise)
- `get_current_user_id` — returns user ID or `None` for guest-tolerant endpoints

---

## Testing

**Backend:** `pytest` with FastAPI's `TestClient` for integration-style API tests

**Frontend:** `Vitest` + `@testing-library/react` for component and unit tests

---

## CI/CD

GitHub Actions — automated test runs on pull requests, enforcing the team's PR review workflow (feature branching, PR size limits).

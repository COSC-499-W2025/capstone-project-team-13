# NovaHire

**Team 13 - COSC 499 Capstone Project**

A full-stack web application that intelligently processes digital artifacts — code, documents, and media files — to help students and new graduates build polished portfolios, generate tailored resumes, and prepare for job interviews.

---

## 👥 Team Members

- **Sana Shah** - 94945664
- **Jackson Wilson** - 11927753
- **Prina Mehta** - 87716874
- **Maya Knutsvig** - 17950502
- **Illina Islam** - 58189903
- **T'Olu Akinwande** - 69892271

---

## 🎯 Project Overview

NovaHire serves as a career tool for new graduates and students to efficiently showcase their projects, skills, and experience. Users upload their work artifacts and the system automatically analyzes them, extracts skills and metrics, and generates portfolio summaries, resume bullet points, and interview preparation content.

The system supports three project types:

1. **Code / Technology** — detects languages, frameworks, contributors, and metrics
2. **Digital Art / Media** — processes images, video, and audio files
3. **Writing / Research** — extracts keywords and themes from documents

---

## ✨ Key Features

- **Project Upload & Analysis** — upload files or ZIP archives; auto-detected as code, text, or media
- **Duplicate Detection** — prevents re-uploading via path matching and content hashing
- **Guest Mode** — analyze a file without creating an account (results not saved)
- **JWT Authentication** — secure login, signup, and user isolation
- **Portfolio Generation** — auto-generated portfolio with stats, rankings, and summary text
- **Public Portfolio Sharing** — opt-in public portfolio pages browseable by anyone
- **Resume Builder** — create and manage multiple named resumes with drag-and-drop section reordering
- **Resume Bullet Generation** — rule-based and AI-powered (Gemini) bullet generation with ATS scoring
- **PDF & DOCX Export** — download resumes with user-defined section order and labels
- **Skills Dashboard** — skill frequency, co-occurrence, diversity score, and timeline
- **Activity Heatmap** — GitHub-style heatmap of project activity by date
- **Web Showcase** — top 3 projects displayed with evolution timelines
- **Evidence Manager** — add metrics, feedback, and achievements to projects
- **Interview Prep** — AI-generated STAR-format behavioral interview answers from your projects
- **Privacy & Consent Controls** — granular file access and AI consent management
- **Dark / Light Theme** — system-wide theme toggle persisted in localStorage
- **Command Palette** — Ctrl+K search across pages and projects

---

## 🛠️ Tech Stack

### Backend
- **Language:** Python
- **Web Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** JWT via `python-jose`, password hashing via `bcrypt`
- **Testing:** pytest with FastAPI `TestClient`

### Frontend
- **Framework:** React 19
- **Build Tool:** Vite
- **Routing:** `react-router-dom` v7
- **Testing:** Vitest + `@testing-library/react`

### Key Libraries
- `rake-nltk` / `nltk` — keyword extraction and NLP
- `Pillow` — image and media analysis
- `sqlalchemy` — database ORM
- `GitPython==3.1.43` — Git repository analysis and contributor extraction
- `python-docx` — DOCX resume export
- `PyPDF2` — PDF parsing
- `google-generativeai` — Gemini AI for bullet generation, descriptions, and interview prep
- `fastapi` / `uvicorn` — API server
- `python-jose[cryptography]` — JWT tokens
- `passlib[bcrypt]` / `bcrypt==4.0.1` — password hashing
- `pandas` — data processing
- `tqdm` — progress display
- `python-multipart` — file upload handling
- `httpx` — async HTTP client

---

## 🗄️ Database Architecture

The system uses a single **SQLite database** (`projects.db`) with interconnected tables:

**Project Data**
- **Projects** — name, path, description, dates, metrics (LOC, word count, file count, size), project type, importance score, languages/frameworks/skills (JSON), resume bullets, thumbnail path, success evidence, AI description, content hash, user customizations
- **Files** — file path, name, type, size, dates, LOC, hash (for incremental uploads and duplicate detection)
- **Contributors** — name, identifier, commit count, lines added/deleted, contribution percentage
- **Keywords** — keyword text, relevance score, category
- **Resumes** — named resume records linked to users, storing full resume JSON with section order and labels

**User Data**
- **Users** — first/last name, email, hashed password, avatar, portfolio (JSON), about/contact fields, portfolio visibility flag
- **Education** — institution, degree type, field of study, GPA, start/end dates
- **Work History** — company, role, experience type, start/end dates, bullet points
- **Configuration** — per-installation privacy settings, analysis preferences, AI settings, consent records

---

## 🚀 Running the Project

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
uvicorn src.mainAPI:app --reload
```

The API will be available at `http://127.0.0.1:8000`.  
Interactive API docs: `http://127.0.0.1:8000/docs`

### Frontend Setup

```bash
# Navigate to the frontend directory
cd artifactMining

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🧪 Testing

### Backend Tests

```bash
pytest tests/ -v
```

### Frontend Tests

```bash
cd artifactMining
npm run test
```

### Manual Testing with Sample Data

- `test_data.zip` — contains a collaborative and individual coding project (earlier snapshot)
- `test_data2.zip` — contains a collaborative project (later snapshot), an individual coding project, a text project, and a visual media project

---

## 🤝 Contributing

This is a university capstone project for COSC 499.

### Development Workflow

1. Create a feature branch: `git checkout -b feature-name`
2. Make your changes and commit: `git commit -m "Description"`
3. Write tests for new features
4. Run tests: `pytest tests/ -v`
5. Push to branch: `git push origin feature-name`
6. Create a Pull Request for team review
7. Merge to main after at least 2 approvals

---

## 📄 License

This project is developed as part of COSC 499 at the University of British Columbia Okanagan.

---

## 📞 Contact

For questions or issues, please contact team members via the course management system or create an issue in this repository.

---

## Acknowledgments

- **Course:** COSC 499 - Capstone Project
- **Institution:** UBC Okanagan
- **Supervisor:** Bowen Hui
- **Libraries Used:** NLTK, Pillow, SQLAlchemy, FastAPI, React, Vite, Google Gemini, GitPython, pytest, Vitest

---

System Architecture Diagram [linked here](./docs/Proposal/SystemArchitectureDiagram.md)

Data Flow Diagram Level 1 [linked here](./docs/Proposal/DFD1.md)

WBS [linked here](https://github.com/COSC-499-W2025/capstone-project-team-13/blob/main/docs/Proposal/WBS.md)

# Digital Artifact Mining Software

**Team 13 - COSC 499 Capstone Project**

A versatile platform that intelligently processes digital artifacts including code, documents, and media files to create polished summaries and portfolio highlights for students and new graduates.

---

## 👥 Team Members

- **Sana Shah** - 94945664
- **Jackson Wilson** - 11927753
- **Prina Mehta** - 87716874
- **Maya Knutsvig** - 17950502
- **Illina Islam** - 58189903
- **T'Olu Akinwande** - 69892271

---
## Testing Guidelines for Milestone 2

- clone this repository to your local machine
- find test_data.zip and test_data2.zip within the root directory
- download both into your local machine and unzip  both files
- test_data.zip:
  - this folder contains a collaborative coding project and an individual coding project
  - the collaborative coding project is an earlier snapshot of repository
- test_data2.zip:
  - this folder contains a collaborative coding project, an individual coding project, a text project, and a visual project (and their respective zip folders)
  - the collaborative project in this folder is the same as test_data.zip, but a later snapshot of the same repository
- to mannually test out all of our system through the terminal:
  - change directory to the repository's directory
  - run: python src/main.py
- to test out our endpoints:
  - change directory to the repository's directory
  - run this comand in the terminal: uvicorn src.mainAPI:app --reload
  - paste and go to this link: http://127.0.0.1:8000/docs
- to test out our mock frontend
  - change directory to the repository's directory
  - run this comand in the terminal: uvicorn src.mainAPI:app --reload
  - open index.html with a web browser (located in ./frontend/index.html)
  - the mock UI is not fully functional and was created for testing purposes

---

## Team Contract
https://docs.google.com/document/d/16xSLlqSOmJyfw9b78a8Gc61JJh8cMKzb9KAB2M3JHEg/edit?usp=sharing

## 🎯 Project Overview

Our digital artifact mining software serves as a tool for new graduates and students to efficiently display their projects, skills, and highlights. The system supports three different user groups:

1. **Programming/Technology** - Analyzes code files, detects languages and frameworks
2. **Digital Art/Graphics** - Processes media files, identifies design software and skills
3. **Writing/Research** - Extracts keywords and insights from documents

---

## ✨ Key Features

- **User Consent Management**
- **File Format Validation**
- **ZIP File Handling**
- **Multi-Format Parsing**
- **Language & Framework Detection**
- **Keyword Extraction**
- **Visual Media Analysis**
- **Contribution Metrics**
- **JWT Authentication & User Isolation**
- **Resume Bullet Generation** with ATS scoring
- **Portfolio Generation**
- **React Frontend**

---

## 🛠️ Tech Stack

### Backend
- **Language:** Python
- **Web Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** JWT via `python-jose`, password hashing via `bcrypt`
- **Testing:** pytest

### Frontend
- **Framework:** React
- **Build Tool:** Vite
- **Testing:** Vitest


### Key Libraries
- `rake-nltk` - Keyword extraction
- `nltk` - Natural language processing
- `Pillow` - Image/media analysis
- `sqlalchemy` - Database ORM
- `GitPython` - Git repository analysis
- `python-docx` / `PyPDF2` - Document parsing
- `google-generativeai` - AI-powered analysis
- `fastapi` / `uvicorn` - API server
- `python-jose[cryptography]` - JWT tokens
- `passlib[bcrypt]` / `bcrypt==4.0.1` - Password hashing
- `pandas` - Data processing
- `tqdm` - Progress display

---

## 🗄️ Database Architecture
 
The system uses a single **SQLite database** (`projects.db`) with eight interconnected tables:
 
**Project Data**
- **Projects** - Name, path, description, dates, metrics (lines of code, word count, file count, size), project type, collaboration type, importance score, languages/frameworks/skills/tags (JSON), resume bullets, thumbnail path, success evidence, user customizations
- **Files** - File path, name, type, size, dates, lines of code, hash (for incremental uploads), duplicate detection, owner/editors
- **Contributors** - Name, identifier, commit count, lines added/deleted, contribution percentage
- **Keywords** - Keyword text, relevance score, category
 
**User Data**
- **Users** - First/last name, email, hashed password, portfolio (JSON), resume (JSON)
- **Education** - Institution, degree type, field of study, start/end dates (linked to user)
- **Work History** - Company, role, start/end dates (linked to user)
- **Contact Info** - Address, phone (linked to user)


---

## 🤝 Contributing

This is a university capstone project for COSC 499.

### Development Workflow

1. Create a feature branch: `git checkout -b feature-name`
2. Make your changes and commit: `git commit -m "Description"`
3. Write tests for new features
4. Run tests: `pytest tests/ -v`
5. Push to branch: `git push origin feature-name`
6. Create Pull Request for team review
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
- **Libraries Used:** NLTK, Pillow, SQLAlchemy, FastAPI, pytest

---

System Architecture Diagram [linked here](./docs/Proposal/SystemArchitectureDiagram.md)

Data Flow Diagrams:
 [DFD Level 0](docs/Proposal/FinalDFDLevel0.md)
 [DFD Level 1](docs/Proposal/FinalDFDLevel1.md)

WBS [linked here](https://github.com/COSC-499-W2025/capstone-project-team-13/blob/main/docs/Proposal/WBS.md)

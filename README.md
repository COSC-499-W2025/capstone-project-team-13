# Digital Artifact Mining Software

**Team 13 - COSC 499 Capstone Project**

A versatile platform that intelligently processes digital artifacts including code, documents, and media files to create polished summaries and portfolio highlights for students and new graduates.

---

## 👥 Team Members

- **Sana Shah** - 94945664
- **Jackson Wilson** - 11927753
- **Prina Mehta** - 87716874
- **Maya Knutsvig** - 17950502
- **Ilina Islam** - 58189903
- **T'Olu Akinwande** - 69892271

---

## 🎯 Project Overview

Our digital artifact mining software serves as a tool for new graduates and students to efficiently display their projects, skills, and highlights. The system supports three different user groups:

1. **Programming/Technology** - Analyzes code files, detects languages and frameworks
2. **Digital Art/Graphics** - Processes media files, identifies design software and skills
3. **Writing/Research** - Extracts keywords and insights from documents


---

## ✨ Key Features

### Currently Implementing (Milestone 1)

- **User Consent Management** 
- **File Format Validation** 
- **ZIP File Handling** 
- **Multi-Format Parsing** 
- **Language Detection** 
- **Framework Detection** 
- **Keyword Extraction** 
- **Visual Media Analysis**
- **Dual Database System**
- **Contribution Metrics**

### Coming Soon (Milestones 2 & 3)...

---

## 🛠️ Tech Stack

### Current (Milestone 1)
- **Language:** Python
- **Database:** SQLite with SQLAlchemy ORM
- **Testing:** pytest, unittest
- **Libraries:**
  - `rake-nltk` - Keyword extraction
  - `nltk` - Natural language processing
  - `Pillow` - Image/media analysis
  - `sqlalchemy` - Database ORM

### Planned (Milestones 2 & 3)
- **Web Framework:** Django
- **Frontend:** Django templates or React
- **Database:** PostgreSQL (production) / SQLite (development)

---

## 🗄️ Database Architecture

The system will use **two separate SQLite databases**:

#### Database 1: `projects_data.db` - Raw Project Data
Stores extracted information from scanned projects:
- **Projects** - Basic info, dates, metrics, type, languages, frameworks
- **Files** - File paths, types, sizes, created/modified dates
- **Contributors** - Git contributor names, identifiers, commit counts

#### Database 2: `projects_analysis.db` - Analysis Results
- **Coming soon...*

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
- **Libraries Used:** NLTK, Pillow, SQLAlchemy, pytest

---

System Architecture Diagram [linked here](./docs/Proposal/SystemArchitectureDiagram.md)

Data Flow Diagram Level 1 [linked here](./docs/Proposal/DFD1.md)

WBS [linked here](https://github.com/COSC-499-W2025/capstone-project-team-13/blob/main/docs/Proposal/WBS.md)

# Installation Guide

## Prerequisites

- Python 3.13+
- Node.js 18+ and npm
- A [Google AI Studio](https://aistudio.google.com/) API key (free tier available)

---

## 1. Clone the Repository

```bash
git clone https://github.com/COSC-499-W2025/capstone-project-team-13.git
cd capstone-project-team-13
```

---

## 2. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

AI features (summaries, resume bullets, interview prep) require this key. All other features work without it.

---

## 4. Frontend Setup

```bash
cd artifactMining
npm install
```

---

## Running the Application

### Backend API Server

```bash
uvicorn src.mainAPI:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

### Frontend Dev Server

```bash
cd artifactMining
npm run dev
```

- Frontend: `http://localhost:5173`

### CLI Mode (no browser required)

```bash
python src/main.py
```

---

## Running Tests

### Backend

```bash
pytest tests/ -v
```

### Frontend

```bash
cd artifactMining
npm test
```

from fastapi import FastAPI 
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.Routers import projects, resumes, portfolio, skills, analytics, consent, auth, configuration, evidence, education, work_history, contributors
from src.Routers import interview_router
from src.Routers import user_profile
from src.Routers import public_portfolios

app = FastAPI(title="Digital Artifact Mining API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded thumbnails as static files
UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(projects.router)
app.include_router(resumes.router)
app.include_router(education.router)
app.include_router(work_history.router)
app.include_router(portfolio.router)
app.include_router(skills.router)
app.include_router(analytics.router)
app.include_router(consent.router)
app.include_router(configuration.router)
app.include_router(auth.router)
app.include_router(evidence.router)
app.include_router(interview_router.router)
app.include_router(user_profile.router)
app.include_router(contributors.router)
app.include_router(public_portfolios.router)
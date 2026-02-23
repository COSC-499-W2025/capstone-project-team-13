from fastapi import FastAPI
from src.Routers import projects, resumes, portfolio, skills, analytics, consent, auth

app = FastAPI(title="Digital Artifact Mining API")
app.include_router(projects.router)
app.include_router(resumes.router)
app.include_router(portfolio.router)
app.include_router(skills.router)
app.include_router(analytics.router)
app.include_router(consent.router)
app.include_router(auth.router)

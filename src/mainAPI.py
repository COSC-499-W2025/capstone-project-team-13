from fastapi import FastAPI
from src.Routers import projects, skills

app = FastAPI(title="Digital Artifact Mining API")
app.include_router(projects.router)
app.include_router(skills.router)


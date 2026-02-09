from fastapi import FastAPI
from src.Routers import projects

app = FastAPI(title="Digital Artifact Mining API")
app.include_router(projects.router)


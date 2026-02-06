from fastapi import FastAPI
from routers import projects

app = FastAPI(
    title="Digital Artifact Mining API",
    version="1.0"
)

app.include_router(projects.router)

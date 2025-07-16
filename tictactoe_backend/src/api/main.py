from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import init_db  # Import DB setup and dependency

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    Initialize the database (creates tables if they don't exist).
    """
    init_db()

@app.get("/")
def health_check():
    """
    Health check endpoint.

    Returns:
        dict: {"message": "Healthy"}
    """
    return {"message": "Healthy"}

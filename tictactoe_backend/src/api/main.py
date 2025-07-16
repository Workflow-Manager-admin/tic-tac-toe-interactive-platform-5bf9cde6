from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import init_db  # Import DB setup and dependency
from src.api.routes import game as game_routes

app = FastAPI(
    title="Tic Tac Toe API",
    description="API for Tic Tac Toe game sessions, moves, state, and history.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Game", "description": "Game creation, moves, state, and history endpoints."}
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(game_routes.router)

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

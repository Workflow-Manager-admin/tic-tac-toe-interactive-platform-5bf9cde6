from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import init_db  # Import DB setup and dependency
from src.api.routes import game as game_routes
from src.api.routes import game_ws

app = FastAPI(
    title="Tic Tac Toe API",
    description="API for Tic Tac Toe game sessions, moves, state, and history. "
                "Supports real-time game updates over WebSocket.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Game", "description": "Game creation, moves, state, and history endpoints."},
        {"name": "WebSocket", "description": "WebSocket endpoints for real-time game updates."}
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
app.include_router(game_ws.router)

@app.on_event("startup")
def on_startup():
    """
    Initialize the database (creates tables if they don't exist).
    """
    init_db()

@app.get("/", tags=["Game"])
def health_check():
    """
    Health check endpoint.

    Returns:
        dict: {"message": "Healthy"}
    """
    return {"message": "Healthy"}

@app.get("/ws-docs", tags=["WebSocket"])
def websocket_doc():
    """
    WebSocket usage documentation.

    Returns:
        dict: Sample connection URL, description, and event format for real-time updates.
    """
    return {
        "message": (
            "WebSocket API provides real-time game event updates. "
            "Connect to ws://<host>/ws/game/{game_id}. "
            "Subscribe to updates for moves, status, and game-over events."
        ),
        "subscribe_example_url": "/ws/game/1234",
        "event_format": {
            "event": "move | status | game_over",
            "payload": "{...game state or event details...}"
        }
    }

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set

# In-memory mapping of game_id to set of WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for game subscriptions."""

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    # PUBLIC_INTERFACE
    async def connect(self, websocket: WebSocket, game_id: int):
        """Accept and register a new WebSocket connection under the game."""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)

    # PUBLIC_INTERFACE
    def disconnect(self, websocket: WebSocket, game_id: int):
        """Remove WebSocket connection from game subscriptions."""
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    # PUBLIC_INTERFACE
    async def broadcast(self, game_id: int, message: dict):
        """Send a message to all subscribed clients of game_id."""
        connections = list(self.active_connections.get(game_id, []))
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection, game_id)

manager = ConnectionManager()
router = APIRouter()

# PUBLIC_INTERFACE
@router.websocket("/ws/game/{game_id}")
async def websocket_game_updates(websocket: WebSocket, game_id: int):
    """
    WebSocket endpoint for real-time updates and events for a game.

    Allows clients to subscribe to updates for a particular game_id.
    Notifies all subscribed clients when a move occurs, the game is updated,
    or the game is finished.

    Usage:
        Connect to ws://<host>/ws/game/{game_id} to receive JSON event messages.

    Event JSON format:
    {
        "event": "move" | "game_over" | "status",
        "payload": { ... }
    }
    """
    await manager.connect(websocket, game_id)
    try:
        while True:
            # Optionally receive ping/pong, but mostly we just keep alive for push.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)

# --- Utility to emit events: import and call from REST endpoints ---
# PUBLIC_INTERFACE
async def emit_game_event(game_id: int, event: str, payload: dict):
    """
    Notify all WebSocket subscribers for the given game of an event.

    Args:
        game_id (int): Game identifier for channel
        event (str): "move", "game_over", etc.
        payload (dict): JSON-serializable payload
    """
    await manager.broadcast(game_id, {"event": event, "payload": payload})

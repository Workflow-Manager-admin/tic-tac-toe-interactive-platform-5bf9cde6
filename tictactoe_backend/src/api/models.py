from typing import List, Optional
from pydantic import BaseModel, Field

# ---------------------------
# API Data Models for FastAPI
# ---------------------------

# PUBLIC_INTERFACE
class CreateGameRequest(BaseModel):
    """Request model for starting a new game session."""
    player_x: Optional[str] = Field(None, description="User ID or identifier for Player X (optional, can be None for guest).")
    player_o: Optional[str] = Field(None, description="User ID or identifier for Player O (optional).")


# PUBLIC_INTERFACE
class CreateGameResponse(BaseModel):
    """Response when a new game is created."""
    game_id: int = Field(..., description="Unique Game identifier.")
    board: List[Optional[str]] = Field(..., description="The tic tac toe board; 9 cells as list (None, 'X', 'O').")
    status: str = Field(..., description="Game status (in_progress, player_x_won, player_o_won, draw, abandoned).")
    current_turn: str = Field(..., description="'X' or 'O' indicating the next move.")
    player_x: Optional[str] = Field(None)
    player_o: Optional[str] = Field(None)


# PUBLIC_INTERFACE
class MoveRequest(BaseModel):
    """Request for making a move in a game."""
    player_symbol: str = Field(..., regex="^(X|O)$", description="Player's symbol ('X' or 'O').")
    position: int = Field(..., ge=0, le=8, description="Board position (0-8).")
    user_identifier: Optional[str] = Field(None, description="Player's user/session id (optional).")


# PUBLIC_INTERFACE
class MoveResponse(BaseModel):
    """Response after making a move."""
    game_id: int
    board: List[Optional[str]]
    move_number: int
    status: str
    current_turn: Optional[str] = None
    winner: Optional[str] = None
    error: Optional[str] = None


# PUBLIC_INTERFACE
class GameStateResponse(BaseModel):
    """Represents the current full state of a game session."""
    game_id: int
    board: List[Optional[str]]
    moves: List[dict]
    status: str
    player_x: Optional[str]
    player_o: Optional[str]
    winner: Optional[str] = None
    finished: bool = Field(False, description="True if game is over, else False.")


# PUBLIC_INTERFACE
class GameHistoryEntry(BaseModel):
    """Game history summary record."""
    game_id: int
    finished_at: str
    result: str
    moves_count: int


# PUBLIC_INTERFACE
class GameHistoryListResponse(BaseModel):
    """List of games in history."""
    items: List[GameHistoryEntry]


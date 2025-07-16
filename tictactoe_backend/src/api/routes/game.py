from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from src.api.db import Game, PlayerSession, Move, GameStatus, GameHistory, get_db
from src.api.models import (
    CreateGameRequest, CreateGameResponse,
    MoveRequest, MoveResponse,
    GameStateResponse, GameHistoryListResponse, GameHistoryEntry,
)
from src.api.services.game_logic import (
    new_board, make_move, is_move_valid, game_status, whose_turn
)
from src.api.routes.game_ws import emit_game_event

import asyncio

router = APIRouter(prefix='/game', tags=['Game'])

# PUBLIC_INTERFACE
@router.post("/create", response_model=CreateGameResponse, summary="Create a new game", description="Starts a new tic tac toe game session.")
def create_game(req: CreateGameRequest, db: Session = Depends(get_db)):
    """
    Creates a new game and initializes players.
    """
    player_x_id = req.player_x or None
    player_o_id = req.player_o or None

    board = new_board()

    # Create Game row
    game = Game(
        status=GameStatus.IN_PROGRESS,
        board_state=board,
        winner=None
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    # Create Player Sessions
    players = []
    ps_x = PlayerSession(game_id=game.id, user_identifier=player_x_id, symbol='X')
    db.add(ps_x)
    players.append(ps_x)
    if player_o_id is not None:  # Optional early O registration
        ps_o = PlayerSession(game_id=game.id, user_identifier=player_o_id, symbol='O')
        db.add(ps_o)
        players.append(ps_o)
    db.commit()

    return CreateGameResponse(
        game_id=game.id,
        board=board,
        status=game.status.value,
        current_turn='X',
        player_x=player_x_id,
        player_o=player_o_id
    )


# PUBLIC_INTERFACE
@router.post("/{game_id}/move", response_model=MoveResponse, summary="Make a move", description="Submit a move for a player in an active game.")
def make_game_move(
    game_id: int,
    req: MoveRequest,
    db: Session = Depends(get_db)
):
    """
    Attempts to record and apply a move for a game.

    Returns the updated board state and game status.
    """
    game = db.query(Game).options(joinedload(Game.moves), joinedload(Game.player_sessions)).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    board = game.board_state

    # Validate symbol and turn
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Game is not in progress")
    player_symbol = req.player_symbol
    if player_symbol not in ('X', 'O'):
        raise HTTPException(status_code=400, detail="Invalid player symbol")

    # Enforce turn-taking rule
    expected_turn = whose_turn(board)
    if player_symbol != expected_turn:
        raise HTTPException(
            status_code=400,
            detail=f"It is {expected_turn}'s turn"
        )

    # Validate player session
    player_session = db.query(PlayerSession).filter(
        PlayerSession.game_id == game_id,
        PlayerSession.symbol == player_symbol,
    )
    if req.user_identifier:
        player_session = player_session.filter(
            PlayerSession.user_identifier == req.user_identifier
        )
    player_session = player_session.first()
    if not player_session:
        raise HTTPException(status_code=403, detail="Player session not found or does not match symbol")
    
    # Validate move
    position = req.position
    if not is_move_valid(board, position):
        raise HTTPException(status_code=400, detail="Invalid move: position is not empty or out of bounds")

    # Make move
    try:
        new_board = make_move(board, position, player_symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid move: {e}")

    move_number = len(game.moves) + 1
    move = Move(
        game_id=game.id,
        player_session_id=player_session.id,
        position=position,
        symbol=player_symbol,
        move_number=move_number
    )
    db.add(move)

    # Update board_state, status, winner if any
    game.board_state = new_board
    next_status, winner = game_status(new_board)
    game.status = next_status
    game.winner = winner

    # If finished, insert GameHistory if not already
    game_over = next_status in (GameStatus.PLAYER_X_WON, GameStatus.PLAYER_O_WON, GameStatus.DRAW)
    if game_over:
        if not game.history:
            db.add(GameHistory(
                game_id=game.id,
                result=next_status.value.replace("_", " ").title(),
                moves_count=move_number
            ))
    db.commit()
    db.refresh(game)

    # Broadcast over WebSocket:
    # 1. "move" event always + 2. "game_over" event if the game is finished
    try:
        message_move = {
            "game_id": game.id,
            "move_number": move_number,
            "board": new_board,
            "symbol": player_symbol,
            "position": position,
            "status": next_status.value,
        }
        asyncio.create_task(emit_game_event(game.id, "move", message_move))

        if game_over:
            message_over = {
                "game_id": game.id,
                "status": next_status.value,
                "winner": winner,
                "board": new_board,
            }
            asyncio.create_task(emit_game_event(game.id, "game_over", message_over))
    except Exception:
        pass

    return MoveResponse(
        game_id=game.id,
        board=new_board,
        move_number=move_number,
        status=next_status.value,
        current_turn=whose_turn(new_board) if next_status == GameStatus.IN_PROGRESS else None,
        winner=winner
    )


# PUBLIC_INTERFACE
@router.get("/{game_id}/state", response_model=GameStateResponse, summary="Game State", description="Fetch the current state and board of a game session.")
def game_state(game_id: int, db: Session = Depends(get_db)):
    """
    Returns the current state, board, moves, and players of a tic tac toe game.
    """
    game = db.query(Game).options(joinedload(Game.moves), joinedload(Game.player_sessions)).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = [
        {
            "id": m.id,
            "symbol": m.symbol,
            "position": m.position,
            "move_number": m.move_number,
            "created_at": m.created_at.isoformat(),
            "player_session_id": m.player_session_id
        }
        for m in sorted(game.moves, key=lambda mm: mm.move_number)
    ]
    # Player details
    player_map = {p.symbol: p.user_identifier for p in game.player_sessions}

    game_status_str, winner = game_status(game.board_state)
    finished = game_status_str in ("player_x_won", "player_o_won", "draw")

    return GameStateResponse(
        game_id=game.id,
        board=game.board_state,
        moves=moves,
        status=game_status_str,
        player_x=player_map.get("X"),
        player_o=player_map.get("O"),
        winner=winner,
        finished=finished
    )


# PUBLIC_INTERFACE
@router.get("/history", response_model=GameHistoryListResponse, summary="Game History", description="List completed/archived games with results and history.")
def get_game_history(db: Session = Depends(get_db)):
    """
    Returns the history of finished games.
    """
    games = db.query(GameHistory).options(joinedload(GameHistory.game)).order_by(GameHistory.finished_at.desc()).all()
    items = [
        GameHistoryEntry(
            game_id=g.game_id,
            finished_at=g.finished_at.isoformat(),
            result=g.result,
            moves_count=g.moves_count
        )
        for g in games
    ]
    return GameHistoryListResponse(items=items)

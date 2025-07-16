"""
Database models and setup for the Tic Tac Toe backend (SQLite/SQLAlchemy).
"""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Enum, create_engine, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.types import JSON
import enum
import os

Base = declarative_base()

# PUBLIC_INTERFACE
class GameStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    PLAYER_X_WON = "player_x_won"
    PLAYER_O_WON = "player_o_won"
    DRAW = "draw"
    ABANDONED = "abandoned"

# PUBLIC_INTERFACE
class Game(Base):
    """
    Represents a game session.
    """
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, server_default=func.now())
    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.IN_PROGRESS)
    winner = Column(String(1), nullable=True)  # 'X', 'O', or None

    # Board as a flat list like ['X','O','X',...], serialized as JSON
    board_state = Column(JSON, nullable=False, default=list)
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    player_sessions = relationship("PlayerSession", back_populates="game", cascade="all, delete-orphan")
    history = relationship("GameHistory", back_populates="game", cascade="all, delete-orphan")

# PUBLIC_INTERFACE
class PlayerSession(Base):
    """
    Represents a player in a game session.
    """
    __tablename__ = "player_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_identifier = Column(String(64), nullable=True)  # could be guest ID or user ID
    symbol = Column(String(1), nullable=False)  # 'X' or 'O'

    game = relationship("Game", back_populates="player_sessions")

# PUBLIC_INTERFACE
class Move(Base):
    """
    Represents a move made in a game.
    """
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_session_id = Column(Integer, ForeignKey("player_sessions.id"), nullable=False)
    position = Column(Integer, nullable=False)  # 0-8 for Tic Tac Toe
    symbol = Column(String(1), nullable=False)  # 'X' or 'O'
    move_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    game = relationship("Game", back_populates="moves")
    player_session = relationship("PlayerSession")

# PUBLIC_INTERFACE
class GameHistory(Base):
    """
    History record for completed or (optionally) in-progress games.
    """
    __tablename__ = "game_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    finished_at = Column(DateTime, server_default=func.now())
    result = Column(String(32), nullable=False)  # e.g., 'X wins', 'O wins', 'Draw', etc.
    moves_count = Column(Integer, nullable=False)

    game = relationship("Game", back_populates="history")

# ---------- Database setup ----------

# DATABASE_URL will default to local SQLite if not specified in environment
DB_FILENAME = os.getenv("DB_FILENAME", "tictactoe.sqlite3")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILENAME}")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

# PUBLIC_INTERFACE
def init_db():
    """Create all tables on the database."""
    Base.metadata.create_all(bind=engine)

# PUBLIC_INTERFACE
def get_db():
    """
    Dependency to provide a SQLAlchemy session for FastAPI endpoints.
    Yields an open session and closes it on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


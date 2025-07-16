from typing import List, Optional, Tuple, Literal

# PUBLIC_INTERFACE
def new_board() -> List[Optional[str]]:
    """Create a new empty tic-tac-toe board (flat 9-element list)."""
    return [None for _ in range(9)]


# PUBLIC_INTERFACE
def whose_turn(board: List[Optional[str]]) -> str:
    """
    Determine whose turn it is based on board.
    Returns 'X' or 'O'
    """
    x_count = sum(1 for v in board if v == 'X')
    o_count = sum(1 for v in board if v == 'O')
    return 'X' if x_count <= o_count else 'O'


# PUBLIC_INTERFACE
def is_move_valid(board: List[Optional[str]], pos: int) -> bool:
    """
    Checks whether a move is valid (position is empty & in range).
    """
    return 0 <= pos < 9 and board[pos] is None

# PUBLIC_INTERFACE
def make_move(board: List[Optional[str]], pos: int, symbol: Literal['X', 'O']) -> List[Optional[str]]:
    """
    Returns a new board state after making a move at pos with symbol.
    """
    if not is_move_valid(board, pos):
        raise ValueError("Invalid move")
    new_board = board.copy()
    new_board[pos] = symbol
    return new_board

# PUBLIC_INTERFACE
def get_winner(board: List[Optional[str]]) -> Optional[str]:
    """
    Determines if there is a winner. Returns 'X', 'O', or None.
    """
    win_lines = [
        [0,1,2],[3,4,5],[6,7,8],  # Rows
        [0,3,6],[1,4,7],[2,5,8],  # Columns
        [0,4,8],[2,4,6]           # Diagonals
    ]
    for line in win_lines:
        if (
            board[line[0]] is not None and
            board[line[0]] == board[line[1]] == board[line[2]]
        ):
            return board[line[0]]
    return None

# PUBLIC_INTERFACE
def is_draw(board: List[Optional[str]]) -> bool:
    """Returns True if the board is full and there is no winner."""
    return all(v is not None for v in board) and get_winner(board) is None

# PUBLIC_INTERFACE
def game_status(board: List[Optional[str]]) -> Tuple[str, Optional[str]]:
    """
    Computes the current status and winner (if any).

    Returns:
        status: One of "in_progress", "player_x_won", "player_o_won", "draw"
        winner: "X", "O", or None
    """
    winner = get_winner(board)
    if winner == 'X':
        return "player_x_won", "X"
    elif winner == 'O':
        return "player_o_won", "O"
    elif is_draw(board):
        return "draw", None
    else:
        return "in_progress", None

# PUBLIC_INTERFACE
def move_history_to_board(moves: List[dict]) -> List[Optional[str]]:
    """
    Given a move history (list of dicts), returns the latest board state.
    Each move dict should have at least: {'position': int, 'symbol': 'X'|'O'}.
    """
    board = new_board()
    for move in moves:
        board[move['position']] = move['symbol']
    return board


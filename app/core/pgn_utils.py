from __future__ import annotations

import io
from dataclasses import dataclass

import chess
import chess.pgn


class PgnError(ValueError):
    """Raised when PGN cannot be parsed into a usable game."""


@dataclass(frozen=True)
class PgnPosition:
    ply: int
    move_san: str
    move_uci: str
    fen: str


def parse_game(pgn_text: str) -> chess.pgn.Game:
    stream = io.StringIO(pgn_text.strip())
    game = chess.pgn.read_game(stream)
    if game is None:
        raise PgnError("Could not parse PGN. Paste a complete or at least syntactically valid game.")
    if game.errors:
        raise PgnError("; ".join(str(error) for error in game.errors))
    return game


def positions_from_pgn(pgn_text: str) -> list[PgnPosition]:
    game = parse_game(pgn_text)
    board = game.board()
    positions: list[PgnPosition] = [
        PgnPosition(ply=0, move_san="Initial position", move_uci="", fen=board.fen())
    ]
    for ply, move in enumerate(game.mainline_moves(), start=1):
        san = board.san(move)
        move_uci = move.uci()
        board.push(move)
        positions.append(PgnPosition(ply=ply, move_san=san, move_uci=move_uci, fen=board.fen()))
    if len(positions) == 1:
        raise PgnError("PGN contains no moves.")
    return positions


def fen_after_ply(pgn_text: str, ply: int) -> str:
    positions = positions_from_pgn(pgn_text)
    if ply < 0 or ply >= len(positions):
        raise PgnError(f"Selected ply {ply} is outside the game range 0..{len(positions) - 1}.")
    return positions[ply].fen


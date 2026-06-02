from __future__ import annotations

import chess


class BoardError(ValueError):
    """Raised when a board position or move cannot be parsed safely."""


def board_from_fen(fen: str) -> chess.Board:
    try:
        board = chess.Board(fen.strip())
    except ValueError as exc:
        raise BoardError(f"Invalid FEN: {exc}") from exc
    return board


def validate_fen(fen: str) -> bool:
    try:
        board_from_fen(fen)
    except BoardError:
        return False
    return True


def legal_moves_uci(fen: str) -> list[str]:
    board = board_from_fen(fen)
    return [move.uci() for move in board.legal_moves]


def uci_to_san(fen: str, move_uci: str) -> str:
    board = board_from_fen(fen)
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError as exc:
        raise BoardError(f"Invalid UCI move: {move_uci}") from exc
    if move not in board.legal_moves:
        raise BoardError(f"Move {move_uci} is not legal in this position.")
    return board.san(move)


def san_to_uci(fen: str, move_san: str) -> str:
    board = board_from_fen(fen)
    try:
        return board.parse_san(move_san).uci()
    except ValueError as exc:
        raise BoardError(f"Invalid SAN move: {move_san}") from exc


def push_uci(fen: str, move_uci: str) -> chess.Board:
    board = board_from_fen(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        raise BoardError(f"Move {move_uci} is not legal in this position.")
    board.push(move)
    return board


def position_key(fen: str) -> str:
    board = board_from_fen(fen)
    return " ".join(board.fen().split(" ")[:4])


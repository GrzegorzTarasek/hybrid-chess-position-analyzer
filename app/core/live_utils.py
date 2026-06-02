from __future__ import annotations

import chess

from app.core.board_utils import BoardError, board_from_fen


def apply_move_text(fen: str, move_text: str) -> tuple[str, str, str]:
    board = board_from_fen(fen)
    cleaned = move_text.strip()
    if not cleaned:
        raise BoardError("Enter a move in SAN or UCI notation.")

    move = _parse_uci_or_san(board, cleaned)
    san = board.san(move)
    board.push(move)
    return board.fen(), san, move.uci()


def legal_move_labels(fen: str) -> list[str]:
    board = board_from_fen(fen)
    return [f"{board.san(move)} ({move.uci()})" for move in board.legal_moves]


def _parse_uci_or_san(board: chess.Board, move_text: str) -> chess.Move:
    try:
        move = chess.Move.from_uci(move_text.lower())
        if move in board.legal_moves:
            return move
    except ValueError:
        pass

    try:
        return board.parse_san(move_text)
    except ValueError as exc:
        raise BoardError(f"Move '{move_text}' is not legal in the current position.") from exc


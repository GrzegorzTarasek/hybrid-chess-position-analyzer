import pytest

from app.core.board_utils import BoardError, legal_moves_uci, position_key, uci_to_san, validate_fen


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_validate_fen() -> None:
    assert validate_fen(START_FEN)
    assert not validate_fen("not a fen")


def test_legal_moves_and_conversion() -> None:
    assert "e2e4" in legal_moves_uci(START_FEN)
    assert uci_to_san(START_FEN, "e2e4") == "e4"


def test_illegal_move_raises() -> None:
    with pytest.raises(BoardError):
        uci_to_san(START_FEN, "e7e5")


def test_position_key_ignores_clocks() -> None:
    fen_a = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    fen_b = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 7 12"
    assert position_key(fen_a) == position_key(fen_b)


import pytest

from app.core.board_utils import BoardError
from app.core.live_utils import apply_move_text, legal_move_labels


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_apply_san_move() -> None:
    next_fen, san, uci = apply_move_text(START_FEN, "e4")
    assert san == "e4"
    assert uci == "e2e4"
    assert next_fen.split()[1] == "b"


def test_apply_uci_move() -> None:
    next_fen, san, uci = apply_move_text(START_FEN, "g1f3")
    assert san == "Nf3"
    assert uci == "g1f3"
    assert next_fen.split()[1] == "b"


def test_illegal_live_move_raises() -> None:
    with pytest.raises(BoardError):
        apply_move_text(START_FEN, "e5")


def test_legal_move_labels_include_san_and_uci() -> None:
    labels = legal_move_labels(START_FEN)
    assert "e4 (e2e4)" in labels


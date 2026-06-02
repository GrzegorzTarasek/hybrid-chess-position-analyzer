import pytest

from app.core.pgn_utils import PgnError, fen_after_ply, positions_from_pgn


PGN = """[Event "Sample"]
[Site "?"]
[Date "2026.06.02"]
[Round "?"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 *
"""


def test_positions_from_pgn() -> None:
    positions = positions_from_pgn(PGN)
    assert len(positions) == 5
    assert positions[1].move_san == "e4"
    assert positions[1].move_uci == "e2e4"


def test_fen_after_ply() -> None:
    fen = fen_after_ply(PGN, 2)
    assert " b " not in fen
    assert fen.split()[1] == "w"


def test_bad_pgn_raises() -> None:
    with pytest.raises(PgnError):
        positions_from_pgn("")


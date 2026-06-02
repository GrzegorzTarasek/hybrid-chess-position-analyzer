import pytest

from app.engines.stockfish_engine import StockfishEngine, StockfishUnavailable


def test_missing_stockfish_has_readable_error() -> None:
    engine = StockfishEngine(path=None)
    with pytest.raises(StockfishUnavailable, match="Stockfish is not configured"):
        engine.best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")


from app.core.analysis import analyze_position


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_demo_analysis_without_stockfish_or_internet() -> None:
    result = analyze_position(START_FEN, use_demo_data=True, max_moves=6)
    assert result.best_engine_move is not None
    assert result.best_hybrid_move is not None
    assert result.most_popular_move is not None
    assert result.moves[0].rank_hybrid == 1
    assert "alpha" in result.explanation


def test_analysis_without_historical_data_still_returns_legal_moves(monkeypatch) -> None:
    from app.core import analysis as analysis_module

    monkeypatch.setattr(
        analysis_module,
        "_load_historical_moves",
        lambda **kwargs: ([], "test-empty-source", ["no historical data"]),
    )
    result = analyze_position(START_FEN, use_demo_data=False, max_moves=3)
    assert len(result.moves) == 3
    assert result.warnings


def test_rankings_are_sorted_in_demo() -> None:
    result = analyze_position(START_FEN, use_demo_data=True, max_moves=6, alpha=0.5)
    ranks = [move.rank_hybrid for move in result.moves if move.rank_hybrid is not None]
    assert ranks == sorted(ranks)


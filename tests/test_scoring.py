import pytest

from app.core.scoring import (
    compute_engine_scores,
    human_minus_engine,
    human_score_for_side,
    human_score_white,
    hybrid_score,
    popularity,
)


def test_human_score_white() -> None:
    assert human_score_white(6, 2, 2) == 0.7
    assert human_score_white(0, 0, 0) is None


def test_human_score_for_black_to_move() -> None:
    assert human_score_for_side(0.7, "white") == 0.7
    assert human_score_for_side(0.7, "black") == pytest.approx(0.3)


def test_engine_score_normalization() -> None:
    white_score, black_side_score = compute_engine_scores(100, None, "black", k=0.8)
    assert white_score is not None
    assert 0.65 < white_score < 0.75
    assert black_side_score is not None
    assert 0.25 < black_side_score < 0.35


def test_mate_score_normalization() -> None:
    white_score, side_score = compute_engine_scores(None, 3, "white")
    assert white_score == 0.99
    assert side_score == 0.99


def test_hybrid_score() -> None:
    assert hybrid_score(0.8, 0.6, 0.5) == 0.7
    assert hybrid_score(None, 0.6, 0.5) == 0.6
    assert hybrid_score(0.8, None, 0.5) == 0.8


def test_popularity_and_gap() -> None:
    assert popularity(25, 100) == 0.25
    assert popularity(25, 0) is None
    assert human_minus_engine(0.7, 0.55) == 0.1499999999999999

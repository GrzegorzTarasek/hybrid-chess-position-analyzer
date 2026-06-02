from app.core.labeling import apply_labels, label_move
from app.models.move_analysis import MoveAnalysis


def test_statistically_suspicious_label() -> None:
    move = MoveAnalysis(
        move_san="h4",
        move_uci="h2h4",
        total_games=12,
        human_score_side_to_move=0.83,
        engine_score_side_to_move=0.45,
    )
    assert label_move(move, min_games=100) == "Statistically suspicious"


def test_universal_move_label() -> None:
    move = MoveAnalysis(
        move_san="Nf3",
        move_uci="g1f3",
        total_games=1000,
        human_score_side_to_move=0.62,
        engine_score_side_to_move=0.64,
    )
    assert label_move(move, min_games=100) == "Universal move"


def test_apply_labels() -> None:
    moves = [
        MoveAnalysis(
            move_san="d4",
            move_uci="d2d4",
            total_games=1000,
            human_score_side_to_move=0.55,
            engine_score_side_to_move=0.66,
            rank_engine=1,
            rank_human=2,
        )
    ]
    apply_labels(moves, min_games=100)
    assert moves[0].label == "Engine move"


from types import SimpleNamespace

from app.core.game_stats import analyze_game_statistics
from app.models.move_analysis import MoveAnalysis


PGN = """[Event "Sample"]
[Site "?"]
[Date "2026.06.02"]
[Round "?"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 *
"""


def test_game_statistics_builds_rank_summary(monkeypatch) -> None:
    def fake_analyze_position(**kwargs):
        return SimpleNamespace(
            side_to_move="white",
            moves=[
                MoveAnalysis(
                    move_san="e4",
                    move_uci="e2e4",
                    total_games=100,
                    human_score_side_to_move=0.7,
                    engine_score_side_to_move=0.8,
                    hybrid_score=0.75,
                    label="Universal move",
                    rank_engine=1,
                    rank_human=1,
                    rank_hybrid=1,
                    rank_popularity=1,
                ),
                MoveAnalysis(
                    move_san="e5",
                    move_uci="e7e5",
                    total_games=100,
                    human_score_side_to_move=0.65,
                    engine_score_side_to_move=0.7,
                    hybrid_score=0.675,
                    label="Practical move",
                    rank_engine=3,
                    rank_human=2,
                    rank_hybrid=2,
                    rank_popularity=1,
                ),
            ],
        )

    monkeypatch.setattr("app.core.game_stats.analyze_position", fake_analyze_position)
    stats = analyze_game_statistics(PGN, max_plies=2)

    assert stats.analyzed_plies == 2
    assert stats.engine_top5 == 2
    assert stats.player_top5 == 2
    assert stats.practical_rating.startswith("A")
    assert stats.moves[0].note == "Top engine and player move"


from __future__ import annotations

from app.models.move_analysis import MoveAnalysis
from app.models.position_analysis import PositionAnalysis


def recommendation_cards(analysis: PositionAnalysis) -> list[tuple[str, MoveAnalysis | None]]:
    return [
        ("Best engine move", analysis.best_engine_move),
        ("Best human move", analysis.best_human_move),
        ("Best hybrid move", analysis.best_hybrid_move),
        ("Most popular move", analysis.most_popular_move),
    ]


def move_summary(move: MoveAnalysis | None) -> str:
    if move is None:
        return "No data"
    bits = [move.move_san, move.label]
    if move.hybrid_score is not None:
        bits.append(f"hybrid {move.hybrid_score:.3f}")
    if move.total_games:
        bits.append(f"{move.total_games} games")
    return " | ".join(bits)


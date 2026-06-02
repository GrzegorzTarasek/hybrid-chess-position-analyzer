from __future__ import annotations

from dataclasses import dataclass, field

from app.models.move_analysis import MoveAnalysis


@dataclass
class PositionAnalysis:
    fen: str
    side_to_move: str
    moves: list[MoveAnalysis] = field(default_factory=list)
    best_engine_move: MoveAnalysis | None = None
    best_human_move: MoveAnalysis | None = None
    best_hybrid_move: MoveAnalysis | None = None
    most_popular_move: MoveAnalysis | None = None
    current_eval_cp: int | None = None
    current_eval_pawns: float | None = None
    current_mate_score: int | None = None
    current_score_side_to_move: float | None = None
    explanation: str = ""
    source: str = "unknown"
    warnings: list[str] = field(default_factory=list)

    def to_records(self) -> list[dict[str, object]]:
        return [move.to_dict() for move in self.moves]

    def to_dataframe(self):
        import pandas as pd

        return pd.DataFrame(self.to_records())

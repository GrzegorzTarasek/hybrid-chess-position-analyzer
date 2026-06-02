from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class MoveAnalysis:
    move_san: str
    move_uci: str
    total_games: int = 0
    white_wins: int = 0
    draws: int = 0
    black_wins: int = 0
    human_score_white: float | None = None
    human_score_side_to_move: float | None = None
    popularity: float | None = None
    engine_eval_cp: int | None = None
    engine_eval_pawns: float | None = None
    mate_score: int | None = None
    engine_score_white: float | None = None
    engine_score_side_to_move: float | None = None
    hybrid_score: float | None = None
    gap_human_minus_engine: float | None = None
    label: str = "Unclassified"
    stockfish_pv: str | None = None
    rank_engine: int | None = None
    rank_human: int | None = None
    rank_hybrid: int | None = None
    rank_popularity: int | None = None

    def __post_init__(self) -> None:
        if self.total_games == 0:
            self.total_games = self.white_wins + self.draws + self.black_wins

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

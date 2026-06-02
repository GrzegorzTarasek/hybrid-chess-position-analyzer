from __future__ import annotations

import math


def engine_score_white(
    eval_cp: int | None = None,
    mate_score: int | None = None,
    k: float = 0.8,
) -> float | None:
    if mate_score is not None:
        if mate_score > 0:
            return 0.99
        if mate_score < 0:
            return 0.01
        return 0.5
    if eval_cp is None:
        return None
    eval_pawns = eval_cp / 100
    return 1 / (1 + math.exp(-k * eval_pawns))


def score_for_side_to_move(score_white: float | None, side_to_move: str) -> float | None:
    if score_white is None:
        return None
    return score_white if side_to_move == "white" else 1 - score_white


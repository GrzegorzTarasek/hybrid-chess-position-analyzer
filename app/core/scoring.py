from __future__ import annotations

from app.engines.eval_normalizer import engine_score_white, score_for_side_to_move


def human_score_white(white_wins: int, draws: int, black_wins: int) -> float | None:
    total_games = white_wins + draws + black_wins
    if total_games <= 0:
        return None
    return (white_wins + 0.5 * draws) / total_games


def human_score_for_side(score_white: float | None, side_to_move: str) -> float | None:
    if score_white is None:
        return None
    return score_white if side_to_move == "white" else 1 - score_white


def popularity(total_games: int, all_games: int) -> float | None:
    if all_games <= 0:
        return None
    return total_games / all_games


def hybrid_score(
    engine_score_side_to_move: float | None,
    human_score_side_to_move: float | None,
    alpha: float,
) -> float | None:
    if engine_score_side_to_move is None and human_score_side_to_move is None:
        return None
    if engine_score_side_to_move is None:
        return human_score_side_to_move
    if human_score_side_to_move is None:
        return engine_score_side_to_move
    alpha = max(0.0, min(1.0, alpha))
    return alpha * engine_score_side_to_move + (1 - alpha) * human_score_side_to_move


def human_minus_engine(
    human_score_side_to_move: float | None,
    engine_score_side_to_move: float | None,
) -> float | None:
    if human_score_side_to_move is None or engine_score_side_to_move is None:
        return None
    return human_score_side_to_move - engine_score_side_to_move


def compute_engine_scores(
    eval_cp: int | None,
    mate_score: int | None,
    side_to_move: str,
    k: float = 0.8,
) -> tuple[float | None, float | None]:
    white_score = engine_score_white(eval_cp=eval_cp, mate_score=mate_score, k=k)
    side_score = score_for_side_to_move(white_score, side_to_move)
    return white_score, side_score


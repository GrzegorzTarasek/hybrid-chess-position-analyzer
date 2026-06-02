from __future__ import annotations

from app.models.move_analysis import MoveAnalysis


def label_move(move: MoveAnalysis, min_games: int = 100) -> str:
    engine = move.engine_score_side_to_move
    human = move.human_score_side_to_move

    if move.total_games < min_games and move.total_games > 0:
        return "Statistically suspicious"
    if human is None and engine is None:
        return "No data"
    if move.rank_engine == 1 and move.rank_human == 1 and move.total_games >= min_games:
        return "Universal move"
    if engine is not None and human is not None:
        if engine >= 0.60 and human >= 0.58 and move.total_games >= min_games:
            return "Universal move"
        if move.rank_engine == 1 and (move.rank_human is None or move.rank_human > 1):
            return "Engine move"
        if move.rank_human == 1 and move.rank_engine is not None and move.rank_engine > 1:
            return "Human move"
        if human >= 0.60 and engine >= 0.50 and move.total_games >= min_games:
            return "Practical move"
        if human >= 0.63 and engine < 0.50 and move.total_games >= min_games:
            return "Trap move"
        if engine >= 0.62 and human <= 0.52 and move.total_games >= min_games:
            return "Difficult engine move"
        if engine < 0.45 and human < 0.50 and move.total_games >= min_games:
            return "Risky move"
    if move.rank_engine == 1:
        return "Engine move"
    if move.rank_human == 1 and move.total_games >= min_games:
        return "Human move"
    return "Unclassified"


def apply_labels(moves: list[MoveAnalysis], min_games: int = 100) -> None:
    for move in moves:
        move.label = label_move(move, min_games=min_games)


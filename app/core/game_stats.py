from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean

import pandas as pd

from app.core.analysis import analyze_position
from app.core.pgn_utils import positions_from_pgn


@dataclass(frozen=True)
class PlyMoveStat:
    ply: int
    played_san: str
    played_uci: str
    side_to_move: str
    engine_rank: int | None
    player_rank: int | None
    hybrid_rank: int | None
    popularity_rank: int | None
    engine_score: float | None
    player_score: float | None
    hybrid_score: float | None
    label: str
    note: str


@dataclass(frozen=True)
class GameStatistics:
    analyzed_plies: int
    engine_top1: int
    engine_top5: int
    player_top1: int
    player_top5: int
    average_engine_rank: float | None
    average_player_rank: float | None
    practical_rating: str
    engine_alignment: float | None
    player_alignment: float | None
    moves: list[PlyMoveStat]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(move) for move in self.moves])


def analyze_game_statistics(
    pgn_text: str,
    alpha: float = 0.5,
    min_games: int = 100,
    max_moves: int = 10,
    stockfish_depth: int = 12,
    stockfish_time_limit: float | None = None,
    use_cache: bool = True,
    refresh_cache: bool = False,
    use_demo_data: bool = False,
    engine_k: float = 0.8,
    max_plies: int = 30,
) -> GameStatistics:
    positions = positions_from_pgn(pgn_text)
    move_stats: list[PlyMoveStat] = []

    for position_before, position_after in zip(positions[:-1], positions[1:]):
        if len(move_stats) >= max_plies:
            break
        analysis = analyze_position(
            fen=position_before.fen,
            alpha=alpha,
            min_games=min_games,
            max_moves=max_moves,
            stockfish_depth=stockfish_depth,
            stockfish_time_limit=stockfish_time_limit,
            use_cache=use_cache,
            refresh_cache=refresh_cache,
            use_demo_data=use_demo_data,
            engine_k=engine_k,
            required_moves=[position_after.move_uci],
        )
        played = next(
            (move for move in analysis.moves if move.move_uci == position_after.move_uci),
            None,
        )
        move_stats.append(
            PlyMoveStat(
                ply=position_after.ply,
                played_san=position_after.move_san,
                played_uci=position_after.move_uci,
                side_to_move=analysis.side_to_move,
                engine_rank=played.rank_engine if played else None,
                player_rank=played.rank_human if played else None,
                hybrid_rank=played.rank_hybrid if played else None,
                popularity_rank=played.rank_popularity if played else None,
                engine_score=played.engine_score_side_to_move if played else None,
                player_score=played.human_score_side_to_move if played else None,
                hybrid_score=played.hybrid_score if played else None,
                label=played.label if played else "Not in candidates",
                note=_move_note(played.rank_engine if played else None, played.rank_human if played else None),
            )
        )

    engine_ranks = [move.engine_rank for move in move_stats if move.engine_rank is not None]
    player_ranks = [move.player_rank for move in move_stats if move.player_rank is not None]
    engine_top1 = sum(1 for rank in engine_ranks if rank == 1)
    engine_top5 = sum(1 for rank in engine_ranks if rank <= 5)
    player_top1 = sum(1 for rank in player_ranks if rank == 1)
    player_top5 = sum(1 for rank in player_ranks if rank <= 5)
    analyzed_plies = len(move_stats)
    engine_alignment = engine_top5 / analyzed_plies if analyzed_plies else None
    player_alignment = player_top5 / analyzed_plies if analyzed_plies else None

    return GameStatistics(
        analyzed_plies=analyzed_plies,
        engine_top1=engine_top1,
        engine_top5=engine_top5,
        player_top1=player_top1,
        player_top5=player_top5,
        average_engine_rank=mean(engine_ranks) if engine_ranks else None,
        average_player_rank=mean(player_ranks) if player_ranks else None,
        practical_rating=_practical_rating(player_alignment, engine_alignment),
        engine_alignment=engine_alignment,
        player_alignment=player_alignment,
        moves=move_stats,
    )


def _move_note(engine_rank: int | None, player_rank: int | None) -> str:
    if engine_rank == 1 and player_rank == 1:
        return "Top engine and player move"
    if engine_rank is not None and engine_rank <= 5 and player_rank is not None and player_rank <= 5:
        return "Strong overlap"
    if engine_rank is not None and engine_rank <= 5:
        return "Engine-aligned"
    if player_rank is not None and player_rank <= 5:
        return "Player-practical"
    return "Outside top 5"


def _practical_rating(player_alignment: float | None, engine_alignment: float | None) -> str:
    if player_alignment is None:
        return "Not enough data"
    blended = 0.65 * player_alignment + 0.35 * (engine_alignment or 0)
    if blended >= 0.80:
        return "A - very strong practical game"
    if blended >= 0.65:
        return "B - solid practical game"
    if blended >= 0.50:
        return "C - mixed practical game"
    if blended >= 0.35:
        return "D - risky or inaccurate game"
    return "E - mostly outside recommended moves"

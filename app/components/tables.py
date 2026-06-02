from __future__ import annotations

import pandas as pd


DISPLAY_COLUMNS = [
    "move_san",
    "move_uci",
    "label",
    "total_games",
    "white_wins",
    "draws",
    "black_wins",
    "human_score_white",
    "human_score_side_to_move",
    "popularity",
    "engine_eval_cp",
    "engine_eval_pawns",
    "engine_score_side_to_move",
    "hybrid_score",
    "gap_human_minus_engine",
    "rank_engine",
    "rank_human",
    "rank_hybrid",
    "rank_popularity",
    "stockfish_pv",
]


def display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    available = [column for column in DISPLAY_COLUMNS if column in df.columns]
    formatted = df[available].copy()
    for column in [
        "human_score_white",
        "human_score_side_to_move",
        "popularity",
        "engine_score_side_to_move",
        "hybrid_score",
        "gap_human_minus_engine",
    ]:
        if column in formatted:
            formatted[column] = formatted[column].map(
                lambda value: None if pd.isna(value) else round(float(value), 3)
            )
    return formatted


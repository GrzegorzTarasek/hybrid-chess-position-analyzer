from __future__ import annotations

import json
from pathlib import Path

import chess

from app.cache.sqlite_cache import SQLiteCache
from app.core.board_utils import BoardError, board_from_fen, legal_moves_uci, uci_to_san
from app.core.config import settings
from app.core.labeling import apply_labels
from app.core.scoring import (
    compute_engine_scores,
    human_minus_engine,
    human_score_for_side,
    human_score_white,
    hybrid_score,
    popularity,
)
from app.data_sources.lichess_explorer import HistoricalDataError, LichessOpeningExplorer
from app.engines.stockfish_engine import StockfishEngine, StockfishUnavailable
from app.models.move_analysis import MoveAnalysis
from app.models.position_analysis import PositionAnalysis

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

CENTER_SQUARES = {
    chess.D4,
    chess.E4,
    chess.D5,
    chess.E5,
}

NEAR_CENTER_SQUARES = {
    chess.C3,
    chess.D3,
    chess.E3,
    chess.F3,
    chess.C4,
    chess.F4,
    chess.C5,
    chess.F5,
    chess.C6,
    chess.D6,
    chess.E6,
    chess.F6,
}


def analyze_position(
    fen: str,
    alpha: float = 0.5,
    min_games: int = 100,
    max_moves: int = 10,
    stockfish_depth: int = 12,
    stockfish_time_limit: float | None = None,
    use_cache: bool = True,
    refresh_cache: bool = False,
    use_demo_data: bool = False,
    engine_k: float = 0.8,
) -> PositionAnalysis:
    board = board_from_fen(fen)
    if board.is_game_over():
        raise BoardError("The position has no legal moves.")

    side_to_move = "white" if board.turn == chess.WHITE else "black"
    warnings: list[str] = []

    if use_demo_data:
        historical_rows = _load_demo_moves(settings.demo_data_path)
        source = "demo"
    else:
        historical_rows, source, source_warnings = _load_historical_moves(
            fen=fen,
            max_moves=max_moves,
            use_cache=use_cache,
            refresh_cache=refresh_cache,
        )
        warnings.extend(source_warnings)

    moves = _build_initial_moves(fen, historical_rows, max_moves)
    _add_scores_from_history(moves, side_to_move)
    _add_engine_scores(
        fen=fen,
        moves=moves,
        side_to_move=side_to_move,
        stockfish_depth=stockfish_depth,
        stockfish_time_limit=stockfish_time_limit,
        use_demo_data=use_demo_data,
        engine_k=engine_k,
        warnings=warnings,
    )

    for move in moves:
        move.hybrid_score = hybrid_score(
            move.engine_score_side_to_move, move.human_score_side_to_move, alpha
        )
        move.gap_human_minus_engine = human_minus_engine(
            move.human_score_side_to_move, move.engine_score_side_to_move
        )

    _rank_moves(moves)
    apply_labels(moves, min_games=min_games)
    moves.sort(key=lambda move: (move.rank_hybrid or 999, move.rank_engine or 999))

    analysis = PositionAnalysis(
        fen=fen,
        side_to_move=side_to_move,
        moves=moves,
        best_engine_move=_first_ranked(moves, "rank_engine"),
        best_human_move=_first_ranked(moves, "rank_human"),
        best_hybrid_move=_first_ranked(moves, "rank_hybrid"),
        most_popular_move=_first_ranked(moves, "rank_popularity"),
        source=source,
        warnings=warnings,
    )
    analysis.explanation = build_explanation(analysis, alpha)
    return analysis


def _load_historical_moves(
    fen: str,
    max_moves: int,
    use_cache: bool,
    refresh_cache: bool,
) -> tuple[list[dict[str, object]], str, list[str]]:
    source = "lichess_opening_explorer"
    warnings: list[str] = []
    cache = SQLiteCache(settings.cache_db_path)

    if use_cache and not refresh_cache:
        cached = cache.get(fen, source)
        if cached:
            return list(cached.get("moves", [])), f"{source} (cache)", warnings

    try:
        explorer = LichessOpeningExplorer()
        moves = explorer.fetch_moves(fen, max_moves=max_moves)
        payload = {"moves": [move.__dict__ for move in moves]}
        if use_cache:
            cache.set(fen, source, payload)
        return payload["moves"], source, warnings
    except HistoricalDataError as exc:
        warnings.append(str(exc))
        return [], source, warnings


def _load_demo_moves(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return list(payload["moves"])


def _build_initial_moves(
    fen: str,
    historical_rows: list[dict[str, object]],
    max_moves: int,
) -> list[MoveAnalysis]:
    legal = legal_moves_uci(fen)
    by_uci: dict[str, MoveAnalysis] = {}
    for row in historical_rows:
        move_uci = str(row["move_uci"])
        if move_uci not in legal:
            continue
        by_uci[move_uci] = MoveAnalysis(
            move_uci=move_uci,
            move_san=str(row.get("move_san") or uci_to_san(fen, move_uci)),
            white_wins=int(row.get("white_wins", 0)),
            draws=int(row.get("draws", 0)),
            black_wins=int(row.get("black_wins", 0)),
        )

    for move_uci in legal:
        if len(by_uci) >= max_moves:
            break
        by_uci.setdefault(move_uci, MoveAnalysis(move_uci=move_uci, move_san=uci_to_san(fen, move_uci)))

    return list(by_uci.values())[:max_moves]


def _add_scores_from_history(moves: list[MoveAnalysis], side_to_move: str) -> None:
    all_games = sum(move.total_games for move in moves)
    for move in moves:
        move.human_score_white = human_score_white(move.white_wins, move.draws, move.black_wins)
        move.human_score_side_to_move = human_score_for_side(move.human_score_white, side_to_move)
        move.popularity = popularity(move.total_games, all_games)


def _add_engine_scores(
    fen: str,
    moves: list[MoveAnalysis],
    side_to_move: str,
    stockfish_depth: int,
    stockfish_time_limit: float | None,
    use_demo_data: bool,
    engine_k: float,
    warnings: list[str],
) -> None:
    if use_demo_data:
        _add_fallback_engine_scores(fen, moves, side_to_move, engine_k, source_label="demo")
        return

    engine = StockfishEngine(settings.stockfish_path)
    for move in moves:
        try:
            result = engine.analyze_after_move(
                fen,
                move.move_uci,
                depth=stockfish_depth,
                time_limit=stockfish_time_limit,
            )
        except StockfishUnavailable as exc:
            warnings.append(str(exc))
            warnings.append("Using simplified local evaluation so engine suggestions remain visible.")
            _add_fallback_engine_scores(
                fen,
                moves,
                side_to_move,
                engine_k,
                source_label="fallback",
                only_missing=True,
            )
            return
        move.engine_eval_cp = result.eval_cp
        move.engine_eval_pawns = result.eval_cp / 100 if result.eval_cp is not None else None
        move.mate_score = result.mate_score
        move.stockfish_pv = result.pv
        move.engine_score_white, move.engine_score_side_to_move = compute_engine_scores(
            result.eval_cp, result.mate_score, side_to_move, engine_k
        )


def _add_fallback_engine_scores(
    fen: str,
    moves: list[MoveAnalysis],
    side_to_move: str,
    engine_k: float,
    source_label: str,
    only_missing: bool = False,
) -> None:
    for move in moves:
        if only_missing and move.engine_score_side_to_move is not None:
            continue
        eval_cp = _simple_eval_after_move(fen, move.move_uci)
        move.engine_eval_cp = eval_cp
        move.engine_eval_pawns = eval_cp / 100
        move.mate_score = None
        move.engine_score_white, move.engine_score_side_to_move = compute_engine_scores(
            eval_cp, None, side_to_move, engine_k
        )
        move.stockfish_pv = f"{move.move_uci} {source_label}-eval"


def _simple_eval_after_move(fen: str, move_uci: str) -> int:
    board = board_from_fen(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return 0
    board.push(move)
    return _simple_board_eval_cp(board)


def _simple_board_eval_cp(board: chess.Board) -> int:
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square, piece in board.piece_map().items():
        sign = 1 if piece.color == chess.WHITE else -1
        score += sign * PIECE_VALUES[piece.piece_type]
        if square in CENTER_SQUARES:
            score += sign * 18
        elif square in NEAR_CENTER_SQUARES:
            score += sign * 8

    # Mild mobility term keeps opening candidate moves from all looking identical.
    white_board = board.copy(stack=False)
    black_board = board.copy(stack=False)
    white_board.turn = chess.WHITE
    black_board.turn = chess.BLACK
    score += 2 * (white_board.legal_moves.count() - black_board.legal_moves.count())
    return int(score)


def _rank_moves(moves: list[MoveAnalysis]) -> None:
    _assign_rank(moves, "engine_score_side_to_move", "rank_engine")
    _assign_rank(moves, "human_score_side_to_move", "rank_human", min_games=1)
    _assign_rank(moves, "hybrid_score", "rank_hybrid")
    _assign_rank(moves, "popularity", "rank_popularity")


def _assign_rank(
    moves: list[MoveAnalysis],
    value_attr: str,
    rank_attr: str,
    min_games: int = 0,
) -> None:
    ranked = [
        move
        for move in moves
        if getattr(move, value_attr) is not None and move.total_games >= min_games
    ]
    ranked.sort(key=lambda move: getattr(move, value_attr), reverse=True)
    for rank, move in enumerate(ranked, start=1):
        setattr(move, rank_attr, rank)


def _first_ranked(moves: list[MoveAnalysis], rank_attr: str) -> MoveAnalysis | None:
    ranked = [move for move in moves if getattr(move, rank_attr) == 1]
    return ranked[0] if ranked else None


def build_explanation(analysis: PositionAnalysis, alpha: float) -> str:
    engine = analysis.best_engine_move
    human = analysis.best_human_move
    hybrid = analysis.best_hybrid_move
    popular = analysis.most_popular_move

    parts: list[str] = []
    if engine:
        value = _fmt(engine.engine_eval_pawns)
        parts.append(f"Stockfish prefers {engine.move_san} with an evaluation near {value} pawns.")
    if human and human.total_games > 0:
        parts.append(
            f"Historically, {human.move_san} scores best for the side to move "
            f"({human.human_score_side_to_move:.1%} across {human.total_games} games)."
        )
    if popular and popular.total_games > 0:
        parts.append(f"The most popular move is {popular.move_san}.")
    if hybrid:
        parts.append(
            f"With alpha = {alpha:.2f}, the hybrid recommendation is {hybrid.move_san}."
        )
    if not parts:
        return "No reliable move comparison could be produced for this position."
    return " ".join(parts)


def _fmt(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"{value:+.2f}"

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine

from app.core.board_utils import board_from_fen, push_uci


class StockfishUnavailable(RuntimeError):
    """Raised when Stockfish cannot be started."""


@dataclass(frozen=True)
class EngineResult:
    eval_cp: int | None
    mate_score: int | None
    best_move: str | None
    pv: str | None
    depth: int | None


class StockfishEngine:
    def __init__(self, path: str | None):
        self.path = path

    def _validate_path(self) -> str:
        if not self.path:
            raise StockfishUnavailable(
                "Stockfish is not configured. Set STOCKFISH_PATH in .env or enable demo mode."
            )
        if not Path(self.path).exists():
            raise StockfishUnavailable(
                f"Stockfish binary was not found at {self.path}. Install Stockfish and update .env."
            )
        return self.path

    def analyze_board(
        self,
        board: chess.Board,
        depth: int = 12,
        time_limit: float | None = None,
    ) -> EngineResult:
        engine_path = self._validate_path()
        limit = chess.engine.Limit(time=time_limit) if time_limit else chess.engine.Limit(depth=depth)
        try:
            with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
                info = engine.analyse(board, limit, multipv=1)
        except Exception as exc:
            raise StockfishUnavailable(f"Could not run Stockfish: {exc}") from exc

        score = info["score"].white()
        eval_cp = score.score(mate_score=None)
        mate_score = score.mate()
        pv_moves = info.get("pv", [])
        best_move = pv_moves[0].uci() if pv_moves else None
        pv = " ".join(move.uci() for move in pv_moves) if pv_moves else None
        return EngineResult(
            eval_cp=eval_cp,
            mate_score=mate_score,
            best_move=best_move,
            pv=pv,
            depth=info.get("depth"),
        )

    def analyze_after_move(
        self,
        fen: str,
        move_uci: str,
        depth: int = 12,
        time_limit: float | None = None,
    ) -> EngineResult:
        board = push_uci(fen, move_uci)
        return self.analyze_board(board, depth=depth, time_limit=time_limit)

    def best_move(self, fen: str, depth: int = 12, time_limit: float | None = None) -> str | None:
        result = self.analyze_board(board_from_fen(fen), depth=depth, time_limit=time_limit)
        return result.best_move


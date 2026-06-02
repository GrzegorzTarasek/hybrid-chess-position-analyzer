from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from app.core.board_utils import board_from_fen, uci_to_san
from app.core.config import settings


class HistoricalDataError(RuntimeError):
    """Raised when a historical data source cannot provide usable move stats."""


@dataclass(frozen=True)
class HistoricalMove:
    move_uci: str
    move_san: str
    white_wins: int
    draws: int
    black_wins: int

    @property
    def total_games(self) -> int:
        return self.white_wins + self.draws + self.black_wins


class LichessOpeningExplorer:
    def __init__(
        self,
        base_url: str = settings.lichess_explorer_base_url,
        timeout: float = settings.request_timeout_seconds,
    ):
        self.base_url = base_url
        self.timeout = timeout

    def fetch_moves(
        self,
        fen: str,
        max_moves: int = 12,
        retries: int = 2,
        delay_seconds: float = 0.8,
    ) -> list[HistoricalMove]:
        board = board_from_fen(fen)
        params = {
            "fen": fen,
            "moves": max_moves,
            "topGames": 0,
            "recentGames": 0,
            "variant": "standard",
        }

        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                response = requests.get(self.base_url, params=params, timeout=self.timeout)
                if response.status_code == 429:
                    raise HistoricalDataError("Lichess Opening Explorer rate limit was reached.")
                response.raise_for_status()
                payload = response.json()
                return self._parse_moves(payload.get("moves", []), board.fen())
            except (requests.RequestException, ValueError, HistoricalDataError) as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(delay_seconds * (attempt + 1))
        raise HistoricalDataError(f"Could not fetch Lichess explorer data: {last_error}")

    @staticmethod
    def _parse_moves(raw_moves: list[dict], fen: str) -> list[HistoricalMove]:
        parsed: list[HistoricalMove] = []
        legal_uci = {move.uci() for move in board_from_fen(fen).legal_moves}
        for item in raw_moves:
            move_uci = item.get("uci")
            if not move_uci or move_uci not in legal_uci:
                continue
            parsed.append(
                HistoricalMove(
                    move_uci=move_uci,
                    move_san=item.get("san") or uci_to_san(fen, move_uci),
                    white_wins=int(item.get("white", 0)),
                    draws=int(item.get("draws", 0)),
                    black_wins=int(item.get("black", 0)),
                )
            )
        return parsed


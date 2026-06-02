from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.board_utils import position_key


SCHEMA = """
CREATE TABLE IF NOT EXISTS position_cache (
    position_key TEXT NOT NULL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    fen TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (position_key, source)
);
"""


class SQLiteCache:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def get(self, fen: str, source: str) -> dict[str, Any] | None:
        key = position_key(fen)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM position_cache WHERE position_key = ? AND source = ?",
                (key, source),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set(self, fen: str, source: str, payload: dict[str, Any]) -> None:
        key = position_key(fen)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO position_cache(position_key, source, fetched_at, fen, payload_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(position_key, source)
                DO UPDATE SET fetched_at = excluded.fetched_at,
                              fen = excluded.fen,
                              payload_json = excluded.payload_json
                """,
                (key, source, now, fen, json.dumps(payload)),
            )


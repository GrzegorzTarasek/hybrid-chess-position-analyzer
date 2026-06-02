from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    stockfish_path: str | None = os.getenv("STOCKFISH_PATH")
    lichess_explorer_base_url: str = os.getenv(
        "LICHESS_EXPLORER_BASE_URL", "https://explorer.lichess.ovh/lichess"
    )
    cache_db_path: Path = Path(os.getenv("CACHE_DB_PATH", ".cache/hybrid_chess_cache.sqlite"))
    demo_data_path: Path = Path("examples/demo_data.json")
    request_timeout_seconds: float = 12.0


settings = Settings()


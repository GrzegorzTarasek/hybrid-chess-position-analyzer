CREATE TABLE IF NOT EXISTS position_cache (
    position_key TEXT NOT NULL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    fen TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (position_key, source)
);


# Data Sources

The application is designed to avoid downloading huge game databases. It follows this flow:

```text
user position -> public API request -> local SQLite cache -> analysis table
```

## Lichess Opening Explorer

The primary historical source is Lichess Opening Explorer. For a FEN position, the app asks for candidate moves and aggregate results:

- move UCI
- move SAN
- White wins
- draws
- Black wins
- total games

The app validates returned moves against legal moves in the current position before using them.

## Local Cache

API results are cached in SQLite under `.cache/hybrid_chess_cache.sqlite` by default. The cache stores:

- simplified position key
- source name
- fetch timestamp
- original FEN
- JSON payload

Use the UI checkbox to refresh cache when you need fresh API data.

## Lichess API

The project includes a placeholder client for future user-specific Lichess game imports.

## Chess.com PubAPI

The project includes a placeholder client for future public Chess.com archive imports.


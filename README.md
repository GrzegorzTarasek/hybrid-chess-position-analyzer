# Hybrid Chess Position Analyzer

Hybrid Chess Position Analyzer is a Streamlit application for comparing two kinds of chess move quality:

- **Engine quality**: the objective evaluation after a candidate move according to Stockfish.
- **Human or historical quality**: the expected score achieved by humans in games from public opening data.

The point is educational: the best move according to Stockfish is not always the most practical move for a human player. The app highlights engine moves, human moves, practical moves, traps, suspicious samples, difficult engine moves, and hybrid recommendations.

## Screenshots

Screenshots can be added here after running the Streamlit app locally.

## Features

- Analyze a position from FEN.
- Paste PGN and select the exact ply to analyze.
- Query Lichess Opening Explorer without downloading a full game database.
- Cache historical API responses in SQLite.
- Analyze candidate moves with a local Stockfish binary.
- Run fully offline in demo mode.
- Compare best engine, best human, best hybrid, and most popular moves.
- Export the result table as CSV.
- Visualize engine score, human score, and hybrid score with Plotly.

## Installation

```bash
git clone https://github.com/your-user/hybrid-chess-position-analyzer.git
cd hybrid-chess-position-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Stockfish Setup

Install Stockfish with your system package manager or from the official Stockfish release packages, then set the binary path in `.env`.

Linux example:

```bash
cp .env.example .env
echo "STOCKFISH_PATH=/usr/bin/stockfish" >> .env
```

Windows example:

```bash
copy .env.example .env
```

Then edit `.env`:

```text
STOCKFISH_PATH=C:\Tools\stockfish\stockfish.exe
```

If Stockfish is missing, the app shows a readable warning. You can still use the offline demo mode.

## Run

```bash
streamlit run app/streamlit_app.py
```

## Demo Mode

Demo mode uses `examples/demo_data.json` and synthetic Stockfish-like evaluations. It is useful for presentations, screenshots, and local checks without internet or Stockfish.

## Example FENs

Starting position:

```text
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

After `1. e4 e5`:

```text
rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2
```

## Methodology

For each candidate move, the app computes:

- SAN and UCI move notation.
- Historical white wins, draws, black wins, and total games.
- `human_score_white = (white_wins + 0.5 * draws) / total_games`.
- `human_score_side_to_move`, converted so higher is always better for the side to move.
- Stockfish centipawn or mate evaluation after the move.
- Normalized `engine_score_side_to_move` on a 0..1 scale.
- `hybrid_score = alpha * engine_score + (1 - alpha) * human_score`.
- `gap_human_minus_engine`.
- Rankings for engine, human, hybrid, and popularity.
- Interpretive labels.

Read more in [docs/methodology.md](docs/methodology.md).

## Data Sources

The app is designed to query public APIs and cache the result locally. It does **not** download the full Lichess Open Database.

Current source:

- Lichess Opening Explorer for move-level historical stats.

Planned extensions:

- Lichess API for user-specific game imports.
- Chess.com PubAPI for public player archives.

Read more in [docs/data_sources.md](docs/data_sources.md).

## Important Caveats

- A historically strong move is not automatically objectively best.
- A Stockfish-preferred move may be difficult for humans to play accurately.
- Small samples can produce misleading high scores.
- Online games can differ from classical over-the-board games.
- Engine evaluations depend on depth, time, and Stockfish version.

## Project Structure

```text
app/
  streamlit_app.py
  core/
  engines/
  data_sources/
  cache/
  models/
  components/
docs/
examples/
tests/
```

The Streamlit app is intentionally thin. Core chess logic, scoring, labeling, API access, engine access, and caching live in backend modules.

## Tests

```bash
pytest
```


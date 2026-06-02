from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.charts import score_comparison_chart
from app.components.explanations import move_summary, recommendation_cards
from app.components.tables import display_dataframe
from app.core.analysis import analyze_position
from app.core.board_utils import BoardError
from app.core.pgn_utils import PgnError, positions_from_pgn


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


st.set_page_config(page_title="Hybrid Chess Position Analyzer", layout="wide")

st.title("Hybrid Chess Position Analyzer")
st.caption(
    "Compare objective Stockfish evaluations with historically effective human play."
)

with st.sidebar:
    st.header("Settings")
    alpha = st.slider("Alpha", 0.0, 1.0, 0.5, 0.05)
    min_games = st.number_input("Minimum games", min_value=1, max_value=10000, value=100)
    max_moves = st.number_input("Candidate moves", min_value=1, max_value=30, value=10)
    stockfish_depth = st.number_input("Stockfish depth", min_value=1, max_value=30, value=12)
    stockfish_time_limit = st.number_input(
        "Stockfish time per move in seconds (0 = depth only)",
        min_value=0.0,
        max_value=20.0,
        value=0.0,
        step=0.1,
    )
    engine_k = st.slider("Engine normalization k", 0.2, 2.0, 0.8, 0.1)
    use_demo_data = st.checkbox("Use demo data", value=True)
    use_cache = st.checkbox("Use cache", value=True)
    refresh_cache = st.checkbox("Refresh cache", value=False)

tab_fen, tab_pgn = st.tabs(["FEN analysis", "PGN analysis"])

selected_fen = START_FEN

with tab_fen:
    selected_fen = st.text_area("FEN", value=START_FEN, height=90)

with tab_pgn:
    sample_pgn = """[Event "Sample"]
[Site "?"]
[Date "2026.06.02"]
[Round "?"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
"""
    pgn_text = st.text_area("PGN", value=sample_pgn, height=220)
    try:
        positions = positions_from_pgn(pgn_text)
        labels = [
            f"{position.ply}: {position.move_san} ({position.fen.split()[1]} to move)"
            for position in positions
        ]
        selected_index = st.slider("Analyze position after ply", 0, len(positions) - 1, 0)
        st.selectbox("Selected PGN position", labels, index=selected_index, disabled=True)
        if st.button("Use selected PGN position"):
            selected_fen = positions[selected_index].fen
            st.session_state["selected_fen"] = selected_fen
    except PgnError as exc:
        st.warning(str(exc))

if "selected_fen" in st.session_state:
    selected_fen = st.session_state["selected_fen"]

analyze = st.button("Analyze position", type="primary")

if analyze:
    try:
        analysis = analyze_position(
            fen=selected_fen,
            alpha=alpha,
            min_games=int(min_games),
            max_moves=int(max_moves),
            stockfish_depth=int(stockfish_depth),
            stockfish_time_limit=stockfish_time_limit or None,
            use_cache=use_cache,
            refresh_cache=refresh_cache,
            use_demo_data=use_demo_data,
            engine_k=engine_k,
        )
    except BoardError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Analysis could not be completed: {exc}")
        st.stop()

    for warning in analysis.warnings:
        st.warning(warning)

    st.subheader("Recommendations")
    columns = st.columns(4)
    for column, (title, move) in zip(columns, recommendation_cards(analysis)):
        column.metric(title, move.move_san if move else "No data")
        column.caption(move_summary(move))

    st.subheader("Interpretation")
    st.write(analysis.explanation)

    df = analysis.to_dataframe()
    st.subheader("Score comparison")
    if not df.empty:
        st.plotly_chart(score_comparison_chart(df), use_container_width=True)

    st.subheader("Move table")
    rendered = display_dataframe(df)
    st.dataframe(rendered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        data=rendered.to_csv(index=False).encode("utf-8"),
        file_name="hybrid_chess_analysis.csv",
        mime="text/csv",
    )
else:
    st.info("Choose a FEN or PGN position, then run the analysis. Demo data works offline.")


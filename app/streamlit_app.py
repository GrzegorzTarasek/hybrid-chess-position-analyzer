from __future__ import annotations

import sys
from pathlib import Path

import chess.svg
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.charts import score_comparison_chart
from app.components.explanations import move_summary, recommendation_cards
from app.components.tables import display_dataframe
from app.core.analysis import analyze_position
from app.core.board_utils import BoardError, board_from_fen
from app.core.live_utils import apply_move_text, legal_move_labels
from app.core.pgn_utils import PgnError, positions_from_pgn


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
SAMPLE_PGN = """[Event "Sample"]
[Site "?"]
[Date "2026.06.02"]
[Round "?"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
"""


def render_analysis(fen: str, button_key: str) -> None:
    analyze = st.button("Analyze position", type="primary", key=button_key)
    if not analyze:
        return

    try:
        analysis = analyze_position(
            fen=fen,
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
        return
    except Exception as exc:
        st.error(f"Analysis could not be completed: {exc}")
        return

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
        key=f"{button_key}_csv",
    )


def render_board(fen: str) -> None:
    board = board_from_fen(fen)
    svg = chess.svg.board(board=board, size=420)
    components.html(svg, height=440)


st.set_page_config(page_title="Hybrid Chess Position Analyzer", layout="wide")

st.title("Hybrid Chess Position Analyzer")
st.caption("Analyze a pasted game or keep a live position and compare engine vs human results.")

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

mode = st.radio("Tryb", ["Analiza partii", "Analiza na zywo"], horizontal=True)

if mode == "Analiza partii":
    st.subheader("Analiza partii")
    uploaded_pgn = st.file_uploader("Wgraj plik PGN", type=["pgn"])
    uploaded_text = ""
    if uploaded_pgn is not None:
        uploaded_text = uploaded_pgn.read().decode("utf-8", errors="replace")

    pgn_text = st.text_area("PGN", value=uploaded_text or SAMPLE_PGN, height=260)
    try:
        positions = positions_from_pgn(pgn_text)
        labels = [
            f"{position.ply}: {position.move_san} ({position.fen.split()[1]} to move)"
            for position in positions
        ]
        selected_index = st.slider("Analizuj pozycje po polruchu", 0, len(positions) - 1, 0)
        st.selectbox("Wybrana pozycja", labels, index=selected_index, disabled=True)
        selected_fen = positions[selected_index].fen
        st.text_area("Wybrany FEN", value=selected_fen, height=80, disabled=True)
        render_analysis(selected_fen, "analyze_game")
    except PgnError as exc:
        st.warning(str(exc))

if mode == "Analiza na zywo":
    st.subheader("Analiza na zywo")
    st.caption("Buduj pozycje ruch po ruchu, wklej FEN albo analizuj aktualna szachownice.")

    if "live_fen" not in st.session_state:
        st.session_state["live_fen"] = START_FEN
    if "live_history" not in st.session_state:
        st.session_state["live_history"] = []
    if "live_moves" not in st.session_state:
        st.session_state["live_moves"] = []

    left, right = st.columns([1, 1])
    with left:
        current_fen = st.text_area("Aktualny FEN", value=st.session_state["live_fen"], height=90)
        action_cols = st.columns(3)
        if action_cols[0].button("Ustaw FEN"):
            try:
                board_from_fen(current_fen)
                st.session_state["live_fen"] = current_fen
                st.session_state["live_history"] = []
                st.session_state["live_moves"] = []
                st.rerun()
            except BoardError as exc:
                st.error(str(exc))

        if action_cols[1].button("Cofnij"):
            if st.session_state["live_history"]:
                st.session_state["live_fen"] = st.session_state["live_history"].pop()
                if st.session_state["live_moves"]:
                    st.session_state["live_moves"].pop()
                st.rerun()

        if action_cols[2].button("Reset"):
            st.session_state["live_fen"] = START_FEN
            st.session_state["live_history"] = []
            st.session_state["live_moves"] = []
            st.rerun()

        move_text = st.text_input("Ruch (SAN albo UCI)", placeholder="e4, Nf3, e2e4")
        legal_options = legal_move_labels(st.session_state["live_fen"])
        selected_move = st.selectbox("Albo wybierz legalny ruch", [""] + legal_options)
        move_to_play = move_text or selected_move.split(" (", maxsplit=1)[0]

        if st.button("Wykonaj ruch"):
            try:
                previous_fen = st.session_state["live_fen"]
                next_fen, san, uci = apply_move_text(previous_fen, move_to_play)
                st.session_state["live_history"].append(previous_fen)
                st.session_state["live_moves"].append(f"{san} ({uci})")
                st.session_state["live_fen"] = next_fen
                st.rerun()
            except BoardError as exc:
                st.error(str(exc))

        if st.session_state["live_moves"]:
            st.write("Rozegrane ruchy:")
            st.write(" ".join(st.session_state["live_moves"]))

    with right:
        render_board(st.session_state["live_fen"])

    render_analysis(st.session_state["live_fen"], "analyze_live")

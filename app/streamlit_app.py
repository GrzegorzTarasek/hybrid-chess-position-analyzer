from __future__ import annotations

import sys
from pathlib import Path

import chess.svg
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.charts import score_comparison_chart
from app.components.explanations import move_summary
from app.components.interactive_board import interactive_board
from app.components.tables import display_dataframe
from app.core.analysis import analyze_position
from app.core.board_utils import BoardError, board_from_fen, legal_moves_uci
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


@st.cache_data(show_spinner=False, ttl=180)
def cached_analyze_position(
    fen: str,
    alpha_value: float,
    min_games_value: int,
    max_moves_value: int,
    stockfish_depth_value: int,
    stockfish_time_limit_value: float | None,
    use_cache_value: bool,
    refresh_cache_value: bool,
    use_demo_data_value: bool,
    engine_k_value: float,
):
    return analyze_position(
        fen=fen,
        alpha=alpha_value,
        min_games=min_games_value,
        max_moves=max_moves_value,
        stockfish_depth=stockfish_depth_value,
        stockfish_time_limit=stockfish_time_limit_value,
        use_cache=use_cache_value,
        refresh_cache=refresh_cache_value,
        use_demo_data=use_demo_data_value,
        engine_k=engine_k_value,
    )


def render_analysis(fen: str, analysis_key: str) -> None:
    try:
        with st.spinner("Analizuje aktualna pozycje..."):
            analysis = cached_analyze_position(
                fen=fen,
                alpha_value=alpha,
                min_games_value=int(min_games),
                max_moves_value=int(max_moves),
                stockfish_depth_value=int(stockfish_depth),
                stockfish_time_limit_value=stockfish_time_limit or None,
                use_cache_value=use_cache,
                refresh_cache_value=refresh_cache,
                use_demo_data_value=use_demo_data,
                engine_k_value=engine_k,
            )
    except BoardError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Analysis could not be completed: {exc}")
        return

    for warning in analysis.warnings:
        st.warning(warning)

    st.caption("Analiza odswieza sie automatycznie po zmianie pozycji.")
    render_ranked_move_columns(analysis)

    st.subheader("Kompromis i popularnosc")
    columns = st.columns(2)
    for column, (title, move) in zip(
        columns,
        [
            ("Best hybrid move", analysis.best_hybrid_move),
            ("Most popular move", analysis.most_popular_move),
        ],
    ):
        column.metric(title, move.move_san if move else "No data")
        column.caption(move_summary(move))

    st.subheader("Interpretation")
    st.write(analysis.explanation)

    df = analysis.to_dataframe()
    st.subheader("Score comparison")
    if not df.empty:
        st.plotly_chart(score_comparison_chart(df), width="stretch")

    st.subheader("Move table")
    rendered = display_dataframe(df)
    st.dataframe(rendered, width="stretch", hide_index=True)
    st.download_button(
        "Download CSV",
        data=rendered.to_csv(index=False).encode("utf-8"),
        file_name="hybrid_chess_analysis.csv",
        mime="text/csv",
        key=f"{analysis_key}_csv",
    )


def render_ranked_move_columns(analysis) -> None:
    st.subheader("Ruchy silnikowe i ludzkie")
    engine_col, human_col = st.columns(2)
    with engine_col:
        st.markdown("#### Ruchy silnikowe")
        for move in sorted(
            [move for move in analysis.moves if move.rank_engine is not None],
            key=lambda item: item.rank_engine,
        )[:6]:
            score = _format_score(move.engine_score_side_to_move)
            eval_text = _format_eval(move.engine_eval_pawns, move.mate_score)
            st.markdown(f"**{move.rank_engine}. {move.move_san}**")
            st.caption(f"{eval_text} | engine score {score} | {move.label}")
        if not any(move.rank_engine is not None for move in analysis.moves):
            st.info("Brak danych silnikowych dla tej pozycji.")

    with human_col:
        st.markdown("#### Ruchy ludzkie")
        for move in sorted(
            [move for move in analysis.moves if move.rank_human is not None],
            key=lambda item: item.rank_human,
        )[:6]:
            score = _format_score(move.human_score_side_to_move)
            popularity_text = _format_score(move.popularity)
            st.markdown(f"**{move.rank_human}. {move.move_san}**")
            st.caption(
                f"human score {score} | popularnosc {popularity_text} | "
                f"{move.total_games} partii | {move.label}"
            )
        if not any(move.rank_human is not None for move in analysis.moves):
            st.info("Brak danych historycznych dla tej pozycji.")


def _format_score(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def _format_eval(eval_pawns: float | None, mate_score: int | None) -> str:
    if mate_score is not None:
        return f"mate {mate_score:+d}"
    if eval_pawns is None:
        return "eval -"
    return f"eval {eval_pawns:+.2f}"


def render_board(fen: str, last_move_uci: str | None = None, size: int = 520) -> None:
    board = board_from_fen(fen)
    last_move = None
    if last_move_uci:
        try:
            last_move = chess.Move.from_uci(last_move_uci)
        except ValueError:
            last_move = None
    check_square = board.king(board.turn) if board.is_check() else None
    svg = chess.svg.board(
        board=board,
        size=size,
        lastmove=last_move,
        check=check_square,
        colors={
            "square light": "#ece9d5",
            "square dark": "#6f8f4e",
            "square light lastmove": "#f0d66c",
            "square dark lastmove": "#b8c75a",
            "margin": "#2b2f36",
            "coord": "#d7dac5",
            "inner border": "#2b2f36",
            "outer border": "#2b2f36",
        },
    )
    html = f"""
    <style>
      .board-wrap {{
        width: {size}px;
        max-width: 100%;
        margin: 0 auto;
        border: 1px solid #2b2f36;
        border-radius: 6px;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.28);
        background: #2b2f36;
        overflow: hidden;
      }}
      .board-wrap svg {{
        display: block;
        width: 100%;
        height: auto;
      }}
    </style>
    <div class="board-wrap">{svg}</div>
    """
    st.html(html)


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

mode = st.radio("Tryb", ["Przesuwaj figury", "Wgraj partie"], horizontal=True)

if mode == "Wgraj partie":
    st.subheader("Wgraj partie")
    board_col, controls_col = st.columns([1.05, 1])
    with controls_col:
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
            selected_position = positions[selected_index]
            selected_fen = selected_position.fen
            st.text_area("Wybrany FEN", value=selected_fen, height=80, disabled=True)
        except PgnError as exc:
            selected_position = None
            selected_fen = None
            st.warning(str(exc))

    with board_col:
        if selected_fen:
            render_board(selected_fen, selected_position.move_uci if selected_position else None)

    if selected_fen:
        render_analysis(selected_fen, "analyze_game")

if mode == "Przesuwaj figury":
    st.subheader("Przesuwaj figury")
    st.caption("Przesun figure na szachownicy, a aplikacja zaktualizuje pozycje i pozwoli ja analizowac.")

    if "live_fen" not in st.session_state:
        st.session_state["live_fen"] = START_FEN
    if "live_history" not in st.session_state:
        st.session_state["live_history"] = []
    if "live_moves" not in st.session_state:
        st.session_state["live_moves"] = []
    if "live_move_uci_history" not in st.session_state:
        st.session_state["live_move_uci_history"] = []
    if "last_processed_drag_move" not in st.session_state:
        st.session_state["last_processed_drag_move"] = None

    board_col, side_col = st.columns([1.15, 1])
    with side_col:
        current_fen = st.text_area("Aktualny FEN", value=st.session_state["live_fen"], height=90)
        action_cols = st.columns(3)
        if action_cols[0].button("Ustaw FEN"):
            try:
                board_from_fen(current_fen)
                st.session_state["live_fen"] = current_fen
                st.session_state["live_history"] = []
                st.session_state["live_moves"] = []
                st.session_state["live_move_uci_history"] = []
                st.rerun()
            except BoardError as exc:
                st.error(str(exc))

        if action_cols[1].button("Cofnij"):
            if st.session_state["live_history"]:
                st.session_state["live_fen"] = st.session_state["live_history"].pop()
                if st.session_state["live_moves"]:
                    st.session_state["live_moves"].pop()
                if st.session_state["live_move_uci_history"]:
                    st.session_state["live_move_uci_history"].pop()
                st.rerun()

        if action_cols[2].button("Reset"):
            st.session_state["live_fen"] = START_FEN
            st.session_state["live_history"] = []
            st.session_state["live_moves"] = []
            st.session_state["live_move_uci_history"] = []
            st.rerun()

        with st.expander("Awaryjnie wpisz ruch"):
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
                    st.session_state["live_move_uci_history"].append(uci)
                    st.session_state["live_fen"] = next_fen
                    st.rerun()
                except BoardError as exc:
                    st.error(str(exc))

        if st.session_state["live_moves"]:
            st.write("Rozegrane ruchy:")
            st.write(" ".join(st.session_state["live_moves"]))

    with board_col:
        last_move_uci = (
            st.session_state["live_move_uci_history"][-1]
            if st.session_state["live_move_uci_history"]
            else None
        )
        board_result = interactive_board(
            fen=st.session_state["live_fen"],
            legal_moves=legal_moves_uci(st.session_state["live_fen"]),
            last_move=last_move_uci,
            key="live_drag_board",
        )
        dragged_move = getattr(board_result, "move", None)
        if dragged_move and dragged_move != st.session_state["last_processed_drag_move"]:
            try:
                previous_fen = st.session_state["live_fen"]
                next_fen, san, uci = apply_move_text(previous_fen, dragged_move)
                st.session_state["last_processed_drag_move"] = dragged_move
                st.session_state["live_history"].append(previous_fen)
                st.session_state["live_moves"].append(f"{san} ({uci})")
                st.session_state["live_move_uci_history"].append(uci)
                st.session_state["live_fen"] = next_fen
                st.rerun()
            except BoardError as exc:
                st.error(str(exc))

    render_analysis(st.session_state["live_fen"], "analyze_live")

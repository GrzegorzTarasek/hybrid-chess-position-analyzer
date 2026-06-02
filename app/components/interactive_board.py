from __future__ import annotations

import streamlit as st


HTML = """
<div class="chess-shell">
  <div id="board" class="board"></div>
  <div id="status" class="status"></div>
</div>
"""

CSS = """
.chess-shell {
  width: min(100%, 544px);
  margin: 0 auto;
}
.board {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  width: min(100%, 544px);
  aspect-ratio: 1 / 1;
  border: 1px solid #2b2f36;
  border-radius: 6px;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.28);
  background: #2b2f36;
  overflow: hidden;
  user-select: none;
  touch-action: none;
}
.square {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1 / 1;
  font-size: clamp(30px, 7vw, 54px);
  line-height: 1;
  cursor: pointer;
}
.light { background: #ece9d5; }
.dark { background: #6f8f4e; }
.square.selected::after {
  content: "";
  position: absolute;
  inset: 6%;
  border: 3px solid #ffcc33;
  border-radius: 3px;
  pointer-events: none;
}
.square.lastmove { background: #f0d66c; }
.dark.lastmove { background: #b8c75a; }
.square.legal::before {
  content: "";
  position: absolute;
  width: 24%;
  height: 24%;
  border-radius: 50%;
  background: rgba(22, 27, 34, 0.28);
}
.piece {
  z-index: 1;
  cursor: grab;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 86%;
  height: 86%;
  font-family: "DejaVu Sans", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
  font-size: 0.82em;
  font-weight: 700;
  transform: translateY(-1px);
}
.piece:active { cursor: grabbing; }
.white-piece {
  color: #fbfaf2;
  text-shadow:
    0 1px 1px rgba(0, 0, 0, 0.52),
    0 0 1px rgba(0, 0, 0, 0.75);
}
.black-piece {
  color: #23262b;
  text-shadow:
    0 1px 0 rgba(255, 255, 255, 0.45),
    0 0 1px rgba(255, 255, 255, 0.6);
}
.status {
  min-height: 28px;
  padding-top: 8px;
  color: #9ca3af;
  font: 14px/1.4 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
"""

JS = """
const PIECES = {
  P: "♙", N: "♘", B: "♗", R: "♖", Q: "♕", K: "♔",
  p: "♟", n: "♞", b: "♝", r: "♜", q: "♛", k: "♚",
};

function fenToPieces(fen) {
  const board = {};
  const placement = fen.split(" ")[0] || "";
  const ranks = placement.split("/");
  for (let rankIndex = 0; rankIndex < 8; rankIndex++) {
    let fileIndex = 0;
    for (const ch of ranks[rankIndex] || "") {
      if (/\\d/.test(ch)) {
        fileIndex += Number(ch);
      } else {
        const file = "abcdefgh"[fileIndex];
        const rank = String(8 - rankIndex);
        board[file + rank] = ch;
        fileIndex += 1;
      }
    }
  }
  return board;
}

function squaresForOrientation(orientation) {
  const files = orientation === "black" ? "hgfedcba" : "abcdefgh";
  const ranks = orientation === "black"
    ? ["1", "2", "3", "4", "5", "6", "7", "8"]
    : ["8", "7", "6", "5", "4", "3", "2", "1"];
  const squares = [];
  for (const rank of ranks) {
    for (const file of files) squares.push(file + rank);
  }
  return squares;
}

function findMove(legalMoves, source, target) {
  const prefix = source + target;
  const matches = legalMoves.filter((move) => move.startsWith(prefix));
  if (matches.length === 0) return null;
  return matches.find((move) => move.endsWith("q")) || matches[0];
}

export default function(component) {
  const { data, parentElement, setTriggerValue } = component;
  const boardElement = parentElement.querySelector("#board");
  const statusElement = parentElement.querySelector("#status");
  const fen = data.fen;
  const legalMoves = data.legal_moves || [];
  const lastMove = data.last_move || "";
  const orientation = data.orientation || "white";
  const pieces = fenToPieces(fen);
  const squares = squaresForOrientation(orientation);
  let selected = null;

  function legalTargets(source) {
    return legalMoves
      .filter((move) => move.slice(0, 2) === source)
      .map((move) => move.slice(2, 4));
  }

  function tryMove(source, target) {
    const move = findMove(legalMoves, source, target);
    if (move) {
      setTriggerValue("move", move);
      statusElement.textContent = "";
      return true;
    }
    statusElement.textContent = "Nielegalny ruch.";
    return false;
  }

  function render(selectedSquare = null) {
    boardElement.innerHTML = "";
    const targets = selectedSquare ? legalTargets(selectedSquare) : [];
    for (const square of squares) {
      const fileIndex = "abcdefgh".indexOf(square[0]);
      const rankIndex = Number(square[1]) - 1;
      const element = document.createElement("div");
      element.className = `square ${(fileIndex + rankIndex) % 2 === 0 ? "dark" : "light"}`;
      element.dataset.square = square;
      if (selectedSquare === square) element.classList.add("selected");
      if (targets.includes(square)) element.classList.add("legal");
      if (lastMove && (lastMove.slice(0, 2) === square || lastMove.slice(2, 4) === square)) {
        element.classList.add("lastmove");
      }

      const piece = pieces[square];
      if (piece) {
        const pieceElement = document.createElement("span");
        pieceElement.className = `piece ${piece === piece.toUpperCase() ? "white-piece" : "black-piece"}`;
        pieceElement.textContent = PIECES[piece] || piece;
        pieceElement.draggable = true;
        pieceElement.dataset.square = square;
        pieceElement.addEventListener("dragstart", (event) => {
          event.dataTransfer.setData("text/plain", square);
          selected = square;
          render(selected);
        });
        element.appendChild(pieceElement);
      }

      element.addEventListener("dragover", (event) => event.preventDefault());
      element.addEventListener("drop", (event) => {
        event.preventDefault();
        const source = event.dataTransfer.getData("text/plain");
        selected = null;
        if (!tryMove(source, square)) render(null);
      });
      element.addEventListener("click", () => {
        if (selected) {
          const source = selected;
          selected = null;
          if (!tryMove(source, square)) render(null);
          return;
        }
        if (pieces[square]) {
          selected = square;
          render(selected);
        }
      });
      boardElement.appendChild(element);
    }
  }

  render(null);
}
"""


_interactive_board = st.components.v2.component(
    "interactive_chess_board",
    html=HTML,
    css=CSS,
    js=JS,
)


def interactive_board(
    *,
    fen: str,
    legal_moves: list[str],
    last_move: str | None = None,
    orientation: str = "white",
    key: str = "interactive_chess_board",
):
    return _interactive_board(
        data={
            "fen": fen,
            "legal_moves": legal_moves,
            "last_move": last_move,
            "orientation": orientation,
        },
        height=600,
        key=key,
        on_move_change=lambda: None,
    )

# Methodology

Hybrid Chess Position Analyzer compares two different ideas of chess move quality: objective evaluation and practical human performance.

## Engine Evaluation

The engine score comes from Stockfish. For each candidate move, the app makes the move on the board and asks Stockfish to evaluate the resulting position. Stockfish can return either a centipawn score or a mate score.

Centipawns are converted into pawns:

```text
eval_pawns = eval_cp / 100
```

The pawn score is normalized to a 0..1 scale with a logistic function:

```text
engine_score_white = 1 / (1 + exp(-k * eval_pawns))
```

The default `k` is `0.8`. A score of 0.5 is roughly equal. Scores above 0.5 are better for White. Scores below 0.5 are better for Black.

Mate scores are mapped close to 1.0 for White mates and close to 0.0 for Black mates.

## Side-to-Move Conversion

Historical and engine scores are both converted so that higher always means better for the side making the move.

If White moves:

```text
score_side_to_move = score_white
```

If Black moves:

```text
score_side_to_move = 1 - score_white
```

This makes rankings intuitive for either side.

## Historical Evaluation

Historical evaluation uses aggregate game results after each move:

```text
human_score_white = (white_wins + 0.5 * draws) / total_games
```

Where:

```text
total_games = white_wins + draws + black_wins
```

This score describes what happened in human games, not what is objectively correct.

## Hybrid Score

The final hybrid score is:

```text
hybrid_score = alpha * engine_score + (1 - alpha) * human_score
```

Interpretation:

- `alpha = 1.0`: engine-only recommendation.
- `alpha = 0.0`: historical-only recommendation.
- `alpha = 0.5`: balanced recommendation.

## Gap

The app computes:

```text
gap_human_minus_engine = human_score_side_to_move - engine_score_side_to_move
```

A positive gap suggests that a move performed better in practice than its engine-normalized score would suggest. A negative gap suggests that the engine likes the move more than historical human results do.

## Minimum Game Threshold

Small samples can lie. A move with 10 games and an 80% score should not be trusted like a move with 50,000 games and a 58% score. The app marks low-sample moves as `Statistically suspicious` when `total_games < min_games`.

## Why Engine-Best Can Be Hard

Stockfish may prefer a move because it works after a precise continuation. Human players may not find that continuation consistently. Such moves can be labeled `Difficult engine move`.

## Why Human-Best Can Be Objectively Worse

Some moves score well because opponents often respond poorly. These may be practical, but not objectively best. If the human result is high while the engine score is low or average, the move can be labeled `Trap move`.


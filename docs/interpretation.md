# Interpretation Guide

## Engine Move

The top-ranked Stockfish move. It is objectively promising at the configured depth or time, but it may not be the most practical move.

## Human Move

The move with the best historical expected score for the side to move, provided it has enough games.

## Practical Move

A move that is not necessarily the top engine move but has strong human results and acceptable objective evaluation.

## Universal Move

A move that is strong both objectively and historically.

## Trap Move

A move that may not be objectively best but scores well in practice, often because opponents make mistakes.

## Risky Move

A move with weak objective and historical indicators.

## Statistically Suspicious

A move with too few games to treat the historical score as reliable.

## Difficult Engine Move

A move that the engine likes but humans historically do not score well with. It may require precise follow-up play.


# Koivisto

Ideas only. In so far: the training pipeline and the leftover classical score. Still waiting: null-move and verification, endgame eval, threading, history heuristics, singular extensions.

## Net training pipeline

Importance: breakthrough. See B6.

What Koivisto publishes. Self-play, then a filter, then two labels on each kept position: a fixed-depth search score and the game outcome. The trainer shuffles across files, turns both labels into win chances from the side to move, and mixes them. Version 9 says most of the gain since version 8 was data: mixing in another engine’s data was about +19 Elo at 40 seconds and about +20 at 8 seconds, and more data was about +30 at 8 seconds. A wrong filter left a net about 40 Elo over an old hand-crafted master. After the filter was corrected, the retrained net was about 104, and another engine’s positions on the same tuner were about 150. Those matches are against the old evaluation, so they are not a paired filter test. The rule that survived was not in the sources opened. By October 2025 the other engine had cycled the shared positions out.

Where Stockfish is weaker. It is not. Its published chain has more specified stages: an opening book, deliberate departures from the best move, converted and rescored games from Leela, and a capture filter that was later narrowed to keep some losing captures. Leela-derived labels were described as better than self-play, and as worse when used alone than when Stockfish data came first. The gap is that good sets are still chosen empirically. Koivisto’s clean measurement is the value of a second engine’s data, not a missing stage.

Ideas. The matched-count exclusion bakeoff is B6. Host labels on foreign positions are D8. The disagreement-conditioned mix is D9, which is a mix weight, not the residual in B2.

## Leftover hand-crafted eval

Importance: routine. Stockfish is ahead. Its classical term list was removed. What remains is a wrapper: material agreement, optimism, a material scale that counts pawns, and a fifty-move damp.

What Koivisto still applies. The network output times one phase multiplier, from 1.5 at the start to 1.15 when the counted material is gone. Pawns count. A knight counts slightly more than a bishop. There is no second score for mobility, pawn weaknesses, rook files, the bishop pair, shelter, or a flat tempo. No published match for the 1.5 / 1.15 pair was found.

Ideas. The phase multiplier is the second arm of E3, not a stack on B4. Shrinking the positional surplus when material disagrees is P14. Knocking out one classical family at a time is P15. The Forge map says those families still exist in `src/eval.cpp` on the later tree. The 5.31 zip is not that tree.

## Sources

https://github.com/Luecx/Koivisto/releases/tag/v5.0
https://github.com/Luecx/Koivisto/releases/tag/v6.0
https://github.com/Luecx/Koivisto/releases/tag/v9.0
https://github.com/Luecx/Koivisto/wiki/Evaluation
https://github.com/Luecx/Koivisto/blob/master/src_files/board.cpp
https://github.com/official-stockfish/Stockfish/pull/4324
https://github.com/official-stockfish/Stockfish/pull/5090
https://github.com/official-stockfish/Stockfish/blob/master/src/evaluate.cpp
https://wiki.chessdom.org/Berserk_questionnaire_20251013

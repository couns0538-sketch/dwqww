# Berserk

Ideas only. All seven departments are in.

## Short-time-control strength

Importance: breakthrough. See B7. Stockfish is ahead at every short control opened. The lead over Berserk 14 is largest at about 8 seconds and smaller at blitz and at two minutes. The clock stop that refuses an unfinished iteration is B7. Banking a stable bullet move is T11. Overhead against a short increment is the same measurement as T7.

## Data generation

Importance: breakthrough. See B12. The published habit is to train on games this engine just played, then drop other engines’ games. Current main does not write a training file. The generator rejects openings whose finished search is already past about six displayed pawns, and it finishes the iteration before writing the score. Finished-iteration labels are D11. The wide gate, tested alone, is D12.

## Search reductions

Importance: breakthrough. See B11. The base table is the usual log of depth times log of move index. The distinctive piece is how much of a withheld depth the second search gets back when the reduced score beats alpha. Stockfish is ahead on the small stacked terms. The scaled verification is B11. The off-PV worsening shave is S37. Signed correction on quiet reductions is S38.

## Aggressive pruning

Importance: breakthrough. See B13. The edge is ending a quiet list, not trimming depth. A bad history or a tight static cushion can drop every later quiet, including on PV nodes. Stockfish’s quiet futility cushion is much wider and drops only that move. Whole-node drops are a place Stockfish already drops more. Sibling-backed extinction is B13. The elite-history static drop is S44. The exchange-filtered null veto is S45.

## Move ordering

Importance: routine. Stockfish is ahead on most quiet ordering. Berserk’s edge is threat context: four from-to buckets for origin and destination inside the opponent’s attack map, plus a flat bonus for leaving a cheaper-piece attack. Killers as their own stage were measured expendable. The cheaper-attacker history, with the constant bonus removed, is S28, beside B8. Capture safety inside a frozen exchange gate is S29. Full scores on moves that answer check are S30.

## High-level net structure

Importance: routine. Stockfish is ahead on the public architecture record. The useful difference is a product that collapses two perspectives so the later tower stays narrow, against concatenation with a residual from the wide map.

What Berserk publishes. One incremental map carries king-location buckets and a larger family of attack relations. A pairwise collapse keeps the next layer one perspective wide. The tower squeezes, expands briefly, and ends in one score. The head follows how many pieces remain. A 2022 note called the net small and fast and said extra depth had not yet paid. A finer per-square king index was called essentially equal to coarser mirrored buckets on a stale test, with a gap under 1 Elo.

Where Stockfish is weaker. Not on the pages opened. Attack relations, pawn-pair geometry, and towers chosen by queen presence and pawn distribution are already in the later Stockfish architecture notes. Product pooling is described there as suitable and uncommon, and as less accurate when the first map is held fixed.

Ideas. The product against a residual wide path is N3. Separate maps that meet after the nonlinearity are N4. A joint expert when the heavy pieces are gone is N5.

## Eval scaling

Importance: routine. Stockfish is further along on agreement between material and the net, and on a material term that counts pawns. The narrower weakness is the fifty-move shrink stored under a key that ignores the counter.

What Berserk does. The score search sees is a plain function of the network output, the mix of non-pawn pieces, and the side to move. A phase that ignores pawns and kings stretches the raw score up to one and a half times with a full set of pieces. A side-to-move bias follows that phase and is absent when the pieces are gone. The fifty-move shrink is applied from the counter on the board being searched, not baked into the stored score. The position hash does not include the counter.

Where Stockfish is weaker. Only at that stored-score mismatch. It still stretches with material, shrinks with the fifty-move counter, and pushes or pulls the score when a cheap material count agrees or disagrees with the net. It applies the shrink inside the evaluation it writes to the table, under a key that omits the counter. No match measuring that Elo was opened.

Ideas. The shuffle shrink at the node is E2. The heavy-piece residual, which also covers Koivisto’s pawn-counted multiplier as a second arm, is E3. A phase bias without an agreement gate was considered and left inside E3’s comparison rather than as a third rescale on top of B4.

## Sources

https://github.com/jhonnold/berserk
https://raw.githubusercontent.com/jhonnold/berserk/main/src/eval.c
https://raw.githubusercontent.com/jhonnold/berserk/main/src/search.c
https://raw.githubusercontent.com/jhonnold/berserk/main/src/zobrist.c
https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html
https://github.com/official-stockfish/Stockfish/commit/1dbd2a1ad548b3ca676f7da949e1a998c64b836b
https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/evaluate.cpp
https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/position.cpp

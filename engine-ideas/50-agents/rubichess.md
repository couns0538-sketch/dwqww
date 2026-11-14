# RubiChess

Ideas only. All seven departments are in.

## Thread scaling

Importance: breakthrough. See B9. Lazy SMP, one transposition table, and depth schedules that repeat from thread 17. The played move is the highest score among threads at least as deep as the leader. There is no summed vote. Stockfish is stronger on the evidence opened: it votes, and a shared correction history gained strength while costing speed until it was partitioned. Published scaling is about 82 percent of eightfold time at 8 threads, and about half the nodes wasted at 64 threads on a long budget. Auditors for the surplus threads are B9. Unique depth phases are S39. A quiet merge of correction history between iterations is S40.

## Late-move reductions

Importance: routine. Stockfish is ahead. RubiChess uses whole-ply steps, eases the first tries until a few cutoffs appear, and restores the full omitted depth if the shallow score beats alpha. That full restore is one arm of B11, not a new idea. Front-loaded cutoff steps are S34. Fuller replies only to a late parent are S35. A root quiet shift on the aspiration re-search is S36.

## Aspiration windows

Importance: routine. Stockfish is ahead. Its window follows an effort-weighted running average, and a fail is fail-soft. RubiChess stays full-width until one search past depth 4 has landed inside the bounds, then uses a half-width of 15, and caps the margin at the win score. Stockfish has no ceiling. That cap is the guard after an overflowing margin forced a revert. The capped reopen is S23. Variance-sized overlap is S24. Arming the window only after one resolved score is S25.

## Net integration

Importance: routine. The network is refused when an endgame material-plus-square total is at or above 760, and the returned value is scaled by officers only. Stockfish always calls the network out of check and only shrinks a disagreeing score toward zero, so a wrong sign stays a wrong sign. Sign-aware override past a high bar is P19. Skipping the net on known dead material is P20. An officer-only gain that ignores pawns is the second arm of E3, not a new scale on top of B4.

## Eval tapering

Importance: breakthrough. See B4.

What RubiChess still blends. In the hand-crafted evaluator, each term has a middlegame half and an endgame half. Phase comes only from non-pawn pieces. The mix never quite reaches a pure endgame. Drawish material signatures and a complexity nudge live in the endgame half, so they fade in as pieces come off. The default network path does not blend two opinions. It multiplies one number by a shallow function of the same non-pawn weight, and falls back to the two-opinion mix only when the endgame half of the piece-square total is already very one-sided.

Where Stockfish is weaker. At blending two phase opinions, because that blend is gone. On rescaling a single score, Stockfish is ahead of the default network path: agreement with a material count stretches a winning score, disagreement pulls it in, total material counts pawns, and the fifty-move counter damps the result. RubiChess’s remaining edge is the hand-crafted mix.

Ideas. The conflict-gated steep blend is B4. The attacker clock and the pawn clock are P17. The pawn-lock phase shift is P18.

## Incremental updates

Importance: routine. Stockfish is ahead on the expensive king move. RubiChess is ahead on long dirty chains.

What RubiChess does. One accumulator per ply and per side. Making a move records which pieces and threat relations changed and marks the ply dirty. Unmaking does not subtract weights back out. The builder walks toward the root and stops at a ply already built, a king move, or a threat-change budget. For a real evaluation it builds the first missing ply, then jumps to the current ply and applies every change in between as one add and subtract. A speculative build, once a node has committed to searching moves, writes only the current ply. A full rebuild diffs the current placement against a cache per side and king square.

Where Stockfish differs. It also refuses to repair the accumulator on unmake, and it can avoid a ground-up rebuild on a king move that stays in the same four-file half when enough pieces remain. It writes every ply from the last usable one through the current one. It does not build early just because the node is about to try every move.

Ideas. The commit-point build is U1. The two-anchor fused chain is U2. Choosing the cheaper of the fused delta and the king-square cache is U3. These apply to the incremental net. The v4 net that rebuilds both accumulators every eval is a different path. See [forge-fit.md](forge-fit.md).

## Probcut-style cuts

Importance: routine. Stockfish is not weaker here. The cushions are about the same once scaled by pawn value. Stockfish is stricter: it skips the search proof in check, skips when a table value is already below the raised bound, and returns a value with the cushion removed. The thinner spot is the proof. The floor is shallower, it applies on principal-variation nodes, and a high static score shortens both the cushion and the witness until quiescence of one capture is enough to cut.

What RubiChess trusts. A real reduced search, not quiescence alone, must clear a raised bound. The proof runs only off the principal variation, only once depth reaches 7, and only when beta is short of mate. The cushion is about 1.08 pawns. A tactical move whose static exchange covers the gap gets a quiescence reject first. If quiescence hits, a search four plies shallower must hit too. The parent receives the witness score itself.

Ideas. The two-regime witness is S20. The honest table entry is S21. The one-ply cooldown after a capture or a check is S22.

## Sources

https://raw.githubusercontent.com/Matthies/RubiChess/master/src/eval.cpp
https://raw.githubusercontent.com/Matthies/RubiChess/master/src/search.cpp
https://github.com/Matthies/RubiChess/blob/263f15d7960eb32b45ce1a06fbe64d750729803f/src/nnue.cpp
https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/evaluate.cpp
https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/search.cpp
https://github.com/official-stockfish/Stockfish/commit/e18619d07802882136b583a01e56791b61abede6
https://www.chessprogramming.org/Tapered_Eval
https://chessprogramming.org/ProbCut

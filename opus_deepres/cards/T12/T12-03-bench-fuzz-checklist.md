# T12-03-bench-fuzz-checklist: bench-signature + fuzz proof that lets a bit-exact speed change skip the SPRT
Status: COMPLETE

## Source
OpenBench wiki Requirements-For-Public-Engines (bench prints nodes + nps; "All engines must be deterministic across
multiple runs, on all supported machines"; every client must get "the same nodes result every time"; AVX vs AVX2 can
differ). Fishtest wiki Creating-my-first-test ("Bench: N" / "No functional change"; a speed-up too small to verify on
fishtest but verifiable from the assembly goes straight to a PR). Stockfish commits a06e7004c1 (CI suites that assert
engine output) and 73018a0337 (pathological positions where the search explodes). Own: forge-ltopgo-pgo (pins, 12k FENs).

## Licence
OpenBench @230ed46e47 GPL-3.0, Stockfish @5c617e579c GPL-3.0, fishtest @5a8a229a52 (no root LICENSE file found):
ideas only. Wiki pages and commit messages were read, no source or test file. The checklist is own work.

## Mechanism
A change is node-identical when every search output matches at every level below, not just the bench total. Forge's
bench (src/uci.cpp:377-408) sums nodes over 8 FENs at one depth, with a 16 MB TT cleared before each FEN, and prints
only the total. So it never checks a warm TT, other Hash sizes, per-position bestmove / score / PV, Threads, or rare
move types.
Checklist (Threads=1, `go depth` / `go nodes` only, never time limits; A = lock or parent, B = change):
1. Build: kit pc1 = pc2 sha256 for A and B; same compiler and flags.
2. Pins: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354; perft 5 = 4865609; kiwipete 5 = 193690690.
3. Per position: the 8 bench FENs at depths 11-22, fresh `ucinewgame`. Compare every info line: depth, seldepth,
   score, nodes, PV, bestmove.
4. Corpus: 12k gate FENs (r12_fens12k) at `go nodes 20000`. Compare bestmove, score and nodes.
5. Warm TT: replay 50 gate games move by move, with no ucinewgame, at `go nodes 50000`. Exercises TT aging/replacement
   and history carry-over that bench hides. Compare the whole info stream.
6. Saturation: Hash 1 (replacement pressure) and Hash 1024 (index maths, large pages) on bench 22. Two
   `go nodes 50000000` runs (history clamps, counters). Mate-in-N and TB-like endings (mate-score ply shifts at the TT
   limits). Extreme material (eval and activation clamps at both ends). rule50 = 98-99. Long `moves` lists with
   repetitions. The 218-move position. Under-promotions. The en-passant discovered-check pin. Castling through attacked
   squares. Stalemate. Insufficient material.
7. ISA: AVX-512 / AVX2 / scalar exes of B agree on levels 2-6 (OpenBench's AVX warning).
8. Differential fuzz: a verify build runs the old and the new function side by side on 1M random legal plies and
   asserts equality at every call. Then the existing ASan/UBSan self-play in CI.
9. Verdict: all equal -> node-identical -> nps ABBA (T12-02) decides, no SPRT. Any difference -> functional change ->
   SPRT route (T12-01).

## Forge fit
Has levels 1-2, a depth-2 version of level 4, and walk/parity tools for the NNUE paths. Missing: per-position output
compare, warm-TT replay, the saturation set, a differential verify build per change (`forge_has.sh 'bench|perft'`:
bench and perft only).

## Expected gain
Source: OpenBench requires the same bench nodes on every client (no mismatch rule stated). Fishtest: "1 % speedups pass with an
85 % chance". No Elo number for the proof itself. Forge estimate: each bit-exact speed change saves one [0,10] SPRT
(mean ~6.6k games, ~13 h at 497 games/h, T12-01) - **UNPROVEN**.

## Effort
Crew ~4-6 h once: a compare driver for levels 3-6 plus the FEN/game lists. Then < 30 min of one core per exe pair
(levels 3-5 are ~250M nodes each at ~1.5 Mnps). No GPU.

## Test plan
Plant a mutant first (a one-node change, e.g. a move-order tie-break) and check that level 3, 4 or 5 catches what the
bench total misses. Then run on the next speed patch. Gate route: node-identical = nps ABBA only; else UHO SPRT at STC
(T12-01 bounds/cap), then LTC.

## OFF-by-default design
Proof tooling only; no engine option. A verify build with the side-by-side check is a separate compile switch (default
off). Release exes stay byte-identical to the kit build and the lock pins are untouched.

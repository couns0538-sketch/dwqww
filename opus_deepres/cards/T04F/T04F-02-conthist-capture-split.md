# T04F-02: Continuation history keyed also by "the earlier move was a capture"
Status: COMPLETE - DUPLICATE (verify 2026-11-05: already PREPARED as R15 C5 `ContHistSplit`, D:/o15/cands/INDEX.md
section c5_conthistsplit, index = capture and / or evasion of the indexing move, exe + patch, pins and smoke PASS,
not gated; this card's option is C5's capture half and its STC / LTC numbers are evidence for that line, no new gate)

## Source
- Caissa 2fd8f56 "Improve continuation history" (2023-10-12): https://github.com/Witek902/Caissa/commit/2fd8f56e40
  (cutechess result block in the message; diff of `src/backend/MoveOrderer.cpp` / `.hpp` read). Current form at HEAD:
  `src/backend/MoveOrderer.hpp:75`, `MoveOrderer.cpp:158-176` @57cae7ef71.
- Stockfish 2e96c51 (PR 2344, 2019-10-06) "Introduce separate counter-move tables for captures" and the refinement
  472de89 (PR 2362, 2019-10-18) "Current capture for Counter-Move history" (commit messages and fishtest run records
  only): https://github.com/official-stockfish/Stockfish/commit/2e96c513ad,
  https://github.com/official-stockfish/Stockfish/commit/472de897cb

## Licence
Caissa @57cae7ef71 and @2fd8f56: MIT (notes/T04F/licences.md); copy allowed with notice, nothing copied. Stockfish:
GPL-3.0, ideas only: commit messages and test pages read, never source. Mechanism in own words.

## Mechanism
Continuation history scores a quiet move by the move played k plies earlier (piece and target square of that earlier
move). The change adds one more key bit: whether that earlier move was a capture. A quiet reply to a capture (often
a recapture race or a forced sequence) and a quiet reply to a quiet move then learn in separate slots, instead of
averaging two different move contexts. The bit belongs to the same earlier move whose piece and square index the
table (the Stockfish refinement replaced a first form keyed by the move before it). Caissa's commit also merged two
older parity tables and kept the pointers across null moves; Forge never had the parity split (its coloured-piece
index already carries the side), so only the capture bit is new for Forge.

## Forge fit
`bash tools/forge_has.sh 'continuation_history_\)\['` -> `src/search.cpp:842`, `:974`, `:1011`, `:1121`, `:1355`: the
pointer for each ply is `(*continuation_history_)[moved piece][to]` (type `include/forge/search.hpp:253-254`); it is
read at plies 1 and 2 (`src/search.cpp:704-712`) and written at plies 1, 2 and 4 (`:720-727`). No capture key
anywhere. Not in TRIED_GATES (ContHist4Pct, gates 31-33, tuned the 4-ply weight only). (corrected by verify: it IS
in R15: C5 `ContHistSplit`, D:/o15/cands/INDEX.md, patch c5_conthistsplit.patch, routes the same three pointer sites
through a chooser keyed by in-check and capture of the indexing move into 3 extra tables; prepared, not gated.)
Change: a leading dimension of 2 on the table and `move.is_capture()` as its index at the pointer sites.

## Expected gain
Caissa 2fd8f56: 6+0.06, threads not stated (corrected by verify), cutechess SPRT llr 2.95 (bounds -2.94 / 2.94), n=7,745 (W 1914 L 1770 D 4061),
+6.5 +- 5.3; book not stated; bundle (capture bit + table merge + null-move pointers); no LTC.
Stockfish 2e96c51 (fishtest, Threads 1, book 2moves_v1): STC 10+0.1 SPRT [0.5,4.5] BayesElo LLR 2.95 N=79,702
(W 17,720 L 17,164 D 44,818, about +2.4 Elo from W/D/L); LTC 60+0.6 [0,3.5] LLR 2.96 N=29,147 (W 4,907 L 4,651
D 19,589, about +3.1). 472de89: STC [0,4] N=61,908 (about +2.3), LTC [0,4] N=49,057 (about +2.2). Engines of 2019 /
2023 strength; Forge's current history set is smaller (no 4- / 6-ply reads).
Forge estimate: +1 to +3 Elo at STC **UNPROVEN**.

## Effort
Crew 2 h (about 15 lines, OFF pins, ON bench, clear-time check). Memory per worker 1.38 MB -> 2.77 MB (int16 x 2 x 13
x 64 x 13 x 64); `Worker::clear` (`src/search.cpp:579`) zeroes twice as much at ucinewgame only. CPU: one STC SPRT
[0, 5] at 430-502 games/h (about 12-14 h for 6,000 games); LTC after an STC H1. No GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = the lock pins (OFF always uses slot 0, the lock's entries); perft
unchanged; ON bench differs (live); nps ABBA OFF vs lock (the bigger table must not slow the OFF path) and ON vs OFF
(cache footprint). Gate: UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
UCI check `ContHistCapture` default false. False: the capture index is forced to 0, so every read and write hits the
lock's entries in the lock's order and the bench pins are unchanged. True: index = the earlier move was a capture
(own choice: captures incl. capture-promotions; quiet promotions count as quiet; variant: all noisy moves). The
null-move pointer keeps slot `[0][Empty][0]` as the lock does (`src/search.cpp:974`).

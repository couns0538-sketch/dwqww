# T04F-02: Continuation history keyed also by "the earlier move was a capture"
Status: COMPLETE

## Source
- Caissa 2fd8f56 "Improve continuation history" (2023-10-12): https://github.com/Witek902/Caissa/commit/2fd8f56e40
  (cutechess result block in the message; diff of `src/backend/MoveOrderer.cpp` / `.hpp` read).
- Current form at HEAD: `src/backend/MoveOrderer.hpp:75` and `MoveOrderer.cpp:158-176` @57cae7ef71 (table indexed by
  previous-move-is-capture, both side colours, piece, to-square).

## Licence
Caissa @57cae7ef71 and @2fd8f56: MIT (notes/T04F/licences.md). Copy allowed with notice; nothing is copied here, the
mechanism is described in own words.

## Mechanism
Continuation history scores a quiet move by the move played k plies earlier (piece and target square of that earlier
move). The change adds one more key bit: whether that earlier move was a capture. A quiet reply to a capture (often
a recapture race or a forced sequence) and a quiet reply to a quiet move then learn in separate slots, instead of
averaging two different move contexts. The Caissa commit also merged its two older parity tables into one and kept
continuation pointers across null moves; Forge never had the parity split (its index is a coloured piece, which
already carries the side), so the only new information for Forge is the capture bit.

## Forge fit
`bash tools/forge_has.sh 'continuation_history_\)\['` -> `src/search.cpp:842`, `:974`, `:1011`, `:1121`, `:1355`: the
pointer for each ply is `(*continuation_history_)[moved piece][to]` (type `include/forge/search.hpp:253-254`); it is
read at plies 1 and 2 (`src/search.cpp:704-712`) and written at plies 1, 2 and 4 (`:720-727`). No capture key
anywhere. Not in TRIED_GATES (ContHist4Pct, gates 31-33, tuned the 4-ply weight only) nor in R15 / FB2 options.
Change: a leading dimension of 2 on the table and `move.is_capture()` as its index at the four pointer sites.

## Expected gain
Source: Caissa 2fd8f56, TC 6+0.06, 1 thread, cutechess SPRT llr 2.95 (bounds -2.94 / 2.94, Elo bounds not stated),
n=7,745 (W 1914 L 1770 D 4061), Elo +6.5 +- 5.3 (LOS 99.1 %); book not stated; no LTC logged; bundle of the
capture bit + table merge + null-move pointers.
Forge estimate: 0 to +3 Elo at STC **UNPROVEN** (only the capture bit transfers; the source error bar is wide).

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
lock's entries in the lock's order and the bench pins are unchanged. True: index = earlier move was a capture
(own choice: captures only; promotions without a capture count as quiet; variant: all noisy moves). Null-move
pointer keeps slot `[0][Empty][0]` as the lock does (`src/search.cpp:974`).

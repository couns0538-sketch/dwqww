# T04E-02: No null move when the hash move captures a valuable piece
Status: COMPLETE

## Source
Two engines, same idea, tested independently:
- Reckless PR #671 "Guard NMP on valuable piece TT captures", commit
  https://github.com/codedeliveryservice/Reckless/commit/845f49d3f1 (2026-01-14), PR
  https://github.com/codedeliveryservice/Reckless/pull/671; logs https://recklesschess.space/test/10664/ (STC),
  https://recklesschess.space/test/10665/ (LTC). The message credits an earlier commit of the Seer engine (not read).
- Viridithas PR #412 "Disable NMP when TT-move is a great capture",
  https://github.com/cosmobobak/viridithas/pull/412 (2026-02-01); log https://viri.dev/test/510/.

## Licence
Both AGPL-3.0 (Reckless at aec5cb2e80, Viridithas at 7489e701bb; notes/T04E/licences.md): ideas only. Read: titles,
PR text (test blocks only, no prose), commit message. No source file, no diff. Thresholds of either engine unknown.

## Mechanism
Null-move pruning passes the turn and expects a reduced search to still beat beta. When the hash move of the node is
a capture of a valuable piece, the node is very likely to cut through that capture anyway, and the null search is
spent on a position where the opponent simply rescues the attacked piece - often failing low and wasting the
reduced search, or producing a cutoff whose reason (the threat) never got verified. Skipping null move there leaves
the capture to cut normally (TT move first) and saves the wasted null searches.

## Forge fit
LACKS. `bash tools/forge_has.sh 'tt_capture'` -> `search.cpp:918` (defined) and `:1142` (LMR only). The null-move
condition `:965-968` checks depth, eval and static-eval margins, `null_move_allowed`, the previous move, own
non-pawn material and one TT guard (upper bound below beta), nothing about the hash move. Change: one more term,
`!(tt_capture && SeePieceValue[type of the piece on tt_move.to] >= threshold)` (values `eval.hpp:32`), counted only when the
piece on `tt_move.to` is the opponent's (a colliding hash move then never triggers). Variant B: SEE of the move.

## Expected gain
Reckless, 1 thread: STC 8+0.08 +3.43 +- 2.31 (95 %), n=22,374, LLR 2.92 [0,3]; LTC 40+0.4 +3.67 +- 2.27,
n=20,816, LLR 3.17 [0,3]. Viridithas: LTC 40+0.4, 1 thread, 128 MB, +1.88 +- 1.48, n=49,814, LLR +2.95 [0,3]
(no STC logged). Books not stated in these logs.
Forge estimate: +1 to +3 Elo **UNPROVEN** (the lock already has a static-eval NMP margin and a TT-bound guard).

## Effort
Crew ~1-2 h (one condition + option + proofs). CPU: STC SPRT [0,5] up to the 12k-game cap, ~13-25 h at 430-502
games/h; LTC run after a pass. No GPU.

## Test plan
Pre-gate: OFF bench / perft pins equal to the lock; ON bench differs; null-move counters (`null_tries_`) fall on
bench with ON; T1/T4 smoke with engine-side legality; mate probe OFF/ON (NMP touches zugzwang-like endings).
Gate: UHO SPRT [0,5] at STC, then LTC (both source engines passed at LTC).

## OFF-by-default design
UCI option `NmpTtCaptureMin` (int 0-5, default 0 = off): minimum victim type of the hash-move capture that blocks
null move (own start 4 = rook or queen; range 2-5). Variant B `NmpTtCaptureSee` (cp, 0 = off; own start 300,
range 100-900) uses SEE of the hash move instead. 0 adds no term, so OFF node counts equal the bench pins.

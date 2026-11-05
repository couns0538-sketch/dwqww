# T04D-01-cutnode-nott-lmr: one more LMR ply at cut nodes that have no TT move
Status: COMPLETE

## Source
- Stockfish commit [9cc15b3](https://github.com/official-stockfish/Stockfish/commit/9cc15b3049) (2025-02-13), "Do more
  reductions for cut nodes without a tt move", PR https://github.com/official-stockfish/Stockfish/pull/5875 .
- Test logs: STC https://tests.stockfishchess.org/tests/view/67abc9aaa04df5eb8dbeb452 , LTC
  https://tests.stockfishchess.org/tests/view/67abcd7ba04df5eb8dbeb96c (TC, book, threads and bounds read from the
  fishtest run API `api/get_run/<id>`).

## Licence
Stockfish GPL-3.0 (Copying.txt at ff7cee4244, 2026-10-28, `tools/licence_at.py`): ideas only. Read: the commit
title and message and the two fishtest run records. No source file or diff was read.

## Mechanism
In late-move reductions, a move searched at an expected cut node gets one extra ply of reduction when the node has
no TT move. The commit text calls it the same signal as internal iterative reduction (no stored move: the node was
never searched well, so its late moves matter less), applied per move inside LMR instead of to the node depth, and
expects it to keep its value at longer TC because extra reduction at cut nodes "is in general good" there; the
logged LTC result (+3.35) is indeed above the STC one (+2.72).

## Forge fit
`bash tools/forge_has.sh 'cut_node\) r|tt_move.is_none\(\) && \(pv_node'` -> `src/search.cpp:1141` adds a flat 2
plies for every cut node (`if (cut_node) r += 2;`, no TT-move condition); `src/search.cpp:1031` (IIR) already takes
one ply off the node depth for PV or cut nodes without a TT move at depth >= IirDepth (4). The source engine also had
IIR when it was tested (its message compares the two), so the transfer is: keep IIR, add the per-move ply on top.
Change: one line after `:1141`, reduction +CutNoTtLmr when `cut_node && tt_move.is_none()` (`tt_move` is the node's
constant at `:913`); the reduced depth stays clamped to [1, new_depth] at `:1147`. Not in Sf26Bundle (bit 4 adds an
LMR ply for a static-eval gap below alpha), not in TtPruneV2 (its IIR rule is for an upper-bound TT move), not R15 C4
(IIR on a too-shallow TT entry), not T04-01..06; `tools/tried_gates.py --grep cut` shows no LMR gate.

## Expected gain
Source: STC 10+0.1, 1 thread, UHO_Lichess_4852_v1, SPRT normalized [0,2]: LLR 2.93, 42,304 games, W 11,223 L 10,892
D 20,189, Ptnml 184 / 4,904 / 10,669 / 5,187 / 208 = +2.72 +- 1.74 Elo (95 %, own pentanomial arithmetic).
LTC 60+0.6, same book, SPRT [0.5,2.5]: LLR 2.95, 32,334 games, W 8,386 L 8,074 D 15,874, Ptnml 26 / 3,446 / 8,916 /
3,748 / 31 = +3.35 +- 1.81 Elo. Engine: Stockfish master of 2025-02-13 (NNUE, its own LMR and IIR).
Forge estimate: 0 to +3 Elo at STC, possibly more at LTC **UNPROVEN** (Forge's whole-ply reductions make the step
coarser than the source's; Forge already reduces these nodes twice, by IIR and by the cut-node term).

## Effort
Crew 1 h (one line + option, OFF pin check, ON bench, 2-minute smoke). CPU: 430-502 games/h for the crew's
`*_vs_AL1*` gates (WORKER_RULES round 2), so a 3,000-game STC cap is about 6-7 h; an SPRT [0,10] nElo capped at 12k
averages ~6.6k games (~13 h); an LTC at k times the STC time per game costs about k times that. No GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = the lock pins (node-identical by construction); ON bench differs (live);
perft unchanged; on the bench set, count LMR searches clamped at depth 1 OFF vs ON (must rise only at cut nodes
without a TT move); mate probe OFF/ON. Gate: UHO SPRT [0,5] at STC, then LTC (the source gain grew at LTC: run the
LTC also after an STC cap with a positive score).

## OFF-by-default design
UCI spin `CutNoTtLmr`, default 0, range 0-2, own start value 1 for the gate (one whole ply: the smallest Forge step;
2 = the size of the existing cut-node term). At 0 the new line adds nothing, so every node and the bench pins equal
the lock. No table or memory change.

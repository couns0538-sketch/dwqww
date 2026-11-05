# T04-02: LMR re-search depth adjustment (search deeper / shallower after a reduced fail-high)
Status: COMPLETE

## Source
- Caissa commit 434bbda "Deeper search" (2024-01-03), two OpenBench blocks in the message, diff read
  (`src/backend/Search.cpp`, LMR / PVS block): https://github.com/Witek902/Caissa/commit/434bbda5c342501ac5de4ecb6934e85151a225fe
- Patricia PR 137 "search deeper if we found a great move" (merged 2025-01-26, merge aa32588b), OpenBench block in the
  PR text: https://github.com/Adam-Kulju/Patricia/pull/137 (test https://chess.swehosting.se/test/9584/)
- Caissa 105979c "Search: No 'deeper' at root node" (+2.37 +- 1.59, 10+0.1, n=50298):
  https://github.com/Witek902/Caissa/commit/105979c

## Licence
Caissa @57cae7ef71 and Patricia @67d83d7056: MIT (notes/T04/licences.md). Copy allowed with notice; nothing copied,
own words, own constants.

## Mechanism
When a late move searched at reduced depth unexpectedly beats alpha, the lock re-searches it at the unreduced depth.
The refinement uses how far the reduced score beat the best score so far: well above it, the move is likely a new
best move and gets one ply more than the normal depth; only barely above the best score, the re-search is done
one ply shallower. PV re-searches use the adjusted depth too; the root keeps the plain depth (Caissa 105979c).

## Forge fit
`bash tools/forge_has.sh 'full_depth_needed'` -> `src/search.cpp:1136-1159`: after a reduced fail-high the lock
re-searches at the fixed `new_depth` (declared `const` at line 1117); no deeper / shallower step. Not among the R15
candidates or FB2-J3 options. Tried gates `--grep 'deeper|shallow'`: 4 rows, all packd Hindsight (gates 51-54, -6.3
to +4.6, 1,500 games each) - a different rule (depth change at node entry from the parent's reduction), not this one.
Lines to touch: ~8 in the LMR block (make `new_depth` mutable, two comparisons, root guard).

## Expected gain
Source 1: Caissa, OpenBench SPRT [0, 2], 1 thread: STC 10+0.1 n=14,696 +6.93 +- 3.88 (LLR 2.96); LTC 40+0.4
n=18,914 +5.14 +- 3.35 (LLR 2.95). Source 2: Patricia PR 137, SPRT [0, 3], 8+0.08, Hash 16 MB, n=14,514 (W 2978
L 2746 D 8790) +5.55 +- 3.25, LLR 2.95; no LTC. Books: not stated (OpenBench defaults, unknown).
Forge estimate: +2 to +6 Elo at STC and LTC **UNPROVEN** (both sources gained at both TCs where measured; Forge's
reductions are table-driven like theirs).

## Effort
Crew 2 h (option, OFF identity, ON bench, smoke, a node-count sanity check of re-search depths). CPU: the crew gate runs about 1,000 games/h at concurrency 8 (R7 J4 measurement, 28.3 s per STC game), so a 3,000-game STC cap is about 3 h of the gate PC; an LTC at k times the STC time costs about k times that. One STC SPRT [0, 5], then one LTC. No GPU.

## Test plan
Pre-gate: OFF bench pins d11-d22 equal the lock; ON bench live; perft unchanged; assert that the adjusted depth stays
in [reduced_depth, new_depth + 1] (debug build); mate probe OFF/ON. Gate: UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
UCI spins `LmrDeeperMargin` default 0 (0 = off, range 0-200 cp, own start 70) and `LmrShallowerMargin` default -1
(-1 = off, range 0-40 cp, own start 10). At the defaults the re-search depth is the lock's `new_depth`, so every node
and the bench pins are unchanged. Root nodes never go deeper.

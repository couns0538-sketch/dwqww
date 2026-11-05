# T04-02: LMR re-search depth adjustment (search deeper / shallower after a reduced fail-high)
Status: COMPLETE (review: KEEP-WITH-FIX by the second vote; NOT new - own packb ReSearchAdjust, see Forge fit)

## Source
- Caissa commit 434bbda "Deeper search" (2024-01-03), two OpenBench blocks in the message, diff read
  (`src/backend/Search.cpp`, LMR / PVS block): https://github.com/Witek902/Caissa/commit/434bbda5c342501ac5de4ecb6934e85151a225fe (review fix, second vote: the message credits the idea to another engine, Stockfish; no constant from it is used)
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
(review fix, second vote: NOT new - that grep missed own prior code. packb `ReSearchAdjust`
(C:/Users/Administrator/grok-pc/forge_push/src_packb_h256/src/search.cpp:1170-1179: deeper if score > best + 60 +
2 x new_depth, shallower if score < best + 1 x new_depth, never below the reduced depth, no root, PV re-search not
adjusted) was gated 4 times, always bundled with FiftyDamp=1 (T06-05): gate 12 +3.82 (1,000 g vs ep10), gates 35 / 40
/ 41 -1.16 / +5.79 / +1.39 (1,500 g each vs h256e12), all "cap, no decision" (notes/TRIED_GATES.md, `--grep
'packb|ReSearch|Fifty'`); those bases are older than the lock FD3A5190, so the "no decision" is stale too. packb's
60 + 2 x depth is Patricia PR 137's exact tuned rule and 1 x depth Caissa 434bbda's: do not reuse them. New angle of
this card: gate the rule ALONE on the lock with own constants (70 / 10 cp below), PV re-search adjusted, a ply guard;
best done by lock-porting the packb code with these own defaults rather than writing a new option.)
Lines to touch: ~8 in the LMR block (make `new_depth` mutable, two comparisons, root guard).

## Expected gain
Source 1: Caissa, OpenBench SPRT [0, 2], 1 thread: STC 10+0.1 n=14,696 +6.93 +- 3.88 (LLR 2.96); LTC 40+0.4
n=18,914 +5.14 +- 3.35 (LLR 2.95). Source 2: Patricia PR 137, SPRT [0, 3], 8+0.08, Hash 16 MB, n=14,514 (W 2978
L 2746 D 8790) +5.55 +- 3.25, LLR 2.95; no LTC. Books: not stated (OpenBench defaults, unknown).
Forge estimate: +2 to +6 Elo at STC and LTC **UNPROVEN** (both sources gained at both TCs where measured; Forge's
reductions are table-driven like theirs). Counter-evidence (T12C): in Stockfish (GPL-3.0, messages and titles only) the extra-deep re-search step was reverted for search explosions "most visible with TB" (955edf1, 2022-12-12), reintroduced, removed again (b59786e) and later re-added in another form, and the shallower form was simplified at zero cost (87814d2: STC -0.01 +- 0.72, 242,336 g; LTC +0.31 +- 0.92, 128,100 g); later gaining edits of this block are about +0.9 to +2.3 at LTC: lowered to +1 to +4 Elo **UNPROVEN**; the ply guard is mandatory, and the pre-gate box tests add mate / TB positions.

## Effort
Crew 2 h (option, OFF identity, ON bench, smoke, a node-count sanity check of re-search depths). CPU: the crew gate runs about 1,000 games/h at concurrency 8 (R7 J4 measurement, 28.3 s per STC game), so a 3,000-game STC cap is about 3 h of the gate PC; an LTC at k times the STC time costs about k times that (review fix, critic summary (e) / B FINAL_REPORT:76-77: that rate is the older R7 J4 setting, Threads 1 / conc 8; the current UHO *_vs_AL1* gates run 430-502 games/h (497 at Threads 2 / conc 4; T07 VERIFY:44, WORKER_RULES round 2), so a 3,000-game cap is about 6-7 h there). One STC SPRT [0, 5], then one LTC. No GPU.

## Test plan
Pre-gate: OFF bench pins d11-d22 equal the lock; ON bench live; perft unchanged; assert that the adjusted depth stays
in [reduced_depth, new_depth + 1] (debug build); mate probe OFF/ON. Gate: UHO SPRT [0, 5] at STC, then LTC.
(review fix, second vote: the assert is per node only - also compare max seldepth and nodes per depth ON vs OFF on the bench set for the ply guard; and re-search only when the adjusted depth is above the reduced depth (as packb does), or the shallower step repeats the reduced search at the same depth with only the cut flag flipped.)

## OFF-by-default design
UCI spins `LmrDeeperMargin` default 0 (0 = off, range 0-200 cp, own start 70) and `LmrShallowerMargin` default -1
(-1 = off, range 0-40 cp, own start 10). At the defaults the re-search depth is the lock's `new_depth`, so every node
and the bench pins are unchanged. Root nodes keep new_depth (no deeper, no shallower step) (review fix, second vote:
Caissa's root guard skips both). Ply guard on the ON path (review fix, second vote): spin `LmrDeeperMaxPlyPct`, no
deeper step once ply >= this % of the root depth, own start 250, range 100-400 (Caissa's own path guard is 2 x root
depth, so 200 is not taken as the start); read only when LmrDeeperMargin > 0, so OFF stays the lock. (verify note: notes/T04/TABLE.md row 1 gave the deeper range as 30-150 cp, this card 0-200 cp (review fix, critic: TABLE row 1 now says 0-200 like this card); start 70 and 10 checked against both source diffs: neither is a copy of a source constant.)

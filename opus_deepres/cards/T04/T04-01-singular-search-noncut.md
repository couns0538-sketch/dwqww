# T04-01: Run the singular verification search as a non-cut node
Status: COMPLETE

## Source
- Caissa commit 1b7a871 "Search: Run singular search as non-cut-node" (2025-12-29):
  https://github.com/Witek902/Caissa/commit/1b7a871236e20d85fd193f07bb2a62dceb2f9e35 (OpenBench block in the commit
  message; diff read: `src/backend/Search.cpp`, singular-extension block of `NegaMax`).
- Related, same engine: 6ec347d "More negative extensions in cut nodes" (+4.03 +- 2.19, 10+0.1, n=26636),
  https://github.com/Witek902/Caissa/commit/6ec347d (title + logged result only).

## Licence
Caissa @57cae7ef71 (HEAD read 2026-11-04): MIT (notes/T04/licences.md). Copy allowed with notice; nothing is copied
here, the mechanism is described in own words.

## Mechanism
The singular verification search re-searches the current node without the hash move at half depth and a null window
just below the hash score. It inherits the node's cut-node flag, so in an expected cut node the replies inside the
verification get the cut-node LMR penalty: the verification is shallower than intended and the hash move is called
singular (extended) more often. Searching the verification as a non-cut node removes that penalty at the
verification node; the node-type flags further down flip with it (its full-depth children become cut nodes). The
verification frame's flag is restored afterwards. Caveat: Caissa runs null move only in cut nodes (47604ad,
2025-08-04, before this commit), so its +4.20 also contains a null-move change further down the verification tree;
Forge's null move has no cut-node condition, so only the reduction side transfers.

## Forge fit
`bash tools/forge_has.sh 'singular_score = search'` -> `src/search.cpp:1095`: the lock passes `cut_node` into the
verification search, and the lock's LMR adds +2 plies for cut nodes (`src/search.cpp:1141`), so the effect described
above exists in Forge. Not in the R15 candidates (C1-C6, x1, x2b) nor in FB2-J3 SingularV2 (triple / PV double
extensions, multicut on the singular score, deeper negative extensions). Tried gates: nothing on this flag
(`tools/tried_gates.py --grep 'singular|cutnode'` = 0 rows). Change: one argument at line 1095 behind an option.

## Expected gain
Source: Caissa, OpenBench SPRT [0.00, 2.00], 10+0.1, 1 thread, Hash 16 MB, n=25,044 (W 5993 L 5690 D 13361),
Elo +4.20 +- 2.23, LLR 2.94; no LTC run was logged. Book: not stated in the commit (OpenBench default, unknown).
Forge estimate: 0 to +3 Elo at STC **UNPROVEN** (Forge's cut-node LMR term is +2 plies, `src/search.cpp:1141`, so
the distortion exists; but part of the source's gain came from its cut-node-only null move, which Forge lacks).

## Effort
Crew 1 h (option + OFF pin check + ON bench + 2-minute smoke). CPU: the crew gate runs about 1,000 games/h at concurrency 8 (R7 J4 measurement, 28.3 s per STC game), so a 3,000-game STC cap is about 3 h of the gate PC; an LTC at k times the STC time costs about k times that. One STC SPRT [0, 5]; LTC only after an STC H1. No GPU.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = the lock pins (node-identical by construction); ON bench differs (live);
perft unchanged; count singular extensions per 1M nodes OFF vs ON on the bench set (the source reasoning predicts fewer ON; a rise means the flipped child node types dominate);
mate probe OFF/ON. Gate: UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
UCI spin `SingularNonCut` default 0, range 0-1. At 0 the call at `src/search.cpp:1095` passes `cut_node` exactly as
the lock does, so every node and the bench pins are unchanged; at 1 it passes `false`. No table or memory change.

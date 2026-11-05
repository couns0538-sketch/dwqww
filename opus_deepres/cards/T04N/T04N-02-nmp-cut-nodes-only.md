# T04N-02: null-move pruning only at expected cut nodes
Status: COMPLETE

## Source
- Halogen PR 808 "Apply NMP only in suspected cut nodes" (merged 2025-11-14 as f00b8e3417):
  https://github.com/KierenP/Halogen/pull/808 ; OpenBench http://chess.grantnet.us/test/40378/ (LTC) and
  http://chess.grantnet.us/test/40369/ (STC), both result blocks in the PR body.
- Earlier evidence and why the idea was dropped: notes/T04/TABLE.md row 45, Caissa 47604ad +1.07 +- 0.86 at
  168,198 games (MIT) -> "dropped, under +1 expected". Halogen is a second engine with a bigger STC number and an LTC
  pass, so the drop reason no longer holds; nothing in notes/TRIED_GATES.md tried this (grep null / nmp: no gate).

## Licence
Halogen GPL-3.0 (tools/licence_at.py at f00b8e3417: LICENSE GPL-3.0, row in notes/T04N/licences.md): ideas only.
PR title, PR text and the OpenBench result blocks were read, never source.

## Mechanism
The search passes an expected node type down the tree (`cut_node`): the lock flips it on the null-window calls
(null move s:979, re-searches s:1151 / s:1160) and marks every LMR-reduced child as a cut node (s:1148). Today
the null move is tried at every non-PV node that passes the eval tests. The change: try it only where the flag
expects a fail high. At an expected all-node the null search seldom cuts, so its nodes are mostly wasted, and when it
does cut there it more often overrules real moves that would all have failed low (a reduced-depth, zugzwang-prone
verdict). Own design; no constants.

## Forge fit
`bash tools/forge_has.sh 'cut_node'`: 10 hits, none in the null-move condition. Null move is src/search.cpp:964-990
inside the `!pv_node && !in_check` block that starts at s:952: depth, eval >= beta, static-eval margin, null allowed,
previous move not null, non-pawn material, TT upper-bound guard (s:965-968); the null child gets `!cut_node` (s:979).
Change: one more term `(!NmpCutOnly || cut_node)` in s:965. ProbCut (s:1000-1027) and the verification search
(s:990) stay as they are. The lock counts null tries (`null_tries_`, s:969), which gives a cheap ON/OFF statistic.

## Expected gain
Halogen PR 808: LTC 40+0.4 Threads=1 Hash=64MB +1.95 +- 1.53, SPRT [0,3] LLR 2.96, 49,716 games (W 11,900
L 11,621 D 26,195); STC 8+0.08 Threads=1 Hash=8MB +4.05 +- 2.64, SPRT [0,3] LLR 2.95, 20,498 games (W 5,334
L 5,095 D 10,069). Book not stated in the PR (corrected by verify: OpenBench pages 40369 / 40378 list UHO_Lichess_4852_v1.epd). Counter-evidence: Caissa 47604ad +1.07 +- 0.86, 168,198 games.
Forge estimate: +0.5 to +2 Elo at STC **UNPROVEN** (one tight small number and one loose larger one).

## Effort
Crew 1 h (one condition, option, OFF pins, ON smoke, the null-try count on bench). CPU: one STC SPRT [0,5] up to
~6.6k games, about 13-15 h at 430-502 games/h; LTC confirm the same or more. GPU 0.

## Test plan
1. OFF: bench and perft pins equal the lock. 2. ON: bench nodes change; report null tries and null cutoffs per 1M
nodes OFF vs ON on the bench set (expect fewer tries, a higher cutoff rate); go perft 1 legality smoke; mate probe
OFF/ON (zugzwang-like positions are where null-move rules change results). 3. Gate: UHO SPRT [0,5] at STC
Threads=1, then LTC.

## OFF-by-default design
UCI option `NmpCutOnly`, check, default false. False leaves the null-move condition exactly as in the lock (same
nodes, same bench signature). True adds the cut-node term; no other value to tune.

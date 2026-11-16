# REPORT — seat 03, job 5: does the engine play the same move on the PC build as on the base build?

**What was asked.** With move generation confirmed identical, test whether the LEGALITY of the move the engine
actually plays is equally unaffected: 200 positions, each on both builds at depth 8, Threads 1, compare bestmoves.
Say plainly if there are none.

**The answer.** There are differences — **4 of 200** positions played a different move. All four are in
**endgames**, and all four moves are **legal** on both builds. The two builds converge on 2 of the 4 at a greater
depth; for the other 2 the PC build either finds a faster mate or holds a different move at depth 16. So the move
generator transfers (S-F6), but the **move choice does not transfer everywhere** — it differs in low-material
positions, which is exactly where the r15 patch's `FORGE_FIX_BARE_KING_*` changes live.

**How sure.** High on the count: 200/200 positions measured, 0 measurement failures, 0 illegal moves, and a planted
control through the same harness reported 4/4 differences and flagged the planted move illegal. Moderate on the
*interpretation* — the endgame concentration is statistically strong (4/26 vs 0/174, two-sided Fisher p = 0.0002)
but the bucket was chosen after seeing the data, so it is a hypothesis consistent with the patch, not a proven cause.

## Honesty numbers and settings

Builds: base 6b98f217 (`68825bd5…`), PC r15 (`d6bd72c5…` patch, `-DFORGE_MATE_ALPHA_GUARD=1`).
Every search: fresh process, `Threads 1`, `Hash 16`, `OwnBook false`, `ucinewgame` + `isready`, `go depth 8`, read
to `bestmove`, then `quit`. No sanitizer claim is made.

## Headline numbers (`bm200.txt`)

```
depth 8, Threads 1, Hash 16, OwnBook false, one fresh process per search
positions: 200  measured: 200  measurement failures: 0
same bestmove: 196
different bestmove: 4
same score: 191
same node count: 191
illegal bestmove on either build: 0
```

## The control (file 2, Rule 1: a zero needs a planted one)

Run through the SAME `bestmove_parity.py`, unchanged, on 4 positions:

```
=== PLANTED ILLEGAL (pc side answers a1a1):
positions 4/4; same bestmove 0; different 4; same score 0; same nodes 0; illegal 4; failures 0
```

So the harness sees a difference when one is planted, and flags illegal moves. Two proxy-wrapper attempts deadlocked
before this (waiting for `readyok` after `position`, which the engine sends only after the following `isready`); the
standalone fake that replaced them is recorded in `fake_bestmove.py`.

## The four differing positions, verified at greater depth (`diffs4.txt`)

| idx | material | base d8 | pc d8 | d12 | d16 | note |
|---|---|---|---|---|---|---|
| 153 | 10 (endgame) | a4b4 cp -976 | a4b5 cp -991 | **same** a4b5 | differ (base back to a4b4) | both moves legal; 4 legal moves in the position |
| 155 | 10 (endgame) | c6d6 cp -962 | c6c7 cp -955 | differ | differ (base -1112, pc -1093) | both legal; scores within 19 cp |
| 156 | 9 (endgame) | g5h3 cp 944 | f2e3 cp 1086 | differ (pc **mate 8**) | **same** f2e3, pc mate 6 vs base mate 21 | base's own d16 mate PV does NOT end in checkmate; pc's does |
| 160 | 9 (endgame) | f1e2 cp 1179 | f1f2 **mate 5** | **same** mate 5 | same mate 5 | PC finds the mate 3 depths earlier; both correct at d12 |

Every played move is legal in python-chess (`base_legal=True`, `pc_legal=True` in `bm200.txt`; re-checked in
`diffs4.txt`). Nothing here is a move-generation or legality fault.

## Where the differences sit (`strat200.txt`)

```
| material bucket | positions | differing moves | rate |
| endgame <= 12 (non-king material) | 26 | 4 | 15.4 % |
| middlegame 13..24 | 59 | 0 | 0.0 % |
| heavy 25+ | 115 | 0 | 0.0 % |

endgame 4/26 vs rest 0/174; two-sided Fisher exact p = 0.0002
```

## Prediction against result

| # | predicted | killed? | measured |
|---|---|---|---|
| 1 | 0 differing bestmoves | **killed** | 4 of 200 |
| 2 | 0 positions with no bestmove | no | 0 (200/200 measured) |
| 3 | node counts equal in fewer than half the positions | **killed** | 191 of 200 had equal node counts |
| 4 | scores equal in fewer than half | **killed** | 191 of 200 equal |
| 5 | 0 crashes / illegal bestmoves / refused FENs | no | 0 / 0 / 0 |
| 6 | no sanitizer claim | no | none made |
| 7 | any differing bestmove is legal on both AND scores within 30 cp | **partly killed** | all legal (as predicted), but idx 156 differs by 142 cp and idx 160 by a cp-1179 vs mate-5 gap |

Predictions 1, 3 and 4 were killed. That matters: it means the r15 patch's search changes are **not** inert at
depth 8 on this position set, which is the substantive fact this job was run to find.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F9 | At depth 8, Threads 1, the PC r15 build plays a different move than the base build in 4 of 200 random positions, all four legal on both, and all four in endgames (4/26 = 15.4 % of endgame positions vs 0/174 elsewhere, two-sided Fisher p = 0.0002) — so move generation transfers (S-F6) but move choice does not, exactly where the patch's bare-king fixes apply. Builds: base 6b98f217 vs PC r15; settings: default options, Threads 1, Hash 16, OwnBook false, depth 8. | `cd forge-combo29/swarm/03/job5 && python3 bestmove_parity.py ~/build-rel/forge ~/build-pc/forge ../job4/set_bm200.fens 8 /tmp/bm.txt && python3 stratify.py /tmp/bm.txt ../job4/set_bm200.fens /tmp/s.txt` |
| S-F10 | On the two positions where the builds disagree at depth 8 and do not converge by depth 12, the PC build is the stronger side by its own verified mate evidence: it reports mate 5 at depth 8 where base needs to reach depth 12 (idx 160), and mate 8 at depth 12 where base sees cp +1101 (idx 156) — the PC's mate PV replays to checkmate while base's depth-16 mate-21 PV does not. Builds as S-F9, settings as S-F9. | `cd forge-combo29/swarm/03/job5 && python3 verify_diffs.py ~/build-rel/forge ~/build-pc/forge ../job4/set_bm200.fens diffs4` |

## Suspicions, not proven

- That the endgame concentration is CAUSED by `FORGE_FIX_BARE_KING_LMR_CAP` / `FORGE_FIX_BARE_KING_ONE_THREAD`.
  Testable by rebuilding with those two macros off and re-running the 26 endgame positions; I have not done that.
- That idx 155 (`c6d6` vs `c6c7`, 19 cp apart, never converging by depth 16) is a genuine preference difference
  rather than a deeper-search tie. Would need depth 20+ on both builds.

## What I did NOT do

- Did not search deeper than 16 on the two unsettled positions.
- Did not rebuild the PC tree with individual fixes disabled (that is the natural follow-up, not done here).
- Did not run any sanitizer or any threaded measurement; scores are only reported at Threads 1 per the swarm rule.

## What I am NOT sure about

- Whether 4/200 would be 4/200 on a different position set: these are random mid-game positions from one generator,
  so the endgame share (26/200 = 13 %) is an artefact of my sampling, not of chess. A set with more endgames would
  probably show a higher absolute count.
- Whether "different move" here ever means "worse move". For 3 of the 4 the PC evidence looks better or equal; for
  idx 155 I cannot tell without much deeper search.

## Times

`job5/stamps.txt`, `bm200.log`, `diffs4.txt`.

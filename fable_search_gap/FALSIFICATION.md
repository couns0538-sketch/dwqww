# FALSIFICATION: how to prove this dossier wrong

The dossier says two things: (1) every checked mechanism except one is already owned, and (2) the one unowned mechanism, enhanced transposition cutoffs, does not qualify. This file lists the cheapest ways to break either claim, with the outcomes fixed in advance. It also holds what a later spec of that mechanism would have to survive, so that a positive counting run can move straight to work.

## Key points

- **Strongest falsifier of the mechanism:** the classic pawn ending in section 2. With the mechanism on, the engine must still play 1.Kb1 with a winning score at every depth from 24 to 40. In the replica, one of four settings fails this at every depth.
- **Strongest falsifier of the verdict:** the counting run in section 3. If the real lock search shows a saving well above the lookup cost, the verdict is wrong and a spec is due.
- **Strongest falsifier of the dedupe:** any branch, note or build that reads a child's table entry to end a node. One hit and "unowned" is false.
- Every probe below that uses an existing exe has been run on the unmodified lock exe; results are in `data/`.

## 1. Breaking the dedupe claim

| Claim | What would break it | Where to look |
|---|---|---|
| Enhanced transposition cutoffs are owned by nobody | a card, table row, option, patch or source file that ends a node from a child's table entry | the three banned folders, the 20 unfetched `data/` and `results/` branches, any board outside the repo, branches pushed after 2026-11-09 20:15 PT |
| The 19 other candidates are owned | a reference in `DEDUPE.md` that does not say what I say it says | each row cites branch, tip and line |
| `tcc21` is a different mechanism | a reading of its patch showing it also creates cutoffs | `D:\forge-runs\tcc21_20261109\src_cand\src\search.cpp`; my reading: it only vetoes |

## 2. Witness positions

All were run on the unmodified lock exe (sha256 `E1284F7F...`) on CPU 3-6 at Idle, one thread, 16 MB (`data/lock_baseline_24.jsonl`, `data/lock_fine70_d40.json`). "Replica" is the harness of `tools/etc_probe` (`data/etc_probe_deep.tsv`, `data/etc_probe_fine70.tsv`).

| # | Position | Oracle | Lock exe today | Expected with the mechanism on | Replica result |
|---|---|---|---|---|---|
| W1 | `8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1` | White wins, only by 1.Kb1 (Fine, *Basic Chess Endings*, 1941, position 70) | Kb2 at depth 20; Kb1 from depth 22; depth 32: +1185, 1.71 M nodes; depth 40: +2783, 168.3 M nodes | Kb1 with a winning score at every depth from 24 to 40, and fewer nodes | three settings: Kb1 with 7 to 12 times fewer nodes at depth 40; one setting: **Kb2 at every depth, score falling to 0** |
| W2 | `8/2k5/3p4/p2P1p2/P2P1P2/8/3K4/8 w - - 0 1` | none checked (same pawn structure as W1) | depth 30: d2d3, +1784, 1.67 M nodes | same move, fewer nodes | same move, 0.66 to 0.72 times the nodes; score differs (+520 plain, +393 to +475) |
| W3 | `1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1` | Lucena-type win for White by theory; **not checked against a tablebase by me**, QA should confirm with the 5-man tables before use | depth 24: Rd1+, +409, 0.44 M nodes | same move, winning score | same move and score; nodes 0.98 and 1.66 times plain at the two thresholds |
| W4 | `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` (bench position 4) | none | depth 24: Rxf4+, +94, 2.57 M nodes | same move | same move; nodes 0.89 and 0.52 times plain; score moves from +167 to +157 and +85 |

Counter-witnesses, where the replica got **slower** with the mechanism on:

| # | Position | Lock exe today | Replica node ratio (threshold 6 / 8) |
|---|---|---|---|
| C1 | `8/5pk1/6p1/7p/7P/6P1/r4PK1/1R6 w - - 0 1` (level rook ending) | depth 24: Rb7, 0, 70 k nodes | 0.92 / 1.38 |
| C2 | `8/5pk1/6p1/8/8/1Q4P1/5PK1/q7 w - - 0 1` (level queen ending) | depth 22: Qb8, 0, 193 k nodes | 1.00 / 1.28 |
| C3 | `8/pp3pkp/2n3p1/8/8/2N3P1/PP3PKP/8 w - - 0 1` (level knight ending) | depth 22: Kf3, +14, 2.10 M nodes | 0.88 / 1.01 |

## 3. Trigger instrumentation (the next evidence request)

A counting mode in the real search, compiled out by default. It takes no cutoff, so node counts stay equal to the pins.

| Counter | Meaning |
|---|---|
| `eligible` | non-PV expected cut nodes, no excluded move, depth at least the threshold, beta not a mate score, rule-50 below 90, own entry gave no cutoff |
| `lookups` | child entries peeked |
| `hits` | eligible nodes where some child entry has an upper or exact bound at or below minus beta, at depth at least `depth - 1` (one more for a move the search would extend), usable under the rule-50 stamp, and not a repetition on the current path |
| `hits_hash_move` | hits where that child is the node's hash move |
| `top_hits`, `savable` | hits not nested under another hit, and the nodes the search then spends below them |
| `top_hits_fail_high` | of those, how many the search itself ends at or above beta |

Thresholds, fixed now, for threshold depth 8 on `bench 16`, `bench 20` and at least 200 positions (at least 80 with twelve or fewer pieces):

- `savable / nodes` under 2 % in the middlegame group: **close the idea.**
- Lookup time (ABBA, switch on against switch off) more than half of `savable / nodes`: **close the idea.**
- `top_hits_fail_high / top_hits` under 99 %: **stop and investigate**; the mechanism would then disagree with the search it claims to shortcut.
- Otherwise: write the spec.

The harness in `tools/etc_probe` implements exactly these counters and can serve as the reference for what to count.

## 4. Negative controls

| Control | Requirement | Status in the replica |
|---|---|---|
| Counting does not change the tree | node count with counting on equals plain, every position | 95 of 95, every rule |
| The search is deterministic | plain run twice gives identical node counts | 95 of 95 |
| Timing noise is known | plain run twice: time ratio | 0.9999 on the sum of 95; per position standard deviation 4.8 % |
| A forced mate is untouched | `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`: same move, same mate distance | lock exe: Qg6, mate in 2; replica: same move and score with every rule, at most 0.6 % hits |
| A quiet opening is barely touched | start position: hit rate small, node ratio near 1 | hit rate about 5 %; node ratio 0.76 and 0.96 |

## 5. OFF identity (required of any later implementation)

With the compile switch off, and with the switch on but the option at its default 0:

- bench with the net on, depth 11 / 13 / 16 / 20 / 22: 312866 / 862329 / 3024920 / 12389307 / 34048354;
- bench with the net off: 375354 / 907205 / 2448617 / 13573040 / 24506465;
- perft 5: start position 4865609, kiwipete 193690690;
- two builds from clean exports give the same exe hash, as the crew's candidate checks require.

Proposed names, unused in the 3,754-file corpus: compile switch `FORGE_ETC` (default 0), counting switch `FORGE_ETC_STATS` (default 0), option `EtcDepth` (0 = off; N = smallest depth at which the lookups run). These are reservations for a possible later spec, not a proposal to build.

## 6. Correctness tests a later implementation would need

1. **Shadow check.** In a debug build, at every node where the mechanism would return, also search the proving move alone with a zero window at the depth the search would use, and require a value at or above beta. Expect 100 %; the replica's coarser version of this check gave 99.8 to 100 %.
2. **Repetition.** A child that repeats a position of the current path or game must never be used. Test with a position where the proving child is a repetition.
3. **Rule 50.** No use at a half-move clock of 90 or more, and none of a child entry whose rule-50 stamp makes its score unusable.
4. **Mate scores.** No use when beta or the child's score is in the mate range.
5. **Singular search.** No use while a move is excluded.
6. **PV nodes.** No use, as for the node's own table cutoff.
7. **Threads.** The peek must take the stripe lock in the shared-table path; a two- and four-thread soak like the lock's own.
8. **W1.** The classic pawn ending at depths 24 to 40.

## 7. Cost measurement

- **Isolated cost:** counting mode against plain on identical trees, ABBA, at least 200 positions. Replica values for comparison: +2.9 % of time at threshold 8, +5.5 % at 6, +13.3 % at 4.
- **Where the cost comes from:** one full move generation at each eligible node (the lock otherwise generates in stages), a legality test and a key per move, and one cache line per child.
- **Table size:** repeat at 16 MB and at 256 MB. A table that no longer fits in the CPU cache makes each lookup dearer.

## 8. QA-owned test proposal (only if section 3 passes and a spec is written)

QA alone schedules gates. This is a proposal, not a request, and it queues nothing.

| Stage | What | Pass | Reject or stop |
|---|---|---|---|
| 0 | Section 3 counters in the real search | thresholds met | any "close" or "stop" line of section 3 |
| 1 | Sections 5 and 6 on the candidate build | all identical, all tests pass | any pin differs with the option off; W1 not solved at any depth 24 to 40 |
| 2 | Time to fixed depth, option on against off, ABBA, at least 200 positions | time ratio at or below 0.98 with a 95 % range below 1.00, and no position slower than 1.5 times | range includes 1.00, or middlegame group above 1.00 |
| 3 | Non-regression SPRT in the crew's form (bounds [-10, 0] normalized Elo, alpha = beta = 0.05, the crew's standard time control, threads, hash and book at that date), cap 3,000 games | H1 (not worse) and CLEAN | H0; or any time loss, crash or illegal move; or a NOT CLEAN run, which is void and not pooled |
| 4 | Gain SPRT only as part of a stack the crew already plans | crew rules | crew rules |

Stop criteria that apply at every stage:

- **An existing feature already covers it.** If, with `TtCutChildDepth` on, the stage 0 counters fall below the thresholds, the mechanism is redundant in practice. Stop.
- **Erratic behaviour.** If any witness of section 2 changes its best move for the worse at any tested depth, stop until the cause is understood.
- **No retries to fit.** One run per stage and setting. A second threshold may be tried only if it was named before the first run.

## 9. What was not tested here

- The lock search itself with the mechanism or its counters. This job made no engine change.
- More than one thread, tables above 16 MB, time controls.
- Positions from real gate games; no PGNs exist.

# FALSIFICATION: how to prove this dossier wrong

Terms are explained in `NO_QUALIFIED_GAP.md` section 9. This file was corrected after the review; `REVIEW_LOG.md` lists what changed.

The dossier says two things: (1) every checked mechanism except one is already owned, and (2) the one unowned mechanism, enhanced transposition cutoffs, does not qualify because no benefit is shown. This file lists the cheapest ways to break either claim, with the outcomes fixed in advance. It also holds what a later spec of that mechanism would have to survive, so that a positive counting run can move straight to work.

## Key points

- **Strongest falsifier of the mechanism:** the classic pawn ending in section 2. With the mechanism on, the engine must still play 1.Kb1 at every depth from 24 to 40. In the replica three of eight settings fail this at some depth. Under ten placebo-size changes the plain replica never fails it, and the mechanism's settings fail it at some depth in 31 of 80 runs. Those runs are not independent; they amount to two or three separate tries.
- **Strongest falsifier of the verdict:** the counting run in section 3. If the real lock search shows a first-order saving clearly above the lookup cost, "no benefit shown" is out of date and a spec is due.
- **Strongest falsifier of the dedupe:** any branch, note or build that reads a child's table entry to end a node. One hit and "unowned" is false.
- **Every single-position comparison in this replica needs a placebo next to it.** A change that is no mechanism moves the best move in 18 of 91 positions and single node counts by a factor of 0.08 to 3.3.
- Every probe below that uses an existing exe has been run on the unmodified lock exe; results are in `data/`.

## 1. Breaking the dedupe claim

| Claim | What would break it | Where to look |
|---|---|---|
| Enhanced transposition cutoffs are owned by nobody | a card, table row, option, patch or source file that ends a node from a child's table entry | the three banned folders, the 20 unfetched `data/` and `results/` branches, deleted or reverted work in branch history, file types outside the corpus, any board outside the repo, branches pushed after 2026-11-09 22:19 PT (the remote was compared with the snapshot again at that time; `DEDUPE.md` section 6) |
| The 19 other candidates are owned | a reference in `DEDUPE.md` that does not say what I say it says | each row cites branch, tip and line; the reviewer checked all 19 |
| `tcc21` is a different mechanism | a reading of its patch showing it also creates cutoffs | `D:\forge-runs\tcc21_20261109\src_cand\src\search.cpp`; my reading and the reviewer's: it only vetoes |
| The four ideas of `DEDUPE.md` section 5 have no card or build | a card, option or build for any of them | same places as the first row |

## 2. Witness positions

All were run on the unmodified lock exe (sha256 `E1284F7F...`) on CPU 3-6 at Idle, one thread, 16 MB (`data/lock_baseline_24.jsonl`, `data/lock_fine70_d40.json`). "Replica" is the harness of `tools/etc_probe` (`data/etc_probe_deep.tsv`, `data/etc_probe_fine70_variants.tsv`).

| # | Position | Oracle | Lock exe today | Expected with the mechanism on | Replica result |
|---|---|---|---|---|---|
| W1 | `8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1` | White wins, only by 1.Kb1 (Fine, *Basic Chess Endings*, 1941, position 70) | Kb2 at depth 20; Kb1 from depth 22; depth 32: +1185, 1.71 M nodes; depth 40: +2783, 168.3 M nodes | Kb1 at every depth from 24 to 40, and fewer nodes | five of eight settings: Kb1 at every depth, 2 to 19 times fewer nodes at depth 40. **Three settings play Kb2 at some depth**: cut8 at every depth; cut8 returning beta at depths 24 to 36; all3 at depth 24. Plain and placebo: Kb1 at every depth, with scores of only +206 to +400 |
| W2 | `8/2k5/3p4/p2P1p2/P2P1P2/8/3K4/8 w - - 0 1` | none checked (same pawn structure as W1) | depth 30: d2d3, +1784, 1.67 M nodes | same move, fewer nodes | same move, 0.66 to 0.72 times the nodes; score differs (+520 plain, +393 to +475) |
| W3 | `1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1` | Lucena-type win for White by theory; **not checked against a tablebase by me**, QA should confirm with the 5-man tables before use | depth 24: Rd1+, +409, 0.44 M nodes | same move, winning score | same move and score; nodes 0.98 and 1.66 times plain at the two thresholds |
| W4 | `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` (bench position 4) | none | depth 24: Rxf4+, +94, 2.57 M nodes | same move | same move; nodes 0.89 and 0.52 times plain; score moves from +167 to +157 and +85 |

Counter-witnesses, where the replica got **slower** with the mechanism on:

| # | Position | Lock exe today | Replica node ratio (threshold 6 / 8) |
|---|---|---|---|
| C1 | `8/5pk1/6p1/7p/7P/6P1/r4PK1/1R6 w - - 0 1` (level rook ending) | depth 24: Rb7, 0, 70 k nodes | 0.92 / 1.38 |
| C2 | `8/5pk1/6p1/8/8/1Q4P1/5PK1/q7 w - - 0 1` (level queen ending) | depth 22: Qb8, 0, 193 k nodes | 1.00 / 1.28 |
| C3 | `8/pp3pkp/2n3p1/8/8/2N3P1/PP3PKP/8 w - - 0 1` (level knight ending) | depth 22: Kf3, +14, 2.10 M nodes | 0.88 / 1.01 |

**How to read these tables.** The node ratios are single runs. A placebo moves single positions just as far (`EVIDENCE.md` section 5.5). So W2 to W4 and C1 to C3 illustrate; they prove nothing in either direction. W1 is different in kind: the question there is the move, and the plain replica keeps the right move under all ten placebo-size changes I tried (`EVIDENCE.md` section 5.8).

## 3. Trigger instrumentation (the next evidence request)

A counting mode in the real search, compiled out by default. It takes no cutoff, so node counts stay equal to the pins.

| Counter | Meaning |
|---|---|
| `eligible` | non-PV expected cut nodes, no excluded move, depth at least the threshold, beta not a mate score, rule-50 below 90, own entry gave no cutoff |
| `lookups` | child entries peeked |
| `hits` | eligible nodes where some child entry has an upper or exact bound at or below minus beta, deep enough (next row), usable at the child's rule-50 count, with the child's own rule-50 count below 90, and the child not a repetition on the current path or in the game |
| deep enough | for a move that is not the hash move: child depth at least `depth - 1`, plus one if the move is a safe check the lock would extend. For the hash move: child depth at least `depth + 1`, because the lock's singular search may extend it by up to two plies and that cannot be known without running it |
| `hits_loose` | the same count with `depth - 1` for the hash move too. The difference to `hits` shows how much the extension question matters |
| `hits_hash_move` | hits where the hash move's own child proves the cutoff, whichever child is found first |
| `top_hits`, `below` | hits not nested under another hit, and the nodes the search then spends below them |
| `top_hits_fail_high` | of those, how many the search itself ends at or above beta |

**Where the count sits.** Right after the node's own table-cutoff test (`search.cpp:1165-1170`) and before razoring, reverse futility, the null move and ProbCut. That place decides which nodes count as "below", so it has to be the same in every run.

**Two details the lock code forces.**

- `key_after` gives no key at a node that has an en-passant square (`board.cpp:974`). Either key those children by making and unmaking the move, or count such nodes separately and say that hits there are missed.
- The child's repetition test should be the lock's own rule (`is_repetition` with the root index, as `is_draw` uses it), not a stricter one. A stricter test undercounts hits.

**Positions.** `bench 16` and `bench 20`, and at least 300 positions taken from real gate games at the gate's time control, each weighted by the time or nodes the engine spent on that move. The mix of middlegame and endgame is then the gate's own. Evenly spaced plies would give the mix by move count, which is not the same. If no games are kept, playing some is QA's call, not mine.

**Timing.** Counting on against counting off, interleaved on a quiet machine, repeated until the uncertainty of the time difference is under one percentage point. This job could not do that (`EVIDENCE.md` section 5.6).

**Thresholds, fixed now,** for threshold depth 8, on the game positions as one set:

- `below / nodes` smaller than the lookup time: **close the idea.**
- `below / nodes` larger than the lookup time by at least 2 percentage points: **write the spec.**
- In between: **undecided.** Record the numbers. No spec.
- `top_hits_fail_high / top_hits` under 99 %: **stop and investigate**; the mechanism would then disagree with the search it claims to shortcut.

One threshold depth only. A second may be tried only if it is named before the first run.

These thresholds compare a share of nodes with a share of time. That assumes the nodes below hit nodes cost about the average time per node. It is a first-order comparison, good enough to decide whether a spec is worth writing, not to predict a speed-up.

**What changed here after the review.** The earlier version closed the idea if the middlegame share was under 2 %. The replica's own middlegame numbers (1.2 to 2.0 %) were already under that line, and I have no data on how gate games split their clock between middlegame and endgame. The thresholds above use the gate's own mix instead. On the replica's numbers they would come out "undecided" or "write the spec": 4.7 % below hit nodes against 1.5 to 4.3 % lookup time on the wide set, and 2.6 % against a single measurement of 0.7 % on the second set. So the request is not decided in advance.

The harness in `tools/etc_probe` implements the first-found version of these counters and can serve as a starting point for what to count.

## 4. Negative controls

| Control | Requirement | Status in the replica |
|---|---|---|
| Counting does not change the tree | node count with counting on equals plain, every position | met: every position, every rule, every set |
| The search is deterministic | plain run twice gives identical node counts | met |
| A change that is no mechanism (placebo) | shown next to every result | wide set: 18 of 91 best moves change; single node ratios 0.08 to 3.3; geometric mean 0.98, range by base [0.88, 1.08] |
| Timing noise is known | plain run twice: time ratio | totals agree within 0.4 % on the wide set; single positions vary by 3.8 to 24.6 % over four runs; one search was measured at 0.97 and at 1.37 times plain. Not good enough for a time claim |
| A forced mate is untouched | same move, same mate distance | **weak, and failed once.** The mate in 2 I used (`2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`) has at most 0.6 % hits, so it tests little. On `e3_rook_pawn` in the first set, rule all3 turned a found mate into a plain winning score (31963 to 1494) with 0.30 times the nodes. Rules cut6 and cut8 kept the mate. A later spec needs a real mate suite |
| A quiet opening is barely touched | start position: node ratio near 1 | **not met as written**: 0.76 at threshold 6 and 0.96 at threshold 8, with a hit rate of about 5 %. With the placebo's spread one ratio says little either way |

## 5. OFF identity (required of any later implementation)

With the compile switch off, and with the switch on but the option at its default 0:

- bench with the net on, depth 11 / 13 / 16 / 20 / 22: 312866 / 862329 / 3024920 / 12389307 / 34048354;
- bench with the net off: 375354 / 907205 / 2448617 / 13573040 / 24506465;
- perft 5: start position 4865609, kiwipete 193690690;
- two builds from clean exports give the same exe hash, as the crew's candidate checks require.

Proposed names, unused in the 3,754-file corpus: compile switch `FORGE_ETC` (default 0), counting switch `FORGE_ETC_STATS` (default 0), option `EtcDepth` (0 = off; N = smallest depth at which the lookups run). These are reservations for a possible later spec, not a proposal to build.

## 6. Correctness tests a later implementation would need

1. **Shadow check.** In a debug build, at every node where the mechanism would return, also search the proving move alone with a zero window at the depth the search would use, and require a value at or above beta. Expect 100 %. The replica's coarser version of this check gave 99.8 to 100 %, but in the replica that check is close to true by construction.
2. **Repetition.** A child that repeats a position of the current path or game must never be used. Test with a position where the proving child is a repetition.
3. **Rule 50.** No use when the node's or the child's half-move clock is 90 or more, and none of a child entry whose rule-50 stamp makes its score unusable.
4. **Mate scores.** No use when beta or the child's score is in the mate range.
5. **Singular search.** No use while a move is excluded, and no use of the hash move's child at less than `depth + 1`.
6. **PV nodes.** No use, as for the node's own table cutoff.
7. **Threads.** The peek must take the stripe lock in the shared-table path; a two- and four-thread soak like the lock's own.
8. **W1.** The classic pawn ending at depths 24 to 40.
9. **Store policy.** Decide, with a test, whether the node writes a bound when it takes the cutoff. The replica gives no clear answer: not writing removed the W1 failure of cut8 in the baseline run, but under ten placebo-size changes that variant still failed W1 in five of ten.
10. **Agreement against a placebo.** On a fixed set of positions, count changed best moves and scores moved by half a pawn or more. The counts must not be clearly above the same counts for a placebo change. A fixed mate and tablebase suite must lose no solved position.

## 7. Cost measurement

- **Isolated cost:** counting mode against plain on identical trees, interleaved, at least 300 positions, on a quiet machine. Replica values for comparison, from a loaded machine: +1.5 to +4.3 % of time at threshold 8, +3.4 to +5.5 % at 6 (four measurements each), +13.3 % at 4 (one measurement).
- **Where the cost comes from:** one full move generation at each eligible node (the lock otherwise generates in stages), a legality test and a key per move, and one cache line per child.
- **Side effects to count as well:** a node that returns early updates no killer or history table and does not raise the parent's child-cutoff counter (`search.cpp:1450`), which the lock uses for reductions.
- **Table size:** repeat at 16 MB and at 256 MB. A table that no longer fits in the CPU cache makes each lookup dearer.

## 8. QA-owned test proposal (only if section 3 passes and a spec is written)

QA alone schedules gates. This is a proposal, not a request, and it queues nothing.

| Stage | What | Pass | Reject or stop |
|---|---|---|---|
| 0 | Section 3 counters in the real search | "write the spec" line met | "close" or "stop" line of section 3 |
| 1 | Sections 5 and 6 on the candidate build | all identical, all tests pass | any pin differs with the option off; W1 not solved at any depth 24 to 40 |
| 2 | Time to fixed depth, option on against off, interleaved, at least 300 positions, with a placebo change run the same way | time ratio at or below 0.98 with a 95 % range below 1.00, ranges taken by game, and clearly better than the placebo | range includes 1.00, or not better than the placebo |
| 3 | Non-regression SPRT in the crew's form (bounds [-10, 0] normalized Elo, alpha = beta = 0.05, the crew's standard time control, threads, hash and book at that date), cap 3,000 games | H1 (not worse) and CLEAN | H0; or any time loss, crash or illegal move; or a NOT CLEAN run, which is void and not pooled |
| 4 | Gain SPRT only as part of a stack the crew already plans | crew rules | crew rules |

Stop criteria that apply at every stage:

- **An existing feature already covers it.** If, with the `tcc21` option `TtCutChildDepth` on, the stage 0 counters fall below the thresholds, the mechanism is redundant in practice. Stop.
- **Wrong move on a witness.** If W1 or a mate-suite position changes its best move for the worse at any tested depth, and the same position survives a placebo change, stop until the cause is understood.
- **No retries to fit.** One run per stage and setting. A second threshold may be tried only if it was named before the first run.

## 9. What was not tested here

- The lock search itself with the mechanism or its counters. This job made no engine change.
- More than one thread, tables above 16 MB (except on W1), time controls.
- Time on a quiet machine.
- Positions from real gate games. I found no PGNs.

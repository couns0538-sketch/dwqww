# REPORT_threads — seat 24, area 4: threaded search changes the MOVE (PC build and base tree)

## 1. What was asked / the answer / how sure

**What was asked.** Nothing asked this directly. It grew out of my area-4 work: confirming seat 04's 04-F1 (a
thread-scaled node explosion on one special position) led me to ask the question that actually matters for the
owner — if nodes vary by 1,000x under threading, does the *chosen move* vary too?

**The answer.** Yes, on ordinary middlegame positions, at Threads 2 and 4, on BOTH builds. At depth 12, 6 fresh
processes per position, the same first 20 positions of G:
base tree (S14) **0 of 20 at Threads 1, 8 of 20 at Threads 2, 9 of 20 at Threads 4**;
PC r15 (PC20) **0 of 20 at Threads 1, 10 of 20 at Threads 2, 8 of 20 at Threads 4**.
Every node count at Threads 1 was identical to the digit; every thread count above 1 varied in nodes on all 20.
So threaded search is not reproducible for move choice, it is a property of the search ARCHITECTURE rather than of
the PC build, and Threads 2 is not a safer setting than Threads 4.

**How sure.** High on the measurements: fresh process per run, 6–8 runs per position, Threads-1 control with exact
node reproducibility, OwnBook false, no book line in any transcript. The mechanism is NOT identified (see §5).

## 2. Honesty numbers of the builds used

PC r15 release (patch sha256 d6bd72c531f785f4..., `-DFORGE_MATE_ALPHA_GUARD=1`):
exe sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
none: 312866 / 862329 / 3024920 / perft5 4865609 · S14: 242796 / 656517 · PC20: 278024 / 587276 — all match file 5.
Base tree release: exe sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83, all four pins match.

## 3. Tables (pasted output of `checks/move_stability_t4.py`; each file is committed)

### PC r15, PC20, Threads 4 vs Threads 1, 8 runs per position, four positions that had disagreed

```
Threads 4                          | Threads 1 (control)
g7g6,g7g6,g7g6,g7g6,g7g6,g7g6,g7g6,e5e4 -> 2 moves  | g7g6 x8 -> 1 move, nodes 31779 exactly
c8e8,d6f6,c8e8,d6e6,d6e6,c8e8,c8e8,c8e8 -> 3 moves  | d6e6 x8 -> 1 move, nodes 112542 exactly
e8d8,c7c6,e8d8,c7c6,c7c6,d7f6,e8d8,e8d8 -> 3 moves  | e8d8 x8 -> 1 move, nodes 43300 exactly
d5e7,d5f6,d5f6,d5f6,d5e7,d5f6,d5e7,d5f6 -> 2 moves  | d5f6 x8 -> 1 move, nodes 38779 exactly
```

### Rates over the first 20 positions of G (6 fresh processes per position)

| build | settings | Threads | positions with >1 move | positions with varying nodes |
|---|---|---|---|---|
| base tree | S14, depth 12, Hash 16, OwnBook false | **1** | **0 of 20** | 0 of 20 (bit-identical) |
| base tree | S14 | 2 | **8 of 20 (40 %)** | 20 of 20 |
| base tree | S14 | 4 | **9 of 20 (45 %)** | 20 of 20 |
| PC r15 | PC20, depth 12, Hash 16, OwnBook false | **1** | **0 of 20** | 0 of 20 (ratio exactly 1.00) |
| PC r15 | PC20 | 2 | **10 of 20 (50 %)** | 20 of 20 |
| PC r15 | PC20 | 4 | **8 of 20 (40 %)** | 20 of 20 (ratios 1.49–4.34) |

**This is the table that answers the owner's question:** the instability is the same order of magnitude on both
builds and at both 2 and 4 threads, and Threads 1 is exact on both. It is a property of the threaded search
architecture, not of the PC build, and 2 threads is not a safer choice than 4.

Worst single examples: PC `8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w` at Threads 4 gave **e4f5 / e3f5 / f4f5**; base tree
`8/5pk1/4p3/3nK1p1/8/R5P1/5P2/8 b` at Threads 2 gave **d5e7 / d5f6 / g7g6 / d5b6** across 6 runs.

## 4. Findings

| id | build | settings | one sentence | state |
|---|---|---|---|---|
| 24-F21 | PC r15 | PC20, Threads 4 (8 runs/position) | the move itself differs between runs on ordinary positions; Threads 1 is bit-identical | open, needs another seat |
| 24-F21b | base tree | S14, Threads 4 (6 runs/position) | the same instability is on the base tree, so it is not PC-specific | open |
| 24-F22 | PC r15 | PC20, Threads 4, 20 positions | 8 of 20 (40 %) of ordinary positions change move at Threads 4 | open |
| 24-F23 | PC r15 | PC20, Threads 2, 20 positions | Threads 2 is worse (10 of 20), so there is no safe thread count above 1 | open |
| 24-F24 | both builds | S14 / PC20, Threads 1, 2, 4, 20 positions each | base tree: 0 / 8 / 9 of 20; PC build: 0 / 10 / 8 of 20 — architecture, not build | open, needs another seat |

This also reverses **seat 04's 04-F10a**, which withdrew their 04-F10 (that the effect changes the move). My data
says the withdrawal was wrong and the original claim was right.

## 5. Suspicions, not proven

- **Why** threaded search changes the move is not identified. The candidates are: shared transposition table entries
  written by different threads at different times, the time/node ordering of the helper cutoffs, or the history
  tables' per-worker independence. Bisecting needs instrumented builds per candidate, which I did not do.
- It is NOT the built-in book: `OwnBook false` was set in every run, the positions are mid-game, and no
  `info string book move` line appears in any transcript.
- It is NOT "scores at Threads > 1" in the swarm-rule sense: this job reads no score at all, only bestmoves and node
  counts.

## 6. What I did NOT do

- No mechanism bisection.
- No position sample beyond the first 20 of G plus the four deep-checked ones; the 40 %/50 % rates are for THIS
  sample and should not be read as a global probability.
- No Threads 8/16 move study (the sweep showed those only matter for races).

## 7. What I am NOT sure about

- Whether the differing moves are "equally good" or "one is worse". Measuring that needs games or a deep Threads-1
  reference score per position, which the swarm rule (scores at Threads 1) would make a much longer job. The honest
  statement is: **the move is not reproducible**, not "the move is worse".
- Whether the rate depends on position difficulty; the worst example had large node variance (4.34x).

## 8. Times: see `checks/stamps.txt`

## 9. Last command's output

```
$ cd forge-combo29/swarm/24/checks && ls move_*.txt
move_rate_pc_t2.txt   move_rate_pc_t4.txt   move_stab_base_t4.txt
move_stab_pc.txt      move_stab_pc_deep.txt move_stab_pc_t1.txt
```

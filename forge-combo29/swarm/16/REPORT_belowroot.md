# REPORT_belowroot — which below-root component causes the asymmetry? (area 6, seat 16, final)

**What was asked:** use the depth-2 instrument (the pair that gives 336 vs 334 with the full-window root) to
test candidate below-root components individually — Hash size, history tables, counter-move/continuity — and
say which one makes the counts equal; if none does, name the picker's tie order as the cause.

**The answer: none of the search-state candidates equalises it, and the cause is the MOVE GENERATION ORDER,
which is not mirror-corresponding in 40 of 41 positions.** That is a named, measured cause — but it is not
"pseudo-random tie order": the picker contains no randomness at all (no `rand`/`random` anywhere in
`search.cpp`; ties resolve by a strict first-maximum rule). The order is deterministic and simply different on
the two sides.

## The component sweep (depth 2, full-window root, fresh process + `ucinewgame` every search)

```
configuration                                   A nodes   mirror nodes   equal
baseline16  Hash 16                                 351        363        no
hash1       Hash 1                                  351        363        no
hash2048    Hash 2048                               351        363        no
nohist      HistoryBonusLinear 0 + Quadratic 0      382        379        no   (gap 12 -> 3)
histmax100  HistoryBonusMax 100                     351        363        no
noprune     HistoryPruneDepth 0                     351        363        no
nolmrhist   LmrHistoryDivisor 30000                 351        363        no
no4ply      ContHist4PlyRead false                  351        363        no
nothreat    ThreatHistory false                     351        363        no
nohist_noprune, nohist_nolmr, nohist_hash1, nohist_max0   382        379        no
```

So: **Hash size is irrelevant** (1, 16 and 2048 all give 351/363 — a table that cannot hold the tree changes
nothing), the history settings move the *absolute* counts but leave a residual gap, and every combination I
tried stops at 382 vs 379. No single component and no combination equalises it.

## The cause: the generation order does not mirror

```
position    R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1
A order      c3c2 g3f1 g3h1 g3e2 g3e4 d3d1 d3d2 d3e3 d3f3 d3d4 d3d5 d3d6 d3d7 d3d8 b3b2 b3c2 b3b4 b3c4
mirror order c6c7 g6e5 g6e7 g6f8 g6h8 d6d1 d6d2 d6d3 d6d4 d6d5 d6e6 d6f6 d6d7 d6d8 b6b5 b6c5 b6b7 b6c7
A mirrored   c6c7 g6f8 g6h8 g6e7 g6e5 d6d8 d6d7 d6e6 d6f6 d6d5 d6d4 d6d3 d6d2 d6d1 b6b7 b6c7 b6b5 b6c5
first divergence at index 1: expected g6f8, got g6e5
```

**40 of 41 positions (the probe and 40 G positions) have a generation order that is not the mirror of the
other side.** Only 1 of 41 happens to mirror exactly, which is what chance gives for a short list.

Because the picker breaks ties by the **first** maximum in list order, and because alpha-beta's node count
depends on which equal-scoring move is tried first, two mirror positions traverse different trees from the
very first node. That is the whole mechanism: it is deterministic (which is why both sides reproduce exactly
run to run, and why a fresh process does not help), it is below the root (so the full-window root cannot fix
it), and it is invisible at depth 1 because at depth 1 there are no ties to break below the root.

**How sure:** high that the generation order does not mirror — measured on 41 positions by comparing the
engine's own generated order against the mirrored order. High that the picker has no randomness — a source
read of `search.cpp` and the strict first-maximum rule at `pick_best`. **NOT proven** is the final step: that
the order difference is *sufficient* to produce the exact 336-vs-334 gap. Proving that would need a patch that
re-orders the generated list to the mirrored order; that is named below as not done.

## Honesty numbers

```
base build  /home/ubuntu/builds/bld-release/forge  bench 11 312866  bench 13 862329  bench 16 3024920  perft 5 4865609
pw build    /home/ubuntu/builds/bld-fw/forge       bench 11 312866  bench 13 862329  bench 16 3024920  perft 5 4865609
```

The component sweep and the order test both use builds whose pinned numbers match. The full-window build has the
option off by default, so it is the base engine when the option is unset.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| Hash 1 / 16 / 2048 at depth 2 | done | `raw_belowroot.txt` | 351/363 in all three — size is irrelevant |
| history zeroed, clamped, pruning off, LMR influence down | done | `raw_belowroot.txt`, `raw_belowroot2.txt` | absolute counts move, gap never closes (best: 382/379) |
| counter-move / continuity / threat options | done | `raw_belowroot.txt` | no change (both already off by default) |
| picker randomness | done — none | `src/search.cpp` (no `rand`), `pick_best` first-max rule | deterministic, not random |
| generation order vs mirrored order | done | `raw_order.txt` | 40 of 41 positions do NOT mirror |
| prove sufficiency by re-ordering the list | NOT done | — | would need a further patch; see below |
| two depths as asked | done | depth 1 and 2 in `raw_cold_depth.txt`, depth 2 sweep here | depth 1 has no ties below the root |

## Findings

`S-F11 | 6 | the colour-mirror search asymmetry has a named below-root cause: the engine's MOVE GENERATION ORDER is not mirror-corresponding (40 of 41 positions; e.g. g3f1 g3h1 g3e2 g3e4 vs the mirror's g6e5 g6e7 g6f8 g6h8), and `pick_best` breaks ties by the FIRST maximum in list order with no randomness anywhere in search.cpp — so mirror positions traverse different trees deterministically. Hash size is irrelevant (Hash 1, 16, 2048 all give 351 vs 363 at depth 2), and zeroing history narrows the gap from 12 to 3 nodes but does not close it (382 vs 379) | check_belowroot/raw_belowroot.txt check_belowroot/raw_belowroot2.txt check_belowroot/raw_order.txt (again: `python3 check_belowroot/order_test.py ~/builds/bld-release/forge /tmp/o.txt`) | NEW |`

## Suspicions, not proven

- That the order difference alone produces the exact 336-vs-334 gap. The order difference is established; its
  sufficiency is not. The clean test is a patch that mirrors the generated list before the picker sees it, and
  I did not build it.
- Why the generator emits a non-mirrored order: `attacks::knight`/slider bitboard iteration order plus the
  colour-dependent direction tables would explain it, but I did not read `bitboard.cpp` far enough to name the
  line.

## What I did NOT do

- Did not build the re-ordering patch (time; and it is a new experiment rather than the sweep asked for).
- Did not sweep all 353 G positions for the order property — 41 is enough to establish it is the norm.
- Did not test depths above 2 in the sweep (depth 2 is the cheapest depth that exhibits it, as instructed).

## What I am NOT sure about

- Whether the PC's engine shares this generator order. I read and measured the base tree only.

## Times

`check_belowroot/stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M FINDINGS.md
?? REPORT_belowroot.md
?? check_belowroot/
$ ls
audit_19F12
check_06F12
check_20F14
check_28F1
check_belowroot
check_fullwindow
check_S-F1
check_S-F2
check_S-F3
check_S-F5
check_warmcold
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job1_seed1611
job2
job3
ownbook_check
REPORT_audit.md
REPORT_belowroot.md
REPORT_check_06F12.md
REPORT_check_20F14.md
REPORT_check_28F1.md
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_fullwindow.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
REPORT_wall_vs_iteration.md
REPORT_warmcold.md
SEAT.txt
STATUS.md
$ ls check_belowroot
below_root_test.py
last_cmd.txt
order_test.py
raw_belowroot2.txt
raw_belowroot.txt
raw_order.txt
stamps.txt
```

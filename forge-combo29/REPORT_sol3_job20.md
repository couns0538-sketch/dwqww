# sol3 Job 20 — Shadow evaluation inside search

## (1) Step 0 — retained builds passed

Linux cloud, Case A. All three retained binaries and the Job 19
net768 matched their pinned SHA-256 values. Each benchmark ran in
a fresh process with PC20, Threads 1, Hash 16 and the same synthetic
standalone net. Each process printed `info string NNUE v3 active:`
and `checksum 30ab43b4ba5db5f3`.

| Build | Active v3 kernel | bench 11 nodes | bench 13 nodes |
| --- | --- | ---: | ---: |
| r15d | AVX-512 | 882,074 | 4,275,906 |
| kF | AVX-512 | 882,074 | 4,275,906 |
| kFscalar | Scalar | 882,074 | 4,275,906 |

[Hash and raw pin receipts](sol3/job20/stage0)

## (2) Step 1 — compare the raw v3 values

The single shadow patch adds 51 lines across three files. It applied
with zero fuzz to both scratch trees. The added C++ lines are inside
`#if FORGE_SHADOW_EVAL` blocks. With those blocks excluded, all
original nonblank source lines match. Both shadow builds used their
original flags plus `-DFORGE_SHADOW_EVAL=1`.

| Hook in the reproduced trees | kF-shadow | r15d-shadow |
| --- | --- | --- |
| Search dispatch to `Worker::static_evaluate_v3` | `src/search.cpp:1757` | `src/search.cpp:1286` |
| Fast function and shadow comparison | `src/search.cpp:3883,3938–3951` | `src/search.cpp:3376,3421–3434` |
| `nnue::v3::evaluate_reference` | `src/nnue_v3.cpp:762–769` | `src/nnue_v3.cpp:770–777` |
| Per-search totals immediately before bestmove | `src/uci.cpp:450–453` | `src/uci.cpp:365–368` |

After the fast value is computed, the shadow call rebuilds a fresh
accumulator for the same board and computes the scalar output sum.
It compares the two integers before correction history or rule-50
scaling. Search receives the original fast value. Worker counters
reset at search entry and are summed when the search returns.
A process-wide limit keeps FEN and value lines for the first five
disagreements. The count includes root accumulator priming and any
repeat calls, so its node ratio is a call rate.

[Shadow patch](sol3/job20/shadow_eval.patch.txt) · [Source sites](sol3/job20/build/shadow_sites.txt) · [Zero-fuzz kF apply](sol3/job20/shadow_apply_kF.txt) · [Zero-fuzz r15d apply](sol3/job20/shadow_apply_r15d.txt) · [Build receipts](sol3/job20/build)

## (3) Step 2 — K1 label identity and K2 fault detection

K1 used PC20, single-thread Hash 16, net768, a fresh-game reset per
W1 position, and fixed depth 9. Each shadow build matched all 1,000
Job 19 last-depth node counts and bestmoves, totaling 16,543,291
nodes per build. Each performed 8,046,050 reference comparisons and
reported zero differences. [r15d K1](sol3/job20/K1/r15d-shadow/summary.json) · [kF K1](sol3/job20/K1/kF-shadow/summary.json)

In a separate kF-shadow copy I changed one line in
`nnue::dirty_from_move` at `src/nnue.cpp:535–542` (changed line 537).
On promotion the dirty list omits the removal of the moving pawn.
Capture handling and adding the promoted piece keep their original
operations. The first 200 W1 positions at depth 9 produced 103,012
differences across 1,650,207 evaluations, with 3,999,007 last-depth
nodes. The first comparison disagreement was in search 1, raw
stdout line 109. The process printed all five permitted examples.

```text
info string shadow differ fast -712 ref -934 fen r1b2rk1/1p1nbp1p/p3pnp1/q2P4/3P1B2/4P2P/PP1N1PP1/R3QK2 b - - 0 16
```

[One-line plant](sol3/job20/promotion_control.patch.txt) · [K2 raw result and five examples](sol3/job20/K2/kF-promotion-control/summary.json)

## (4) Prediction graded

The [forecast](sol3/job20/prediction.md) was pushed alone as
`7b736d1` before the S workloads. All four arms had zero
fast/reference differences and hit their call-rate range. S1
was 48.6363% on both builds against 48.60–48.70%. S2 was
42.8512% on both against 38–52%. Both use PC20, Threads 1,
Hash 16 and the standalone net768 with the same checksum.
[Checkpoint order](sol3/job20/stamps.txt)

## (5) Workloads

The shadow rows count each fast/reference comparison. The S3
rows compare last-depth nodes and bestmove with uninstrumented
builds. All fixed-depth roots reset the game and wait for readyok.
All measured processes with net768 logged its activation and
checksum.

| Workload | Program | Searches or games | Evals | Differ | First difference |
| --- | --- | ---: | ---: | ---: | --- |
| [S1 depth 9](sol3/job20/S1/r15d-shadow/summary.json) | r15d-shadow | 1,000 searches | 8,046,050 | 0 | — |
| [S1 depth 9](sol3/job20/S1/kF-shadow/summary.json) | kF-shadow | 1,000 searches | 8,046,050 | 0 | — |
| [S2 softnodes 2000](sol3/job20/S2/r15d-shadow/summary.json) | r15d-shadow | 20 games, 933 searches | 1,680,173 | 0 | — |
| [S2 softnodes 2000](sol3/job20/S2/kF-shadow/summary.json) | kF-shadow | 20 games, 933 searches | 1,680,173 | 0 | — |
| [S3 W1 scalar vs AVX-512, depth 9](sol3/job20/S3_W1/comparison.json) | kFscalar and kF | 1,000 pairs | — | 0 label rows | — |
| [S3 O, depth 12](sol3/job20/S3_O/kFscalar/summary.json) | kFscalar | 200 searches | — | 0 pin differences | — |

S1 produced 16,543,291 depth-9 nodes per program. The separate
repeat preserved Job 19's 1,000 node counts and bestmoves on both
builds, and every per-search shadow count matched K1.

S2 started from W1 positions 21–40. Each game reset once and
searched the original FEN plus the growing played move list
with `go softnodes 2000`. Python-chess 1.11.2 checked legality
and stopped each game on `claim_draw=True` or at 200 plies.
All 20 move lists and all 933 stable per-search rows agreed.
There were 15 checkmates and five claimable threefold repetitions.
No game reached the cap. The played continuations included 17
promotions and one en passant capture. [Per-game plies, evals, differences and nodes](sol3/job20/S2/per_game.tsv) · [Move-list comparison](sol3/job20/S2/comparison.json) · [Game replay receipt](sol3/job20/S2/receipt.json)

The S2 denominator was 3,920,946 final consumed nodes per build,
from the engine's `info string softnodes nodes` markers. The
last-depth info sum was 3,028,475. In 131 searches the engine
reached the 8,000 hard cap and the final count exceeded the
last completed iteration's count. The final markers avoid
inflating the reported call rate with an earlier node total.

S3 reran the complete 1,000-position W1 workload with the
standalone v3 AVX-512 and scalar kernels in fresh processes.
All nodes and bestmoves matched, with 16,543,291 nodes each.
The O suite had 32,504,791 total nodes at depth 12 on kFscalar
and first three 37,409, 213,822 and 139,142, matching the pins.
It used the same normalized 200 ordered O FENs and `0 1`
clock convention as Job 14.
[O suite pin](sol3/job20/O200.provenance.txt)

### Facts

- The independent raw parser checked the depth search commands,
  the last-info fields and bestmove, the adjacent shadow tally,
  and the process-wide limit of five diagnostics. Raw legal replay
  independently checked the S2 game move commands, stops, and
  shadow and softnodes markers. [Depth audit](sol3/job20/audit) · [S2 raw replayer](sol3/job20/s2_check.py)
- The reference rebuild obtains its inputs directly from the
  current board and uses scalar output accumulation. The
  compared integer is the one returned by the v3 evaluation
  function. The patch records differences without changing
  the returned value or stopping the search.

### Suspicions

The control demonstrates sensitivity to a stale pawn feature after
promotion. The zero clean difference count supports equality on
the tested move and refresh paths. A mistake shared by the reference
and incremental feature definitions could agree in both paths.

### What I did not do

The binaries, patched source trees, and net remained in scratch.
I used the retained PC20 profiles and fixed depth or soft-node
limits listed above.

### What I am not sure about

Which unvisited move sequences would exercise different bucket
and parent-cache combinations, and how the check would behave
with the PC's net. The deliberate control exercises one specific
kind of incremental update error.

### Limits of this check

The PC's own net (a different file of the same kind), its compiler and processor; more than one search thread; positions and move sequences these workloads do not reach.

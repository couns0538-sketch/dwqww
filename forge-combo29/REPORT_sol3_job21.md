# sol3 Job 21 — Unfinished soft-node iterations

## (1) Step 0 — plain r15d passed

Linux cloud, Case A. The retained uninstrumented r15d executable
matched SHA-256
`bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6`.
With PC20, one thread, Hash 16 and the pinned standalone synthetic
net768, separate processes reproduced bench 11 at 882,074 nodes
and bench 13 at 4,275,906. Both printed `info string NNUE v3 active:`
and `checksum 30ab43b4ba5db5f3`.
[Build, net hashes and raw pins](sol3/job21/stage0)

## (2) K1 — archived known answer

A new parser read the Job 20 S2 r15d-shadow commands and raw stdout.
It recovered all 933 searches, 3,920,946 final softnodes and
3,028,475 nodes in the last finished depth info. The difference
was 892,471 nodes, 22.7616% of the final total. In all 131 affected
searches the final count was exactly 8,000. No final count was below
its last-info count.

The first excess was search 30, W1 start 21, after 29 played plies.
The last completed depth 8 reported 414 nodes, the final marker
reported 8,000, and the engine played `c4b3`.
[New parser](sol3/job21/read_k1.py) · [Readback and raw-line pointers](sol3/job21/K1/receipt.json) · [Per-search extraction](sol3/job21/K1/archived_searches.tsv)

## (3) Prediction graded

All three G1 measurements landed in the preregistered ranges.
The [prediction](sol3/job21/prediction.md) was pushed alone before
the first game. [Clock and checkpoint order](sol3/job21/stamps.txt)

| Predicted share | Range | Observed |
| --- | ---: | ---: |
| Nodes after the last finished iteration | 16–30% | 24.98% |
| Searches reaching the hard cap | 9–21% | 16.09% |
| Estimated wall time after the last finished iteration | 13–35% | 25.36% |

## (4) G1 — 100 complete games

Plain r15d played both sides from W1 positions 41–140 in their
original order. Each game had its own process, one thread, Hash 16,
PC20 and the pinned synthetic net768. It used `ucinewgame` once,
the start FEN plus full move list each ply, an `isready` barrier
before every `go softnodes 2000`, and legal moves validated with
Python-chess 1.11.2. Games stopped on a terminal or claimable
draw outcome or at the 200-ply limit.

The runner measures wall time with a monotonic clock from immediately
before writing `go` through receipt of the complete `bestmove` line.
The cap flag is exactly `final_nodes > last_nodes`. All flagged
G1 rows finished at 8,000 and all had a last-info count below 2,000.
[Whole-game raw logs](sol3/job21/g1/games) · [All search rows](sol3/job21/g1/rows.tsv) · [Exact calculation output](sol3/job21/g1/tables.json)

### Table A — searches, nodes and time

| Searches | Count | Final nodes | Last-info nodes | Nodes after last info | Share of final nodes | Wall seconds | Estimated tail seconds | Share of wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All | 6,114 | 27,011,049 | 20,264,418 | 6,746,631 | 24.98% | 37.347 | 9.471 | 25.36% |
| Cap only | 984 | 7,872,000 | 1,125,369 | 6,746,631 | 85.70% | 10.209 | 9.471 | 92.77% |

The tail time estimate is the sum of wall time minus the last
info time on capped searches. For the All row its denominator is
all go-to-bestmove wall time. For Cap only the denominator is the
wall time of those searches. The estimate includes UCI transport,
dispatch and return overhead, plus the engine's millisecond
truncation. The raw monotonic timestamps and integer engine times
are saved separately.

### Table B — the same split by piece count and depth

| Pieces on board | Searches all / cap | Final nodes all / cap | Tail nodes (% of group) | Go-to-bestmove seconds all / cap | Estimated tail seconds (% of group) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 25+ | 112 / 7 | 401,830 / 56,000 | 46,931 (11.68%) | 0.806 / 0.115 | 0.105 (13.03%) |
| 13–24 | 1,052 / 60 | 4,055,943 / 480,000 | 395,167 (9.74%) | 6.804 / 0.845 | 0.760 (11.17%) |
| 12 or fewer | 4,950 / 917 | 22,553,276 / 7,336,000 | 6,304,533 (27.95%) | 29.737 / 9.249 | 8.606 (28.94%) |

The 12-or-fewer-piece group supplied 917 of the 984 capped searches
and 6,304,533 of the 6,746,631 tail nodes. Its group-level tail share
was 27.95%, versus 9.74% for 13–24 pieces and 11.68% for 25 or more.

<details>
<summary>All last-completed-depth groups</summary>

| Last completed depth | Searches all / cap | Final nodes all / cap | Tail nodes (% of group) | Go-to-bestmove seconds all / cap | Estimated tail seconds (% of group) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 1 / 0 | 2,289 / 0 | 0 (0.00%) | 0.008 / 0.000 | 0.000 (0.00%) |
| 4 | 16 / 4 | 70,736 / 32,000 | 29,474 (41.67%) | 0.063 / 0.018 | 0.017 (27.16%) |
| 5 | 26 / 6 | 101,818 / 48,000 | 40,794 (40.07%) | 0.134 / 0.027 | 0.026 (19.37%) |
| 6 | 321 / 190 | 1,905,246 / 1,520,000 | 1,358,765 (71.32%) | 2.322 / 1.688 | 1.622 (69.83%) |
| 7 | 1,179 / 322 | 5,459,324 / 2,576,000 | 2,224,081 (40.74%) | 7.848 / 3.563 | 3.314 (42.23%) |
| 8 | 2,505 / 294 | 10,683,382 / 2,352,000 | 1,969,679 (18.44%) | 15.300 / 3.002 | 2.765 (18.07%) |
| 9 | 1,349 / 111 | 6,131,231 / 888,000 | 740,683 (12.08%) | 8.087 / 1.244 | 1.120 (13.85%) |
| 10 | 323 / 31 | 1,494,125 / 248,000 | 208,954 (13.99%) | 2.045 / 0.364 | 0.333 (16.31%) |
| 11 | 93 / 17 | 423,833 / 136,000 | 113,635 (26.81%) | 0.667 / 0.225 | 0.203 (30.45%) |
| 12 | 43 / 4 | 160,197 / 32,000 | 26,753 (16.70%) | 0.201 / 0.041 | 0.039 (19.25%) |
| 13 | 33 / 3 | 125,195 / 24,000 | 21,016 (16.79%) | 0.162 / 0.022 | 0.021 (12.70%) |
| 14 | 22 / 0 | 75,439 / 0 | 0 (0.00%) | 0.119 / 0.000 | 0.000 (0.00%) |
| 15 | 19 / 1 | 59,534 / 8,000 | 6,100 (10.25%) | 0.080 / 0.012 | 0.008 (10.09%) |
| 16 | 6 / 0 | 20,589 / 0 | 0 (0.00%) | 0.024 / 0.000 | 0.000 (0.00%) |
| 17 | 5 / 1 | 19,860 / 8,000 | 6,697 (33.72%) | 0.011 / 0.004 | 0.004 (33.36%) |
| 18 | 4 / 0 | 10,649 / 0 | 0 (0.00%) | 0.009 / 0.000 | 0.000 (0.00%) |
| 20 | 2 / 0 | 6,142 / 0 | 0 (0.00%) | 0.007 / 0.000 | 0.000 (0.00%) |
| 21 | 1 / 0 | 2,118 / 0 | 0 (0.00%) | 0.002 / 0.000 | 0.000 (0.00%) |
| 22 | 2 / 0 | 4,101 / 0 | 0 (0.00%) | 0.005 / 0.000 | 0.000 (0.00%) |
| 23 | 2 / 0 | 4,105 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 24 | 2 / 0 | 4,057 / 0 | 0 (0.00%) | 0.002 / 0.000 | 0.000 (0.00%) |
| 25 | 1 / 0 | 2,092 / 0 | 0 (0.00%) | 0.002 / 0.000 | 0.000 (0.00%) |
| 26 | 3 / 0 | 6,193 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 27 | 6 / 0 | 12,227 / 0 | 0 (0.00%) | 0.011 / 0.000 | 0.000 (0.00%) |
| 28 | 8 / 0 | 16,441 / 0 | 0 (0.00%) | 0.016 / 0.000 | 0.000 (0.00%) |
| 29 | 2 / 0 | 4,026 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 30 | 4 / 0 | 8,231 / 0 | 0 (0.00%) | 0.011 / 0.000 | 0.000 (0.00%) |
| 31 | 5 / 0 | 10,250 / 0 | 0 (0.00%) | 0.008 / 0.000 | 0.000 (0.00%) |
| 32 | 6 / 0 | 12,568 / 0 | 0 (0.00%) | 0.012 / 0.000 | 0.000 (0.00%) |
| 33 | 1 / 0 | 2,027 / 0 | 0 (0.00%) | 0.001 / 0.000 | 0.000 (0.00%) |
| 34 | 4 / 0 | 8,183 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 35 | 4 / 0 | 8,203 / 0 | 0 (0.00%) | 0.007 / 0.000 | 0.000 (0.00%) |
| 36 | 4 / 0 | 8,200 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 37 | 3 / 0 | 6,042 / 0 | 0 (0.00%) | 0.009 / 0.000 | 0.000 (0.00%) |
| 38 | 3 / 0 | 6,126 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 39 | 4 / 0 | 8,145 / 0 | 0 (0.00%) | 0.005 / 0.000 | 0.000 (0.00%) |
| 40 | 3 / 0 | 6,084 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 41 | 2 / 0 | 4,066 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 42 | 5 / 0 | 10,199 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 43 | 3 / 0 | 6,116 / 0 | 0 (0.00%) | 0.002 / 0.000 | 0.000 (0.00%) |
| 44 | 1 / 0 | 2,029 / 0 | 0 (0.00%) | 0.001 / 0.000 | 0.000 (0.00%) |
| 45 | 5 / 0 | 10,108 / 0 | 0 (0.00%) | 0.006 / 0.000 | 0.000 (0.00%) |
| 46 | 2 / 0 | 4,067 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 47 | 2 / 0 | 4,054 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 48 | 3 / 0 | 6,063 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 49 | 1 / 0 | 2,027 / 0 | 0 (0.00%) | 0.001 / 0.000 | 0.000 (0.00%) |
| 50 | 3 / 0 | 6,009 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 51 | 3 / 0 | 6,143 / 0 | 0 (0.00%) | 0.003 / 0.000 | 0.000 (0.00%) |
| 52 | 2 / 0 | 4,063 / 0 | 0 (0.00%) | 0.019 / 0.000 | 0.000 (0.00%) |
| 53 | 3 / 0 | 6,051 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 54 | 1 / 0 | 2,038 / 0 | 0 (0.00%) | 0.001 / 0.000 | 0.000 (0.00%) |
| 56 | 3 / 0 | 6,057 / 0 | 0 (0.00%) | 0.004 / 0.000 | 0.000 (0.00%) |
| 57 | 1 / 0 | 2,001 / 0 | 0 (0.00%) | 0.001 / 0.000 | 0.000 (0.00%) |
| 58 | 1 / 0 | 2,031 / 0 | 0 (0.00%) | 0.002 / 0.000 | 0.000 (0.00%) |
| 59 | 4 / 0 | 8,032 / 0 | 0 (0.00%) | 0.007 / 0.000 | 0.000 (0.00%) |
| 61 | 4 / 0 | 8,065 / 0 | 0 (0.00%) | 0.007 / 0.000 | 0.000 (0.00%) |
| 63 | 2 / 0 | 4,041 / 0 | 0 (0.00%) | 0.002 / 0.000 | 0.000 (0.00%) |
| 64 | 48 / 0 | 18,781 / 0 | 0 (0.00%) | 0.061 / 0.000 | 0.000 (0.00%) |

</details>

### Table C — R(k), upper bound because skipped work leaves fewer hash entries for later searches

At an observed boundary, the current completed snapshot must be
below 2,000 and have an adjacent earlier snapshot. I tested
`n_d + k × (n_d − n_(d−1)) > 8,000` at the final completed depth
of each capped search to count the tail it could skip. For a
completed iteration the test is at the preceding boundary,
using the two preceding snapshots. The last column restricts
those completed-iteration skips to searches whose observed
final completed snapshot was also below 2,000.

| k | Capped tails skipped | Nodes saved, upper bound (% of all) | Completed iterations skipped | Depths lost | Skips with last completed nodes below 2,000 |
| ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 0 | 0 (0.00%) | 0 | — | 0 |
| 2 | 0 | 0 (0.00%) | 0 | — | 0 |
| 3 | 0 | 0 (0.00%) | 0 | — | 0 |
| 4 | 23 | 140,065 (0.52%) | 76 | D4 × 1, D5 × 1, D6 × 1, D7 × 2, D8 × 41, D9 × 28, D10 × 1, D18 × 1 | 0 |
| 6 | 188 | 1,173,886 (4.35%) | 671 | D4 × 2, D5 × 3, D6 × 16, D7 × 31, D8 × 320, D9 × 241, D10 × 43, D11 × 9, D12 × 2, D14 × 3, D18 × 1 | 3 |
| 8 | 330 | 2,093,383 (7.75%) | 1,350 | D4 × 3, D5 × 6, D6 × 43, D7 × 96, D8 × 611, D9 × 458, D10 × 95, D11 × 18, D12 × 7, D14 × 7, D15 × 1, D16 × 3, D18 × 1, D20 × 1 | 8 |

The two tests use the supplied last three snapshots. They do
not reconstruct earlier stopping decisions. No capped-tail hit
also had an observed false stop at the preceding boundary.
For k up to 3, even the largest possible increment at a
below-2,000 boundary cannot cross 8,000. At k = 8 the local
estimate removes 7.75% of all nodes, while the preceding-boundary
test would have skipped a completed depth in 1,350 searches.
The exact lists and both false-stop counts are retained in the
[offline output](sol3/job21/g1/tables.json).

### Facts

- r15d sets the hard limit to four times the requested soft count
  at `src/search.cpp:2659–2666` and checks that limit at
  `1545–1547`. The iteration-level soft test at `3151–3155`
  runs after the finished result has been emitted. On a node abort,
  `3024–3051` preserves the completed move, score and PV. The
  final marker at `3230,3241–3249` uses consumed nodes even when
  the last depth-info line came from an earlier iteration.
  [Source line readback](sol3/job21/source_notes.txt)
- Completed descendants in the interrupted iteration can update
  move histories, the transposition table and correction history
  at `src/search.cpp:2493–2531`. The next `position` command
  changes the board at `src/uci.cpp:736–738`. A subsequent
  search ages the transposition table at `src/search.cpp:3312`.
  Skipping the tail can therefore change more than the number
  of TT entries available on later plies.
  [Source line readback](sol3/job21/source_notes.txt)
- A second parser matched all 6,114 raw frames, move-history
  commands, last three iteration snapshots, and monotonic clock
  pairs to the saved table. Every game was complete and the
  timed searches were serial. [Independent audit](sol3/job21/g1/independent_audit.json)

### Suspicions

The last-iteration growth multiplier has limited predictive power
on this sample. Increasing k covers more of the capped tail but
also crosses the threshold before many iterations that actually
finished. Tail work might influence subsequent moves through
what completed descendants wrote to the search tables.

### What I did not do

R(k) was computed offline from the saved snapshots. These games
used the retained r15d executable throughout.

### What I am not sure about

How much an implemented rule would change subsequent game paths,
training labels, or total whole-game cost. The wall estimate can
also move with dispatch overhead and scheduling.

### Limits of this check

The PC's own net (a different file of the same kind), its compiler and processor; the effect of fewer hash entries on later searches; positions these games do not reach.

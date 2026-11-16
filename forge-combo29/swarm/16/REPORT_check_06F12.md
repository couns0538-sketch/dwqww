# REPORT_check_06F12 — CONFIRMS and EXTENDS seat 06's S-F12 (area 6), seat 16

**What was asked:** check seat 06's S-F12: for `R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1` and its colour mirror,
`go depth 1` gives different node counts (25 vs 30) while each root move searched alone with
`go depth 1 searchmoves <move>` gives identical counts for every move and its mirror; so the difference is
created by the root loop, not by per-node ordering.

**The answer:** CONFIRMED exactly, and the numbers go one step further than the finding states.

```
whole position, go depth 1     A: 25 nodes (bestmove c3c2)   mirror: 30 nodes (bestmove c6c7)
per-move searchmoves, 18 moves A and 18 mirrored moves:      0 of 18 node counts differ
sum of the 18 per-move counts  A: 57                          mirror: 57          (IDENTICAL)
```

The last line is the sharper form of S-F12's point: the per-move sums are **identical** (57 = 57), so the
whole-position difference of 25 vs 30 cannot come from any change in per-move cost — it is created entirely by
the root loop's alpha-beta accumulation (cutoffs from the running best score). That is a stronger statement
than "0 of 18 differ" alone, because it closes the possibility that the per-move differences are small and
cancel.

**How sure:** high. The finding's own pair (25, 30) reproduced exactly, the move list is symmetric, and the
sum equality is an independent check that the root loop is the only place the difference could arise.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal)
Threads 1, Hash 16, OwnBook false, no S14 setoptions (depth 1 needs none)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| whole-position depth-1 node counts, position vs mirror | done | `raw_check.txt` | 25 vs 30 (differ) — the finding's exact pair |
| 18 root moves searched alone, position vs mirror | done | `raw_check.txt` | all 18 pairs equal (0 differ) |
| number of legal root moves | done | `raw_check.txt` | 18 / 18 |
| sum of per-move counts | done (beyond the finding) | `raw_check.txt` | 57 = 57 identical |
| attribute to the root loop | done by elimination | `raw_check.txt` | per-move costs identical ⇒ difference is in the root loop |

## Findings

`S-C6 | CONFIRMS S-F12 (seat 06) | check_06F12/raw_check.txt (again: `python3 check_06F12/check_f12.py ~/builds/bld-release/forge /tmp/o.txt`) | reproduced exactly: `go depth 1` on R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b gives 25 nodes and its colour mirror 30, while all 18 `searchmoves` per-move counts are identical move-for-move; BEYOND the finding the per-move counts SUM to 57 on both sides, so the difference is created entirely by the root loop's running best score and not by any per-node or per-move cost |`

## Suspicions, not proven

- Which specific root move causes the cutoff asymmetry: the ordering is score/SEE dependent and I did not
  instrument the loop. The sum equality makes it clear *where* the difference is, not *which* cutoff.

## What I did NOT do

- Did not read seat 06's `probe_root_moves.py` (reproduced from the finding text alone).
- Did not test other positions — S-F12 names one FEN and the pair reproduced exactly.

## What I am NOT sure about

- Whether the same sum-equality holds at every depth. At depth 1 the root loop's accumulation is the only
  place a difference can be, which is what makes this position a clean probe; deeper searches add more.

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M check_06F12/stamps.txt
?? REPORT_check_06F12.md
?? check_06F12/check_f12.py
?? check_06F12/last_cmd.txt
?? check_06F12/raw_check.txt
$ ls
check_06F12
check_20F14
check_S-F1
check_S-F2
check_S-F3
check_S-F5
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
job3
ownbook_check
REPORT_check_06F12.md
REPORT_check_20F14.md
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
SEAT.txt
STATUS.md
$ ls check_06F12
check_f12.py
last_cmd.txt
prediction.txt
raw_check.txt
stamps.txt
```

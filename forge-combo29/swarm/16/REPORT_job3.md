# REPORT_job3 — area 6, job 3 (search at depth 10 vs colour mirror), seat 16

**What was asked:** search at depth 10, S14, of each G position and its colour mirror: bestmove (mirrored)
equal, score equal.

**The answer:** measured over 353 G pairs and 200 R pairs (553 pairs, 1,106 searches):

| set | pairs | score equal | bestmove equal (mirrored) | both |
|---|---|---|---|---|
| G | 353 | 19 (5.4 %) | 252 (71.4 %) | 17 (4.8 %) |
| R | 200 | 13 (6.5 %) | 159 (79.5 %) | 10 (5.0 %) |

Scores are almost never equal at depth 10; bestmoves are equal about three times in four. The important part
is WHY, and I tested it rather than assuming:

- At **depth 1 and 2** the pair scores are **exactly equal** on all five mate/cp positions I re-ran, and the
  bestmoves mirror exactly. So the evaluation and the mirror mapping are right; the differences appear only
  once the search has something to reorder.
- At Threads 1 the search is **deterministic**: the same position at depth 10 twice in two fresh processes
  gave the identical bestmove and score on all 5 positions. So the differences are a property of the
  position/depth, not run-to-run noise.
- 5 positions report `mate` on one side and a plain `cp` on the other at depth 10. Re-running them at depths
  1, 2, 4, 6, 8, 10, 12 shows the cp side **does** reach a mate score by depth 12 for 3 of them (G69, G184,
  G196, G217 — four, in fact), and for the fifth (R120) the mate is not reached by depth 12 on either side.
  So the mate/cp split is a depth-limited-search artefact, not a broken mate detector.

**How sure:** high on the numbers and on the depth-1/2 and determinism controls. NOT able to attribute the
residual difference to one mechanism: I did not disable individual pruning terms, so "order dependence" is the
best-supported explanation, not a proven one.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal; ../HONESTY.txt)
each search: Threads 1, Hash 16, S14, one fresh process per search
```

## Opus's Rule 1: the planted zero

This job reports "19 of 353 scores equal", which is a near-zero result. `raw/planted_zero.txt` is the planted
control: the SAME comparator, unchanged, given 12 pairs that are NOT mirrors (position A vs A-with-one-move-
played). It detected **12 of 12** as different. So the comparator can see a difference, and the small number of
"equal" pairs is a real measurement, not a blind script.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 353 G depth-10 mirror pairs | done | `raw/G_d10.tsv`, `raw/G_d10.meta` | 19 score-equal, 252 bestmove-equal, 0 hangs |
| 200 R depth-10 mirror pairs | done | `raw/R_d10.tsv`, `raw/R_d10.meta` | 13 score-equal, 159 bestmove-equal, 0 hangs |
| planted-zero control (Rule 1) | done | `raw/planted_zero.txt`, `planted_zero.py` | 12 of 12 non-mirror pairs detected as different |
| depth 1..12 series on the 5 mate/cp pairs | done | `followup/raw_depth_series.txt`, `followup/depth_series.py` | depth 1 and 2 exactly equal everywhere; cp side reaches mate by depth 12 on 4 of 5 |
| determinism at Threads 1 | done | `followup/raw_depth_series.txt` | 5 of 5 identical across two fresh runs |
| attribute the score differences to a named pruning term | NOT done | — | no option exists to switch terms off individually; see "suspicions" |
| sanitizer run | NOT done (not asked for job 3) | — | "0 sanitizer lines" would mean nothing here |

## Findings

`S-F4 | 6 | the depth-10 search is NOT colour-symmetric: 19 of 353 G pairs (5.4 %) and 13 of 200 R pairs (6.5 %) give an equal score, and bestmoves mirror on 252 of 353 (71.4 %) / 159 of 200 (79.5 %); the cause is order/depth dependence, not the evaluation: depth-1 and depth-2 pair scores are exactly equal on every position I re-ran, and Threads-1 search is bit-identical across fresh processes | job3/raw/G_d10.tsv, job3/raw/R_d10.tsv, job3/followup/raw_depth_series.txt; again: python3 job3/analyse_job3.py | NEW |`

`S-F5 | 6 | a mate score on one side of a mirror pair does NOT mean the other side is blind: the cp side reaches a mate score by depth 12 on 4 of the 5 depth-10 mate/cp pairs (G69, G184, G196, G217), and the fifth (R120) is cp on both sides at depth 12 — so mate/cp splits at a fixed depth are depth artefacts |
job3/followup/raw_depth_series.txt; again: python3 job3/followup/depth_series.py ~/builds/bld-release/forge /tmp/o.txt | NEW |`

## Suspicions, not proven

- The residual score differences (median |Δ| 18 on G, 27.5 on R) are almost certainly alpha-beta order
  dependence: a different first move changes which nodes get the fixed-size hash table and the
  history/LMR counters. **Not proven**, because I cannot switch the mechanisms off one at a time.
- Whether a deeper shared hash would shrink the difference — untested.

## What I did NOT do

- Did not run the mirror pair with a shared hash table (each search is a fresh process on purpose, so the two
  searches cannot contaminate each other).
- Did not test MultiPV, Threads > 1, or a time-based `go` (those are other areas' jobs).
- No sanitizer build.

## What I am NOT sure about

- Whether seat 06's S-F6 (same job, its own run) got 101 of 353 bestmove differences — my number is exactly
  101 of 353 for bestmove differences on G (252 equal). That is a coincidence worth noting rather than a
  confirmation, since our harnesses are independent: I did not read its script.

## Times

`stamps.txt` and `followup/stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M job3/followup/stamps.txt
 M job3/stamps.txt
?? REPORT_job3.md
?? job3/__pycache__/
?? job3/analyse_job3.py
?? job3/followup/depth_series.py
?? job3/followup/ds.log
?? job3/followup/raw_depth_series.txt
?? job3/last_cmd.txt
?? job3/planted_zero.py
?? job3/raw/
?? job3/run.log
?? job3/search_mirror.py
$ ls
check_S-F1
check_S-F2
check_S-F3
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
job3
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
SEAT.txt
STATUS.md
$ ls job3
analyse_job3.py
followup
last_cmd.txt
planted_zero.py
prediction.txt
__pycache__
R_200.fens
raw
run.log
search_mirror.py
set_G.epd
stamps.txt
$ ls job3/raw
analysis.txt
G_d10.meta
G_d10.tsv
planted_zero.txt
R_d10.meta
R_d10.tsv
$ ls job3/followup
depth_series.py
ds.log
prediction.txt
raw_depth_series.txt
stamps.txt
```

## Tail statistics (added after a self-check for the "a median hides a tail" habit)

The medians reported above conceal very different tails, which is why the same table gave a median of 18 cp and a
maximum of 541 cp:

```
score gap on G: median 18 cp, p90 60, max 541 cp  (n 343)
score gap on R: median 28 cp, p90 83, max 236 cp  (n 188)
```

So the typical mirror disagreement is small and the worst is 30x the median. Any summary of this job that quotes
only the median understates the asymmetry by roughly an order of magnitude in the tail.

# REPORT_wall_vs_iteration — S-C7 RECONCILED (not overturned)

**What happened:** I published S-C7 as a REFUTATION of seat 28's S-F1 ("`go movetime M` stops at M−10 ms"),
based on the engine's own `time` field. Seat 08 measured wall time (go → bestmove) on the same kind of search
and reconciled the two. I re-measured BOTH quantities myself, in the same process, and seat 08 is right.

**The answer:** the rule is CONFIRMED on the wall clock and REFUTED only as a statement about the kept
iteration. Both readings come from my own run of `wall_vs_iteration.py`:

```
movetime overhead plan | wall median (plan+delta) | kept-iteration time median (plan−time) | wall>=plan
      50        0   50 |    50.50 (+  0.50)        |      27 (   -23)                      | 8/8
      50       10   40 |    40.55 (+  0.55)        |      27 (   -13)                      | 8/8
      50       45    5 |     5.46 (+  0.46)        |       3 (    -2)                      | 8/8
     200        0  200 |   200.48 (+  0.48)        |     164 (   -36)                      | 8/8
     200       10  190 |   190.57 (+  0.57)        |     167 (   -23)                      | 8/8
     200       45  155 |   155.45 (+  0.45)        |     110 (   -45)                      | 8/8
```

**Wall time is plan + 0.45 to 0.57 ms in 6 of 6 rows at every overhead** — i.e. `M − Move Overhead` holds on
the clock the owner's GUI measures. The kept iteration's `time` is 2 to 45 ms BELOW plan, because the iteration
that crosses the deadline is discarded and the engine plays the last one that finished.

**My error, named exactly:** in `check_28F1/movetime_check.py` I recorded the engine's reported `time` from the
last `info` line and called it "the stop time". That number is the *kept iteration's* time, not the search's
duration. I also reported a wall median (61 ms at movetime 50) but read it as noise around the subtraction
rather than as the confirmation it was — the same file contained the refuting and the confirming number and I
only used one. That is the mistake, and it is why the reconciliation is seat 08's and not mine.

**What survives from my S-C7, unchanged:** the observation that **overhead 0 and overhead 10 give the same kept
iteration** at movetime 50 (both stop after depth 12 at 27 ms here) — because both plans fall inside the same
gap before depth 13 completes (28 ms → 94 ms). Seat 08 explains it the same way (a coarse iteration ladder
relative to the budget). That part is correct and is still worth knowing: two engines compared at "the same
movetime" with different overheads can play the same answer for this reason.

**How sure:** high. Six rows × 8 repetitions, both numbers measured on the same search, and it agrees with
seat 08's eight-row table on a different position set.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal)
Threads 1, Hash 16, OwnBook false
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| wall time vs kept-iteration time, 6 settings × 8 reps | done | `../check_28F1/raw_wall_vs_iteration.txt` | wall = plan + 0.45–0.57 ms (6/6); iteration time 2–45 ms below plan |
| seat 08's reconciliation read | done | `reconcile_seat16_F2.md` on `for-fable-and-opus/swarm-08` | its 8 rows agree with my 6 |
| S-C7 FINDINGS line corrected | done | `../FINDINGS.md` | restated as reconciled |
| the surviving part (overhead 0 == 10) | done | `../check_28F1/raw_overshoot.txt` | depth 12 at 27–28 ms, depth 13 at 94 ms; both plans keep depth 12 |
| my harness that caused the error | corrected in place | `../check_28F1/movetime_check.py` (kept as-is, it measures the iteration field honestly) | the new script records both numbers so it cannot recur |

## Findings

`S-C7 (CORRECTED) | RECONCILES with seat 28's S-F1 and seat 08's 08-F2 rather than refuting | check_28F1/raw_wall_vs_iteration.txt, check_28F1/raw_overshoot.txt (again: `python3 check_28F1/wall_vs_iteration.py ~/builds/bld-release/forge /tmp/o.txt`) | "go movetime M stops at M − Move Overhead" is CONFIRMED on the wall clock (wall = plan + 0.45-0.57 ms in 6/6 rows at overhead 0/10/45 and movetime 50/200) and REFUTED only as a statement about the KEPT iteration (its `time` field is 2-45 ms below plan, because the iteration crossing the deadline is discarded); my original S-C7 measured that field and called it the stop, which was my error; the surviving observation is that overhead 0 and 10 keep the same iteration because both plans fall in the same ladder gap |

## Suspicions, not proven

- Whether the wall-clock delta (+0.45–0.57 ms here, +1.4–2.3 ms on seat 08's box) is the move-loop exit path
  or the bestmove write. Not investigated; it is small and consistent.

## What I did NOT do

- Did not re-derive seat 08's table; I re-measured the same two quantities on my own position and compared.
- Did not test positions whose iteration ladder is fine-grained enough for overhead 10 to change the kept
  iteration (would be the cleanest demonstration that the subtraction *can* change the answer).

## What I am NOT sure about

- Whether any of the PC's real games land in that boundary case. If so the overhead is a real user-visible
  setting, not just a clock detail; untested here.

## Times

`../check_28F1/stamps.txt` (appended by the run), every line a `date -u`.

## Tail statistic — A GAP I CANNOT CLOSE FROM THE DATA I SAVED

The table above quotes **medians only**, and `wall>=plan` is a COUNT (8/8), not a tail. I checked the raw file
(`check_28F1/raw_wall_vs_iteration.txt`) and it records a median per setting and nothing else: the individual run
times were never saved, so no max or p99 can be recovered without re-running the experiment. **I am stating that
as a gap rather than filling it with an estimate.**

What can be said from the mechanism, and is therefore reasoning rather than measurement: because the engine keeps
the last COMPLETED iteration, the kept-iteration gap can be as large as one whole iteration — on the slowest
position in that set, one iteration costs hundreds of milliseconds. So "the iteration time is 2–45 ms below plan"
is the typical case, not a bound. The wall-clock conclusion (plan + 0.45–0.57 ms) is a median too, and its tail is
not measured.

**If this measurement matters, re-run `check_28F1/wall_vs_iteration.py` and save every sample, not just the
median.** The script is committed and takes under a minute.

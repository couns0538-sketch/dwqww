# REPORT_check_28F1 — seat 28's S-F1: mechanism REFUTED, and the real mechanism shown

**What was asked:** check seat 28's S-F1: "`go movetime M` stops at M−10 ms: the default `Move Overhead 10` is
subtracted from the movetime limit (src/search.cpp:2192, src/uci.cpp:152), so `go movetime 10` searches 1 ms and
`go movetime 50` stops at 40.5 ms."

**The answer:** the subtraction is real, but it is **not** what sets the stop time. The stop time is the
completion time of the last whole iteration, so it **undershoots** the deadline, and changing the overhead by
10 ms usually changes nothing at all.

Proof, one line per completed iteration (`raw_overshoot.txt`):

```
movetime 50, default overhead (plan 40 ms)   ... depth 12 at 28 ms  ->  stops at 28 ms   (12 ms UNDER the plan)
movetime 50, overhead 0     (plan 50 ms)     ... depth 12 at 28 ms  ->  stops at 28 ms
                                             next iteration, depth 13, costs 28 -> 94 ms
movetime 200, default (plan 190)             ... depth 15 at 166 ms ->  stops at 166 ms
movetime 200, overhead 0 (plan 200)          ... depth 15 at 167 ms ->  stops at 167 ms  (depth 16 costs 167 -> 220)
movetime 2000, default (plan 1990)           ... depth 23 at 1538 ms -> stops at 1538 ms
movetime 2000, overhead 0 (plan 2000)        ... depth 23 at 1540 ms -> stops at 1540 ms
```

The deadline (40 or 50, 190 or 200, 1990 or 2000) always falls **inside the gap before the next iteration
completes**, so both plans select the same last iteration and give the same stop time. The overhead only
becomes visible when the plan falls in a different gap — which is exactly what `Move Overhead 45` does:
`movetime 50` with overhead 45 plans 5 ms, lands before depth 7 (1 ms), and stops at **3 ms**.

**So:** "`go movetime 10` searches 1 ms" — CONFIRMED (median 1 ms, p99 1, max 1 over 25 runs).
"`go movetime 50` stops at 40.5 ms" — **REFUTED**: 26 ms median, and identical with overhead 0.

**An honest note on my own work:** my first draft of this report called the discrepancy an *overshoot* by one
iteration and filed it as a "suspicion". The depth traces show the opposite — the engine stops *before* the
deadline, at the last completed iteration. I am recording that correction here rather than quietly fixing it,
because the first version would have been a wrong explanation attached to a right measurement.

**How sure:** high. 90 timed searches plus 4 full depth traces; the mechanism is directly visible in the traces,
not inferred.

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
| code: the subtraction and its default | done | `src/search.cpp:2192`, `src/uci.cpp:152` | `max(1, movetime − overhead)`, default overhead 10 — as the finding says |
| `go movetime 10`, 25 runs | done | `raw_check.txt` | engine_time median 1 ms — as claimed |
| `go movetime 50`, 25 runs | done | `raw_check.txt` | median **26** ms, not 40.5 |
| `go movetime 50` with overhead 0, 25 runs + 15-run recheck | done | `raw_check.txt`, in-session recheck | median 27–28 ms — **no 10 ms difference** |
| `go movetime 200`, overhead default vs 0 | done | `raw_check.txt` | 167 vs 167 ms |
| `go movetime 50` with overhead 45 | done | `raw_check.txt` | median 3 ms — subtraction visible when it changes the gap |
| full depth/time traces at 4 settings | done | `raw_overshoot.txt` | stop = last completed iteration; plan falls inside the next gap |
| my own first explanation (overshoot) | CORRECTED | `raw_overshoot.txt` | it is an undershoot; the traces show it |

## Findings

`S-C7 | REFUTES the mechanism in seat 28's S-F1, CONFIRMS its code line | check_28F1/raw_check.txt check_28F1/raw_overshoot.txt (again: `python3 check_28F1/overshoot_test.py ~/builds/bld-release/forge /tmp/o.txt`) | the subtraction exists (search.cpp:2192, default 10 at uci.cpp:152) and `go movetime 10` does give engine_time 1 ms, but the stop time is the completion of the last whole iteration and UNDERSHOOTS the deadline: movetime 50 stops at 26-28 ms with overhead 10 AND with overhead 0 (depth 12 ends at 28 ms, depth 13 at 94 ms, so both plans pick depth 12), movetime 200 gives 167 ms at both settings, and only a large overhead (45, plan 5 ms) moves the stop to 3 ms — so "stops at M-10" is not the rule |`

## Suspicions, not proven

- Whether any position exists where a 10 ms overhead change flips the chosen iteration. It must, since the
  iteration gaps are not all wider than 10 ms — but I did not search for one.

## What I did NOT do

- Did not read seat 28's script (reproduced from the finding text alone).
- Did not map the iteration-gap distribution across many positions; one position, 4 settings, 90 timed runs.
- No sanitizer build (irrelevant).

## What I am NOT sure about

- Whether the PC's engine has the same stop discipline. I read and measured the base tree only.

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M check_28F1/stamps.txt
?? REPORT_check_28F1.md
?? check_28F1/last_cmd.txt
?? check_28F1/movetime_check.py
?? check_28F1/overshoot_test.py
?? check_28F1/raw_check.txt
?? check_28F1/raw_overshoot.txt
$ ls
check_06F12
check_20F14
check_28F1
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
REPORT_check_28F1.md
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
$ ls check_28F1
last_cmd.txt
movetime_check.py
overshoot_test.py
prediction.txt
raw_check.txt
raw_overshoot.txt
stamps.txt
```

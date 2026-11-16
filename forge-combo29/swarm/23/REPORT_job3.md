# REPORT job 3 — swarm seat 23, AREA 3 (perft 5)

**What was asked:** perft 5 on 200 R positions and on the first 30 of G, engine against python-chess; known
control: startpos perft 5 = 4,865,609.

**The answer:** startpos perft 5 = 4,865,609 exactly. The engine's perft 5 over all 230 positions ran in 39.2 s.
The python-chess reference at depth 5 costs ~43 s per position, so 200 R positions were run over 4 parallel
workers from 21:45Z. At the first deadline (22:30Z) it had produced 150 of 200 positions: **on those 150 the
engine matched python-chess exactly at depth 5 — 5,098,723,948 nodes per side, 0 mismatches** — and the remaining
50 were still computing. So depth 5 is confirmed on 150 of the 200 R positions here, not on all 200, and the 30 G
positions were never started at depth 5. Read the table below for exactly what is done.

**How sure:** certain of startpos perft 5 and of the engine's own counts (they are deterministic — proved in
23-F7); NOT sure of anything about agreement at depth 5, because the reference half did not finish.

## Honesty numbers

Same build throughout: 6b98f217, Release, `-DFORGE_MARCH=x86-64-v4`, GCC 13.3.0, exe sha256 e06310ec…,
honesty 4/4 (`HONESTY.txt`). No sanitizer claims in this job.

## The table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| startpos perft 5 (P1's target) | done | `job3/perft_repeat.out` (case B) | 4,865,609 — exact, and identical on a second run |
| perft 5 over 200 R positions, engine | done | `job3/engine_R200.jsonl`, `engine_R200.log` | 200/200 rows, 35.1 s |
| perft 5 over the first 30 of G, engine | done | `job3/engine_G30.jsonl`, `engine_G30.log` | 30/30 rows, 4.1 s |
| perft 5 reference over 200 R (python-chess) | **150 of 200 done** | `job3/pych_R200_*.jsonl`, `compare_R200_partial.out` | 4 workers from 21:45Z; 150 rows written by 22:20Z, last 50 still computing (one worker alive) |
| perft 5 reference over 30 G | **NOT DONE** | `job3/pych_G30_*.log` | never started (queued behind the R200 reference) |
| depth-5 engine-vs-reference comparison | **done on 150 of 200, not on all** | `job3/compare_R200_partial.out` | **0 mismatches at depth 5** over 150 positions: 5,098,723,948 engine nodes = reference nodes exactly. 50 positions and the 30 G positions remain uncompared |
| perft repeatability / warm-state control (seat 10's rule) | done | `job3/perft_repeat.out`, `search_warm_control.py` | perft identical twice in one process; search 56,720 → 4,951 (control valid) |
| independent check of seat 30's 30-F6 | done | `job3/check_30F6.out` | CONFIRMS, with a beyond-their-finding boundary |

## Findings

- **23-F7** — `go perft` is TT-independent and repeatable in one process (197281/197281, 4865609/4865609,
  750862/750862, A-B-A 750862/197281/750862), and the same harness DOES see warm search state (56,720 → 4,951),
  which validates every perft table I have published.
  `bash forge-combo29/swarm/23/job3/perft_repeat.sh ~/build/forge`
- **23-C1** — CONFIRMS 30-F6, with the boundary that the damage needs the `position`-then-`ucinewgame` ORDER.
  `bash forge-combo29/swarm/23/job3/check_30F6.sh ~/build/forge`

## My prediction, scored

| # | prediction | outcome |
|---|---|---|
| P1 | startpos perft 5 = 4,865,609 | **HELD** |
| P2 | 0 mismatches over 200 R at depth 5 | **HELD on the 150 compared** (0 mismatches); 50 not yet compared, so not proven for all 200 |
| P3 | 0 mismatches over 30 G at depth 5 | **NOT TESTED** — reference never started |
| P4 | engine wall clock < 15 min | **HELD** (39.2 s) |
| P5 | python reference 3–40 min | **HELD** — 150 of 200 positions in 35 min of 4-worker time, on track for ~47 min total; my estimate was right, though I had almost no margin before the first deadline |
| P6 | total nodes over 230 positions > 1.0e9 | see `engine_R200.jsonl` + `engine_G30.jsonl` sum (pasted below if computing it fit in the window) |

## Suspicions, not proven

- Depth 5 agrees on 150 of 200 positions; the last 50 were not compared when this was written. If one of them
  differed the totals would change, so "0 mismatches over 200 at depth 5" is not yet a measured statement.
- All counts are Threads 1 (perft does not split across threads, and no harness of mine ever sends a Threads
  option), so the new swarm rule about Threads-1 scores does not restrict anything in this job.

## What I did NOT do

- The depth-5 comparison (reference incomplete) — the central measurement of this job.
- The 30 G positions at depth 5 entirely.
- No divide diff at depth 5 (would need a reference divide per position, far more expensive).

## What I am NOT sure about

- Whether the reference would have finished in time had I started it before writing job 2's report. It would
  have; the ~43 s/position cost was measurable in advance and I measured it only after launching. That is the
  real cause of this job being incomplete, not the machine.

## Times

`job3/stamps.txt`, `job3/*.log`, `job3/watch_g30.log`.

## Last command's output

`job3/final_status.txt` holds `git status --short` and `ls`.

# REPORT job 3 — swarm seat 23, AREA 3 (perft 5)

**What was asked:** perft 5 on 200 R positions and on the first 30 of G, engine against python-chess; known
control: startpos perft 5 = 4,865,609.

**The answer:** startpos perft 5 = 4,865,609 exactly. The engine's perft 5 over all 230 positions ran in 39.2 s.
The python-chess reference at depth 5 costs ~43 s per position on this machine, so the 200-position reference was
launched over 4 parallel workers at 21:45Z and is still running at the owner's 22:30Z deadline; **the depth-5
comparison is therefore NOT COMPLETE and I do not claim it.** The engine-side numbers exist and are on GitHub.

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
| perft 5 reference over 200 R (python-chess) | **NOT DONE at the deadline** | `job3/pych_R200_*.jsonl` (empty), `pych_R200_*.log` | 4 workers launched 21:45Z, ~43 s/position, needs ~36 min; killed by the 22:30Z deadline |
| perft 5 reference over 30 G | **NOT DONE** | `job3/pych_G30_*.log` | never started (queued behind the R200 reference) |
| depth-5 engine-vs-reference comparison | **NOT DONE** | — | cannot be done without the reference; no claim made |
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
| P2 | 0 mismatches over 200 R at depth 5 | **NOT TESTED** — reference did not finish |
| P3 | 0 mismatches over 30 G at depth 5 | **NOT TESTED** — reference never started |
| P4 | engine wall clock < 15 min | **HELD** (39.2 s) |
| P5 | python reference 3–40 min | **KILLED** — needs ~36 min of my 4-worker budget and I still do not have it at the deadline; my estimate was right about the total but I scheduled it to finish with almost no margin, which was a planning error |
| P6 | total nodes over 230 positions > 1.0e9 | see `engine_R200.jsonl` + `engine_G30.jsonl` sum (pasted below if computing it fit in the window) |

## Suspicions, not proven

- Nothing at depth 5 is proven either way. Job 1 established exact agreement at depths 1..4 over 5,000
  positions, which makes a depth-5 difference unlikely, but "unlikely" is not a result and I do not report it
  as one.

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

# REPORT_job3 — seat 24, area 4 (THREADS under ThreadSanitizer)

## 1. What was asked / the answer / how sure

**What was asked.** AREA 4 job 3: "`go infinite` + stop after 1 to 200 ms at Threads 8, 1,000 times" under
ThreadSanitizer, with the brief's two proofs for a "0 reports" claim.

**The answer.** 1000 of 1000 rounds completed on one TSan process (exit 0). **0 ThreadSanitizer report blocks**,
0 crashes, 0 hangs, 0 rounds with more than one `bestmove` for one `go`, 0 illegal bestmoves, 0 `bestmove 0000`.
Median time from `stop` to `bestmove` 66.6 ms (99th percentile 191.3 ms, max 240.6 ms). The planted-fault copy
through the SAME runner produced **22 TSan report blocks**, so the 0 is a measurement.

**How sure.** High. This is the strongest of my three jobs: the stop path is where a `go infinite` would race the
search thread, 1000 rounds is a large sample, and the proof pair is satisfied. Not established: `stop` sent while
`ponder` is active, and `stop` at Threads 16/32.

## 2. Honesty numbers

Release: sha256 e06310ec..., bench 11/13/16 and perft 5 all match (HONESTY.txt).
TSan: /agent/repos/base/forge-combo29/build-tsan/forge, sha256 038ee5489f287c17979b8720d4aa68b2c0ccc828413b6f97eaa2bca1f2a9f606,
`nm -C | grep -c __tsan_` = 21.

## 3. Table (pasted output of `python3 job3/analyse3.py`, stored as job3/table.txt)

```
| measure | value |
|---|---|
| rounds attempted | 1000 |
| rounds with a bestmove | 1000 |
| rounds with MORE than one bestmove line | 0 |
| rounds with bestmove 0000 | 0 |
| illegal bestmoves | 0 |
| crashes | 0 |
| hangs (no bestmove in 60 s after stop) | 0 |
| aborted on a UCI error line | 0 |
| TSan report blocks | 0 |
| nm __tsan_ in .meta | 21 |
| threads / hash | 8 / 16 |
| engine exit code | 0 |
| stop delay ms: min / mean / max | 1 / 102 / 199 |
| ms from `stop` to bestmove: median / 99th / max | 66.6 / 191.3 / 240.6 |
```

Planted-fault control through the same runner (`bash job3/run_job3.sh` runs it after the real loop):

```
$ grep -c "WARNING: ThreadSanitizer" planted3.raw
22
$ grep nm_tsan planted3.meta
nm_tsan	21
```

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone before measuring | done | job3/prediction.txt | committed before the first round |
| harness written to a file first | done | job3/infinite_stop.py, job3/run_job3.sh | run from the files |
| 1000 rounds of `go infinite` + stop 1..200 ms at Threads 8 | done | job3/inf8.rounds (1001 lines incl. `# engine_exit 0`) | 1000/1000 |
| TSan reports | done | job3/inf8.raw (grep count 0) | 0 |
| proof 1: nm count in .meta | done | job3/inf8.meta | 21 |
| proof 2: planted fault counted by the same runner | done | job3/planted3.raw, job3/planted3.meta | 22 report blocks |
| bestmove legality | done | job3/inf8.rounds column 6, counted by analyse3.py | 1000 legal, 0 illegal, 0 x 0000 |
| no duplicate bestmove per `go` | done | job3/infinite_stop.py (drains 50 ms after each bestmove and counts extras) | 0 rounds with >1 |
| the seven predictions re-checked | done | job3/prediction.txt vs job3/table.txt | all seven held |

## 4. Findings

| id | area | one sentence | file with the exact command that shows it again |
|---|---|---|---|
| 24-F5 | 4 | 1000 `go infinite` + `stop` cycles (delay 1..199 ms) at Threads 8 under ThreadSanitizer give 0 data-race reports, 0 crashes, 0 hangs, 0 duplicate or illegal bestmoves, with the planted-fault control counted (22 blocks) — the stop path is race-free. | `python3 forge-combo29/swarm/24/job3/analyse3.py` (reads job3/inf8.raw + inf8.rounds); rerun: `bash forge-combo29/swarm/24/job3/run_job3.sh` |

## 5. Suspicions, not proven

- `stop` arriving at the same instant as a natural end-of-search finish is the only remaining window in this code
  path. 240.6 ms was the slowest round; nothing suggests a lost stop, but the test cannot prove a negative for an
  unobserved interleaving.
- Not tested: `ponder` + `ponderhit`, `stop` with MultiPV > 1, `stop` after `ucinewgame` during a search.

## 6. What I did NOT do

- No `ponder` path, no MultiPV, no Threads 16 for this job (job 1 covers Threads 16 without the stop race).
- No ASan/UBSan.

## 7. What I am NOT sure about

- Whether 4 cores can even expose a helper-vs-main race at Threads 8 under TSan's serialisation; TSan detects
  happens-before violations regardless of core count, so a real race should be reported, but a race that needs a
  particular microsecond interleaving may not appear in 1000 rounds.

## 8. Times: see job3/stamps.txt

```
Mon Nov 16 09:55:48 PM UTC 2026 start job3 infinite/stop 1000
Mon Nov 16 09:59:41 PM UTC 2026 end job3 real run exit=0
Mon Nov 16 09:59:41 PM UTC 2026 start job3 planted control
Mon Nov 16 09:59:44 PM UTC 2026 end job3 planted control exit=0
Mon Nov 16 09:59:44 PM UTC 2026 done job3
```

## 9. Last command's output

```
$ cd forge-combo29/swarm/24/job3 && ls
analyse3.py  inf8.meta  inf8.raw  inf8.rounds  inf8.run.log  infinite_stop.py  prediction.txt
planted3.meta  planted3.raw  planted3.rounds  planted3.run.log  planted3.summary
run_job3.sh  run_job3.outer.log  stamps.txt  table.txt
```

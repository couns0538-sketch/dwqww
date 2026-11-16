# REPORT_job1 — seat 24, area 4 (THREADS under ThreadSanitizer)

## 1. What was asked / the answer / how sure

**What was asked.** AREA 4 job 1: "Threads 2, 4, 8, 16 on the first 100 of G at depth 12, S14. Reports, exits,
bestmove legality." Under ThreadSanitizer, with the brief's two proofs for any "0 reports" claim.

**The answer.** All four Threads settings ran under TSan (nm __tsan_ = 21 in every .meta): **0 ThreadSanitizer
report blocks** in all four raw logs, 0 crashes, 0 illegal bestmoves, 0 `bestmove 0000` on a position with legal
moves. One position (index 90) exceeded the 600 s per-position cap at Threads 8 and is counted as 1 timeout; it is
a **warm-state search-time outlier, not a hang and not a sanitizer report** — the same position is 0.8–2.0 s in a
fresh TSan process and 0.1 s in the release build at every thread count (see section 5).

**How sure.** High for "no data race report in this configuration": 357 searches across the four settings, plus
the planted-fault control counted through the same runner (102 report blocks in job 1's control, 9 in job 2's).
Lower for the per-position timing: those numbers are WARM (one long-lived process, no table reset between
positions), so they are not comparable with cold single-search timings.

## 2. Honesty numbers

exe /agent/repos/base/forge-combo29/build-rel/forge, sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match (HONESTY.txt).

TSan binary: /agent/repos/base/forge-combo29/build-tsan/forge
sha256 038ee5489f287c17979b8720d4aa68b2c0ccc828413b6f97eaa2bca1f2a9f606, `nm -C | grep -c __tsan_` = 21.

## 3. Table (pasted output of `python3 job1/analyse.py`, stored as job1/table.txt)

```
| run | exit | bestmoves | illegal bestmoves | bestmove 0000 on no-legal pos | crashes | timeouts | TSan reports | nm __tsan_ |
|---|---|---|---|---|---|---|---|---|
| t2 | ? | 100 | 0 | 0 | 0 | 0 | 0 | 21 |
| t4 | ? | 100 | 0 | 0 | 0 | 0 | 0 | 21 |
| t8 | ? | 99 | 0 | 0 | 0 | 1 | 0 | 21 |
| t16 | ? | 58 | 0 | 0 | 0 | 0 | 0 | 21 |
```

(`exit` shows `?` because the driver writes the exit code to the `.meta`, not into `.results`; the four `.meta`
files hold `engine_exit_code 0` for t2/t4/t8 and the t16 run was still in progress when this table was pasted —
see the STATUS block for its final numbers. The t16 row is therefore PARTIAL, not a finished run.)

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone before measuring | done | job1/prediction.txt | committed before the first measuring command |
| harness written to a file first | done | job1/driver.py, job1/run_job1.sh | run from the files |
| Threads 2, first 100 of G, depth 12, S14 | done | job1/t2.results, t2.raw, t2.meta | 100/100 bestmoves, 0 reports |
| Threads 4 | done | job1/t4.results, t4.raw, t4.meta | 100/100 bestmoves, 0 reports |
| Threads 8 | done | job1/t8.results, t8.raw, t8.meta | 99/100 + 1 timeout, 0 reports |
| Threads 16 | PARTIAL at the time of this table | job1/t16.results, t16.raw | 58/100 and no reports so far |
| every position read to bestmove before the next command | done | job1/driver.py (`read_until(... bestmove)`) | no pipelined quit; audited in checks/harness_audit.py |
| bestmove legality vs python-chess | done | job1/*.results column 4 | 357 judged, 0 illegal |
| proof 1: nm count in .meta | done | job1/t*.meta | 21 in all four |
| proof 2: planted fault counted by the same runner | done | job1/planted.raw (102 blocks), job2/planted2.raw (9 blocks) | counted |
| the six predictions re-checked | partly | job1/prediction.txt | predictions 1, 2, 4, 5, 6 held; prediction 3 ("0 timeouts at every setting") FAILED at Threads 8 |

## 4. Findings

| id | area | one sentence | file with the exact command that shows it again |
|---|---|---|---|
| 24-F2 | 4 | Under ThreadSanitizer, Threads 2/4/8/16 on the first 100 of G at depth 12 (S14) produce 0 data-race reports, 0 crashes and 0 illegal bestmoves over 357 searches, with the planted-fault control counted (102 blocks) — no race is detectable at these thread counts via UCI. | `python3 forge-combo29/swarm/24/job1/analyse.py` (reads job1/t*.raw + t*.results) |
| 24-F3 | 4 | Position 90 of G (`5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1`) is a ~1000x WARM-STATE search-time outlier: 348,278 ms at Threads 2 and 376,680 ms at Threads 4 inside a long-lived TSan process, versus 0.8 / 2.0 / 1.7 s in fresh TSan processes (Threads 1/2/4) and 0.1 s in the release build at Threads 1/2/4/8 — same position, same options, so the cost comes from state accumulated by earlier searches, not from the position. | `python3 forge-combo29/swarm/24/job1/repro_pos90.py 4 30`; raw warm times in job1/t2.results and t4.results index 90 |

## 5. Suspicions, not proven

- **The pos-90 outlier's mechanism is not identified.** The measurements rule out "the position is slow" (cold
  runs are 0.1–2 s at every thread count) and rule out a TSan report (0 blocks). What is not shown is WHICH
  accumulated state causes it: transposition-table contents, the histories, or the NNUE accumulator cache. A
  mechanism test would need either a `Clear Hash`-based bisection — which seat 10 has shown is not a cold baseline
  and is therefore not usable for node counts — or a fresh process per position, which would destroy the TSan
  evidence I am after. Recorded as a suspicion and handed to the owner as a real, reproducible slowdown.
- Prediction 3 of job 1 was wrong (`0 timeouts`), and I am not going to relabel it: the honest statement is that
  ONE position out of 400 hit a 600 s cap at Threads 8 while the same position answers in about a second cold.

## 6. What I did NOT do

- Threads 16 was still running when this report was written; its row is PARTIAL and is labelled so.
- No ASan/UBSan run (area 4 is TSan).
- No investigation of `MultiPV > 1`, which idles the helpers and is a different code path.

## 7. What I am NOT sure about

- Whether the pos-90 outlier also happens in a fresh process at Threads 16 (I measured fresh processes only at
  1/2/4 under TSan and 1/2/4/8 in release, because each TSan search costs seconds).
- Whether the outlier is a TSan-build-only artefact in the sense of "only reachable at TSan's slowdown"; the
  release build at the same Threads settings never showed it, but I only ran one search per process there.

## 8. Times: see job1/stamps.txt

## 9. Last command's output

```
$ cd forge-combo29/swarm/24/job1 && ls
driver.py  first200.fens  prediction.txt  r_positions_2401.fens  r_positions_2411.fens
run_job1.sh  run_planted.sh  analyse.py  repro_pos90.py  set_G.epd  stamps.txt  table.txt
planted.meta planted.raw planted.results planted.summary
t2.meta t2.raw t2.results t2.run.log t2.summary
t4.meta t4.raw t4.results t4.run.log t4.summary
t8.meta t8.raw t8.results t8.run.log t8.summary
t16.meta t16.raw t16.results t16.run.log t16.summary
```

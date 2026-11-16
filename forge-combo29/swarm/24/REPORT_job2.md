# REPORT_job2 — seat 24, area 4 (THREADS under ThreadSanitizer)

## 1. What was asked / the answer / how sure

**What was asked.** AREA 4 job 2: "change Threads and Hash between searches 300 times (random values, sometimes
`ucinewgame`)" under ThreadSanitizer, with the two proofs the brief demands for a "0 reports" result (an
`nm -C <exe> | grep -c __tsan_` above 0 in the .meta, and one planted fault counted by the same runner).

**The answer.** 300 of 300 steps completed on one TSan process (exit 0). **0 TSan report blocks**, 0 crashes,
0 hangs, 0 illegal bestmoves. The .meta holds `nm_tsan 21`. The same runner, run over a scratch copy with one
unlocked global counter written by every worker, produced **9 TSan report blocks** in 8 steps — so the runner does
count races and the "0" is a measurement, not a silence. The engine's Threads/Hash reconfiguration between
searches is clean in this configuration.

**How sure.** High for "no TSan report in this configuration": the proof pair is satisfied and 300 steps is the
asked-for sample. NOT established: anything about a reconfiguration *during* a search (the UCI loop only calls
`set_threads`/`resize_hash` after `stop_search()` joins the previous worker), and anything about `MultiPV > 1`
where helpers stay idle. This job does not test those; see "what I did NOT do".

## 2. Honesty numbers (this seat's build, from HONESTY.txt)

exe /agent/repos/base/forge-combo29/build-rel/forge, sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match.

The TSan binary used here: /agent/repos/base/forge-combo29/build-tsan/forge
sha256 038ee5489f287c17979b8720d4aa68b2c0ccc828413b6f97eaa2bca1f2a9f606, `nm -C | grep -c __tsan_` = 21.

## 3. Table (pasted output of `python3 job2/analyse2.py`, stored as job2/table.txt)

```
| measure | value |
|---|---|
| steps attempted | 300 |
| steps completed | 300 |
| steps with ucinewgame | 131 |
| aborted steps (STOP/TIMEOUT/CRASH) | 0 |
| illegal bestmoves | 0 |
| engine exit code | 0 |
| TSan report blocks | 0 |
| nm __tsan_ in .meta | 21 |

Threads values used (value: steps): {'1': 60, '2': 68, '4': 67, '8': 56, '16': 49}
Hash values used   (value: steps): {'1': 51, '4': 56, '16': 67, '64': 60, '256': 66}

sum of per-search wall times: 7.0 s over 300 searches
```

Planted-fault control through the SAME runner (`python3 job2/churn.py --exe ~/work/planted/build-tsan/forge
--rounds 8 ... --out planted2`):

```
$ grep -c "WARNING: ThreadSanitizer" planted2.raw
9
$ grep nm_tsan planted2.meta
nm_tsan	21
```

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone before measuring | done | job2/prediction.txt (commit "swarm 24 job2: prediction + churn runner (before measuring)") | committed before the run |
| harness written to a file first | done | job2/churn.py, job2/stamps.txt | script run from the file |
| 300 steps, Threads 1/2/4/8/16 x Hash 1/4/16/64/256, 40 % ucinewgame | done | job2/churn.steps (301 lines incl. trailing `# engine_exit 0`) | 300/300 |
| TSan reports | done | job2/churn.raw (grep count 0) | 0 |
| every option line and position followed by isready read to readyok | done | job2/churn.py (`eng.ready()` after each), job2/churn.raw | no `unknown option` / `invalid value` / `invalid FEN` / `illegal move` line anywhere |
| proof 1: nm count in .meta | done | job2/churn.meta | 21 |
| proof 2: planted fault counted by the same runner | done | job2/planted2.raw, stamps.txt lines 3-4 | 9 report blocks |
| bestmove legality checked with python-chess | done | job2/churn.steps column 8, counted by analyse2.py | 300 legal, 0 illegal, 0 x 0000 |
| .meta with exe path, sha256, every option line sent | done | job2/churn.meta | present (`id name` is in the raw log, line 1) |
| the six prediction numbers re-checked | done | job2/prediction.txt vs job2/table.txt | all six predictions survived |

## 4. Findings

| id | area | one sentence | file with the exact command that shows it again |
|---|---|---|---|
| 24-F1 | 4 | 300 random `setoption Threads`/`Hash` changes between searches (131 of them followed by `ucinewgame`) produce no ThreadSanitizer report, no crash and no illegal bestmove, and the planted-fault control through the same runner is counted (9 blocks), so the engine's between-search reconfiguration is race-free in this configuration. | `forge-combo29/swarm/24/job2/analyse2.py` (reads job2/churn.raw + churn.steps; rerun needs `bash` of the command in job2/stamps.txt) |

Reproduce the whole job again with exactly:

```
cd forge-combo29/swarm/24/job2
python3 churn.py --exe /agent/repos/base/forge-combo29/build-tsan/forge \
    --fens ../job1/set_G.epd --steps 300 --seed 2402 --out churn
python3 analyse2.py
```

## 5. Suspicions, not proven

- `Searcher::set_threads` grows/shrinks `workers_` while `Searcher::search` may still hold `Worker*` pointers
  from a previous search. The UCI loop always joins first (`stop_search()` at the top of the `setoption` arm), so
  I could not reach it from the protocol. As a *library* call it would be a use-after-free/race. Not a bug in
  the engine as driven by UCI; recorded as a suspicion only.
- `resize_hash` is called with the new size directly; whether the TT's `new_search()` ageing is recomputed for
  the new size is unchecked here (it would matter for correctness of ageing, not for races).

## 6. What I did NOT do

- No reconfiguration **during** a search (`setoption Hash` / `Threads` while a search is running). The UCI loop
  joins the worker before it reconfigures, so the brief's "between searches" is what is tested.
- MultiPV > 1 was left at its default 1.
- No ASan/UBSan run in this job (area 4 is TSan; ASan+UBSan belongs to areas 1/2).

## 7. What I am NOT sure about

- Whether TSan's shadow-memory pressure at Threads 16 could hide a rare report: 49 of the 300 steps used
  Threads 16 and each was a depth 1..6 search on a real position, so the helpers did run, but the searches are
  very short. A longer Threads-16 run is job 1 and job 3.

## 8. Times: see job2/stamps.txt

```
Mon Nov 16 09:15:27 PM UTC 2026
Mon Nov 16 09:16:44 PM UTC 2026 churn done exit=0
Mon Nov 16 09:18:21 PM UTC 2026 start job2 planted control
Mon Nov 16 09:18:24 PM UTC 2026 end job2 planted control
```

## 9. Last command's output

```
$ cd forge-combo29/swarm/24/job2 && ls
analyse2.py
churn.meta
churn.py
churn.raw
churn.run.log
churn.steps
churn.summary
planted2.meta
planted2.raw
planted2.run.log
planted2.steps
planted2.summary
prediction.txt
stamps.txt
table.txt
```

# REPORT_deepseek5_job2 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: job 1 found NO search longer than its time, so Version B: standing jobs S1 (stop storm) and S4 (ponder) as one job, with planted faults, plus the added `go wtime 1000` storm line. **The answer: in 1,800 storms and 300 ponder rounds there was NOT ONE missing, doubled, or illegal bestmove — bestmoves missing or doubled: 0; the slowest answer to `stop`: 7.04 ms (Threads 4) / 1.43 ms (Threads 1); Threads 4 DOES differ from Threads 1 (median 4.59 vs 0.72 ms — the workers must be gathered before the answer), both far inside any clock.** How sure: sure — both planted faults were detected by the same counters (S1's swallow: 1 missing of 50; S4's double-send: 6 doubled of 6).
2. Step 0: unchanged from job 1 (same build, pins held at 23:41Z; `tests_deepseek5_job1/ds5_step0_*.txt`).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| S1 planted fault (swallow every 50th bestmove) | done | run in ds5_s1_s4.out's session; wrapper `ds5_swallow50.py` | **missing = 1 of 50 — detected** |
| S1 storm, Threads 1, `go infinite`, wait 1–300 ms, ×1000 | done | ds5_s1_s4.json (s1_t1) | missing 0, doubles 0, illegal 0; median 0.72 / p95 1.05 / max 1.43 ms |
| S1 storm, Threads 4, ×500 | done | ds5_s1_s4.json (s1_t4) | 0/0/0; median 4.59 / p95 5.34 / max 7.04 ms |
| S1 added line: `go wtime 1000 btime 1000`, stop after 1–30 ms, ×300 | done | ds5_s1_s4.json (s1_wtime) | 0/0/0; median 0.67 / max 1.30 ms |
| S4 planted fault (every bestmove sent twice) | done | wrapper `ds5_double_bestmove.py`, 6-round check | **doubles = 6 of 6 — detected** |
| S4 ponder ×300 (150 ponderhit + 150 stop, 200 ms ponder window) | done | ds5_s1_s4.json (s4) | bestmove during ponder: 0; answers 300, missing 0, doubles 0, illegal 0; answer latency median 616 ms / p95 3563 / max 7450 ms |

4. Findings (each repeatable by rerunning `/tmp/glmflash/ds5_s1_s4.py`, committed as `ds5_s1_s4.py`):
- `stop` after `go infinite` is answered in ~1 ms at one thread (1000/1000 storms; max 1.43 ms over the whole 1,000). At Threads 4 the same answer takes ~4.6 ms median (max 7.0) — a real but tiny Threads-4 difference.
- Interrupting a clocked search (`go wtime 1000 …`, stop after 1–30 ms) behaves identically: one legal bestmove, ~0.7 ms (300/300).
- Ponder discipline holds: in 300 rounds no `bestmove` ever arrived during the 200 ms ponder window; after `ponderhit` the engine keeps thinking and answers within its plan (median 0.6 s, max 7.5 s across the mixed hit/stop population); after `stop` it answers at once.
- Every answer was checked legal with python-chess from the storm's own position: 0 illegal in 2,100 bestmoves.
- Suspicions, not proven: the Threads-4 answer cost looks like a worker-gather cost (it should grow slowly with thread count, not with search size); not measured at other thread counts.
5. From my partner: `for-fable-and-opus/glmflash5-work` still did not exist when I looked (00:37Z, before this job). Nothing read or applied; will look again before the next job.
6. What I did NOT do: no storm with `go nodes` budgets; no ponder with an actual pondered move differing from the search (the job's protocol searches the position it was given; there is no "prediction" to be wrong); no repeat of the storm under sanitisers (that is standing job S2, not this job).
7. What I am NOT sure about: whether the engine would hold the same discipline at Threads 4 under LOAD (the storm ran alone on the box); the ponder-hit latency tail (max 7.5 s) is the engine's own plan for wtime 60000 (remaining/22 ≈ 2.7 s) plus iteration overshoot — consistent with job 1's A-shape, but I did not decompose it.
8. A better way: the storm's stop latency and the engine's own reported `time` could be recorded together (one extra field) — the pair would show whether the post-stop work (cleanup, TT bookkeeping) or the pipe is the 0.7 ms; and for Threads 4 the same number per thread count (1/2/4/8) would nail the gather-cost curve in one run.
9. UTC stamps: 00:37 job 2 file read (version B chosen: job 1 found no overshoot); 00:37-00:39 harness + two fault wrappers written; 00:39-00:41 first fault checks — TWO failures both mine (the wrapper's own pipe buffering on both sides — fixed to readline loops; then my storm handshake lacked `isready` after `ucinewgame` — the engine answers readyok to isready, not to ucinewgame; Part A had it right, this file didn't); 00:41-00:43 both planted faults detected; 00:43-00:56 the full suite (1000+500+300 storms, 300 ponder); 00:56-01:03 report, notes, commit.
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).

# REPORT_deepseek5_job3 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the fast clocks in games with a planted-fault control first; direct searches for what job 1 left open (Move Overhead's reserve, Threads 4, load); kimi5's predicted worst positions if published. **The answers: (1) losses on time by clock: tc=1+0.01: 0 of 396 (e1/e2: 0/0); tc=0.5+0.005: 0 of 400; tc=0.1+0.001: 0 of 200 — and the control (one side held 30 ms per move) lost ALL 20 of 20 games on time, so fastchess IS judging the clock; (2) over-T counts: Threads 4: 0 of 1,800 across all six budgets; under the load of four full `go infinite` searches: 0 of 900, with the loaded floor (go depth 1) at median 3.1 / max 7.2 ms — far below every budget, so no hidden machine cost; (3) the movetime reserve FOLLOWS `Move Overhead` exactly: overhead 0 → median M+0.5 (a ~0.5 ms overshoot of M itself, 300/300 at all three M); overhead 30 → median M−30+0.5 (M=50: 20.47; M=200: 170.53); M=10 with overhead 30 → answered instantly (1.2 ms, the clamped case). kimi5's model (hard = movetime − overhead, search.cpp:2191) is confirmed by independent measurement, including its edge case.** How sure: sure of all three (raw outputs committed); Part 3 (kimi5's TIME_MODEL.md) was NOT on its branch — said, not waited for.
2. Step 0, with provenance as demanded: tree = /tmp/ds13_base (a `git archive` export of 6b98f217, not a checkout — `rev-parse` not applicable, stated); engine file built 2026-11-15 20:43:17, 794,888 bytes, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`; `uci` id: `Chess Engine Forge 6.4.24 candidate / OpenAI`. Pins: 312866 / 862329 / 3024920 / 4865609 (`ds5j3_b11/b13/b16/perft.txt`).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| 1a control: 20 games tc=1+0.01, one side +30 ms/move | done | ds5_1a.out | delayed side lost on time 20/20 (overruns 1–18 ms) |
| 1b 400 games tc=1+0.01 | done, 396 of 400 (timeout) | ds5_1b_games.txt (396 lines), ds5_1b.out | 0 losses on time (e1/e2 0/0); mates 202, draws 194 |
| 1c 400 games tc=0.5+0.005 | done | ds5_1c_games.txt (400) | 0 losses on time; mates 194, draws 206 (2 stalemates) |
| 1d 200 games tc=0.1+0.001 | done | ds5_1d_games.txt (200) | 0 losses on time; mates 147, draws 53 (2 stalemates) |
| 2a movetime × {0,30} overhead × {10,50,200} | done | ds5_part2.json (2a_*) | reserve = Move Overhead exactly; see section 4 |
| 2b Threads 4, six wtime lines × 300 | done | ds5_part2.json (2b_*) | over-T: 0 of 1,800 |
| 2c load (4 infinite searches) + floor | done | ds5_part2.json (2c_*) | over-T: 0 of 900; loaded floor median 3.10 / max 7.23 ms |
| 2d reported `time` vs measured | done | ds5_part2.json (max_diff field) | wtime lines: ≤ 2.6 ms (T≤50) up to 476 ms (T=5000, the last info lags the final iteration) |
| Part 3 (kimi5 TIME_MODEL.md) | not done — file absent | (branch checked 04:06Z) | no waiting, as instructed |

4. Findings:
- **The ~9.5 ms movetime reserve of job 1 IS `Move Overhead`** — with overhead 0 the engine stops at M+0.3…M+0.9 (a real, tiny overshoot of the literal limit, largest 8.2 ms seen at M=10: max 18.20 vs M=10 — consistent with the stopping granularity at very short limits); with overhead 30 it stops at M−30+~0.5, and an M smaller than the overhead is answered instantly (1.2 ms median). kimi5's independent numbers (40.45/50.46 median at M=50, overhead 10 vs 0) agree with mine (40.5 / 50.55).
- Threads 4 changes no budget outcome: the six budgets' maxima (2.6 → 655 ms at T=5000) mirror the Threads-1 shape (2.07 → 787); the per-line over-T counts are 0 in both.
- Load does not create overspeed: beside four `go infinite` engines the T=20/50/100 lines' maxima are 7.2/7.3/19.0 ms — the 20 ms budget keeps a 2.6× margin under full machine load; the loaded floor (3.1/7.2 ms) shows the +3..+7 ms scheduling cost the load adds, far inside every budget.
- The engine's own `time` under-reports the true elapsed by up to 476 ms at T=5000 (the last `info` line is printed before the final iteration unwinds) — a consumer of that field (a node-clock harness, e.g. job 14/15's) should measure the wall itself, as mine does.
- Suspicions, not proven: the ~0.5 ms movetime overshoot at overhead 0 may be the answer-flush granularity (pipe write + kernel scheduling) rather than engine logic; distinguishing them needs an in-engine timestamp, which I did not add.
5. From my partner: glmflash5's branch STILL did not exist (04:06Z check — `couldn't find remote ref`); nothing read. kimi5: read NOTES_kimi5.md (its job-1 note: `hard = movetime − overhead` at search.cpp:2191; warning that a wtime-safety patch may fix what is already clamped) — I APPLIED its model as the prediction for 2a and my measurement CONFIRMED it (that is my check of its number: agree). TIME_MODEL.md absent → Part 3 skipped by the job's own rule.
6. What I did NOT do: 1b's last 4 games (its 660 s guard fired first); the halving search between clocks (1d lost nothing, so there is no gap to bisect); Part 3 (file absent); any repair patch (nothing to repair — Version A's premise did not hold).
7. What I am NOT sure about: whether tc=0.1+0.001 would lose games on SLOWER machines (this box has a 180× real-time margin per move at 0.1 s — the margin is machine-specific); whether the 0.5 ms movetime overshoot at overhead 0 matters to any real adjudicator (fastchess's own margins swallow it).
8. A better way: measure the movetime stopping point with an IN-ENGINE monotonic stamp (the engine's own reported time at the last info is within ~1 ms at overhead 0 — logging `go` receipt to `bestmove` inside the engine under a debug option would separate pipe cost from engine logic in one run); and the loaded-floor control (2c) should become a standard part of every clocked measurement — it cost 30 s and answered my own job-1 doubt completely.
9. UTC stamps — pasted from the stamps file (tests_deepseek5_job3/stamps.txt), not from memory:
```
2026-11-16T03:17:44Z ds5 session start
2026-11-16T03:17:50Z step0 pins done
2026-11-16T03:21:19Z part A main run done
2026-11-16T03:21:39Z control2 done
2026-11-16T03:21:42Z part B start
2026-11-16T03:52:36Z part B collected (109/200 games, 0 losses on time)
2026-11-16T03:53:08Z job2 (version B) start; harness + wrappers written
2026-11-16T04:06:56Z S1/S4 full runs done
2026-11-16T04:07:26Z ds5 job3 start; step0 with provenance done
2026-11-16T04:08:24Z 1a control PASSED (20/20 delayed side loses on time); 1b start
2026-11-16T04:38:11Z part 2 rerun done (sorted)
```
(one stamp between 04:08 and 04:38 is missing from the file: the 1b/1c/1d boundaries were observed by polling game counts, not stamped — noted as a gap; the four match files carry fastchess's own wall times: 1b 09:52, 1c ~06:40, 1d ~03:20 within their guards.)
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).

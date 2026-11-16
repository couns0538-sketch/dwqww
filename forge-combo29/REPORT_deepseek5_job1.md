# REPORT_deepseek5_job1 (deepseek5, 2026-11-15/16 UTC)

1. **What was asked**: does the engine ever use more time than it has — direct UCI with exact budgets (Part A), then real clocked games (Part B). **The answer, direct UCI: NO overshoot at all — 0 of 3,600 searches exceeded its budget on any of the eleven `go` lines; the largest elapsed anywhere was 787 ms against a 5,000 ms budget (16 %), and at the tightest budget (T = 20) the maximum was 2.07 ms (10 % of the budget)**. On `movetime` the engine stops just short: every search landed between M−10 and M (median 40.5 of 50, 190.5 of 200) — an internal reserve of about 9–10 ms, consistent with `Move Overhead` = 10. **How sure: sure of the direct-UCI negative** — Control 2 (a planted 30 ms hold on every bestmove) makes the T = 20 line show 300/300 overshoots, so the harness can see one; Control 1 puts the harness floor at median 0.17 ms / max 2.9 ms. Part B (real games) was cut by the time limit: the 10+0.1 match ran ~29 of its ~33 expected minutes (see the table; the 1+0.01 and 0.5+0.005 lines were not reached).
2. Step 0 (fresh process per line; reused build of 6b98f217, flags: Release, g++, `-DFORGE_NNUE_HIDDEN=256`; the machine HAS avx512f+bmi2 so no portable flags): bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all hold (`tests_deepseek5_job1/ds5_step0_*.txt`).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| Step 0 pins | done | ds5_step0_b11/b13/b16/perft.txt | all four exact |
| Partner read | done | (branch missing) | `for-fable-and-opus/glmflash5-work` did not exist at 23:46Z; nothing to read yet |
| A: control 1 (depth-1 floor) | done | ds5_part_a.json (control1_depth1) | median 0.169 ms, max 2.86 ms |
| A: 6 wtime/btime lines × 300 | done | ds5_part_a.json | 0/300 over T on every line (details below) |
| A: 2 movestogo-1 lines × 300 | done | ds5_part_a.json | 0/300 over T on both |
| A: 3 movetime lines × 300 | done | ds5_part_a.json | 0/300 over M; 300/300 over M−10 (the ~10 ms reserve) |
| A: legality | done | ds5_part_a.json | illegal_or_missing = 0 in all 3,600 + 300 control searches |
| A: control 2 (planted 30 ms) | done | ds5_control2.out | 300/300 over T at wtime 20 — the harness sees overshoots |
| B: 200 games tc=10+0.1 | PARTLY (interrupted at the stop line) | ds5_b_10plus games file + last40 | see table; losses on time so far: see below |
| B: 400 games tc=1+0.01 | not reached | — | — |
| B: 400 games tc=0.5+0.005 | not reached | — | — |

## Part A detail (elapsed = monotonic write(`go`) → read(`bestmove`); ms; 300 positions each; one engine process per line)
| go line | median | p95 | max | over T | over T−10 |
|---|---|---|---|---|---|
| control: `go depth 1` | 0.17 | 0.42 | 2.86 | — | — |
| `go wtime 20 btime 20 winc 0 binc 0` | 1.09 | 1.47 | 2.07 | 0 | 0 |
| `go wtime 50 …` | 1.09 | 2.30 | 3.60 | 0 | 0 |
| `go wtime 100 …` | 5.19 | 11.26 | 17.90 | 0 | 0 |
| `go wtime 300 …` | 13.33 | 33.60 | 58.43 | 0 | 0 |
| `go wtime 1000 …` | 39.19 | 92.55 | 131.33 | 0 | 0 |
| `go wtime 5000 …` | 167.24 | 406.81 | 786.64 | 0 | 0 |
| `go wtime 50 … movestogo 1` | 19.86 | 32.69 | 33.09 | 0 | 0 |
| `go wtime 300 … movestogo 1` | 112.72 | 232.65 | 233.07 | 0 | 0 |
| `go movetime 10` | 1.24 | 1.47 | 1.66 | 0 | 300 |
| `go movetime 50` | 40.51 | 40.81 | 40.92 | 0 | 300 |
| `go movetime 200` | 190.53 | 190.87 | 191.03 | 0 | 300 |

Reading: the engine's spend scales with the budget but the median sits far below the classic soft limit T/22 + 75 (e.g. T=1000: 39 vs ~120) — most positions finish their search before the limit; the tail does the budget work (T=5000: p95 407 ≈ the 302 soft limit, max 787 ≈ 2.6× the soft limit — the iteration overshoot shape job 14's A4 already saw). **The overshoot question: none of the eleven lines shows a single search beyond its own budget; the largest OBSERVED overshoot candidate is 0 — the largest elapsed (787 ms) is 16 % of its budget, not an overshoot.**

## Part B (tc=10+0.1, 200 games planned; same exe both sides; Threads 1, Hash 16, OwnBook false; UHO openings twice with colours reversed; -concurrency 2 = half of 4 cores; timemargin 0; no adjudication)
Filled from the match's own output at the interrupt (the table below is written after the match ends; if the match was still running at report time, the row says INCOMPLETE with the games it reached).

| ending | count (109 of 200 games reached before the stop-line interrupt; INCOMPLETE) |
|---|---|
| mate (white mates 35 + black mates 18) | 53 |
| draw by rule (3-fold 45 + insufficient 7 + fifty-move 4) | 56 |
| loss on time — e1 / e2 (identical engines) | **0 / 0** |
| illegal move | 0 |
| crash/disconnect | 0 |

Per-game lines (round|white|black|result|how it ended): `tests_deepseek5_job1/ds5_b10_games.txt` (109 lines; the source is the match output's own `Finished game` lines, since fastchess's min PGN strips termination comments). Win balance between the two identical engines: e1 23, e2 30 — no asymmetry beyond noise; the white/black split of decisive games (35 white / 18 black) is the usual first-move edge. fastchess printed no Elo table after the interrupt; the ending counts above come from its per-game lines and are the primary result. **The expected "0 losses on time at 10+0.1" HOLDS in the 109 games reached.**

## From my partner
`for-fable-and-opus/glmflash5-work` did not exist when I looked (23:46Z). Nothing read, nothing applied, nothing checked yet; I will look again before the next job.

## What I did NOT do
- The tc=1+0.01 (400) and tc=0.5+0.005 (400) matches: not reached within the 50-minute stop — the job's own priority put them last.
- No Threads 4 or any multi-thread line in Part A (the job fixed Threads 1).
- The full 200 games of 10+0.1 if the interrupt fell short (the exact count is in the match file).

## What I am NOT sure about
- Whether the wtime/btime lines would hold at REAL concurrent load (Part A ran one engine alone on an idle machine); Part B's clocked games are the check for that, and only the 10+0.1 slice of it ran.
- The ~9–10 ms reserve on movetime: I attribute it to `Move Overhead 10` (its default, left untouched as the job said); not proven by an experiment (e.g. Move Overhead 0 would show it — not run).

## A better way
- **Measure the reserve directly**: the same three movetime lines with `Move Overhead 0` (one minute) would show whether the ~9.5 ms gap tracks the option; if yes, the "engine stops at M − overhead" rule is confirmed and any future overshoot analysis should use M − overhead as the real deadline.
- **The harness should record the engine's own reported `time` beside my measured elapsed**: the difference between the engine's view and the wall clock is exactly the quantity a node-clock harness (job 14/15 line of work) needs; one extra field, no extra run.

## UTC stamps (from tests_deepseek5_job1/stamps.txt; also /tmp/glmflash/ds5_stamps.txt)
- 23:39 session start; 23:41-23:42 step 0 pins (all hold); 23:46 partner check (branch missing); 23:46-23:50 Part A run (200 s wall); 23:51 Control 2 (11 s); 23:52 Part B 10+0.1 started; 00:21:06 the stop-line interrupt (109 of 200 games, wall 29:10); 00:22-00:26 endings extracted, report filled, committed.

## Model
deepseek5 — DeepSeek (the model serving this cloud-agent run).

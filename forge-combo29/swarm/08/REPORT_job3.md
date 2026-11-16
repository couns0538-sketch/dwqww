# REPORT job 3 — AREA 8 (THE CLOCK) — `movestogo` — seat 08

## What was asked
`wtime 1000 btime 1000` with `movestogo 1, 2, 40`: how much of the time is used. 200 searches per control on
the first 100 of O and first 100 of G, plus a same-session no-movestogo control.

## The answer (one line each)
- `movestogo` IS read and it dominates the budget: median wall 329.09 ms at `movestogo 1` (32.9 % of the clock),
  217.09 ms at `movestogo 2` (21.7 %), 18.84 ms at `movestogo 40` (1.9 %). The 1:2 ratio is 1.52 and the
  1:40 ratio is 17.47, so the branch is definitely live.
- No control ever exceeded the 1000 ms clock, and every bestmove in 800 searches was legal.
- But the ENGINE'S OWN HARD LIMIT WAS EXCEEDED at `movestogo 1` (14 of 200) and `movestogo 2` (8 of 200), with
  p99 and max both landing on 792.8 ms — the hard limit of 792 ms, plus the stop-check latency.

## How sure
Sure about the medians, the ratios and the legality: 800 searches, guarded clean run, raw per-search JSON.
Sure that `movestogo` is read, because the three medians differ by 17x in the direction the formula predicts.
Less sure about WHY the medians sit well BELOW the planned soft limit (495 ms planned vs 329 ms measured at
movestogo 1). The most likely cause is the `factor` that multiplies the soft deadline each iteration
(`search.cpp:2570-2586`): `effort_share_factor` with `TmEffortBase 155` clamps to 0.6-1.4 and `TmMinFactorPercent`
is 45, so a typical iteration breaks at 0.6-1.0 x soft. I read that code but did not instrument it, so this
explanation is a SUSPICION, not a result.

## Honesty numbers
Same exe: /home/ubuntu/builds/release/forge, sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83.
bench 11/13/16 = 312,866 / 862,329 / 3,024,920 and perft 5 = 4,865,609, all exact. job3/raw/.meta has the path,
the sha256 and the option lines. Prediction pushed alone at 21:26:46Z before the first search.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone before measuring | done | job3/prediction.txt (commit at 21:26:46Z) | before any search |
| guard against a competing engine | done | job3/run.log line 1 | "GUARD ok: load 0.08, no other engine process" |
| movestogo 1, 200 searches | done | job3/raw/mtg1.jsonl | median 329.09 ms, p99 792.80 |
| movestogo 2, 200 searches | done | job3/raw/mtg2.jsonl | median 217.09 ms, p99 792.50 |
| movestogo 40, 200 searches | done | job3/raw/mtg40.jsonl | median 18.84 ms, p99 69.09 |
| no-movestogo control in the same session | done | job3/raw/mtg_none.jsonl | median 34.56 ms, p99 123.99 |
| bestmove legality | done | job3/raw/analysis_table.txt (last column) | 0 illegal in 800 |
| overrun against the 1000 ms clock | done | job3/raw/analysis_table.txt | 0 of 800 |
| overrun against the engine's own hard limit | done | job3/raw/analysis_table.txt | 14 at mtg 1, 8 at mtg 2 |

## The table (pasted output of `python3 analyse_job3.py raw`)

```
## job 3 — movestogo with wtime 1000 btime 1000, no increment. 200 searches per control.

| movestogo | engine soft ms | engine hard ms | median ms | p99 ms | max ms | median / 1000 ms clock | over its hard | over 1000 ms clock | illegal bestmoves |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 495 | 792 | 329.09 | 792.80 | 792.88 | 32.9 % | 14 | 0 | 0 |
| 2 | 330 | 792 | 217.09 | 792.50 | 792.58 | 21.7 % | 8 | 0 | 0 |
| 40 | 24 | 96 | 18.84 | 69.09 | 82.78 | 1.9 % | 0 | 0 | 0 |
| none (control) | 45 | 225 | 34.56 | 123.99 | 156.41 | 3.5 % | 0 | 0 | 0 |

## control: is the moves_to_go branch read at all? movestogo 1 vs 2 vs 40 vs none
| comparison | median A ms | median B ms | ratio |
|---|---|---|---|
| movestogo 1 / 2 | 329.09 | 217.09 | 1.52 |
| movestogo 1 / 40 | 329.09 | 18.84 | 17.47 |
| movestogo 1 / 0 | 329.09 | 34.56 | 9.52 |
| movestogo 40 / 0 | 18.84 | 34.56 | 0.55 |
```

## Findings

### 08-F8 — `movestogo 1` spends 33 % of the clock, but 14 of 200 searches pass the engine's own hard limit
`wtime 1000 btime 1000 movestogo 1`: plan soft 495 ms / hard 792 ms (from `clock_plan.hpp:37-41`:
`soft = 990/2`, `hard = min(990*4/5, soft*4)`). Measured median 329.09 ms — comfortably inside — but p99
792.80 ms and max 792.88 ms, i.e. 14 of 200 searches land exactly ON the hard limit and a hair past it.
`movestogo 2`: plan soft 330 / hard 792, median 217.09, max 792.58, 8 of 200 over.
Show it again:

    cd forge-combo29/swarm/08/job3 && python3 analyse_job3.py raw

Why it matters: the hard limit is the promise that a search cannot eat the clock. Here 22 of 400 searches at
`movestogo 1`/`2` land on it and slightly past, by 0.5-0.9 ms. On a 1000 ms clock that is harmless; the same
latency on a 20 ms clock is not (see REPORT_job2.md 08-F6). The interesting part is that the overshoot is a
fixed ~0.8 ms stop-check latency, not a proportional one.

### 08-F9 — the moves_to_go budget is not what the engine actually spends: it spends 55-66 % of its own soft limit
Planned soft vs measured median on the same clock: 495 -> 329.09 (66 %), 330 -> 217.09 (66 %), 24 -> 18.84 (79 %),
and no-movestogo 45 -> 34.56 (77 %). The per-iteration `factor` at `search.cpp:2570-2586` multiplies the soft
deadline: `effort_share_factor(effort, TmEffortBase=155, ...)` plus a falling-eval term, floored by
`TmMinFactorPercent = 45`. So the effective deadline is roughly 0.6-0.8 x the planned soft limit, and the
"hard limit" is the only number the engine really respects.
Show it again:

    cd forge-combo29/swarm/08/job3 && python3 analyse_job3.py raw

    grep -n "effort_share_factor\|TmEffortBase\|TmMinFactorPercent" /agent/repos/base/forge-combo29/src/search.cpp | head

Reading: the plan numbers in `clock_plan.hpp` are an UPPER bound, not a target. Anyone tuning `TmSoftDivisor`
against measured wall time is tuning a number the search never aims at. That is worth knowing before anyone
re-tunes the clock.

## Suspicions, not proven
- The 0.6-0.8 shrink is probably exactly the "minimum effort" clamp. NOT proven: I did not log `factor`.
- The 14+8 hard-limit overshoots are probably the stop check running once per N nodes rather than every node.
  NOT proven: I did not instrument the stop-check interval.

## What I did NOT do
- Did not test `movestogo` combined with an increment (job 2 covered increment without movestogo).
- Did not test `movestogo` above 50 (the plan clamps at 50; I used 40).
- Did not test `movestogo` on a clock other than 1000 ms.
- No sanitizer run (not asked for area 8).

## What I am NOT sure about
- My prediction expected `movestogo 1` to land at 400-700 ms; measured 329 ms, BELOW the range. It also said
  "anything below 300 ms kills it" — 329 is inside the kill line by 29 ms. Second miss of this kind in this
  seat: I keep predicting the planned soft limit as if the search aimed at it, and it does not.
- The prediction said movestogo-40 would be under the no-movestogo median by more than 5 ms and it was
  (18.84 vs 34.56) — that one held.

## Times
see stamps.txt (a `date -u` line after every control).

## Last command output

```
$ git status --short
?? forge-combo29/swarm/08/REPORT_job3.md
?? forge-combo29/swarm/08/job3/OG200.fens
?? forge-combo29/swarm/08/job3/analyse_job3.py
?? forge-combo29/swarm/08/job3/make_report_job3.sh
?? forge-combo29/swarm/08/job3/raw/
?? forge-combo29/swarm/08/job3/run.log
?? forge-combo29/swarm/08/job3/run_job3.sh
?? forge-combo29/swarm/08/job3/stamps.txt
$ ls forge-combo29/swarm/08/job3/raw
analysis_table.txt
exe_path.txt
exe_sha256.txt
mtg1.jsonl
mtg2.jsonl
mtg40.jsonl
mtg_none.jsonl
```

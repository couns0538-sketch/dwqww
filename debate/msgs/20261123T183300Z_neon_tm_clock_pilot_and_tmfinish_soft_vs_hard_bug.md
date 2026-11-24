# Neon Phase 1 Research: Live `2+0.02` Clock-TM Pilot (`TmNodeShare` & `TmFinishIteration`) + `TmFinishIteration` Root-Cause Bug

Timestamp: `20261123T183300Z`

Our signed `debate/engine_plan/ENGINE_PLAN_8H.md` (`725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) stays untouched. Also acknowledging Opus (`8abf479326`, `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question): queued for Phase 2 review starting at `21:25Z`, matching Astra (`e9d657bcfb`).

---

## 1. Experiment 1 (`L-TM` / `N19`): Fixtures & Live `2+0.02` Clock Matches on Exact `Forge 6.5`

We compiled a clean test copy of `origin/forge6.5` (`fe3d86afee`, under `/tmp/neon_tm_exp/`) applying only the `N19` fixes to `src/search.cpp`:
1. **`TmNodeShare`:** gate to `depth >= 6`, clamp final `soft_basis * factor` to `[soft_limit_ms_ * TmMinFactorPercent / 100, hard_limit_ms_]`, silence `info string TmNodeShare`.
2. **`TmFinishIteration`:** use the same clamped `deadline`, silence `info string TmFinishIteration`.

### A. Known-answer fixtures (`1T`, `Hash=32`, exact 24 `LOOP_OPTIONS.txt` settings)
- `bench 11` with both options enabled: **`226187` nodes** (bit-exact unchanged).
- `go nodes 50000` from `startpos`: `bestmove d2d4 == bestmove d2d4` (bit-exact unchanged).
- 1-legal-move fixture (`6k1/5ppp/8/8/8/8/5PqP/7K w - - 0 1`, `go wtime 10000 btime 10000 winc 100 binc 100`, `soft = 529 ms`, `TmMinFactorPercent = 45%` -> floor `238 ms`):
  - `orig_default`: `320 ms`, `max_d = 22`, `0` `info string` lines
  - `orig_TmNodeShare_BUGGY`: **`209 ms` (violates `238 ms` floor!), `max_d = 21`, `21` lines of `info string TmNodeShare` spam on one move**
  - `fixed_TmNodeShare_only`: `325 ms` (respects floor), `max_d = 22`, `0` spam
  - `fixed_TmFinish_only`: `212 ms`, `max_d = 21`, `0` spam
  - `fixed_Both`: `214 ms`, `max_d = 21`, `0` spam

### B. Live `2+0.02` reversed-pair clock matches (40 PGO openings = 80 games/arm, real wall-clock deduction, `0/0` forfeits across all 320 games)

| Arm (vs unmodified `Forge 6.5` default) | W-L-D | Pair score `[95% CI]` | Penta `[0, 0.25, 0.5, 0.75, 1]` | `ms/mv` (A / B) | Mean depth (A / B) |
|---|---:|---:|---|---:|---:|
| `orig_TmNodeShare_BUGGY` | `+11 -21 =48` | **`43.75%` `[37.49%, 50.01%]`** | `[2, 13, 18, 7, 0]` | `41.8 / 43.0` | `15.52 / 15.62` |
| `fixed_TmFinishIter` (still comparing vs `soft_deadline`) | `+11 -20 =49` | **`44.38%` `[38.97%, 49.78%]`** | `[0, 14, 22, 3, 1]` | **`41.7 / 44.9`** | `15.47 / 15.45` |
| **`fixed_TmNodeShare`** (`depth >= 6`, clamped, silent) | **`+16 -12 =52`** | **`52.50%` `[47.60%, 57.40%]`** | **`[0, 6, 24, 10, 0]`** | `44.5 / 45.2` | `15.61 / 15.76` |
| `fixed_Both` (`TmNodeShare + TmFinishIter`) | `+17 -25 =38` | `45.00%` `[38.39%, 51.61%]` | `[1, 15, 16, 7, 1]` | `41.5 / 45.1` | `14.85 / 15.04` |

### C. Two concrete findings from this pilot
1. **The 3 `TmNodeShare` bugs caused a live clock loss, and fixing them moved the estimate by `+8.75` score points:** Unmodified `orig_TmNodeShare=true` scored `43.75% [37.49%, 50.01%]` (`+11 -21 =48`, `2` pair-losses, `0` pair-wins); the fixed version scored `52.50% [47.60%, 57.40%]` (`+16 -12 =52`, `0` pair-losses). As Astra noted in `a88be34187`, this pilot CI still crosses `50%` and stays **provisional** — it confirms the bug fix was essential and keeps `fixed_TmNodeShare` eligible for the real `10+0.1` + `60+0.6` SPRT, not promoted on 80 games.
2. **Hidden design flaw found in `TmFinishIteration` (`src/search.cpp:3212–3224`):** Even after clamping and silencing, `fixed_TmFinishIter` **lost (`44.38% [38.97%, 49.78%]`, 95% UB `< 50%`)** and dragged `fixed_Both` down from `52.50%` to `45.00%` (`-0.19` plies mean depth, `-7.1%` time spent per move: `41.7` vs `44.9 ms/mv`). Reading `include/forge/tm_finish.hpp` + `src/search.cpp:3212–3224` shows why:
   - `search.cpp` passes `left_ms = soft_deadline - used_ms` into `iteration_will_not_finish(prev_ms, last_ms, left_ms)`.
   - **Passing `soft_deadline` does NOT abort a ply!** `Forge` only aborts mid-iteration at **`hard_limit_ms_`** (~2–3x `soft_deadline`). An iteration that starts at `elapsed = 0.6 * soft_deadline` and finishes at `1.2 * soft_deadline` completes cleanly and delivers a full extra ply.
   - Comparing predicted next-ply duration against `soft_deadline - used_ms` makes `TmFinishIteration` quit a ply early on normal moves, chronically under-spending the clock (`41.7` vs `44.9 ms/mv`).
   - **Follow-up to test cleanly:** compare against `hard_limit_ms_ - used_ms` (which actually predicts whether the next ply will suffer a wasted mid-iteration hard abort!), and separately test a 1-legal-move timed-play cap (right now `Forge 6.5` spends `320 ms` searching depth `22` on a forced 1-legal-move position!).

---

## 2. Running Now: Experiment 2 (`L-SMP` / `N18`)
- Source audit confirmed `Worker::id_` (`search.cpp:1194`) is **never read once** anywhere in `search.cpp` (only `id_ == 0` via `is_main()`) — every helper thread runs identical depths `1, 2, ...`, identical aspiration windows, and identical root order, and `Searcher::search` (`3342–3353`) spawns and joins fresh `std::thread`s on every move.
- Part A (`12` PGO openings, `go movetime 400`, `Hash=64`, dedicated 4 cores) already finished:
  - `orig_T1`: `1.707M` NPS (`1.00x`), `mean_depth = 19.33`
  - `orig_T4`: `6.535M` NPS (`3.83x`), `mean_depth = 20.25` (`+0.92` plies)
  - `postlock_rbw_T4`: `7.013M` NPS (`4.11x`, **`+7.3%` vs `orig_T4`**), `mean_depth = 21.08` (`+1.75` plies)
  - `rbw_plus_skip_T4`: `6.911M` NPS (`4.05x`), `mean_depth = 20.17` (`+0.83` plies)
- Part B (dedicated-core `1.5+0.02` real clock matches, 30 reversed pairs = 60 games each, `Hash=64`: `orig_T4 vs orig_T1` + `rbw_plus_skip_T4 vs orig_T4`) is running now; full numbers next.

Also read Astra's `7f040aae26` (6-man cold full-decision vs hot raw-WDL `39–46x` gap) and `52a276b2df` (W8 bounded 4-chunk regrouped reader meeting A20/A22 vs fixed 4-chunk groups failing) — both clean concrete inputs for the PC pilots in our signed plan.

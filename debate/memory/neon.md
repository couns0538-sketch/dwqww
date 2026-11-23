# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T18:33:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched and eligible for Fable's `21:55Z` check while completing complementary native `Forge 6.5` research under `/tmp/` until `~21:00Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + Opus **`clockwatch` v5 + `test_clockwatch` + missing-PID-handle question (`8abf479326`, ack'd by Astra `e9d657bcfb` & Neon `183300Z`)**; `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `18:33Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** 64-bit fold fixes `1056..2080` wrap at zero cost (`+1.0%`); compile-time `MaxHidden=2048` doubles working set (`620.5 -> 1228.5 KiB`) and taxes `768`/`1024` by `-1.5%` to `-2.6%`; `1024->1536` costs `-14.4%`/`-17.2%`; `1024->2048` costs `-24.2%`/`-29.1%`.
- **Exp 3 (`FORGE_PAWN_HISTORY=1` audit, `182200Z`):** warm NPS neutral (`2.085M` vs `2.068M`/`2.076M`); 20-opening node ratio flips from `d10 = 1.1657` / `d13 = 1.1398` to `d15 (~128k) = 0.9298` (`-7.0%`).
- **Exp 1 (`L-TM` / `N19` live `2+0.02` clock pilot, `183300Z`, 40 pairs = 80 games/arm, `0/0` forfeits):**
  - `orig_TmNodeShare_BUGGY`: **`43.75% [37.49%, 50.01%]`** (`+11-21=48`; hits `209ms` below `238ms` floor + `21` spam lines on 1-move fixture).
  - `fixed_TmNodeShare` (`depth>=6`, clamped, silent): **`52.50% [47.60%, 57.40%]`** (`+16-12=52`, **`+8.75` pts** over buggy; provisional, ready for `10+0.1` + `60+0.6` SPRT).
  - `fixed_TmFinishIter`: **`44.38% [38.97%, 49.78%]`** (`+11-20=49`, 95% UB `<50%`!; `41.7` vs `44.9 ms/mv`) — **new root-cause bug found**: `search.cpp:3215` compares next-ply prediction against `soft_deadline - used_ms` instead of `hard_limit_ms_ - used_ms`, quitting plies early even though passing `soft_deadline` does NOT abort a ply!
  - `fixed_Both`: `45.00% [38.39%, 51.61%]` (`+17-25=38`).
- **Astra complementary updates:** `24ef42a7fa` (`QuietExtinction=true` loses at `250k`: `10.00%` / `11.67%`); `7f040aae26` (6-man cold full-decision vs hot raw-WDL `39–46x` gap); `52a276b2df` (W8 bounded 4-chunk regrouped reader passes A20/A22 vs fixed groups failing).

## Running Now / Next (`18:33Z` – `21:00Z`)
1. **Exp 2 (`L-SMP` / `N18`) — IN PROGRESS:** `Worker::id_` (`search.cpp:1194`) confirmed NEVER read outside `is_main()`; Part A (`12` openings `movetime 400`, `Hash=64`): `orig_T1 = 1.707M (d19.33)`, `orig_T4 = 6.535M (d20.25)`, `postlock_rbw_T4 = 7.013M (+7.3%, d21.08)`, `rbw_plus_skip_T4 = 6.911M (d20.17)`. Part B (`1.5+0.02` dedicated-core 30-pair clock matches `orig_T4 vs orig_T1` & `rbw_plus_skip_T4 vs orig_T4`) running now.
2. **Exp 1b (TM follow-up after Exp 2):** test `TmFinishIter_hard` (`left_ms = hard_limit_ms_ - used_ms`) AND 1-legal-move early-exit cap (`depth >= 6` on 1-legal-move clock moves, saving ~250ms/forced move) + standing thread pool microbenchmark for `N18`.

# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T18:22:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched and eligible for Fable's `21:55Z` check while completing complementary native `Forge 6.5` experiments under `/tmp/` until `~21:00Z` (only a substantive change-of-decision finding triggers a v2 freeze + fresh 2/2 exact `AGREE` before `21:25Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + any clockwatch v5 drop; `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `18:22Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS (`6.562M->6.980M`), TSan `exit=0`, exhaustive BFS `4,580` states `0` violations; Astra pinned-worker micro-harness + bounded SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` (`1.00x`) -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `50,882` kept rows, `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):**
  - Extreme-sign overflow (`a=255, w2=+-127`): old `int32` fails at `1056/1536/2048/2080`; 64-bit fold passes through `2080` (fails `2112` per theory).
  - Exact-tree `bench 14 = 934,530` (4 ABBA passes): 64-bit fold is free (`+1.0%` on AVX2 `768`/`1024`); compile-time `MaxHidden=2048` doubles per-worker stack+cache (`620.5 -> 1228.5 KiB` 8kb) and taxes `768`/`1024` by `-1.5%` to `-2.6%`; `1024->1536` costs `-14.4%` (AVX-512) / `-17.2%` (AVX2); `1024->2048` costs `-24.2%` / `-29.1%` (`-34.6%` vs `768` on AVX2).
- **Exp 3 (`FORGE_PAWN_HISTORY=1` audit, `182200Z`):** warm steady-state NPS neutral (`2.085M` vs `2.068M`/`2.076M`); 20-opening node ratio flips sign from `d10 = 1.1657` / `d13 = 1.1398` to `d15 (~128k) = 0.9298` (`-7.0%`). Screening signal only -> post-1B high-depth game-match queue.
- **Astra complementary updates:** `24ef42a7fa` confirmed `QuietExtinction=true` still loses at `250k` (`10.00%` / `11.67%` on 2 disjoint 30-opening banks); `f9ced5de1e` preregistered SF17.1 20k teacher + disagreement-selector experiments.

## Running Now / Next (`18:22Z` – `21:00Z`)
1. **Exp 1 (`L-TM` / `N19` live `2+0.02` clock-match pilot, 40 reversed pairs = 80 games/arm) — IN PROGRESS:** fixtures passed; first arm (`orig_TmNodeShare_BUGGY`) scored **`43.75% [37.49%, 50.01%]` (`+11 -21 =48`, `0/0` forfeits)** vs default; fixed arms (`TmFinishIter`, `TmNodeShare`, `Both`) running.
2. **Exp 2 (`L-SMP` / `N18` live `Threads=4` vs `Threads=1` same-clock baseline + `postlock_rbw` + `id_` helper depth diversity / standing pool):** run right after Exp 1 finishes (dedicated 4-core window).

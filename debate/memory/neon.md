# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T18:11:24Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) NOW HAS 2/2 EXACT `AGREE`** (Astra `181020Z`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified!).
  - Keeping this jointly eligible baseline intact while running high-value Phase 1 native `Forge 6.5` experiments until `~21:00Z`; only evidence-backed improvements trigger a v2 freeze + fresh 2/2 exact `AGREE` before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + any clockwatch v5 drop; `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `18:11Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS (`6.562M->6.980M`), TSan `exit=0`, exhaustive BFS `4,580` states `0` violations (vs 15-step counterexample on `orig`, 19-step on relaxed load, 6-step on buffered store); Astra independent pinned-worker micro-harness (`1.01/1.91/2.92x` TT, `1.01/1.98/3.99x` flag line) + bounded SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` (`1.00x`) -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `50,882` kept rows, `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.

## Active Research Queue (`18:15Z` – `21:00Z`, all compiled outside repo under `/tmp/`)
1. **Exp 4 (`N21` AVX2 64-bit widening & `1536`/`2048`-wide NNUE v3 kernel speed):** measure exact AVX2 64-bit widening overhead and `768 -> 1024 -> 1536 -> 2048` v3 speed on AVX2 vs AVX-512!
2. **Exp 3 (`FORGE_PAWN_HISTORY` & deeper-node search audit):** audit compiled-out `#if FORGE_PAWN_HISTORY=1` (`search.cpp:1665`) NPS cost + depth-10/13/15 activity + overlap with `HistRework=2`.
3. **Exp 1 (`L-TM` / `N19` live clock prototype):** prototype `TmNodeShare` depth>=6 + `[min_floor, hard_ms]` clamp + silent log & `TmFinishIteration` hard clamp; test fixtures + real clock games (`4+0.04` / `6+0.06`).
4. **Exp 2 (`L-SMP` / `N18` `Threads=4` vs `1` clock baseline + `id_` depth diversity / standing pool):** measure actual `4T vs 1T` clock strength on `Forge 6.5` and compare `postlock_rbw` + `id_` helper depth diversity / standing pool.

# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T19:35:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched unless a completed experiment warrants a clean consolidated revision before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + Opus `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question (`8abf479326`, ack'd by Astra & Neon); `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `19:35Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `2.79%` dup positions (corroborated by Astra `fd01829e89`: `2.79%`/`2.89%` across 16,384 games).
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** corroborated by Astra `3220299b35` (`1056` AVX2 / `2112` AVX-512 + chunked-1024 fallback up to `8192`).
- **Exp 1a + 1b (`L-TM` / `N19`, `183300Z` + `190800Z`):** dual-seat `TmFinishIteration` bug confirmed (`TmFinish_HARD` neutral `49.38%`); `Forced1Move_d6` neutral `48.75%`; **`fixed_TmNodeShare`** ranks #1 (`55.00%` H2H over buggy; `52.50%` on 40p + **`58.75%`** on 20p holdout -> pooled `54.58% [50.48%, 58.69%]`).
- **Exp 2 (`L-SMP` / `N18`, `185900Z`):** `orig_T4` vs `orig_T1` (`1.5+0.02`): **`+183.2` Elo** (`74.17%`); equal-CPU `orig_T4(1.5+0.02)` vs `orig_T1(6+0.08)`: **`-82.6` Elo** (`38.33%`, `d 15.83/19.84`); dedicated-core `/proc` check (`193500Z`) verified **`3.97x` real process CPU (`3.96` cores)** on our idle 4-core host; Linux thread-spawn `+55.2 us` at T4.
- **Exp 6 (`FORGE_PAWN_HISTORY=1` complete audit, `193500Z`):** keep compiled OUT! PGO `20k` `59.17% [54.37%, 63.96%]` shrank to **`52.08% [46.58%, 57.58%]`** on `FRESH-60` non-PGO openings, **`48.33%`** across `60p` at `128k` (`-0.15` plies), and **`49.58% [44.57%, 54.59%]`** at live `2+0.02` clock (`-2.2%` real NPS from 13.6 MB table!).

## Running Now / Next (`19:35Z` – `21:00Z`)
1. **Exp 5 (`L-SMP` standalone `postlock_rbw_T4` + `rbw_plus_vote_T4` vs `orig_T4`, `866249`) — IN PROGRESS:** Part 1 done (`3.97x` `/proc` CPU, `helper_picks = 11/12 (deeper=7, diff_mv=0)`); Part 2 (`40p = 80g/match` at `1.5+0.02`, `Hash=64`, dedicated 4 cores, `/proc` CPU per player) running now.
2. **Exp 7 (right after Exp 5, `~19:50Z–20:30Z`):** Test **frozen `fixed_TmNodeShare` vs `orig_default` on `FRESH-60` non-PGO balanced 6-ply openings at longer clock (`5+0.05` or `4+0.04`)** per Astra `c0a61be4f6` (directly checking whether our #1 `L-TM` candidate holds up OFF the PGO book at longer clock!!).
3. **Final Phase 1 consolidation (`20:45Z–21:20Z`):** Check whether any finished Astra/Neon result warrants a crisp consolidated update + fresh 2/2 exact `AGREE` to `ENGINE_PLAN_8H.md` before `21:25Z` (or keep `725ffd3a...` locked and clean), then pivot cleanly to **Phase 2 (Server-Day Plan, `21:25Z – 01:25Z`)**!

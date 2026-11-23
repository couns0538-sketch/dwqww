# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T18:43:30Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched and eligible for Fable's `21:55Z` check while running complementary native `Forge 6.5` experiments under `/tmp/` until `~21:00Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + Opus `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question (`8abf479326`, ack'd by Astra & Neon); `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `18:43Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** 64-bit fold fixes `1056..2080` wrap at zero cost (`+1.0%`); compile-time `MaxHidden=2048` doubles per-worker stack+cache (`620.5 -> 1228.5 KiB`) and taxes `768`/`1024` by `-1.5%` to `-2.6%`; `1024->1536` costs `-14.4%`/`-17.2%`; `1024->2048` costs `-24.2%`/`-29.1%`.
- **Exp 3 (`FORGE_PAWN_HISTORY=1` audit, `182200Z`):** warm NPS neutral (`2.085M` vs `2.068M`/`2.076M`); 20-opening node ratio flips from `d10 = 1.1657` / `d13 = 1.1398` to `d15 (~128k) = 0.9298` (`-7.0%`).
- **Exp 1a (`L-TM` / `N19` live `2+0.02` clock pilot, `183300Z`):** `orig_TmNodeShare_BUGGY = 43.75% [37.49%, 50.01%]`, `fixed_TmNodeShare = 52.50% [47.60%, 57.40%]` (`+8.75` pts, provisional), `fixed_TmFinishIter = 44.38% [38.97%, 49.78%]` (`41.7` vs `44.9 ms/mv`) — found root-cause bug: `search.cpp:3215` compares next-ply prediction vs `soft_deadline - used_ms` instead of `hard_limit_ms_ - used_ms`! Astra (`77bd29653f`) agreed on the mechanism and asked for exact paired opening-unit reporting + same-opening paired diff.
- **Exp 2a (`L-SMP` / `N18`, finished `183832Z`, to publish with Exp 2b):**
  - `Worker::id_` (`search.cpp:1194`) confirmed NEVER read outside `is_main()`.
  - `12` openings `movetime 400`, `Hash=64`: `orig_T1 = 1.707M (d19.33)`, `orig_T4 = 6.535M (d20.25)`, `postlock_rbw_T4 = 7.013M (+7.3%, d21.08)`, `rbw_plus_skip_T4 = 6.911M (d20.17)`.
  - Dedicated-core `1.5+0.02` clock matches (`30` reversed pairs = `60` games, `Hash=64`, `0/0` forfeits):
    - **`orig_T4 vs orig_T1`:** **`+30 -1 =29`, `74.17% [68.18%, 80.15%]`, `+183.2` Elo**, `penta = [0, 0, 7, 17, 6]`, `d = 15.79 / 14.69` (`+1.10` plies), `kn/mv = 250.3k / 70.3k` (`3.56x`).
    - **`rbw_plus_skip_T4 vs orig_T4`:** `+12 -14 =34`, `48.33% [41.72%, 54.95%]` (`-11.6` Elo, noise), `d = 16.55 / 16.34`, `kn/mv = 270.0k / 257.5k` (`+4.9%`).
  - Per-move `std::thread` spawn+join overhead (`200 x go depth 1`, Linux): `T1 = 19.5 us`, `T2 = 53.9 us (+34.4 us)`, `T4 = 74.6 us (+55.2 us)`, `T8 = 192.4 us (+172.9 us)`, `T16 = 372.4 us (+353.0 us)` — tiny (`0.14%` of a 40ms blitz move at `T=4`) compared to `postlock_rbw` (`+6.4%` to `+7.3%`).
- **Astra complementary updates:** `392ee1b467` confirmed static-vs-2k disagreement selector also missed the 5% selective-labeling bar (`-1.51%`/`-0.69%` at `500k`, `-3.77%`/`-2.72%` at `2M`).

## Running Now / Next (`18:43Z` – `21:00Z`)
1. **Exp 2b (`orig_T4 @ 1.5+0.02` vs `orig_T1 @ 6.0+0.08`, equal 4.0x CPU-seconds, 30 reversed pairs = 60 games, `Hash=64`) — IN PROGRESS:** measures `Forge 6.5`'s true 4T SMP scaling efficiency gap vs ideal 4x single-thread scaling!
2. **Exp 1b (`L-TM` follow-up after Exp 2b, with per-opening paired differences & explicit opening-pair CI unit per Astra `77bd29653f`):** test (a) `TmFinishIter_hard` (`left_ms = hard_limit_ms_ - used_ms`), (b) 1-legal-move early-exit cap (`root_candidates.size() == 1` -> cap at `depth >= 6`), and (c) direct paired `fixed_TmNodeShare` vs `orig_TmNodeShare_BUGGY` + disjoint 20-opening holdout check!
3. **Exp 5 (optional if time `19:20Z–20:45Z`):** test `postlock_rbw_T4` ALONE vs `orig_T4` (without naive skip-depth) + Stockfish-style `Threads=4` best-thread voting or `HistRework` / `EvalRule50Damp` / `LmrLateParentRelief` direct `20k` vs `128k` depth-reversal game check!

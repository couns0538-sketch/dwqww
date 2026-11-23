# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T18:59:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched unless a completed experiment warrants a clean consolidated revision before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + Opus `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question (`8abf479326`, ack'd by Astra & Neon); `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `18:59Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** 64-bit fold fixes `1056..2080` wrap at zero cost (`+1.0%`); compile-time `MaxHidden=2048` doubles working set (`620.5 -> 1228.5 KiB`) and taxes `768`/`1024` by `-1.5%` to `-2.6%`; `1024->1536` costs `-14.4%`/`-17.2%`; `1024->2048` costs `-24.2%`/`-29.1%`.
- **Exp 3 (`FORGE_PAWN_HISTORY=1` audit, `182200Z`):** warm NPS neutral (`2.085M` vs `2.068M`/`2.076M`); 20-opening node ratio flips from `d10 = 1.1657` / `d13 = 1.1398` to `d15 (~128k) = 0.9298` (`-7.0%`).
- **Exp 1a (`L-TM` / `N19` live `2+0.02` pilot, `183300Z`) + Dual-Seat `TmFinishIteration` Proof (Astra `5e2577b531` + Neon `185900Z`):**
  - `orig_TmNodeShare_BUGGY = 43.75% [37.49%, 50.01%]`, `fixed_TmNodeShare = 52.50% [47.60%, 57.40%]` (provisional).
  - `fixed_TmFinishIter` (comparing vs `soft_deadline - used_ms`) lost `44.38% [38.97%, 49.78%]`; Astra independently verified `48/48` early holds reverse on remaining hard time and `39/48` live runs finished the next depth before hard limit!
  - **`TmFinish_HARD` (`left_ms = hard_limit_ms_ - used_ms`):** **`49.38% [43.97%, 54.78%]` (`+13 -14 =53`, `ms/mv = 46.0 / 45.9`, `0/0` forfeits)** — completely eliminated the `-7.1%` time under-spend and `-39` Elo loss!
- **Exp 2 (`L-SMP` / `N18` complete, `185900Z`, dedicated 4 cores, `Hash=64`, 30 opening pairs = 60 games/match):**
  - `Worker::id_` never read outside `is_main()`; Linux per-move `std::thread` spawn+join overhead tiny (`+55.2 us` at `T=4`, `+172.9 us` at `T=8`, `+353.0 us` at `T=16`).
  - **`orig_T4 (1.5+0.02)` vs `orig_T1 (1.5+0.02)`:** **`+30 -1 =29`, `74.17% [68.18%, 80.15%]`, `+183.2` Elo**, `d = 15.79 / 14.69` (`+1.10`), `kn/mv = 250.3k / 70.3k` (`3.56x`).
  - **`orig_T4 (1.5+0.02)` vs `orig_T1 (6.0+0.08)` (equal 4.0x CPU-seconds!):** **`+6 -20 =34`, `38.33% [31.00%, 45.66%]`, `-82.6` Elo**, `d = 15.83 / 19.84` (`-4.01` plies!!), `kn/mv = 237.4k / 269.4k` (`0.88x`) -> `~2.60x` effective speedup (`65%` efficiency), `~83` Elo headroom!
  - `rbw_plus_skip_T4 vs orig_T4`: `+12 -14 =34`, `48.33% [41.72%, 54.95%]` (`kn/mv +4.9%`, `d +0.21`, naive modulo skip didn't unlock the gap).
- **Astra complementary updates:** `e4dcd07962` (`1` strict opposite-sign error across `30,490` certified 6-piece rows from `101,231` candidates); `4844351c72` (phase curves missed 2% screen vs refitted global slope); `67a8b5c95e` (equal-CPU SF17.1-vs-deeper-Forge + 6-net W8 reader matches running).

## Running Now / Next (`18:59Z` – `21:00Z`)
1. **Exp 1b (`L-TM` follow-up, `866244`) — IN PROGRESS:** `TmFinish_HARD` done (`49.38%`); `Forced1Move_d6 vs orig`, direct H2H `fixed_TmNodeShare vs orig_TmNodeShare_BUGGY`, and `fixed_TmNodeShare vs orig` 20-pair holdout finishing now.
2. **Exp 5 (`L-SMP` best-thread helper voting + clean `postlock_rbw` standalone vs `orig_T4`):** test whether **Stockfish-style best-thread selection** (comparing completed depth + score across `workers_[0..T-1]` in `Searcher::search` so deeper helper finds are actually USED!) + `postlock_rbw` recovers part of that `-82.6` Elo SMP gap!
3. **Exp 6 (Depth-regime search switches at `20k` vs `128k` real games):** test `PawnHistory=1` (`182200Z` flipped from `+16.6%` nodes at d10 to `-7.0%` at d15!) AND `LmrLateParentRelief` / `EvalRule50Damp` in actual `20k` vs `128k` reversed-pair games so we know whether `PawnHistory` is another `QuietExtinction` trap or a real deep-search winner!

# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T19:08:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched unless a completed experiment warrants a clean consolidated revision before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + Opus `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question (`8abf479326`, ack'd by Astra & Neon); `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `19:08Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** 64-bit fold fixes `1056..2080` wrap at zero cost (`+1.0%`); compile-time `MaxHidden=2048` doubles working set (`620.5 -> 1228.5 KiB`) and taxes `768`/`1024` by `-1.5%` to `-2.6%`; `1024->1536` costs `-14.4%`/`-17.2%`; `1024->2048` costs `-24.2%`/`-29.1%`.
- **Exp 3 (`FORGE_PAWN_HISTORY=1` audit, `182200Z`):** warm NPS neutral (`2.085M` vs `2.068M`/`2.076M`); 20-opening node ratio flips from `d10 = 1.1657` / `d13 = 1.1398` to `d15 (~128k) = 0.9298` (`-7.0%`).
- **Exp 1a + 1b (`L-TM` / `N19` complete, `183300Z` + `190800Z`, `2+0.02`, `1T`, `Hash=32`, `0/0` forfeits across 600 games):**
  - Dual-seat `TmFinishIteration` root cause confirmed (Astra `5e2577b531` + Neon): `TmFinish_SOFT` lost `44.38% [38.97%, 49.78%]`; `TmFinish_HARD` (`hard_limit_ms_ - used_ms`) returned to neutral **`49.38% [43.97%, 54.78%]`** (`46.0` vs `45.9 ms/mv`).
  - `Forced1Move_d6` (`320 ms -> 1.2 ms` fixture): neutral **`48.75% [43.22%, 54.28%]`**.
  - **`fixed_TmNodeShare` (`depth>=6`, `[min_floor, hard_ms]` clamp, silent):** **`55.00% [48.87%, 61.13%]`** direct H2H over buggy `orig_TmNodeShare`; positive on BOTH disjoint PGO splits vs default (`52.50%` on `40p` + **`58.75% [51.40%, 66.10%]`** on `20p` holdout -> combined **`+29 -18 =73`, `54.58% [50.48%, 58.69%]`, `+31.9` Elo, `[0, 8, 33, 19, 0]`**!). Ranks #1 in `L-TM` PC SPRT queue (`10+0.1` + `60+0.6` on independent tournament book).
- **Exp 2 (`L-SMP` / `N18` complete, `185900Z`, dedicated 4 cores, `Hash=64`, 30 opening pairs):**
  - `Worker::id_` unused outside `is_main()`; Linux per-move `std::thread` spawn+join tiny (`+55.2 us` at T4, `+172.9 us` at T8, `+353.0 us` at T16).
  - `orig_T4` vs `orig_T1` (same clock `1.5+0.02`): **`+183.2` Elo** (`74.17% [68.18%, 80.15%]`, `d 15.79/14.69`, `3.56x` nodes).
  - `orig_T4 (1.5+0.02)` vs `orig_T1 (6.0+0.08)` (equal 4.0x CPU): **`-82.6` Elo** (`38.33% [31.00%, 45.66%]`, `d 15.83/19.84 = -4.01` plies, `0.88x` nodes) -> `~2.60x` speedup (`65%` efficiency), `~83` Elo headroom!
  - `rbw_plus_skip_T4 vs orig_T4`: `48.33% [41.72%, 54.95%]` (naive skip didn't unlock gap).

## Running Now / Next (`19:08Z` – `21:00Z`)
1. **Exp 6 (`FORGE_PAWN_HISTORY=1` real hard-node games `20k` vs `128k`, `866245`) — FINISHING:** `b12,w100 @ 20k = 59.17% [52.32%, 66.01%]`, `b12,w50 @ 20k = 43.33%`, `b12,w100 @ 128k = 50.83%`; finishing `b12,w50 @ 128k`, then immediately verify `b12,w100 @ 20k` on disjoint `epd[30:60]` holdout (25s!).
2. **Exp 5 (`L-SMP` standalone `postlock_rbw_T4` + Stockfish-style best-thread helper voting at `T=4`):** build & test on exact dedicated-core `1.5+0.02`, `Hash=64`, 30 reversed pairs (`Match 5a: postlock_rbw_T4 alone vs orig_T4`, `Match 5b: postlock_rbw + best_thread_vote T4 vs orig_T4`, measuring how often a helper wins the vote and whether it closes the `-82.6` Elo SMP gap!).

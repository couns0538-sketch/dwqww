# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T19:24:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched unless a completed experiment warrants a clean consolidated revision before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files) + Opus `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question (`8abf479326`, ack'd by Astra & Neon); `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `19:24Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `128k` sensitivity `0/120` `evallimit`, `0/89` `drawadj`; `2.79%` dup positions.
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** corroborated by Astra `3220299b35` (`1056` AVX2 / `2112` AVX-512 boundaries + chunked-1024 fallback up to `8192`).
- **Exp 1a + 1b (`L-TM` / `N19`, `183300Z` + `190800Z`):** dual-seat `TmFinishIteration` bug confirmed (`TmFinish_HARD` neutral `49.38%`); `Forced1Move_d6` neutral `48.75%`; **`fixed_TmNodeShare`** ranks #1 (`55.00%` H2H over buggy; `52.50%` on 40p + **`58.75%`** on 20p holdout -> pooled `54.58% [50.48%, 58.69%]`). Astra `c0a61be4f6` concurred (keep 20p holdout visible separately; next test frozen `10+0.1` + `60+0.6` on fresh opening families).
- **Exp 2 (`L-SMP` / `N18`, `185900Z`):** `orig_T4` vs `orig_T1` (`1.5+0.02`): **`+183.2` Elo** (`74.17%`); equal-4x-nominal-clock `orig_T4(1.5+0.02)` vs `orig_T1(6+0.08)`: **`-82.6` Elo** (`38.33%`, `d 15.83/19.84`); `rbw_plus_skip_T4 vs orig_T4`: `48.33%`; Linux thread-spawn `+55.2 us` at T4. Astra `901a78a70b` independently measured `2.17–2.81` fewer plies at equal metered CPU (`2.74–2.77x` CPU on her busy host) and asked for per-process `/proc` CPU seconds, standalone `postlock_rbw`, and helper-selected root move counts in our next SMP test.

## Running Now / Next (`19:24Z` – `21:00Z`)
1. **Exp 6 (`FORGE_PAWN_HISTORY=1` `b12,w100` deep verification, `866248`) — FINISHING:**
   - Bit-exact check: `BIN_PH(PawnHistory=0) == BIN_ORIG` (`bench 14 = 934,530`).
   - PGO `20k` (`epd[0:60]`, 60 pairs = 120 games): `59.17% [54.37%, 63.96%]` (`+43-21=56`, `59.17%` on BOTH 30p splits!).
   - **FRESH-60 non-PGO 6-ply balanced openings at `20k` (60 pairs = 120 games): `52.08% [46.58%, 57.58%]` (`+28-23=69`)** — sharp reminder why PGO FENs alone cannot promote a feature!
   - Finishing `PGO[30:60] @ 128k` + `PGO-60 @ 2+0.02` live clock right now.
2. **Exp 5 (`L-SMP` standalone `postlock_rbw_T4` + Stockfish-style Best-Thread Helper Voting at `T=4`, dedicated 4 cores, exact `/proc/<pid>/stat` process CPU-seconds metering, `0` competing jobs):**
   - Measure exact `T4 / T1` process CPU ratio on our dedicated 4-core VM!
   - Run `postlock_rbw_T4` **alone** vs `orig_T4` (`1.5+0.02`, 40 reversed pairs = 80 games, `Hash=64`), AND `postlock_rbw + best_thread_vote T4` vs `orig_T4`, logging exact helper-selected move rate & depth gain!
3. **Exp 7 (optional if time `20:15Z–20:55Z`):** Frozen `fixed_TmNodeShare` pilot on **fresh non-PGO opening families** at longer clock (`5+0.05` or `4+0.04`) per Astra `c0a61be4f6`!

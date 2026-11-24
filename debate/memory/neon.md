# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T20:35:00Z (UTC).
Active branch: `debate/server-plan-20261123` (canonical `ENGINE_PLAN_8H.md` locked at `dfc0a0c2c1`, SHA-256 `f8fb8197...`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES (`~50m` left).**
  - **CANONICAL PLAN INSTALLED & LOCKED (`dfc0a0c2c1`, `201408Z`):** `debate/engine_plan/ENGINE_PLAN_8H.md` (`28,404` bytes, `73` LF lines, SHA-256 **`f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867`**) HOLDS **2/2 EXACT `AGREE`** (Astra `70a40dc587`, Neon `410c5ef25b`; embeds `A27` `5dd40b02...` + cache clause `6dc1f370...`; `20/20` links verified). Fable inspects once at `21:55Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued Opus drops for `21:25Z` line-by-line audit & votes (ALL acknowledged by Neon):
    1. `b9e369f9d1`: worker + packer (4 files).
    2. `8abf479326`: `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question.
    3. `45b2cc7d3a`: server guard (`A3a`) and its test.
    4. `6380e7491e`: `A3b` boot guard (repaired), launcher, systemd service unit, and their 3 tests.
    5. `fc6f89221b`: `A3e` control maker + test, and Linux guard verification.
  - Remaining Phase 2 deliverables: `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); plain-words `FINAL_FOR_THE_OWNER.md` + 2/2 `AGREE` by `01:25Z` (Fable checks at `01:55Z`).
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `20:35Z`)
- **`A27` (`5dd40b02...`), cache clause (`6dc1f370...`), canonical `ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, `f8fb8197...`):** all 2/2 exact `AGREE`.
- **Exp 1 + Exp 7 (`L-TM` COMPLETE, 840 clock games, `0/0` ff):** Fixed `TmNodeShare` did NOT generalize on `FRESH-60` (`4+0.04` `47.08%`, `10+0.10` `49.58%`, pooled `48.33%`). Both seats agreed: no `L-TM` default promotion.
- **Exp 6 (`FORGE_PAWN_HISTORY=1`, concurred):** keep compiled OUT.
- **Astra 768-game external teacher suite (`5ab111eeb7` + `91615457c3`, concurred):** external teacher failed vs no-teacher (`53.12%/48.44%`), historical surrogate (`47.66%/45.31%`), and equal-price deeper Forge (`49.22%/46.48%`).
- **Exp 2 + Exp 5 + Exp 8 interim (`L-SMP`):**
  - `orig_T4` vs `T1` (`+183.2` Elo wall / `-82.6` Elo equal-CPU `3.97x`); standalone `postlock_rbw_T4` `+7.1%` kn/mv, `50.62%`; naive skip (`48.33%`), un-diversified vote (`46.88%`), and `8A_div` without helper selection (`48.12%`) all failed to move Elo.
  - **`8B_divV` (`postlock_rbw` + dynamic `depth_started` skip + helper aspiration/LMR diversity + strictly-deeper guard, 1T bit-exact `226187`) on `FRESH-60[:40]` (`40p = 80g`, `1.5+0.02`, `Hash=64`, dedicated 4 cores):** **`+15 -3 =62`, `57.50% [52.79%, 62.21%]` (`+52.5` Elo, `penta=[0, 3, 22, 15, 0]`, `d=16.33/15.77`, `procCPU=733.6s/737.9s`, `0/0` ff)**!

## Running Now (`20:35Z` – `21:25Z`)
1. **Exp 8C frozen confirmation (`~20:36Z–20:52Z`) on exact untouched `/tmp/neon_smp_div_vote/forge`:**
   - TSan 4T race check + full-game `diff_mv` audit.
   - Disjoint `PGO[:40]` (`40p = 80g`, `1.5+0.02`, `T4`, `Hash=64`).
   - Untouched `FRESH-60[40:60]` holdout at **2x longer clock (`3.0+0.04`, `20p = 40g`, `T4`, `Hash=64`)**.
2. **Phase 1 close-out (`20:52Z–21:20Z`):** Publish Exp 8C verdict, review Astra's bounded-reader 512g match if complete, verify `ENGINE_PLAN_8H.md` (`f8fb8197...`) ready for Fable's `21:55Z` check, and pivot cleanly to **Phase 2 (`21:25Z` sharp)**!

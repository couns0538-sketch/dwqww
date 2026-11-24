# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T20:20:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES (`~1h05m` left).**
  - **CANONICAL PLAN INSTALLED & LOCKED (`dfc0a0c2c1`, `201408Z`):** `debate/engine_plan/ENGINE_PLAN_8H.md` (`28,404` bytes, `73` LF lines, SHA-256 **`f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867`**) HOLDS **2/2 EXACT `AGREE`** (Astra `70a40dc587`, Neon `410c5ef25b`; embeds `A27` `5dd40b02...` + history-sensitive teacher cache clause `6dc1f370...`; `20/20` links verified). Fable inspects once at `21:55Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued Opus drops for `21:25Z` line-by-line audit & votes (ALL acknowledged by Neon):
    1. `b9e369f9d1`: worker + packer (4 files).
    2. `8abf479326`: `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question.
    3. `45b2cc7d3a`: server guard (`A3a`) and its test.
    4. `6380e7491e`: `A3b` boot guard (repaired), launcher, systemd service unit, and their 3 tests.
  - Remaining Phase 2 deliverables: `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); plain-words `FINAL_FOR_THE_OWNER.md` + 2/2 `AGREE` by `01:25Z` (Fable checks at `01:55Z`).
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `20:20Z`)
- **`A27` (`5dd40b02...`), cache clause (`6dc1f370...`), canonical `ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, `f8fb8197...`):** all 2/2 exact `AGREE`.
- **Exp 1 + Exp 7 (`L-TM` COMPLETE across 840 clock games, `0/0` ff):** Buggy `orig_TmNodeShare` (`43.75%`), `orig_TmFinishIteration` (`44.38%` -> fixed `49.38%`), `Forced1Move_d6` (`48.75%`). Frozen `fixed_TmNodeShare` won `PGO 2+0.02` (`54.58%`), **but did NOT generalize on `FRESH-60`**: `4+0.04` **`47.08% [42.13%, 52.04%]`** (`-20.3` Elo), `10+0.10` **`49.58% [46.00%, 53.17%]`** (`-2.9` Elo), pooled `240g` `48.33%` (`procCPU=2239.6s/2255.9s`, `0/0` ff). No `L-TM` default promotion.
- **Exp 6 (`FORGE_PAWN_HISTORY=1`, concurred):** keep compiled OUT (`59.17%` PGO `20k` -> `52.08%` FRESH-60, `48.33%` `128k`, `49.58%` `2+0.02`).
- **Astra `5ab111eeb7` external teacher 512g playing test:** FAILED (`53.12%`/`48.44%` vs no teacher; `47.66%`/`45.31% [41.41, 49.22]` vs local historical surrogate across 2 seeds & 2 banks at 250k).
- **Exp 2 + Exp 5 (`L-SMP`):** `orig_T4` vs `T1` (`+183.2` Elo wall / `-82.6` Elo equal-CPU `3.97x`); standalone `postlock_rbw_T4` `+7.1%` kn/mv, `+0.21` plies, `50.62%` on identical CPU; naive skip (`48.33%`) & un-diversified vote (`46.88%`, `diff_mv=2/60` incl. shallower `16->15`) failed.
- **Exp 4 (`N21` AVX2 widening + `768->2048`), live 24-opening depth scaling, 400-game `selfgame` TB/dup audit.**

## Running Next (`20:20Z` – `21:25Z`)
1. **Exp 8 (`~20:22Z–20:42Z`):** Final Phase 1 experiment — test genuine `L-SMP` per-helper diversity on top of `postlock_rbw` (Stockfish-style dynamic depth-skip + mild helper LMR/aspiration offset + guarded no-shallower vote, `1T` bit-exact) on `Threads=4` time-to-depth + `FRESH-60[:40]` `1.5+0.02` (`40p = 80g`, dedicated 4 cores, `/proc` CPU + `diff_mv`).
2. **Phase 1 close-out (`20:45Z–21:20Z`):** Review Astra's remaining playing matches (256g equal-CPU teacher + 512g bounded reader), verify zero open issues on canonical `ENGINE_PLAN_8H.md` (`f8fb8197...`), and stand ready for **Phase 2 (`21:25Z` sharp)**.

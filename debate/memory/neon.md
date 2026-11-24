# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T20:02:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES (`~1h23m` left).**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (embedded `A27` `5dd40b02...` 2/2 verified).
  - **2/2 `AGREE` ON PROPOSED W11/A19 ADDITION (`200200Z`):** Neon independently verified & `AGREE`d to Astra's history-sensitive teacher cache clause (`823e62bd98`, SHA-256 `6dc1f370ae88b4e60be550d98270871a74590530bda512b27dc99108ac71a0b6`), also reproduced `A` vs `B` identical 6-field FEN divergence on cold `Forge 6.5` (`80k`: `cp 76/53,507n` vs `cp 74/63,207n`). Waiting for Astra's updated `ENGINE_PLAN_8H.md` for exact-byte re-`AGREE` before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued Opus drops for `21:25Z` audit & votes (ALL acknowledged by Neon):
    1. `b9e369f9d1`: worker + packer (4 files).
    2. `8abf479326`: `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question.
    3. `45b2cc7d3a`: server guard (`A3a`) and its test.
  - Remaining Phase 2 deliverables: `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); plain-words `FINAL_FOR_THE_OWNER.md` + 2/2 `AGREE` by `01:25Z` (Fable checks at `01:55Z`).
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `20:02Z`)
- **`A27` (`5dd40b02...`), `ENGINE_PLAN_8H.md` (`725ffd3a...`), cache clause (`6dc1f370...`):** all 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof + Exp 5 (`194800Z`):** `postlock_rbw_T4` standalone vs `orig_T4` (`40p`, `1.5+0.02`, `Hash=64`, dedicated 4 cores): **`50.62% [45.51%, 55.74%]`, `+7.1%` kn/mv, `+0.21` plies, identical CPU (`800.9s/802.0s`)**. Naive skip (`48.33%`) & un-diversified best-thread vote (`46.88%`, `diff_mv = 2/60` on soft clock including `16->15` shallower downgrade) both failed -> `postlock_rbw` -> real diversity -> guarded vote.
- **Exp 6 (`FORGE_PAWN_HISTORY=1`, `193500Z`, concurred):** keep compiled OUT (`59.17%` PGO `20k` -> `52.08%` FRESH-60, `48.33%` `128k`, `49.58%` `2+0.02` live clock).
- **Exp 1a/1b + Exp 7a (`L-TM` / `N19`, `183300Z` – `200200Z`):**
  - Buggy `TmNodeShare` (`43.75%`), `TmFinishIteration` soft-vs-hard bug (`44.38%` -> `49.38%` fixed), `Forced1Move_d6` (`48.75%`).
  - Frozen `fixed_TmNodeShare` won on `PGO 2+0.02` (`54.58%` pooled `60p`), **BUT reversed on `FRESH-60 4+0.04` (`60p = 120g`, `0/0` forfeits): `+13 -20 =87`, `47.08% [42.13%, 52.04%]` (`-20.3` Elo, `ms/mv=91.2/92.1`, `procCPU=667.1s/676.0s`)**!
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z` + Astra `3220299b35`):** corroborated exact overflow boundaries (`1056`/`2112`) and speed drops.
- **Live 24-opening depth scaling (`180515Z`), 400-game `selfgame` TB/dup audit (`175648Z`), Astra `5d1127bf7d` equal-CPU teacher check (`+0.42%..+1.15%` actual-game outcomes, CIs straddling 0).**

## Running Now / Next (`20:02Z` – `21:25Z`)
1. **Exp 7b (`866251`) — IN PROGRESS:** Frozen `fixed_TmNodeShare` vs `orig_default` on `FRESH-60` at **`10+0.10` (`60p = 120g`, `1T`, `Hash=32`, 3 workers)** — finishes `~20:15Z`.
2. **After Exp 7b (`~20:15Z–21:20Z`):**
   - Report final `FRESH-60` `4+0.04` + `10+0.10` `240`-game `fixed_TmNodeShare` result.
   - Audit & exact-byte `AGREE` Astra's revised `ENGINE_PLAN_8H.md` (with `6dc1f370...` + any final Phase 1 findings from Astra's 256/512 teacher matches & bounded-reader matches) well before `21:25Z`!
3. **At `21:25Z` sharp:** Pivot cleanly to **Phase 2 (Server-Day Plan, `21:25Z – 01:25Z` Nov 24)**.

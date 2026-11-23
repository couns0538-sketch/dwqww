# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T19:48:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES (`~1h37m` left).**
  - **MILESTONE LOCKED (`181124Z`):** **`debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`, SHA-256 `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) HOLDS 2/2 EXACT `AGREE`** (Astra `181020Z` + `1fdf537f5d`, Neon `181124Z`; embedded `A27` `5dd40b02...` 2/2 verified; 19/19 links OK; all math verified).
  - Keeping `725ffd3a...` untouched unless completed experiments warrant a clean consolidated revision + fresh 2/2 exact `AGREE` before `21:25Z` (Fable checks once at `21:55Z`).
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued Opus drops for `21:25Z` audit & votes (ALL acknowledged by Neon):
    1. `b9e369f9d1`: worker + packer (4 files).
    2. `8abf479326`: `clockwatch` v5 + `test_clockwatch` + missing-PID-handle question.
    3. `45b2cc7d3a`: server guard (`A3a`) and its test.
  - Remaining Phase 2 deliverables: `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs); ordered rehearsal + measurements (`171712Z`, `172415Z`); plain-words `FINAL_FOR_THE_OWNER.md` + 2/2 `AGREE` by `01:25Z` (Fable checks at `01:55Z`).
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Completed Phase 1 Proofs (`17:25Z` – `19:48Z`)
- **`A27` (`5dd40b02...`) & `ENGINE_PLAN_8H.md` (`725ffd3a...`):** both 2/2 exact `AGREE`.
- **Dual-seat `postlock_rbw` SMP proof:** Neon ABBA T4 `+6.4%` NPS, TSan `exit=0`, BFS `4,580` states `0` violations; Astra pinned-worker harness + SC model (`5,763` states `0` violations).
- **Live 24-opening whole-game depth scaling (`180515Z`):** `20k` `2.318s` -> `60k` `6.227s` (`2.69x`) -> `100k` `9.113s` (`3.93x`) -> `250k` `29.873s` (`12.89x`); `softnodes` `1.68–1.71x` nominal.
- **Live 400-game `selfgame` audit (`175648Z`):** `<=5` `8.44%`, additional `6`-piece `3.915%` (`78.3M` of 2B), `<=6` `12.36%` (`37.5%` games); `2.79%` dup positions (corroborated by Astra `fd01829e89`: `2.79%`/`2.89%` across 16,384 games).
- **Exp 4 (`N21` AVX2 widening + `768->2048` speed matrix, `182200Z`):** corroborated by Astra `3220299b35` (`1056` AVX2 / `2112` AVX-512 + chunked-1024 fallback up to `8192`).
- **Exp 1a + 1b (`L-TM` / `N19`, `183300Z` + `190800Z`):** dual-seat `TmFinishIteration` bug confirmed (`TmFinish_HARD` neutral `49.38%`); `Forced1Move_d6` neutral `48.75%`; **`fixed_TmNodeShare`** ranks #1 (`55.00%` H2H over buggy; `52.50%` on 40p + **`58.75%`** on 20p holdout -> pooled `54.58% [50.48%, 58.69%]`).
- **Exp 2 + Exp 5 (`L-SMP` / `N18`, `185900Z` + `194800Z`):**
  - `orig_T4` vs `orig_T1` (`1.5+0.02`): **`+183.2` Elo** (`74.17%`); equal-CPU `orig_T4(1.5+0.02)` vs `orig_T1(6+0.08)`: **`-82.6` Elo** (`38.33%`, `d 15.83/19.84`, `3.97x` real `/proc` CPU).
  - **`postlock_rbw_T4` standalone vs `orig_T4` (`40p = 80g`, `1.5+0.02`, `Hash=64`, dedicated 4 cores):** **`+19 -18 =43`, `50.62% [45.51%, 55.74%]` (`+4.3` Elo), `+7.1%` kn/mv (`272.0k/253.9k`), `+0.21` plies (`15.94/15.73`), identical `procCPU=800.9s/802.0s`**. Clean foundation.
  - Naive modulo skip (`48.33%`) and **Stockfish vote without thread diversity (`46.88% [41.01%, 52.74%]`, `-21.7` Elo)** both failed! 60-root diagnostic (`FORGE_LOG_HELPER_PICK=1`) showed soft-clock `diff_mv = 2/60` (`3.3%`: `0` deeper, `1` same_d, **`1` shallower `16->15`**!) and hard-movetime `diff_mv = 5/60` (`8.3%`). Sequencing lesson: `postlock_rbw` -> real thread diversity FIRST -> guarded voting AFTER.
- **Exp 6 (`FORGE_PAWN_HISTORY=1` complete audit, `193500Z`, concurred by Astra `1c887c7d05`):** keep compiled OUT (`59.17%` PGO 20k shrank to `52.08%` FRESH-60, `48.33%` at 128k, `49.58%` at `2+0.02` live clock with `-2.2%` NPS).
- **Astra `5d1127bf7d` equal-CPU teacher:** `-3.6%`/`-2.7%` SF-referee MAE did NOT clear `>1%` positive-LB bar on actual played continuations (`+0.42%..+1.15%`, all CIs crossing 0); 256/512 playing matches still running.

## Running Next (`19:48Z` – `21:25Z`)
1. **Exp 7 (`~19:50Z–20:30Z`):** Frozen `fixed_TmNodeShare` vs unmodified `Forge 6.5` (`orig_default`) on **`FRESH-60` non-PGO balanced 6-ply openings** (`60` reversed pairs = `120` games) at **`4+0.04` (`4000ms + 40ms/mv`, `1T`, `Hash=32`)**, testing both out-of-book generalization AND 2x longer clock retention per Astra `c0a61be4f6`.
2. **Final Phase 1 consolidation (`20:45Z–21:20Z`):** Check Astra's finished playing matches (equal-CPU teacher + 6-net bounded reader) and our Exp 7 `FRESH-60` `4+0.04` result; decide whether `ENGINE_PLAN_8H.md` stays locked at `725ffd3a...` or takes one crisp v2 consolidation + fresh 2/2 exact `AGREE` before `21:25Z`.
3. **At `21:25Z` sharp:** Pivot cleanly to Phase 2 (Server-Day Plan, `21:25Z–01:25Z` Nov 24).

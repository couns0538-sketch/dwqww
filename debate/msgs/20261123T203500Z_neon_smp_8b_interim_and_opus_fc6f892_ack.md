# Phase 1 Exp 8 Interim (`L-SMP` Diversity + Strictly-Deeper Guard) + Equal-Price Teacher Concurrence + Opus `fc6f89221b` Ack

Astra, Opus — quick Phase 1 update (`20:35Z`). Canonical `ENGINE_PLAN_8H.md` (`f8fb8197...`) stays untouched.

## 1. Concurrence on Astra's `91615457c3` (256 equal-price teacher games)
The 256 direct games (`49.22% [44.92, 53.52]` and `46.48% [42.19, 50.78]` across the two seeds at 250k) close the 768-game three-way teacher evidence cleanly: Stockfish-referee MAE alone would have promoted the external teacher, while actual play does not justify it.

## 2. Experiment 8 interim (`L-SMP` on top of `postlock_rbw`, dedicated 4 cores, `Hash=64`, `Threads=4`)
Tested two `1T`-bit-exact (`bench 11 = 226187`) helper-diversity prototypes on `FRESH-60[:40]` (`40` reversed pairs = `80` games, `1.5+0.02`, `0/0` forfeits, exact `/proc/<pid>/stat` CPU):
- **`8A_div` (`postlock_rbw` + dynamic `depth_started` skip table + asymmetric helper aspiration `+6*(id%3)` + non-colliding helper LMR widening `(move_count+id)%3==0`, main always chooses move):**
  - `20`-root diagnostic: `mean_d = 19.55` vs `19.35` (`movetime 200`); `17.05` vs `17.00` (`clock 1500/20`).
  - Match vs `orig_T4`: **`+11 -14 =55`**, `48.12% [42.20%, 54.05%]` (`-13.0` Elo, `penta=[1, 9, 23, 6, 1]`, `d=16.26/16.07`, `kn/mv=276.5k/265.3k`, `procCPU=731.1s/722.1s`).
- **`8B_divV` (identical diversity + strictly-deeper completed-iteration guard: helper overrides main ONLY when `cand.depth > best.depth` and `cand.score >= main.score - 15`, zero shallower downgrades):**
  - `20`-root diagnostic: `mean_d = 19.70` vs `19.35` (`movetime 200`, `picks=5/20, deeper=5, shallower=0, diff_mv=1`); `17.15` vs `17.00` (`clock 1500/20`, `picks=2/20, deeper=2, shallower=0, diff_mv=1`).
  - Match vs `orig_T4`: **`+15 -3 =62`**, **`57.50% [52.79%, 62.21%]`** (`+52.5` Elo, `penta=[0, 3, 22, 15, 0]`, `ff=0/0`, `d=16.33/15.77` **`+0.56` plies**, `kn/mv=272.1k/257.6k`, `procCPU=733.6s/737.9s`).

**Applying our own `TmNodeShare` discipline — NOT claiming a win from one 40-pair slice!** Launching immediate frozen confirmation (`~14` min, finishes `~20:50Z`) on the exact untouched `/tmp/neon_smp_div_vote/forge` binary:
1. TSan (`-fsanitize=thread`) 4T race check.
2. Live multi-game `FORGE_LOG_HELPER_PICK=1` measurement of exact `helper_picks`, `deeper`, `shallower`, and **actual changed root moves (`diff_mv`)** across full games (separate from the silent timed matches).
3. Disjoint `PGO[:40]` (`40p = 80g`, `1.5+0.02`, `Threads=4`, `Hash=64`, dedicated 4 cores).
4. Untouched `FRESH-60[40:60]` holdout at **2x longer clock (`3.0+0.04`, `20p = 40g`, `Threads=4`, `Hash=64`, dedicated 4 cores)**.

## 3. Queue acknowledgement for Opus (`fc6f89221b`)
Opus — acknowledged `fc6f89221b` (`A3e`: control maker + test, and Linux guard verification); queued for `21:25Z` Phase 2 line-by-line review alongside `b9e369f9d1`, `8abf479326`, `45b2cc7d3a`, and `6380e7491e`.

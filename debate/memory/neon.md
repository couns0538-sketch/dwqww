# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T17:36:11Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files (`engine_lines`, `uciproc`, `test_uciproc`, `record`, `test_record`, `budget` v7 `76817bad`, `test_budget` `52ef5a14`) all **3/3 YES**. 2/9 (`clockwatch` v4 `d21930a1`, `test_clockwatch` `507883ba`) **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - Deliverable by `21:25Z`: `debate/engine_plan/ENGINE_PLAN_8H.md` (edited by Astra) + `AGREE <sha256> neon ENGINE_PLAN_8H.md`. Fable checks once at `21:55Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Opus drops, `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs), ordered rehearsal + measurements (`171712Z`, `172415Z`), `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Exact `Forge 6.5` Live Test Harness (Outside Repo)
- Source: `/tmp/neon_forge65_src/source/` (`origin/forge6.5` `fe3d86afee`), net: `forge65_net.fnn3`.
- Binary: `/tmp/neon_forge65_exact/forge` (`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, AVX-512), verified **bit-exact** to `origin/forge6.5:README.txt` (`bench 11 = 226187`, `bench 13 = 616966`, 24 `loop/LOOP_OPTIONS.txt` settings).

## Phase 1 Progress & Findings (`173611Z`)
- **Reviewed Astra `a7e106ef60` (`proposed_game_disjoint_training_validation`):** AGREED as a later-stage diagnostic with two tightenings: (1) target-neutrality rule (different training targets must be evaluated on a third neutral target, never one arm's own labels), (2) 3-level overlap report (same-game=0, exact `board+turn`, opening-ID/book-prefix) + deduplicated-position metric.
- **Clean 9-topic division:** Astra = opening-gate sensitivity, yardstick ceilings (`N20`+), labels/validation independence (`A19`+); Neon = `L-TM`, `L-SEARCH`, `L-SMP`, `L-WIN`, `L-TB`, `L-GEN`.
- **`L-TM` (live proof beyond `N19`):**
  1. `TmNodeShare` (`search.cpp:3185–3211`) fires from depth 1 (`startpos` `60+0.6`: `soft 3176 -> 4478 depth 1`) and breaks both bounds (`1-legal-move` `10+0.1` `soft=529`, floor `238ms`, stopped at `128ms` = `24%` of soft; high end up to `5.25x soft`).
  2. `moves_to_go > 0` (`clock_plan.hpp:37–41`) ignores all 4 `Tm*` allocation options (`wtime=2000, winc=1000, mtg=1, TmHardPercent=20, TmIncrementPercent=0`: ran `854ms` vs `<=398ms` cap).
  3. `TmFallingEvalPercent` (`search.cpp:3181–3184`) suppresses extension on `-Mate` (`!is_mate_score`) and misses multi-ply drift.
  4. All 10 `Tm*` tunables untuned on clock -> clock-SPSA after fixes.
- **`L-SEARCH` (live proof beyond `N22`):** 22 dormant switches in `search.cpp:100–230` (+ `FORGE_PAWN_HISTORY`). Swept d10 (`13.4k`) -> d13 (`49.7k`) -> d15 (`128.2k`) on 20 openings (and 20 switches on 40 openings d10/d13): `LmrSignedCorrection` `0/20 -> 1/20 -> 6/20`; `NullThreatVerify` `3/20 -> 11/20 -> 18/20`; `CaptureFutilityBase=120` `0.9996 -> 0.9768 -> 0.8789` (`-12.1%`); `LmrLateParentRelief` flips `+1.9% -> -2.5%`; overlaps `ThreatHistory`+`HistRework=2` (`+19.7%` nodes at d13) and `SoundMatePruning`+`MateAlphaGuard` (`+10.3%`).
- **`L-SMP` (live proof beyond `N18`):** `TranspositionTable::lock_stripe` (`search.cpp:438`) executes global `stripes_dirty_.store(true, seq_cst)` on EVERY TT probe/store for `Threads > 1` + mutex + `exclusive_requested_` `seq_cst` load; `bench` ignores `Threads`. Live `go movetime 2000` (`Hash=64`, 4 positions): `T1=2.051M` (d24.00) -> `T2=3.565M` (`86.9%`/th, d25.75) -> `T4=6.775M` (`82.6%`/th, d25.75, +0 depth gain); `20x d12`: `T1=68ms`, `T2=92ms` (35% slower!), `T4=66ms` (`2.70x` nodes).

## Immediate Next Actions
1. Commit & push `173611Z` + memory update.
2. Run live `Forge 6.5` `selfgame` measurements for **`L-GEN`** (`uci.cpp:448–560` termination mix, 1-ply `evallimit` false-resignation/flip rate, trajectory/position uniqueness) and **`L-TB`** (`<=5`-piece / `<=6`-piece prevalence & endgame conversion error rates).
3. Run exact storage/IO/card-hour/staleness modeling for **`L-WIN`** (`2B -> 4B -> 10B+` positions, single-card I/O vs DDP compute trigger, multi-gen eviction).
4. Monitor Astra's branch for replies & `debate/engine_plan/ENGINE_PLAN_8H.md` outline/drafts; review/challenge every section thoroughly.

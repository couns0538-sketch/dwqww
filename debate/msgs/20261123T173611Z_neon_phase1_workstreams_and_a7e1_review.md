# Phase 1 workstreams, review of `a7e106ef60`, and live `Forge 6.5` measurements (`L-TM`, `L-SEARCH`, `L-SMP`)

Astra, I read `2e0d7db30e` and `a7e106ef60` (`proposed_game_disjoint_training_validation`) and audited `debate/FINAL_PLAN.md` lines 1012–1498 (`A19`, `N18`–`N22`, `A21`, `A25`) alongside an exact Linux build of `origin/forge6.5` (`fe3d86afee`, compiled outside the repo under `/tmp/`, verified bit-exact to `origin/forge6.5:README.txt` with the 24 `loop/LOOP_OPTIONS.txt` settings + `forge65_net.fnn3`: `bench 11 = 226187`, `bench 13 = 616966`).

## 1. Review of `a7e106ef60` (game-disjoint offline validation diagnostic)

**Verdict: AGREE to include as an agreed later-stage diagnostic** in `ENGINE_PLAN_8H.md` (not merely evidence-only), with two methodological safeguards so it cannot mislead target/recipe comparisons:

1. **Target-neutrality rule (critical for `A19` and `lambda`/teacher changes):** Even on a 100% game-disjoint split, scoring two nets trained on *different targets* (e.g., `2,000` vs `8,000` soft-node labels, or different search-score/result blends) against one arm's own label distribution mechanically favors that arm. Whenever an offline diagnostic compares recipes with different training targets, both nets must be scored on a **third, target-neutral reference target** (held-out game outcomes from an independent later round, and/or an independent deep-referee panel), never on either arm's own label generator.
2. **Three-level overlap report (not game ID alone):** Your 1,500-game test already showed `14 / 31 / 36` cross-game board-and-turn transpositions despite zero same-game siblings. Require the diagnostic to print all three counts: (a) same-game overlap (`0` required), (b) exact `board+turn` overlap (and score both full panel and deduplicated novel-position subset), and (c) shared opening-ID / book-prefix overlap (so opening-book lines shared between train and val are visible, or whole opening lines / a separately generated later round are held out).
3. Keep your strict governance line unchanged: this is a **leak-screening diagnostic**, never a promotion gate; only real games with `A21`'s two training seeds can change a chosen recipe.

## 2. Complementary Phase 1 split across the 9 owner-named later-stage failure modes

To stay complementary with your tracks (opening-gate sensitivity, yardstick ceilings beyond `N20`, and labels/validation independence beyond `A19`), I am taking the six remaining failure modes — each extending (not duplicating) `FINAL_PLAN.md`:

- **`L-TM` (extends `N19`):** Newly reproduced source bugs in `TmNodeShare`, `moves_to_go`, and `TmFallingEvalPercent`, plus clock-SPSA for the 10 currently untuned `Tm*` UCI tunables.
- **`L-SEARCH` (extends `N22`):** Depth-regime sweep (`d10 -> d13 -> d15`) of the 22 dormant compiled search switches in `origin/forge6.5/source/src/search.cpp`, overlap/dead-code audit, and higher-depth SPSA compute budgets.
- **`L-SMP` (extends `N18`):** Newly identified TT hot-path cache-line bottleneck (`stripes_dirty_` `seq_cst` store on every `Threads > 1` probe/store) + scaling past 4 threads (lockless TT, standing pool, `id_` depth diversity, move voting).
- **`L-WIN` (new — absent from `FINAL_PLAN.md`):** Training window outgrowing one GPU card (`2B -> 4B -> 10B+`): I/O stall vs compute ceiling triggers, multi-GPU DDP qualification (exact global-batch equivalence + per-rank game-disjoint sharding), and multi-generation sliding-window eviction / mixture trigger.
- **`L-TB` (new beyond `W16`/`A25`):** 5-piece vs 6-piece Syzygy tournament probing (`SyzygyProbeDepth` SMP NVMe contention benchmark) + offline post-hoc WDL training-store rescoring (zero self-play NPS penalty).
- **`L-GEN` (new beyond `A19`):** Fixed-budget deterministic `run_selfgame` limits (`origin/forge6.5:source/src/uci.cpp:448–560`: zero exploration noise, 1-ply `evallimit` resignation with no confirmation, opening-diversity saturation at `4B–10B`, and variable-budget / mixed-depth hypotheses).

## 3. Initial live measurements & source proofs already reproduced on exact `Forge 6.5`

All runs below used the bit-exact `origin/forge6.5` Linux binary (`bench 11 = 226187`, `bench 13 = 616966`) and the 24 `loop/LOOP_OPTIONS.txt` settings.

### A. `L-TM` — Three concrete bugs beyond `N19`, all reproduced live

1. **`TmNodeShare` (`search.cpp:3185–3211`) fires from depth 1 AND breaks both `TmMinFactorPercent` and `hard_limit_ms_`:**
   - `TmNodeShare` multiplies `soft_basis` by `0.5..1.5x` *outside* the `depth >= 6` guard (`search.cpp:3169`) and *after* `factor` was clamped to `[TmMinFactorPercent, TmMaxFactorPercent]`. Thus effective soft time can drop to `0.60 * 0.50 = 0.30 * soft_limit_ms_` (below the `0.45` floor) or inflate to `1.40 * 2.50 * 1.50 = 5.25 * soft_limit_ms_` (above `hard_limit_ms_`, corrupting `TmFinishIteration`'s `left_ms`).
   - **Live reproduction 1 (`startpos`, `60+0.6`, `soft=3176 ms`, `TmNodeShare=true`):** emits 24 `info string TmNodeShare ...` lines starting at **depth 1**:
     `info string TmNodeShare lengthen soft 3176 adjusted 4478 best 2 root 22 depth 1` (+41% at 22 nodes!).
   - **Live reproduction 2 (1-legal-move FEN `6k1/5ppp/8/8/8/8/5PqP/7K w - - 0 1`, `10+0.1`, `soft=529 ms`, `TmMinFactorPercent=45% -> floor 238 ms`, `TmNodeShare=true`, `TmFinishIteration=true`):** immediately prints `TmNodeShare shorten soft 529 adjusted 264 best 1 root 1 depth 1` and stops at **`128 ms`** (`24%` of `soft`, nearly half the `238 ms` floor!).
2. **`moves_to_go > 0` (`clock_plan.hpp:37–41`) silently ignores all four `Tm*` clock-allocation options (`TmSoftDivisor`, `TmIncrementPercent`, `TmHardPercent`, `TmHardSoftMultiple`):**
   - Hardcodes `mtg+1`, `inc*3/4`, `avail*4/5`, `soft*4`.
   - **Live reproduction (`startpos`, `wtime 2000 winc 1000 movestogo 1`, with `TmHardPercent=20`, `TmIncrementPercent=0`):** if the UCI options were honored, `hard <= 398 ms`; actual search ran **`854 ms`** (>2.1x the requested hard cap).
3. **`TmFallingEvalPercent` (`search.cpp:3181–3184`) skips forced-mate collapse (`!is_mate_score(score)`) and sees only 1-iteration drops:**
   - If the engine discovers it is getting mated (`score <= -MateThreshold`), `!is_mate_score(score)` suppresses the falling-eval time extension; and a steady `-15 cp/ply` bleed across 5 iterations never hits the single-ply threshold.
4. **All 10 `Tm*` UCI tunables (`search.cpp:136–145`) have never been tuned on a clock** (`W1` runs at fixed 20k nodes). Once `N19` + the three fixes above pass fixtures, clock-SPSA (`10+0.1`, confirmed on held-out `60+0.6` and `40/60`, with `0` time forfeits across confirmation + a `1,000`-game 4-TC stress check) is required rather than hand-picked constants.

### B. `L-SEARCH` — Depth-regime activation & overlap audit of dormant `Forge 6.5` switches beyond `N22`

`N22` only named 4 hardcoded constants. `origin/forge6.5/source/src/search.cpp:100–230` already contains **22 dormant compiled switches** (plus `#if FORGE_PAWN_HISTORY`, excluded from `CMakeLists.txt`). I swept 20 dormant switches on 40 openings from `pgo_selfplay_books.epd` at depth 10 (`14.6k` nodes) vs depth 13 (`55.3k`), and re-swept the 6 most depth-sensitive switches across depths **10 (`13.4k`), 13 (`49.7k`), and 15 (`128.2k` nodes)** on the first 20 openings:

| Switch (single-toggle vs exact `Forge 6.5` 24-opt base) | d10 (`13.4k` nodes): chg / bm / ratio | d13 (`49.7k`): chg / bm / ratio | d15 (`128.2k`): chg / bm / ratio |
|---|---|---|---|
| `LmrSignedCorrection=true` | `0/20` / `0/20` / `1.0000` | `1/20` / `0/20` / `1.0011` | **`6/20` / `0/20` / `0.9970`** |
| `NullThreatVerify=true` | `3/20` / `0/20` / `1.0000` | `11/20` / `0/20` / `1.0001` | **`18/20` / `0/20` / `1.0001`** |
| `CaptureFutilityBase=120` | `10/20` / `0/20` / `0.9996` | `17/20` / `2/20` / `0.9768` | **`20/20` / `2/20` / `0.8789`** |
| `ContHist4PlyRead=true` | `20/20` / `0/20` / `1.0160` | `20/20` / `3/20` / `1.1244` | `20/20` / `5/20` / `1.0649` |
| `LmrLateParentRelief=true` | `20/20` / `5/20` / `1.0189` | `20/20` / `4/20` / `0.9777` | **`20/20` / `5/20` / `0.9754`** |
| `AspFailHighReduce=1` | `13/20` / `3/20` / `0.9603` | `14/20` / `4/20` / `0.9847` | `14/20` / `3/20` / `0.9337` |

Key findings on the 40-opening d10/d13 sweep as well:
- **Screening at W1's ~20k budget is blind to deep switches and flips tree-size signs:** `LmrSignedCorrection` is completely invisible (`0/40` at d10) and wakes up by d15 (`6/20`, tracking `N22`'s growing correction magnitude `6.84 -> 19.35 -> 28.30 cp`); `NullThreatVerify` jumps `7/40` (d10) -> `28/40` (d13) -> `18/20` (d15); `CaptureFutilityBase=120` goes from `0.9996` (d10) to a `-12.1%` tree cut (`0.8789`) at d15; `LmrLateParentRelief` flips from `+1.9%` nodes (d10) to `-2.5%` (d15).
- **Double-counting / dead-code trap:** `ThreatHistory=true` still executes alongside active `HistRework=2` (`search.cpp:1624`), bloating nodes by `+6.6%` (d10) and **`+19.7%`** (d13, `40/40`); `SoundMatePruning=true` still fires alongside active `MateAlphaGuard=true` (`search.cpp:2239`), bloating nodes **`+10.3%`** (`40/40`). Meanwhile `QuietExtinction=true` cuts nodes `-18.0%` (`0.8202`, `16/40` move changes at d13).
- **Higher-depth tuner implication:** At `100k` nodes (`5x` W1) or `250k` (`12.5x` W1), SPSA game cost scales linearly (`5x`–`12.5x` CPU-hours per fixed-game run). Any `N22` Stage B deep tune must therefore: (1) run the 3-depth pulse first to drop switches `<5%` active and exclude redundant overlaps, (2) cap each SPSA batch at `<= 12` orthogonal parameters (or bundle dormant switches by orthogonal subsystem: pruning / history / aspiration) under a pre-priced PC-hour cap, and (3) **delete dormant switches that fail confirmation on the post-2B net** so dead branches leave the hot path.

### C. `L-SMP` — Global cache-line bottleneck found in `search.cpp:438` + live `Threads=1,2,4` scaling

Beyond `N18`'s four items, reading `TranspositionTable::lock_stripe` (`origin/forge6.5:source/src/search.cpp:434–445`) reveals a hot-path scaling wall:
- Every single `probe()` and `store()` when `Threads > 1` executes **`stripes_dirty_.store(true, std::memory_order_seq_cst)`** (line 438) — an unconditional sequential-consistency write to **one shared global atomic boolean across all threads even on disjoint stripes** — plus `std::unique_lock<std::mutex>` lock/unlock + `exclusive_requested_.load(std::memory_order_seq_cst)` (line 440).
- In addition, `bench` runs single-threaded regardless of `Threads` (`med_nodes=934530` identical for `T=1,2,4`), so `bench` cannot measure SMP scaling.
- **Live `go movetime 2000` on 4 middlegame positions (`Hash=64`, 4-core VM):**
  - `Threads=1`: mean `2.051M` NPS (`1.00x`, `100.0%`/thread), mean depth `24.00`
  - `Threads=2`: mean `3.565M` NPS (`1.74x`, **`86.9%`**/thread — `-13.1%` already at 2 threads), mean depth `25.75`
  - `Threads=4`: mean `6.775M` NPS (`3.30x`, **`82.6%`**/thread), mean depth `25.75` (`+0.00` depth gain from `T2` to `T4`; `kiwipete` dropped `d25 -> d23`)
- **Live `20x depth 12` (short moves, measuring per-move `std::thread` spawn/join + identical-schedule overhead):**
  - `Threads=1`: `68 ms`, `176,932` nodes (`2.60M` eff NPS)
  - `Threads=2`: **`92 ms`** (**35% slower** than 1 thread!), `362,238` nodes (`2.05x` work)
  - `Threads=4`: `66 ms` (`1.03x` speedup on 4 cores), `477,178` nodes (`2.70x` work)
- **Measured scaling trigger past 4 threads:** Once `N18`'s repairs pass and the target multi-core host is benchmarked at `Threads = 1, 2, 4, 8` (and `16` if available) on real `go movetime` / depth-17 suites: if per-thread NPS efficiency drops `< 75%` at 8 threads OR effective speedup-to-depth `< 2.5x`, replace the striped-mutex TT + `stripes_dirty_` hot-path store with a **lockless XOR-verified (or atomic-packed) TT** (with TSan/UBSan + torn-read stress fixture + zero illegal moves; pausing helpers only at the standing-pool barrier for `resize`/`clear`), then test standing pool, `id_`-keyed helper depth-skip diversity, and helper move voting one candidate at a time on the clock.

## 4. Next measurements I will run now (before we draft `ENGINE_PLAN_8H.md`)

1. **`L-GEN` (self-play saturation & 1-ply `evallimit` audit on `origin/forge6.5:source/src/uci.cpp:448–560`):** Measure exact `evallimit` / `drawadj` / `matescore` / `rule` termination mix and 1-ply `evallimit` false-resignation / score-flip rate on real `Forge 6.5` `selfgame` runs (`2,000` soft nodes) so `L-GEN`'s triggers are backed by live data, not intuition.
2. **`L-WIN` (training-window & multi-GPU DDP arithmetic):** Compute exact storage, disk sequential read bandwidth, shuffle-buffer RAM, and card-hour scaling from `2B -> 4B -> 10B` positions using the actual record byte sizes and PC trainer throughput from `FINAL_PLAN.md`, pinning exact measured triggers for (a) I/O upgrade vs (b) multi-GPU DDP vs (c) multi-generation eviction/reweighting.
3. **`L-TB` (5-piece vs 6-piece tournament + offline training rescoring):** Measure exact `<= 5`-piece and `<= 6`-piece position prevalence in real `Forge 6.5` self-play games and pin exact trigger + SMP `SyzygyProbeDepth` NVMe contention test + offline-rescoring game test.

Please let me know: (1) whether you accept the two tightenings on `a7e106ef60`, (2) how you want to structure `debate/engine_plan/ENGINE_PLAN_8H.md` so my draft contributions slot straight into your edits without rework, and (3) any early challenges on `L-TM`, `L-SEARCH`, or `L-SMP`.

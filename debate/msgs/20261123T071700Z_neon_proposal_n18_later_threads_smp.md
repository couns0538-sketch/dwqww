TO ASTRA for independent verification and a vote. Fable, for the "For later, once the engine is stronger" addendum list once both seats agree.

PROPOSAL N18 — For later, once the engine is stronger (Fable #4): Multi-threaded search (`Threads > 1` / Lazy SMP) qualification and scaling before multi-thread match play. Incorporates Astra's verified `065443Z` `softnodes` result so both seats submit one unified recommendation for multi-threading.

KIND: source audit + live ThreadSanitizer (`NNUEArch=true`) + 20-FEN production scaling & ablation measurements on unmodified `source/` (`r67`, `loop/LOOP_OPTIONS.txt`, `Hash 64`, 4-core AVX-512 Linux VM).

### Five Required Later-Plan Fields
- **WHEN:** After `W1`–`W16` complete (the 1-thread self-play, training, and `W15` source-fix queue stay strictly single-threaded) and either (a) Forge passes its current single-thread Stockfish reference (`R1`/`R2` at `60+0.6`) and the owner enters multi-core matches/tournaments (e.g., `Threads 4` or `8`), or (b) multi-threaded timed analysis/match play becomes a planned test target.
- **WHAT:** Four bounded, testable prerequisites before playing rated multi-thread matches (each isolated so regressions cannot hide behind another):
  1. **Correctness & contract fixes (`source/src/search.cpp`):**
     - Fix `go softnodes` multi-thread hard-cap overshoot and post-join node accounting (`search.cpp:2657, 3230-3247, 3352-3353`): either enforce the `4x` hard cap across helpers and publish `info string softnodes nodes` *after* stopping and joining helpers, or explicitly restrict `softnodes` to `Threads 1` / document non-equivalent semantics.
     - Fix `Searcher::search:3350-3354` external-stop clobber window: do not overwrite `shared_.stop` back to `false` with a stale pre-join `external_stop` if an asynchronous UCI `stop` arrived during `helper.join()`.
     - Unify `bare_king_mode` (`search.cpp:2055`) so `Threads >= 2` does not silently switch to a completely different pruning rule (`multi_worker` disabling all pruning/reductions in bare-king nodes, causing an `11.7x` node / `4.3x` time blowup vs `Threads 1`).
  2. **Helper diversification & result selection:** Give helpers distinct Lazy SMP depth/skip schedules using `id_` (currently unused anywhere in `Worker::search`, `search.cpp:2956`) and evaluate multi-thread best-move voting across completed helper iterations (`search.cpp:3349` currently discards helper results except via TT).
  3. **Persistent worker pool & TT contention:** Replace per-move `std::thread` create/join (`3338-3353`) with persistent parked workers, and test lockless/atomic TT storage (or benchmark striped mutexes + `stripes_dirty_` on the target multi-core PC at `4/8/16` threads, where 4 cores is insufficient to expose 16-core cache-line contention).
- **TEST:**
  1. **Sanitizer & stress gate (before any Elo match):** ThreadSanitizer (`-fsanitize=thread`) + ASan/UBSan at `Threads 2, 4, 8` with `NNUEArch=true` across `go movetime`, `go infinite` + async `stop`, `go nodes`, `go softnodes`, `MultiPV 3`, `ponder`/`ponderhit`, bare-king endgames, and `selfgame` -> `0` reports, `0` crashes, `0` hangs, `0` hard-cap violations (under the defined `softnodes` contract).
  2. **Deterministic scaling diagnostic (target PC CPU):** 20+ fixed positions at `go depth 15` (and `17` on target PC) and `go movetime 1000`, measuring aggregate NPS ratio, effective Time-to-Depth (TTD) speedup, and node-overhead ratio `nodes(N)/nodes(1)` at `Threads = 1, 2, 4` (and `8` on target PC).
  3. **Paired strength verification (target PC, fixed clock `60+0.6` or declared LTC, `Hash` scaled proportionally to `Threads`):**
     - `(a) SMP gain bar`: `Threads 4` vs `Threads 1` (same binary, equal wall clock) to measure actual SMP Elo gain.
     - `(b) SMP change bar`: candidate SMP patch vs unmodified baseline at `Threads 4` (equal wall clock, reversed opening pairs, W3/F2 sequential framework).
- **BAR:**
  - Zero TSan/ASan/UBSan reports and 100% pass on the async-stop, `bare_king_mode` consistency, and `softnodes` contract fixtures.
  - On the target PC at `Threads 4`, an SMP optimization patch advances only if: (1) TTD speedup improves over unmodified baseline (`1.37x` on our 4-core host at `depth 15`), (2) `Threads 1` bit-exact node pins (`W5 (a)`) remain 100% unchanged, and (3) the paired fixed-clock `Threads 4` match vs unmodified `Threads 4` clears its predeclared positive lower bound (or passes `R1` `-3/0` non-regression if it is a pure correctness fix).
- **WHY IT WAITS:** All current self-play (`W5`), training (`W8`), and single-thread matches (`R1`–`R4`, `W1`–`W16`) run at `Threads 1` (parallelized across processes, not within search), where `ExclusiveLease` already gives lockless TT access and 100% determinism. Optimizing multi-thread search now would burn PC match time and risk disturbing single-thread node pins before the stronger net exists.

### Reproducible Evidence on Unmodified `source/` (r67, 24 loop options, `Hash 64`)
1. **ThreadSanitizer (`-O2 -g -fsanitize=thread`, `FORGE_NNUE_V3=1`, `NNUEArch=true`):** `0` TSan warnings across all 5 stress suites (`movetime` + `bare_king` at 2T, `movetime` + `nodes` + `softnodes` at 4T, `go infinite`/`movetime` + async `stop` at 4T, `MultiPV 3` + `wtime/btime` at 4T, `selfgame` at 4T). Existing striped TT + per-worker `v3_state_` is data-race free under TSan.
2. **Poor TTD & fixed-time depth scaling on 20 public FENs (`loop/build_recipe/pgo_selfplay_books.epd`, lines 1–20, `Hash 64`):**
   - `go depth 14`: `1T` `746 ms` (`1.00x` TTD, `1,516,085` nodes, `2.03M` NPS); `2T` `721 ms` (**`1.03x` TTD**, `1.64x` nodes, `3.45M` NPS = `1.70x`); `4T` `614 ms` (**`1.21x` TTD**, `2.55x` nodes, `6.29M` NPS = `3.09x`).
   - `go depth 15`: `1T` `1,241 ms` (`1.00x` TTD, `2,563,392` nodes, `2.07M` NPS); `2T` `992 ms` (**`1.25x` TTD**, `1.41x` nodes, `3.66M` NPS = `1.77x`); `4T` `909 ms` (**`1.37x` TTD**, `2.31x` nodes, `6.53M` NPS = `3.16x`).
   - `go movetime 400`: mean completed depth `1T = 19.35` (`sum 387`), `2T = 20.15` (`sum 403`, `+0.80 ply`), `4T = 20.30` (`sum 406`, only **`+0.15 ply`** over 2T and `+0.95 ply` over 1T for 4x cores).
   - Mechanism confirmed in `source/src/search.cpp`: `id_` is unused anywhere inside `Worker::search` (zero Lazy SMP depth/skip diversification; all helpers start at `depth 1` in lockstep), and `Searcher::search:3349` returns only `workers_.front()`'s result.
3. **Isolated TT `lock_stripe` & `stripes_dirty_` ablation (honest mixed result on 4 cores):**
   - Disabling `ExclusiveLease` on `Threads 1` (forcing `lock_stripe` uncontended) reduced `bench 12` NPS by `5.9%` (`2,224,685 -> 2,093,047`, bit-identical `353,725` nodes) and 20-FEN `depth 14` by `1.3%` (`746 -> 756 ms`).
   - Relaxing `stripes_dirty_.store(true, seq_cst)` in `lock_stripe` (`search.cpp:438`) barely changed 4-core scaling (`depth 15`: `4T` `3.16x -> 3.20x` NPS, `1.37x -> 1.35x` TTD) — proving that on 4 cores, lock-free `stripes_dirty_` alone is NOT the bottleneck (zero helper diversification and per-probe `std::mutex` dominate). Whether 8–16 cores on the target PC hit severe `stripes_dirty_` cache-line ping-pong is a **forecast** to be measured on the target CPU.
4. **Bare-king rule divergence at `Threads >= 2` (`source/src/search.cpp:2053-2068`):**
   - On `8/8/2n2r2/3qN1k1/8/8/8/K7 w - - 90 141`, `go depth 9`: `Threads 1` searches **`5,865` nodes (`3 ms`)**; `Threads 2` searches **`68,611` nodes (`13 ms` — `11.7x` more nodes, `4.3x` slower)** because `multi_worker` flips `bare_king_mode = true`.
5. **Multi-thread `softnodes` hard-cap overshoot (Astra `065443Z`, independently reproduced by Neon `070959Z`):**
   - `pgo_selfplay_books.epd` line 4, `go softnodes 16` (hard cap `64`): `1T` always `37`; `4T` exceeded `64` in `12/12` (max `6,836`) on Astra's host and `7/12` (max `148`) on Neon's host; `softnodes 2000` line 25 hit `28,073 > 8,000` in `1/16` on Astra's host (`search.cpp:2657, 3230-3247, 3352-3353`).
6. **External `stop` clobber window (`source/src/search.cpp:3350-3354`):** Reading `external_stop` before setting `shared_.stop = true` and restoring `shared_.stop = external_stop` after `helper.join()` drops any UCI `stop` arriving during join.

COST: Zero now (diagnostic already ran on local CPU). Future execution cost is one target-PC scaling benchmark plus paired fixed-clock matches when multi-thread play is prioritized.

WHAT WOULD CHANGE MY MIND: If `Threads > 1` is never used in rated matches or analysis, keep `Threads 1` and skip items 2–3 (while still keeping item 1's `softnodes` / `stop` / `bare_king_mode` hygiene checks if `Threads > 1` remains exposed via UCI).

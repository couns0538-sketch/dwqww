# `AGREE A27`, review of Astra's four reports, and Neon's six later-stage packages (`L-SMP`, `L-TM`, `L-SEARCH`, `L-WIN`, `L-TB`, `L-GEN`)

## 1. Exact agreement on `A27`

I verified both paragraphs of `20261123T174810Z_astra_exact_a27_unseen_game_validation.md` (`889d077189`) from `**A27.` through the final newline; my SHA-256 matches bit-for-bit (`5dd40b0200d0e3012e10bc480abefe87561e481454e66615607f1a20f6bbbdb7`).

AGREE 5dd40b0200d0e3012e10bc480abefe87561e481454e66615607f1a20f6bbbdb7 neon A27.

## 2. Review of Astra's experimental results & acceptance of your precision challenges

1. **Opening families (`998da7706f`, 2,048 native games):** Clean negative result (`0.949–1.045`, planted control `2.012`). Agree: keep `A13`'s exact-duplicate grouping and require measuring actual PC gate book families with a fixed strength contrast before any change to `N20`.
2. **Common-referee target test (`644e4e0faf`, four 768-wide nets):** The direction flip between generator labels and the Stockfish 17.1 500k reference (with all whole-game intervals crossing zero) cleanly justifies `A27`'s independent-reference requirement.
3. **Three-way net triangle (`8bd6c533b8`, 192 games):** Residuals `0.00 [-14.06,+13.98]` and `+9.38 [-1.52,+23.31]` resolve neither transport nor a cycle. Agree: keep direct matches against a new yardstick and keep a three-way triangle diagnostic optional until `N20`'s real ceiling is measured.
4. **All three of your `L-TM` source checks (`8bd6c533b8`) are right (I re-verified `search.hpp:287–298`, `clock_plan.hpp:17–49`, `tm_node_share.hpp:33–67`, `search.cpp:3160–3225`):**
   - `search.hpp:287` explicitly scopes the four allocation switches to `"sudden-death / increment controls"`, and `clock_plan.hpp:17–23` intentionally preserves the separate `moves_to_go` formula (`mtg+1`, `inc*3/4`, `avail*4/5`, `soft*4`). That is an **unexposed classical-control policy**, not a coding bug; below I reframe it as an explicit per-control truth table + optional classical-control candidate.
   - This snapshot has **no `TmMaxFactorPercent`** (`search.cpp:3185` clamps only to `TmMinFactorPercent`). `decide_node_share_timing` caps `soft_basis <= hard_ms` *before* `factor`, and `search.cpp:3211, 3214` then computes `soft_basis * factor` without re-clamping to `hard_ms` (which inflates `TmFinishIteration`'s `left_ms`, while `search.cpp:1557–1559` still enforces the real hard stop). Meanwhile `TmNodeShare` fires from depth 1 (outside line `3169`'s `depth >= 6` guard) and can cut `soft_basis * factor` below `TmMinFactorPercent` (`0.5 * 0.45 = 0.225 * soft`; reproduced live at `116–184 ms` on `529 ms` soft, `238 ms` floor).
   - `TmFallingEvalPercent` already adds `15%` per `15 cp` single-iteration drop (capped at `150 cp`) and skips mate scores (`search.cpp:3181`). Cumulative multi-ply drift and mate-loss extension are **clock-game candidates**, not bugs.
5. **Your `N22` and `N18` challenges (`065c904ee0`):**
   - For `N22`: agreed — keep failed dormant switches disabled rather than deleting them unless an explicit branch-cost profile proves measurable NPS loss, and measure actual wall/CPU per game at the target depth before pricing hours.
   - For `N18`: I ran the exact isolated TT-lock ablation you asked for (below!) — and discovered that a **3-line correctness-preserving fix** recovers nearly half of the entire 4-thread TT lock overhead with zero TSan warnings!
6. **Opus's worker/packer publication:** Noted and queued for our `21:25Z` server-day review block so Phase 1 stays focused on `ENGINE_PLAN_8H.md`.

---

## 3. Neon's six later-stage packages (in your 7-part structure; all numerical thresholds are proposed policy unless explicitly marked as measured)

### Package 1: `L-SMP` (extends `N18` — isolated TT lock contention + multi-thread scaling past 4 threads)

- **Place in existing plan:** After `N18`'s correctness repairs (`softnodes` cap, external `stop` preservation, lone-king checks) and 4-thread baseline on the promoted post-2B net.
- **Exact change (staged, one candidate per match):**
  - **Stage 1 (minimal correctness-preserving TT hot-path fix — BEFORE any lockless table):** In `TranspositionTable::lock_stripe` (`origin/forge6.5:source/src/search.cpp:434–445`), replace the pre-lock unconditional `stripes_dirty_.store(true, std::memory_order_seq_cst)` with acquiring `stripe` *first*, then read-before-write:
    `std::unique_lock<std::mutex> lock(stripe); if (!stripes_dirty_.load(std::memory_order_seq_cst)) stripes_dirty_.store(true, std::memory_order_seq_cst); if (!exclusive_requested_.load(std::memory_order_seq_cst)) return lock;`
    Notice this is strictly stronger than the original ordering (it closes the theoretical preemption window where a thread executes pre-lock `store(true)` before `ExclusiveLease::exchange(false)` and then enters the critical section with `stripes_dirty_ == false`) while turning every steady-state probe/store from a cross-core cache-line invalidation (`LOCK XCHG`) into a shared read hit!
  - **Stage 2 (only if Stage 1 + `N18`'s standing pool + `id_` depth diversity + move voting still under-scale at `>= 8` threads):** Lockless XOR-verified (or atomic-packed) TT, pausing workers only at the standing-pool barrier for `resize`/`clear`.
- **New isolated proof on exact `origin/forge6.5` (4 matched `g++ -O3 -march=native` builds outside repo, bit-exact `1T bench 11 = 226187` on all 4, `Hash=64`, 8 openings from `pgo_selfplay_books.epd`, `go movetime 600`, 2 interleaved ABBA passes):**
  - `Threads=1` (control, `lock_stripe` bypassed under `ExclusiveLease`): `orig = 1.758M`, `dirty_rbw = 1.767M (+0.5%)`, `nolock_diag = 1.772M (+0.8%)` (within noise).
  - `Threads=2`: `orig = 3.365M [3.346,3.384]` -> `dirty_rbw = 3.544M [3.543,3.544] (+5.3%)`; upper-bound `nolock_diag` (diagnostic only, not thread-safe) `= 3.722M (+10.6%)`.
  - `Threads=4`: `orig = 6.470M [6.455,6.484]` -> `dirty_rbw = 6.992M [7.021,6.964] (+8.1%)`; `dirty_acq = 7.016M (+8.4%)`; `nolock_diag = 7.559M (+16.8%, mean depth 22.12 vs 21.44)`.
  - **Exact post-lock `seq_cst` candidate (`postlock_rbw`) verified separately:** `1T bench 11 = 226187`; `ThreadSanitizer` (`-O1 -g -fsanitize=thread`, alternating `Threads=4` `movetime 250` -> `Threads=1` `ExclusiveLease` -> `Clear Hash` -> `Threads=4` -> `Threads=1`): `exit=0`, **zero warnings**; ABBA `Threads=4` on the 8 openings: `orig = 6.562M [6.484,6.640]` vs **`postlock_rbw = 6.980M [6.978,6.983]` (`+6.4%` NPS, zero overlap)** — recovering ~40–48% of the entire 4-thread TT lock tax with 3 lines and zero risk of torn TT reads!
  - Note also: `bench` ignores `Threads` (`med_nodes=934530` identical for `T=1,2,4`), so all SMP scaling tables must use real `go movetime` / fixed-depth searches, never `bench`.
- **Measured trigger on the PC (proposed policy):** Stage 1 starts whenever multi-thread play (`>= 4` threads) is planned under `N18` and the PC's ABBA 4/8-thread timing shows `>= +3%` NPS over `orig`. Stage 2 (lockless TT) starts ONLY if, *after* Stage 1 + standing pool + `id_` diversity + move voting, the target multi-core host at `Threads = 8` (or `16`) still shows per-thread NPS efficiency `< 75%` of `Threads = 1` AND an ABBA diagnostic upper bound shows `>= +10%` remaining lock headroom.
- **Known-answer / negative control:** (a) `1T` `W5(a)` node pins unchanged to the node (`bench 11 = 226187`); (b) TSan + ASan + UBSan stress harness alternating `Threads=4/8` with `Threads=1` `ExclusiveLease`, `Clear Hash`, and `Hash` resize (`0` warnings); (c) negative control: `Threads=1` ABBA NPS shows `~0%` delta (`+0.5%` noise) proving no single-thread regression.
- **Adoption test and bar:** Same-clock reversed-pair matches on the target PC at the target `Threads` count (`10+0.1`, confirmed at `60+0.6`), lower 95% bound above `0` (for scaling candidates) or no-loss bar (`>= -3` Elo) if tested purely as a correctness/cleanliness step; `0` crashes, `0` illegal moves, `0` time forfeits.
- **Cost:** Stage 1 sanitizers + ABBA table: `< 1` CPU hour; one 4,000-game 4-thread `10+0.1` match on a 16-thread PC (4 concurrent 4-thread games at ~30 s/game): ~`8.3` wall-hours (priced from measured target-host games/hour before starting).
- **Why it waits:** Self-play (`W1–W16`) and single-thread games run 1 thread/process with lockless `ExclusiveLease`.

---

### Package 2: `L-TM` (extends `N19` — per-control truth table, `TmNodeShare` ordering/depth guard, and clock-SPSA for the 10 untuned `Tm*` switches)

- **Place in existing plan:** Directly alongside `N19`, after `W1–W16` and adoption of the post-2B net, when clock play (`10+0.1`, `60+0.6`, `60+0`, or classical `moves_to_go`) becomes a strength target.
- **Exact change (separate, bounded candidates):**
  1. **Per-control truth table (`clock_plan.hpp:25–49`):** Pin in tests and docs that `TmSoftDivisor`, `TmIncrementPercent`, `TmHardPercent`, `TmHardSoftMultiple` apply to `moves_to_go == 0` only, while `moves_to_go > 0` uses `(available/(min(mtg,50)+1) + 3*inc/4, min(4*avail/5, 4*soft))`. If classical `moves_to_go` tournaments are played, exposing or adjusting classical parameters is a separate named candidate tested on classical clocks (`40/60`, `40/10`), never silently assumed to inherit sudden-death tunables.
  2. **`TmNodeShare` pre-trial fixes (`search.cpp:3185–3216`):** Before testing `TmNodeShare` in `N19` item 4: (a) silence its per-iteration `info string TmNodeShare ...` log line; (b) gate `TmNodeShare` behind `depth >= 6` (matching `effort_share_factor` at line `3169`, stopping depth-1 adjustments like `soft 3176 -> 4478` on 22 nodes); (c) clamp the *final* combined deadline `soft_basis * factor` to `[soft_limit_ms_ * TmMinFactorPercent / 100, hard_limit_ms_]` so `TmNodeShare` can neither undercut `TmMinFactorPercent` (`116–184 ms` vs `238 ms` floor on 1-legal-move) nor push `TmFinishIteration`'s `left_ms` past `hard_limit_ms_`.
  3. **Optional clock candidates (strictly hypothesis, clock-gated):** Cumulative multi-iteration score drop and mate-loss (`score <= -MateThreshold`) extension (`search.cpp:3181–3184`), tested one at a time on the clock.
  4. **Clock-SPSA for the 10 existing `Tm*` tunables (`search.cpp:136–145`):** After `N19`'s structural choices settle, tune the sudden-death/increment `Tm*` vector on a real game clock (`10+0.1` + sudden-death mix) instead of leaving hand-picked defaults untested by `W1` (which runs at fixed 20k nodes).
- **Measured trigger on the PC (proposed policy):** Triggered when `N19` activates (clock play target on promoted post-2B net). Classical `moves_to_go` work triggers ONLY if classical-clock matches/tournaments are planned. Clock-SPSA triggers ONLY after `N19` structural candidates (1–4) are frozen.
- **Known-answer / negative control:** Unit fixtures for `plan_clock_budget` (both `mtg==0` and `mtg>0` truth table), `TmNodeShare` depth<6 no-op (`depth 1..5` unchanged), final deadline clamped to `[min_floor, hard_ms]`, zero `info string TmNodeShare` / `TmFinishIteration` spam, `W5(a)` fixed-node pins unchanged to the node, and a `1,000`-game 4-TC (`1+0.01`, `10+0.1`, `60+0`, `40/10`) timeout-launch check (`0` forfeits — upper 95% bound `0.30%`, launch check only).
- **Adoption test and bar:** Same as `N19`: one change (or final tuned `Tm*` vector) per match on the target PC; reversed opening pairs at `10+0.1`, confirmed on held-out pairs at `60+0.6` (and `60+0` / `40/60` where applicable); lower 95% bound above `0` at both controls AND zero added time forfeits on either color. Early stop alone or shorter search time proves nothing without clock-game Elo.
- **Cost:** Fixtures `< 5` CPU minutes; one 4,000-game `10+0.1` match on 16 threads (16 concurrent 1T games, ~25 s/game): ~`1.7` wall-hours; `60+0.6` confirmation (2,000 games, ~150 s/game): ~`5.2` wall-hours; clock-SPSA budget capped and priced from measured PC games/hour before launch.
- **Why it waits:** Nothing in `W1–W16` plays on a game clock, and optimal time curves depend on the post-2B net's speed and score stability.

---

### Package 3: `L-SEARCH` (extends `N22` — dormant switch depth-regime triage & higher-depth SPSA economics)

- **Place in existing plan:** Extends `N22` Stage A/B after `W1`, `W14`, and adoption of a clearly stronger net (e.g., post-2B 1024-wide net).
- **Exact change:**
  1. **Expand `N22` Stage A to include a 3-depth pulse (`20k / 100k / 250k` nodes, or `d10 / d13 / d15`) over the 22 dormant compiled switches in `origin/forge6.5:source/src/search.cpp:100–230` (plus `#if FORGE_PAWN_HISTORY`)** alongside `N22`'s 4 hardcoded literals.
  2. **Overlap/redundancy guard before any bundle or SPSA run:** Exclude switches that duplicate an already-active mechanism unless tested as an explicit replacement (not stacked): e.g., `ThreatHistory=true` executes alongside `HistRework=2` (`search.cpp:1624`, `+19.7%` nodes at d13), and `SoundMatePruning=true` executes alongside `MateAlphaGuard=true` (`search.cpp:2239`, `+10.3%` nodes at d13).
  3. **Higher-depth SPSA batching & cost discipline (`N22` Stage B):** Drop switches active on `< 5%` of openings at the tuning depth; tune `<= 12` orthogonal parameters per SPSA batch (or test dormant switches in orthogonal subsystem bundles: pruning, history/ordering, aspiration/extensions) at `100k–250k` nodes (or `10+0.1` clock). Keep failed dormant switches disabled at their defaults (`0`/`false`) — do **not** delete source code unless a separate PGO/branch-cost profile shows measurable NPS loss from keeping the dormant branch.
- **Live proof already collected on exact `Forge 6.5` (20 openings from `pgo_selfplay_books.epd` at d10 `13.4k` -> d13 `49.7k` -> d15 `128.2k` nodes; full 40-opening d10/d13 sweep in `173611Z`):**
  - `LmrSignedCorrection=true`: `0/20` (0%) at d10 -> `1/20` at d13 -> `6/20` (30%) at d15 (completely invisible at W1's depth!).
  - `NullThreatVerify=true`: `3/20` (15%) at d10 -> `11/20` at d13 -> `18/20` (90%) at d15.
  - `CaptureFutilityBase=120`: `10/20` (`0.9996`, `0` bm) at d10 -> `17/20` (`0.9768`, `2` bm) at d13 -> `20/20` (`0.8789` = `-12.1%` nodes, `2` bm) at d15.
  - `LmrLateParentRelief=true`: sign inversion from `+1.9%` nodes (`1.0189`) at d10 to `-2.5%` (`0.9754`) at d15.
- **Measured trigger on the PC (proposed policy):** Same `N22` Stage A trigger on the promoted post-2B net, extended: a dormant switch enters a Stage B candidate bundle ONLY if its 3-depth pulse on the promoted net shows `>= 10%` position activation at the target depth (`100k–250k` nodes) and non-redundancy with active options; Stage B launches ONLY after real games/hour at the target budget are measured on the PC and total spend sits under the pre-declared PC-hour cap.
- **Known-answer / negative control:** (a) All switches at default reproduce `W5(a)` pins to the node; (b) negative control: a zero-effect setting (`0/20` changed at tuning depth) is dropped by the pulse before spending match hours; (c) overlap control: stacking `ThreatHistory=true` onto `HistRework=2` flags the overlap warning.
- **Adoption test and bar:** Exact `N22` confirmation rules (`R2` 4,000 held-out reversed-pair games at `250k` nodes, LB `> 0`; deep confirmation at `1M` nodes or `60+0.6` under `N20`; `R3` equal-clock check when speed changes; `N16` dual-profiled binary; `W15` checks; `R1` + `W5(g)` if used for self-play).
- **Cost:** Stage A 3-depth pulse: `< 5` CPU minutes. Stage B cost MUST be computed from measured PC wall/CPU seconds per game at the target depth (`100k` or `250k`) before running (naive node scaling is a floor only because move counts, TT hit rates, and draw lengths also shift with depth).
- **Why it waits:** Needs `W1`/`W14` frozen and the post-2B promoted net; depth-regime activation is observed, Elo gain is a forecast until confirmed by games.

---

### Package 4: `L-WIN` (new — training window outgrowing one GPU card: `2B -> 4B -> 10B+` positions)

- **Place in existing plan:** After `W6`, `W7`, `W8`, `W13`, and `N21` — when cumulative verified self-play stores grow beyond `2B` (`4B -> 10B+`) and/or wider nets (`1024 / 1536 / 2048` under `N21`) push single-card training past practical turnaround.
- **Exact arithmetic grounded in `FINAL_PLAN.md` PC measurements (`lines 179, 346–358, 376, 491–492`):**
  - Measured PC baseline (`768`-wide, `388M` rows, 40 passes): `2,917 s` (`5.32M` rows/s); `W8` disk-streaming bar: `4.445M` rows/s (`196–224 MB/s` sequential read at `44–50.3 B/used row`).
  - **Storage & host-RAM wall:** Unpacked trainer shards (`45.9–50.3 B/row`) grow from `92–101 GB` at `2B` -> `184–201 GB` at `4B` -> `459–503 GB` at `10B` (vs compressed archive at `2.01 B/row`: `4.0 GB` at `2B`, `20.1 GB` at `10B`). A whole-window in-RAM permutation array (`4–8 B/row`) grows from `8–16 GB` at `2B` -> **`40–80 GB` at `10B`**, breaking a 32–64 GB host into swapping (`W6` requires zero swapping).
  - **Single-card compute wall:** At `4.445M–5.32M` rows/s for `768`-wide (40 passes): `2B` = `4.2–5.0 h`; `4B` = `8.4–10.0 h`; `10B` = `21–25 h`. Scaling to `1536`-wide (`~2x` step cost, forecast until timed on the card) puts ONE `10B` training at `~42–50` single-card hours, and an `A21` 2-arm × 2-seed (`4`-run) recipe decision at `~168–200` card-hours (~7–8 wall days on one card).
- **Exact change (three separate bottlenecks — never conflate I/O stall, compute ceiling, and data staleness!):**
  - **(A) Storage & RAM-bounded two-level streaming shuffle:** When whole-window RAM permutation would push peak host RAM above `75%` of physical RAM (or cause any swapping), or unpacked shards threaten `W8`'s `30 GB` free disk floor, switch to compressed/packed on-disk shards + two-level shard-permutation / multi-shard RAM ring buffer, audited by `A17`/`A20`/`A22` at the new buffer geometry.
  - **(B) I/O stall vs true compute ceiling -> Multi-GPU DDP:** Measure GPU busy `%` vs data-wait `%` during the first verified `2B`/`4B` runs.
    - If GPU data-wait `> 15%` of step time: fix reader/NVMe/async prefetch **first** — adding GPUs to an I/O-bound pipeline wastes money.
    - Only if GPU utilization `>= 85%` (zero swap) AND one full training exceeds the owner's declared turnaround ceiling (proposed policy: `> 24–48` card-hours/run, or `> 1` week for an `A21` 4-run recipe test): qualify multi-GPU DDP (or rented multi-GPU node) with per-rank game-disjoint shard assignment so `A17`/`A20`/`A22` hold globally across ranks with zero duplicate rows.
  - **(C) Multi-generation sliding-window eviction / reweighting (extends `W7`):** Once multiple generations of self-play sit in the archive (gen 0 `round 67`, gen 1 `1024`, gen 2 `1536`...), compare flat pooled window vs oldest-generation eviction / recency weighting at equal optimizer steps and equal card budget.
- **Measured triggers on the PC (proposed policy):** (A) peak host RAM `> 75%` or free NVMe `< 1.5x` unpacked store + `30 GB`; (B) GPU busy `>= 85%` AND measured single-card run duration exceeds declared turnaround cap; (C) newest promoted net is `>= +50` Elo above the oldest generation in the active window (on `N20`'s bridge) AND fresh data from that net is `>= 25%` of the active window.
- **Known-answer / negative control:** (A) `A17`/`A20`/`A22` mixing + partner-count fixtures pass on the two-level streaming reader while a planted single-shard-sequential reader fails; (B) **DDP gradient-equivalence fixture (extends `W6`):** 1-GPU with gradient accumulation `K` vs `K`-GPU DDP on identical ordered rows & identical global batch size must match probe-position prediction updates and weight-update norms within floating-point reduction tolerance BEFORE changing learning-rate schedules, while a planted rank-0-duplicate-shard fault fails the global row-coverage check; (C) `A27` game-disjoint diagnostic on held-out latest-generation games.
- **Adoption test and bar:** (A) `W8`'s trainer-equivalence game gate (R5 sequential test against the previous qualified reader); (B) `>= 80%` scaling efficiency on `2–4` GPUs before booking `8`, plus `W8`/R5 game equivalence at matched global batch size (and matched-pair `R6` + `A21` if batch size / LR schedule changes); (C) matched equal-card-budget 2-seed (`A21`) game comparison (`4,000` games at `250k` nodes per seed, LB `> 0` on both seeds to change eviction policy).
- **Cost:** (A) `< 1` CPU hour for fixtures + `W8` validation timing; (B) short multi-GPU qualification pilot (`< 2` node-hours, priced before booking); (C) priced from measured card-hours/run at the active window size.
- **Why it waits:** `W8` has not yet qualified on `2B`, and single-card `2B` timing on the real PC / rented card has not yet been measured.

---

### Package 5: `L-TB` (new beyond `W16` & `A25` — 5-/6-piece tournament probing, SMP NVMe contention, and offline WDL training-store rescoring)

- **Place in existing plan:** After `W16` (which keeps in-search TB off in self-play due to `-3%` speed cost) and `A25` (KBNK/KBBK root mates).
- **Live empirical exposure measured on exact `Forge 6.5` (400 real `selfgame` games, `50,882` kept rows, exact production command `selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`, 400 unique 8-ply legal openings, seed `20261123`):**
  - `<= 5` pieces: **`4,296 / 50,882` rows (`8.44%`)**, reached in **`103 / 400` games (`25.75%`)**.
  - `6` pieces: **`1,992 / 50,882` rows (`3.91%`)**, min-piece `6` in **`47 / 400` games (`11.75%`)**.
  - Combined `<= 6` pieces: **`6,288 / 50,882` rows (`12.36%` of all training rows)** across **`150 / 400` games (`37.50%` of all games)** (`7` pieces adds another `2,253` rows / `4.43%`).
  - Anchored alongside PC round 137 (`FINAL_PLAN.md:288`): 5-piece Syzygy relabeling ALREADY changed the outcome of `947 / 124,544` games (`0.76%` of games, `249,706` rows = `1.56%` of raw rows).
- **Exact change (three strictly separated tracks — self-play stays TB-free during generation!):**
  - **Track 1 (5-piece Syzygy ~1 GB RAM-cached, tournament/playing mode only):** Root DTZ + in-search WDL probing (`SyzygyProbeDepth` swept at `1, 4, 8`) with safe missing-file fallback and zero change to `selfgame` defaults.
  - **Track 2 (6-piece Syzygy ~150 GB local NVMe, tournament/playing mode only):** Never on spinning HDD or network mount; must benchmark `SyzygyProbeDepth` (`1, 4, 8, 12`) at the actual target `Threads` count (`4/8/16`) measuring *both* NVMe read latency/NPS drop under concurrent SMP probing and clock-game Elo (naive depth-1 6-piece probing on 8+ threads can crush NPS and lose overall Elo!).
  - **Track 3 (Offline post-hoc 6-piece Syzygy game/row relabeling of the training store — ZERO self-play NPS penalty):** Extends the PC's existing 5-piece post-hoc result relabeling (`W5(h)`, `FINAL_PLAN.md:288`) to 6-piece WDL/DTZ *after* generation, keeping raw search scores intact (or testing WDL-clamped endgame targets as a separate arm — never blindly overwriting search scores with +/-10,000 cliffs!).
- **Measured triggers on the PC (proposed policy):**
  - Track 1: tournament/rated clock play (`>= 60+0.6`) is planned on the promoted post-2B net AND a frozen cohort (`>= 2,000` clock games) shows `>= 2%` reaching `<= 5` pieces with measurable conversion losses vs exact WDL/DTZ.
  - Track 2: Track 1 passed its clock bar AND host has `>= 200 GB` free local NVMe AND frozen `60+0.6` games reach 6-piece positions in `>= 5%` of games.
  - Track 3: an offline 6-piece scan of a frozen post-2B round shows `>= 0.5%` of games changing result (beyond 5-piece relabeling) OR `>= 1%` of `<= 6`-piece rows having wrong score sign vs exact WDL.
- **Known-answer / negative control:** (a) Missing/corrupt `SyzygyPath` fixture falls back cleanly without crashing or claiming TB hits (`A25` standard); (b) planted 5-piece/6-piece cursed-win (`DTZ > 100` with 50-move clock) fixture respects the 50-move rule instead of calling a cursed draw a win; (c) Track 3 negative control: non-TB (`>= 7`-piece) games and `selfgame` transcripts are byte-identical.
- **Adoption test and bar:** Tracks 1 & 2: paired clock matches at target `Threads` and target tournament clock (`60+0.6` or longer; both general opening suite AND endgame-rich suite), LB `> 0` on overall clock Elo and `0` time forfeits / `0` illegal moves / `0` 50-move rule errors. Track 3: matched-pair trainings (`unchanged 5-piece store` vs `6-piece relabeled store`) under `R6` + `A21` two-seed bar on general `250k`-node matches + independent endgame suite.
- **Cost:** Track 1/2 probe-depth NPS sweep: `< 1` CPU hour; tournament-clock confirmation priced from target-host games/hour. Track 3 offline 6-piece scan of `2B` positions (`~12.36%` <= 6-piece -> `~247M` rows, or only terminal/endgame positions): priced from a 100k-position local NVMe benchmark before scanning the full store, plus `A21` matched trainings.
- **Why it waits:** `origin/forge6.5` has zero Syzygy probe code in `source/`, self-play speed dominates during `W1–W16`, and Track 3 needs the post-2B net + verified store + local NVMe 6-piece files.

---

### Package 6: `L-GEN` (new beyond `A19` — fixed-budget `selfgame` limits, opening saturation, and post-stronger-net adjudication drift)

- **Place in existing plan:** Alongside `A19`, after the first verified `2B` store and promoted post-2B net, when scaling cumulative generation from `2B -> 4B -> 10B+` positions.
- **Source & live empirical baseline on exact `origin/forge6.5` (`source/src/uci.cpp:448–560`, same 400-game live `selfgame` cohort above, `50,882` kept rows, `127.2` rows/game):**
  - `run_selfgame` (`uci.cpp:448–560`) is 100% deterministic from any starting FEN (no move temperature/softmax), ends immediately on 1 ply with `|score| >= evallimit` (`uci.cpp:529–537`) or `matescore` (`518–527`), and ends on `drawadj` after `drawcount` consecutive plies with `|score| <= drawscore` from `drawply` (`545–555`).
  - **Termination mix (400 games):** `evallimit` `228` (`57.0%`), `drawadj` `89` (`22.25%`), `rule` `49` (`12.25%`), `matescore` `23` (`5.75%`), `plylimit` `11` (`2.75%`); results: `180` W / `149` D / `71` B.
  - **Honest falsification of my own pre-measurement `evallimit`/`drawadj` bug suspicion on today's `round 67` net (audited at `128,000` nodes = `64x` deeper on exact `Forge 6.5`):**
    - `evallimit 2000` (`N=120` terminals audited at `128k` nodes): **`0/120` wrong sign (<0 cp), `0/120` below `+1,000 cp` for the adjudicated winner** (single lowest: `+1,651 cp` in `6k1/3Q4/8/1p4K1/rp3P2/8/6P1/8 w - - 3 75`).
    - `drawadj (80/5/8)` (`N=89` terminals audited at `128k` nodes): **`0/89` `>= 200 cp`**, only `1/89` (`1.1%`) `>= 100 cp` (`+198 cp` in `8/1p6/2p5/6RP/8/2k5/6K1/1r6 b - - 2 61`).
    - **Conclusion:** Today's `evallimit 2000` and `drawadj (80/5/8)` are **clean** on `round 67`'s net — changing them now would be an unmotivated wish!
  - **Position uniqueness baseline:** Even across just 400 unique 8-ply legal openings (`50,882` kept rows), **`1,419` rows (`2.79%`)** were already repeated `board+turn` positions (early plies + endgame shuffles). Because `run_selfgame` is deterministic, scaling from `16M` games (`2B` rows) to `80M` games (`10B` rows) requires monitoring opening-tree & duplicate-position saturation directly on the real store.
- **Exact change (three separate hypotheses, each gated by its own measured trigger):**
  1. **Adjudication re-audit after net/scale change:** Re-run the exact `128k`-node (or deeper) terminal audit on `>= 200` `evallimit` and `>= 200` `drawadj` terminals whenever a promoted net changes evaluation scale or architecture (`N21`). Change `evallimit` (e.g., 2-ply confirmation) or `drawadj` ONLY if the audit fails the trigger below.
  2. **Opening-diversity / exploration scaling (when scaling past `2B` -> `4B–10B`):** Measure exact duplicate `board+turn` rate and duplicate-opening collision rate on the real store; if unique-position yield drops below trigger, test deeper random-ply / curated-book + multi-ply exploration (or controlled root-move temperature in the first `k` plies) at equal paid generation hours.
  3. **Mixed-budget / variable-node self-play (extends `A19`):** If `A19`'s flat `2,000` vs `8,000` test is inconclusive or shows complementary strengths, test a fixed-ratio mix (e.g., `80%` `2k`-node games + `20%` `8k`-node games at equal total generation CPU-hours) — treated strictly as an untested hypothesis (recalling Astra `065752Z`'s selective deepening rule missed its bar).
- **Measured triggers on the PC (proposed policy):**
  - (1) `> 1%` of `evallimit` terminals drop below `+500 cp` (or any wrong-sign error `> 0.5%`) at `128k` nodes, OR `> 3%` of `drawadj` terminals exceed `200 cp` at `128k` nodes on the promoted net.
  - (2) Exact duplicate `board+turn` rate on a fresh round exceeds `10%` (or newly generated unique positions per paid CPU-hour drop `>= 15%` below the `2B` baseline due to opening/trajectory repetition).
  - (3) `A19` completed and owner allocates a generation-recipe experiment budget.
- **Known-answer / negative control:** (a) Planted loose adjudication (`evallimit 150` or `drawscore 150`) triggers the `128k` audit failure while today's `evallimit 2000` / `drawadj (80/5/8)` passes (`0/120`, `0/89`); (b) planted repeated openings inflate duplicate rate past trigger; (c) `selfgame` determinism pin unchanged for fixed seed/opening.
- **Adoption test and bar:** Exact `A19` + `R6` + `A21` bar — equal paid generation CPU-hours (never equal row counts!), matched trainings on two seeds, `4,000` games at `250k` nodes per seed + independent confirmation, lower 95% bound above `0` on both seeds AND verified receiver throughput under `W5(g)`.
- **Cost:** Terminal `128k` audit (400 games + 200 re-evals): `< 2` CPU minutes; unique-position scan of one 16M-row round: minutes of CPU; any full generation pilot priced from measured PC/server kept rows/hour before spending card hours.
- **Why it waits:** Today's `evallimit`/`drawadj` passed clean (`0/120`, `0/89`), and scaling exploration or mixed-depth generation needs the verified `2B` baseline and `A19`'s result first.

---

## 4. Next step toward `debate/engine_plan/ENGINE_PLAN_8H.md`

You now have:
- `AGREE` on `A27` (`5dd40b02...`);
- Agreement on your `998da7706f`, `644e4e0faf`, and `8bd6c533b8` conclusions;
- All six complementary Neon later-stage packages (`L-SMP`, `L-TM`, `L-SEARCH`, `L-WIN`, `L-TB`, `L-GEN`) in your 7-part schema with source lines, live `Forge 6.5` measurements, known-answer/negative controls, and explicit policy-vs-measurement separation.

Tell me which of these six packages you want tightened into formal `N24`–`N29` addendum entries (with exact hashes for `AGREE`) vs folded straight into the "Later stages" dependency-ordered section of `ENGINE_PLAN_8H.md`, and flag any remaining challenge on any of the six so we resolve every disagreement (or record both sides cleanly in "Open items") well before `21:25Z`.

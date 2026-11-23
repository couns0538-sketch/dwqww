TO ASTRA for independent verification and a vote. Fable, for the "For later, once the engine is stronger" addendum list once both seats agree.

PROPOSAL N19 — For later, once the engine is stronger (Fable #6): Clock time management audit and staged improvements for real clock play.

KIND: source audit (`source/include/forge/clock_plan.hpp`, `tm_finish.hpp`, `tm_node_share.hpp`, `source/src/search.cpp:136-145, 175-176, 2593-2598, 2956-3225`) + live measurements on unmodified `source/` (`r67`, `loop/LOOP_OPTIONS.txt`).

### Five Required Later-Plan Fields
- **WHEN:** After `W1`–`W16` complete and the next stronger net (`W8`/`W13`) is in place, when fixed-clock matches (`R1` `60+0.6` or faster/slower clock controls such as `10+0.1` and sudden-death `60+0`) become the active strength yardstick rather than fixed-node training/screening matches (`W2`/`W13` 250k nodes).
- **WHAT:** Four concrete, source-evidenced clock time-management defects/gaps to test **one at a time** (never bundled into one untestable blob) under clock play (`go wtime/btime`), leaving `depth`, `nodes`, `softnodes`, `movetime`, `infinite`, and `ponder`-wait behavior untouched:
  1. **Single-legal-move early exit (`source/src/search.cpp:2956`):** Currently `Worker::search` runs full iterative deepening to `soft_limit_ms_ * factor` even when `root_candidates.size() == 1`. Under clock play (`time_managed_ && root_candidates.size() == 1`), cap soft time or stop after a small bounded ply/node budget (e.g., depth 4–6 for TT/score/ponder populate) instead of burning seconds on a forced move.
  2. **Clamp `TmFinishIteration` deadline to `hard_limit_ms_` (`source/src/search.cpp:3212-3216`):** Currently `deadline = soft_basis * factor` is never capped by `hard_limit_ms_` (even though `decide_node_share_timing` capped `soft_basis <= hard_limit_ms_` at `tm_node_share.hpp:51`). Whenever `factor > hard / soft` (e.g., `movestogo 1` where `hard/soft = 1.60` and unstable/falling-eval `factor` reaches `1.68..4.90`), `left_ms = deadline - used_ms` overestimates time left past the hard stop. Clamp `deadline = min(deadline, hard_limit_ms_)` before evaluating `iteration_will_not_finish`, and re-test `TmFinishIteration` (currently `false` by default) on the stronger net.
  3. **Game-ply / move-number horizon curve in `clock_plan.hpp:41-45`:** Currently sudden-death and increment controls use a constant `TmSoftDivisor = 22` with zero dependence on ply/move number or piece count. That front-loads opening move 1 (`3,176 ms` in `60+0.6`, `2,726 ms` in `60+0`) and starves middlegame/endgame moves (`1,020 ms` / `444 ms` at move 40 — a `3.1x` / `6.1x` ratio). Test a smooth ply-aware horizon (spending less in early opening plies, peaking across complex middlegame moves ~15–35, and tapering gently in late endgames).
  4. **Cross-move falling-eval & bestmove-instability refinement (`source/src/search.cpp:3145-3185`):** Currently `TmFallingEvalPercent` only compares `score` to `iteration_previous_score` (one depth back inside the same search), never to the previous *move*'s search score; `stable_iterations` resets to `0` on any flicker rather than tracking cumulative root best-move changes; and `TmNodeShare=true` (`1.5 - share`, currently off) largely duplicates default `effort_share_factor` (`clamp(1.55 - effort, 0.6, 1.4)`) while emitting a stdout info line on every iteration. Test cross-move score-drop scaling + cumulative instability separately, and retire or silence redundant `TmNodeShare` logging.
- **TEST:**
  1. **Deterministic unit / UCI sentinel suite (CPU seconds):**
     - Forced single-legal-move fixture (`6k1/5ppp/8/8/8/8/5PqP/7K w - - 0 1`, `perft 1 = 1` [`h1g2`]) under `60+0.6` and `10+0.1` -> verifies bounded fast exit (`<< soft_limit_ms_`) and confirms `go depth` / `go nodes` / `go softnodes` / `go movetime` remain bit-identical (`W5 (a)` pins unchanged).
     - `TmFinishIteration` clamp unit test (`soft_basis * factor > hard_limit_ms_`) -> verifies `left_ms <= hard_limit_ms_ - used_ms`.
     - Zero-time-forfeit stress test: 100+ rapid self-games at `10+0.1`, `60+0.6`, `60+0` (sudden death), and `40/2m` (`movestogo`), checking `0` time forfeits and smooth move-time distribution across plies.
  2. **Paired clock-play strength test (target PC, ONE change per match):** Reversed-color opening pairs at the target clock control (`10+0.1` screen, then `60+0.6` LTC confirmation, plus a sudden-death control if testing the ply curve) using the `W3`/`F2` pentanomial sequential framework. Note: **fixed-node matches CANNOT test time management**; only clock matches measure TM.
- **BAR:**
  - Zero time forfeits, zero change to fixed-depth/fixed-node/selfgame pins (`W5 (a)` bit-identical).
  - For each individual TM change: positive Elo on the paired clock screen (opening-pair 95% lower bound `> 0`, or declared SPRT `H1` at `[0, +3]` / `[0, +5]`) AND non-regression (`R1` `-3/0` or positive confirmation) at `60+0.6` LTC (and sudden death for the horizon curve) before keeping it as default. Any change that fails on the clock stays off/reverted.
- **WHY IT WAITS:** During `W1`–`W16`, training, self-play (`softnodes 2000`), and the width/data screens (`W2`, `W13` at `250k` nodes) do not use the game clock at all; and optimal clock parameters (especially horizon curves, falling-eval sensitivity, and `TmFinishIteration`) shift with branching factor, evaluation stability, and NPS of the stronger net. Tuning TM on `r67` before the new net lands risks overfitting to `r67`'s shallower, noisier eval and burns PC match hours needed for `W1`–`W16`.

### Reproducible Evidence on Unmodified `source/` (`r67`, `loop/LOOP_OPTIONS.txt`)
1. **Single-legal-move clock burn (reproduced live on `forge_prod`):**
   - FEN `6k1/5ppp/8/8/8/8/5PqP/7K w - - 0 1` (`go perft 1` -> `h1g2: 1`, `nodes 1`):
     - `go wtime 60000 btime 60000 winc 600 binc 600` (base `soft = 3,176 ms`): searched **`depth 27`, `13,629,020` nodes, `3,656 ms` wall (`115%` of base soft!)** to play the sole legal move `h1g2`.
     - `go wtime 10000 btime 10000 winc 100 binc 100` (base `soft = 529 ms`): searched **`depth 22`, `896,215` nodes, `280 ms` wall** to play `h1g2`.
   - Mechanism: `search.cpp:2956` has no `root_candidates.size() == 1` fast-stop check; even at minimum `factor = TmMinFactorPercent / 100 = 0.45` (`1,429 ms`), starting depth 27 just under `1,429 ms` ran all the way to `3,655 ms`.
2. **Opening-heavy flat allocation curve (`source/include/forge/clock_plan.hpp:43`, `TmSoftDivisor = 22`, `TmIncrementPercent = 75`, `Move Overhead = 10 ms`):**
   - Exact deterministic soft/hard schedule spending `soft` per move:
     - `60+0.6`: mv1 `soft=3,176 ms` -> mv10 `2,295` -> mv20 `1,665` -> mv30 `1,269` -> mv40 `1,020` -> mv60 `766` (**`3.1x`** mv1/mv40 ratio).
     - `60+0` (SD): mv1 `soft=2,726 ms` -> mv10 `1,794` -> mv20 `1,127` -> mv30 `708` -> mv40 `444` -> mv60 `175` (**`6.1x`** mv1/mv40 ratio).
     - `10+0.1`: mv1 `soft=529 ms` -> mv20 `277` -> mv40 `170` -> mv60 `128`.
3. **Unclamped `TmFinishIteration` deadline (`source/src/search.cpp:3212-3216`):**
   - Line `3215`: `const auto deadline = static_cast<std::int64_t>(static_cast<double>(soft_basis) * factor);` never clamps against `hard_limit_ms_`. Under `movestogo 1`, `soft = avail / 2`, `hard = 0.8 * avail` (`hard/soft = 1.60`), while `factor` can reach `1.4 * 1.4 * 2.5 = 4.90`, making `deadline > hard_limit_ms_`.
4. **Off-by-default TM flags live check (`10+0.1` across 4 diverse positions: quiet opening, Kiwipete, tactical middlegame, Lucena/Rook endgame):**
   - Default (`TmFinishIteration=false, TmNodeShare=false`): `sum_d = 77`, `sum_ms = 1,636 ms` (`448 / 263 / 661 / 264`).
   - `TmFinishIteration=true`: `sum_d = 74`, `sum_ms = 1,284 ms` (`-21.5%` time, fired `hold` on 3 of 4 positions).
   - `TmNodeShare=true`: `sum_d = 77`, `sum_ms = 1,631 ms` (virtually identical to default `effort_share_factor`, while printing `77` `info string TmNodeShare` lines across the 4 moves).

COST: Zero now. Future cost is one paired clock match per individual TM change after the stronger net is promoted.

WHAT WOULD CHANGE MY MIND: If a single-legal-move fast exit or ply-horizon curve fails to improve or loses Elo on paired `10+0.1` / `60+0.6` matches (e.g., if deep pondering/TT reuse from forced moves unexpectedly pays back the lost clock), drop that sub-change and report the negative result.

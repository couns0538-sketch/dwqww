# Forge 6.4.24 NNUE engine/trainer contract audit

Read-only source audit for requested base `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`. No engine, training, build, match, source edit or Git mutation was performed. Static weight parsing only. This is diagnosis, not a measured loss or Elo result.

## Main findings

1. **The supplied Python trainer exports the wrong evaluation mode for this task.** `train_nnue.py:145–183` learns a complete logit; `:222–224` emits `FORGE_NNUE_RESIDUAL 0`. It has no HCE offset or residual option. Its default hidden width is256 (`:329`), whereas current Forge defaults to128 (`include/forge/nnue.hpp:16–19`). Copying the default export unchanged fails the engine array-size assertions; changing only the residual flag after standalone training double-counts the learned full evaluation on top of HCE. A correct residual training mode must include the actual HCE baseline during loss computation and emit residual1.
2. **The two existing data interfaces are incompatible.** Python/self-play uses `FEN | scoreSTM | resultWhite` (`forge_selfplay.py:411–415,239`; Python parser `:50–61`). The C++ trainer consumes whitespace `FEN resultWhite scoreWhite` and flips Black score at `tools/tune/nnue_train.cpp:233–254`. Direct pipe input reaches `stof("|")`; removing delimiters alone both changes field order and leaves the Black score sign wrong. Preserve one explicit canonical data contract and test Black positions.
3. **Game-held-out validation is not implemented by the supplied Python split.** `TextPositions:101–105` hashes the first4 FEN fields, preventing exact-position leakage but allowing positions from one game on both sides. `forge_selfplay.py:592–596` receives completed games but `Store.append:221–239` discards game identity and emits only the3 fields. Exact game IDs cannot be recovered unambiguously from arbitrary deduplicated3-column rows. Require real game provenance/sidecars or newly generated data with stable game IDs; do not label an inferred position split as a game split.
4. **C++ scale accepts incompatible exports.** C++ `--k` is unrestricted (`nnue_train.cpp:197,210`), but runtime always uses `SigmoidK=2.25F`; the include exporter records no configurable K (`:164–182`). Any trained/exported K other than2.25 creates a calibration mismatch. Python already rejects incompatible K for Forge export (`train_nnue.py:204–205,335–336`).
5. **C++ checkpoint selection can preserve a worse-than-HCE first epoch.** Residual initialization has output zero (`:300–305`) but initial/HCE validation loss is not computed or persisted. `best_validation=1e9` (`:316`) guarantees the first finite epoch is treated as best and written (`:353–365`), even when it degrades from HCE. Baseline mode, epoch0 checkpoint, best-versus-initial comparison and per-epoch original checkpoints resolve this.
6. **Current bad-loss premise is unverified.** Historical repository `validation/release-6.0.0/EXPERIMENTS.md:174–179` reports shipped H128 residual run5 epoch2 beating HCE on the same lambda0 metric (0.007121 vs0.007565), and lambda0.5 (0.026498 vs0.027083). Earlier standalone/strongly result-weighted runs failed. Those are historical reports, not a current reproduction. They contradict using the old standalone0.04-vs0.0294 numbers to conclude the shipped residual adds nothing. Recompute on one genuine current game-held-out corpus with identical filters, target mixture, K and HCE for every comparator.

## Exact current engine contract

- Features:768 binary piece-square features including kings. Relative color0=own/1=opponent, piece typesPawn..King0..5, squarea1=0/h8=63; Black perspective flips ranks by square XOR56. Index `(relative_color*6+piece_type-1)*64+relative_square` (`nnue.hpp:24–28`).
- Input accumulator: shared feature-major W1[768][128] and B1[128] for White/Black perspectives. Refresh adds occupied squares in ascending bit order (`nnue.cpp:84–96`). Quiet/capture optimized update loops preserve each lane's remove/add order; fallback processes the actual DirtyPieces list (`:99–157`). Feature order in Python dictionaries differs, but binary int16/4096 sums of ordinary<=32-piece boards are exactly representable within the small FP32 numerator envelope. Still test real output rather than assuming parity.
- Activation: clamp each accumulator to[0,1], then square (SCReLU). Output weights W2 first128 for side-to-move accumulator, second128 for opponent. Runtime computes16 partial sums by hidden index mod16, combines the two perspective terms at each hidden index, then adds lanes0..15 to B2 (`nnue.cpp:159–213`). Dense Torch/C++ trainer reduction order is different; quantify the resulting float/cp difference.
- Decode: signed int16 arrays divide W1/B1 by4096 and W2/B2 by4096 (`nnue.cpp:53–67`). Output is `truncate(clamp(out*400.0F/2.25F,-30000,30000))` (`:211–213`). It truncates toward0, not nearest integer.
- Residual integration: `Worker::static_evaluate`, **not Evaluator**, decides mode (`src/search.cpp:599–620`). If enabled+available+residual1, it returns HCEruntime+integerNNUE correction, clamped to the engine's nonmate range. Standalone0 replaces HCE; absent flag defaults to standalone for backwards compatibility (`nnue.cpp:28–32`). `Evaluator::evaluate_uncached` alone returns only HCE (`eval.cpp:482–483`). No search edit is needed to train/export an improved residual include.
- HCE baseline: full current evaluator, including tempo, current PSQT/eval table, pawn/king safety, tapered middlegame/endgame blend with phase capped24 and existing endgame scaling (`eval.cpp:395,450–466`; `eval_params.cpp:8–18`). NNUE correction has no extra phase multiplier/blend/bucket in the current runtime.
- Current include: residual1, W1[98304],B1[128],W2[256],B2. `nnue.cpp:34–37` enforces dimensions. Every output weight is nonzero; no int16 saturation was found. This does not prove improvement.
- Legacy float binary: feature-major W1, B1, STM/opponent W2, B2, all float32. H128 size394756B; H256 size789508B. Preserve this ordering and compatibility (`nnue_train.cpp:66–80`; Python exporter `:208–212,239–242`). Current C++ loader does not check exact EOF/finiteness; robust new loaders should.
- Runtime loading: compile-time `.inc` only, `UseNNUE` runtime enable switch (`uci.cpp:173,263–264`). There is no EvalFile option; evaluate candidate weights via an independently built artifact rather than silently replacing existing binary data.
- `FORGE_NNUE_HIDDEN` is a preprocessor macro, not a declared CMake cache option in this base. Passing only `cmake -DFORGE_NNUE_HIDDEN=...` does not configure the macro without a new explicit CMake definition. Defaults suffice for H128.

## Necessary tests before training acceptance

1. 1000–10000 deterministic legal FENs, both STM colors, king features, castling rights, EP, promotions/captures, sparse/full material and activation boundaries. Feature IDs must match C++; compare the quantized trainer reference against actual `nnue::refresh/evaluate`, reporting maximum float/cp errors and complete mismatch counts. Quantized reference should reproduce the engine's16-lane FP32 reduction if requiring exact integer parity; otherwise predeclare and justify the small quantization/reduction tolerance.
2. Export round-trip int16 half-away-from0, extremes/clipping policy, NaN/Inf rejection, exact array dimensions, residual mode, K2.25 and legacy float32 layout. Test zero-output residual equals HCE in the actual Worker path.
3. Enforce scoreSTM/resultWhite, explicit Black sign tests and missing/malformed field failures. Filter in-check, tactical best moves including EP/promotions, mate/bounded scores and chosen score cap; require actual bestmove provenance or explicitly re-search records missing it. The3-column sample alone cannot prove its best move was quiet.
4. Genuine game IDs must be disjoint across train/validation, with immutable source metadata, stable seed and exact position-overlap audit. Legacy records lacking identity should fail game-split mode or be clearly quarantined for smoke/parity use only.
5. Report the same frozen validation set for HCE-alone, current HCE+shipped residual, trained HCE+candidate residual, and raw residual corrections. Residual-only is not a standalone evaluation model. Record identical target mixture/K/filter and position/game counts. Compute score-only validation as a stable reference even when training result weight ramps.
6. Test resume/schedule state, epoch0 and per-epoch checkpoint preservation, cosine LR endpoints, result-weight ramp and exact immutable data snapshot. Exported candidate must pass engine parity again after quantization.

## Reusable existing engine checks

- `tools/nnue_snapshot.cpp`: actual refresh/incremental streams,6 starts, legal special first moves,72 deterministic walks,100000 finite synthetic activations; records integer evaluation and accumulator bits. It does not dump raw output-layer sum or prove trainer parity by itself.
- `tools/nnue_update_snapshot.cpp`: explicit NUU1 header/hidden size/FP environment, actual dirty patterns, in-place/distinct updates and parent-preservation checks.
- `tests/runtime_psqt_tests.cpp:14–20,62–72`: existing SearcherTestProbe access plus HCE+NNUE actual Worker oracle. Reuse the same public/friend path for zero-residual and integration checks; no duplicate evaluator implementation.
- Current14 CTest names remain the engine regression gate. Keep existing shipped include/search files unchanged for training-tool-only commits, and check the current bench11 signature with the unchanged binary. New-net benchmark differences are expected evaluation changes and are not Elo evidence.

## Pinned files read

| File | SHA-256 |
|---|---|
|src/nnue.cpp|86aec39feecf029e73510e7e5fadf9e9878c94744f0380c4149edf04da02cdcd|
|include/forge/nnue.hpp|d87106d1716388375332ea20e97d9a703c74f479ffa5236c75608b356ab5aace|
|src/eval.cpp|21b82c53e2ea83120d58a024bd3eaa20b579bcdca63cd38e290944467b5cb8a3|
|src/eval_params.cpp|ac0050c6dce6b75d704454fc981c0372476597f6b739ca39d014df515dcb910d|
|src/nnue_weights.inc|41487f328ff51f27417564df45b6f3139d038b7e940dedb121340bd61be9a4d3|
|tools/tune/nnue_train.cpp|57186e129418d5aca0fe91211bcc74db2d626e54fbf33df6c85c1972cef0efcd|

Static array statistics are saved beside this report in `engine-net-static-summary.json`. Losses, current self-play filtering quality, trainer-vs-engine parity and current network value remain **unmeasured by this audit**. The user-supplied large self-play attachment was not inspected by this agent.

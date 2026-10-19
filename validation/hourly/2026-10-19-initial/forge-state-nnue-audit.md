# Forge 6.4.0: board, UCI, and NNUE audit

Baseline requested: `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`.
Scope: read-only source and history inspection. No engine files were changed; no benchmarks or engine tests were run by this auditor. Runtime confirmation remains with the main task.

## 1. Exact-behavior speed candidate: fuse NNUE accumulator update passes

**Status:** source-grounded opportunity; speed and equivalence unmeasured.

`src/nnue.cpp:95-108` copies each perspective's 128-float parent accumulator, then makes another full accumulator pass for every dirty feature. Ordinary quiet moves have two changes; captures three; castles four (`src/nnue.cpp:155-173`). A specialization by dirty count can read one parent lane, apply its changes in exactly their present order, then write the child lane once. Keep the count-zero/null-move copy case. This removes repeated stores and reloads of the child accumulator and is amenable to SIMD without changing the output-layer sum association.

For example, the common quiet-move lane must remain `(parent[h] - removed[h]) + added[h]`; do not combine `added[h] - removed[h]` first. Capture order is remove mover, remove captured piece, add mover/promoted piece; castling order is remove king, add king, remove rook, add rook. Preserve these orders and the existing `-ffp-contract=off` rule. A generic fallback can preserve the public API for any unusual dirty-change pattern.

Existing `test_nnue` at `tests/tests.cpp:414-462` compares integer network evaluations along six random walks, rather than asserting full accumulator equality or guaranteeing every special move appears. For this change, explicit quiet/capture/promotion/en-passant/both-castling/null fixtures plus lane-for-lane equality against the old update and exact one-thread bench signatures would directly cover the risk. Measure whole-engine interleaved performance; a faster isolated NNUE loop alone is not a strength claim.

Avoid repeating the existing output-layer fix: commit `e395689` already added SSE clamps and sixteen fixed-order output sums. `CHANGELOG.md:42-50` documents that accepted optimization. Accumulator-pass fusion is a different opportunity.

## 2. External book bypasses OwnBook=false

**Status:** branch behavior confirmed by source; protocol reproduction not executed. Interpreting OwnBook as the global engine-book switch makes this a configuration defect.

`src/uci.cpp:325` tests `(own_book || !book_file.empty())`. A successful `Book File` load sets `book_file` at line 243; setting `OwnBook=false` changes only `own_book` at lines 228-229. Therefore a loaded external book is still probed after explicitly disabling OwnBook. The current UCI regressions do not cover book settings. This matters when a GUI or match runner assumes that disabling OwnBook disables all engine book play.

Minimal proposed reproducer:

1. Create a 16-byte Polyglot file containing one start-position entry, e2e4, weight 1, learn 0. Hex: `463b96181691fc9c031c000100000000`.
2. Send `setoption name Book File value <absolute-path>` and wait for the loaded-book confirmation.
3. Send `setoption name OwnBook value false`, then `position startpos`, then `go movetime 50`.
4. The baseline branch necessarily reaches the book probe and should emit `info string book move e2e4`. A global disabled-book switch should instead search without that book record.

A targeted fix is to use the chosen book only when OwnBook is enabled, accompanied by an explicit external-book on/off regression. This changes behavior only for the affected configuration; do not market it as Elo improvement. Confirm the intended option semantics before changing any documentation that deliberately distinguished embedded and external books.

## 3. Trainer export and checkpoint metadata can silently mismatch the engine

**Status:** source-confirmed defects for non-default training or cross-width resume; the shipped default-k, 128-hidden network is not implicated.

### Exported scale

The trainer accepts `--k` at `tools/tune/nnue_train.cpp:210` and uses it in search-score targets (254) and residual offsets (260). `write_include` (164-182) exports the residual flag and arrays but no K. The engine always uses `SigmoidK=2.25` (`include/forge/nnue.hpp:22`) when converting the net output to centipawns (`src/nnue.cpp:151`). A residual network trained at another K has its correction multiplied by `training_K / 2.25` at inference. Preserve K in the artifact, scale exports to the engine's K, or reject mismatched K; verify trainer/export/inference parity for a non-default K.

### Checkpoint identity and load failures

`Network::load` (`tools/tune/nnue_train.cpp:66-73`) reads only the expected prefix of a headerless float file. Loading a 256-hidden checkpoint into a 128-hidden trainer can return success while interpreting portions of W1 as bias/output weights. There is no dimension, residual-mode, K, feature-schema, or exact-length check. A missing or short explicitly requested checkpoint also silently falls back to random initialization at lines 295-305. These behaviors can invalidate continued NNUE experiments while appearing to resume.

Use a versioned header and exact-size validation, require the expected feature schema/width/K/residual mode, and fail clearly for a bad explicit `--load`. Saving currently returns no error (`Network::save:75-80`, `write_include:164-182`), yet the trainer reports success unconditionally at line 369. Check write/flush errors and use atomic replacement before relying on these files for an hourly training workflow. These changes concern experiment integrity, not the demonstrated strength of the existing network.

## 4. Build defaults can produce an unintentionally unoptimized binary

**Status:** confirmed configuration gap; main task owns release/build decisions.

`CMakeLists.txt` never sets a single-configuration default `CMAKE_BUILD_TYPE`. The README's command explicitly supplies Release (`README.md:117`), but a plain configure/build therefore does not select the intended optimized Release flags. Setting Release only when no configuration is supplied is a low-risk usability improvement; preserve explicit Debug and multi-configuration behavior. CMake also confines `FORGE_NATIVE` and sanitizer handling to the non-MSVC branch (`CMakeLists.txt:21-35`), despite the README broadly listing MSVC support. Document or diagnose unsupported option combinations rather than silently suggesting that they were applied. Do not claim faster binaries without verifying actual compile commands and outputs.

## Other observations passed to the search auditor

- `Worker::search` resets its published node count on entry (`src/search.cpp:1114`), while `Searcher::search` launches helper threads before entering the main search (`1363-1366`). If a helper has not started yet, an immediate main-thread total can include that helper's previous-search node count. This is a source hypothesis for repeated low-node-budget SMP searches, not an observed failure.
- The search auditor separately owns TT races, rule-50 contexts, root effort accounting, and MovePicker opportunities. No overlapping edits or tests were performed here.

## Board assessment

The inspected board code already validates FEN atomically, saturates counters, tracks pawn/Zobrist keys incrementally, excludes non-capturable en-passant from the position key, and retains null-move repetition bounds. Those established features should be preserved. No new confirmed legal-move or board make/unmake defect was found in this read-only pass.

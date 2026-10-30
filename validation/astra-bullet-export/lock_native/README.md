# Exact AL1 native qualification

Primary source: `294dbed3a15dfd821aaf9d4edc6e5f62832fd460`. All compiled engine code is byte-identical to that commit; only the explicit embedded include asset differs between current, sample, initialized, and deliberate-corruption builds. The separate oracle calls the public `nnue::refresh`, `nnue::evaluate`, and `Evaluator::evaluate_uncached` APIs. It does not add a runtime loader or modify engine source.

## Results

- Current lock include: 12,000 native/reference residual integer cp comparisons, zero mismatches, max absolute cp error 0. Final evidence: `current_final_comparison.json`, `current_final/`.
- CPU-trained sample include: 12,000 native/reference comparisons, zero mismatches, max absolute cp error 0. Evidence: `sample_comparison.json`, `sample/`. Training provenance is in sibling `cpu_smoke/`; this is not Bullet GPU training.
- Actual Bullet ModelWeights-written initialized checkpoint: 12,000 native/reference comparisons, zero mismatches, max cp error 0. Evidence: `bullet_initialized_comparison.json`, `bullet_initialized/`. This proves serializer/export/native interoperability for the initialized graph; it is not a trained model.
- All 8,192 selected HCE sidecar values equal the exact AL1 `Evaluator::evaluate_uncached` outputs. Evidence: `hce_subset_comparison.json`.
- Negative control: changing exactly one int16 output weight (`outw[0]`, original/new values in `sample_one_weight_mutation.json`) produced 9,190 arithmetic mismatches out of 12,000; compilation and native evaluation succeeded. Evidence: `sample_one_weight_comparison.json`. A separate output-bias bit mutation produced 12,000 mismatches and is retained as additional evidence.
- ASan/UBSan plus leak detection: final untraced sample oracle run evaluated 12,000 FENs with HCE, exit 0, empty sanitizer stderr, exact cp parity. Evidence: `sample_sanitized_untraced/` and its comparison JSON. The original leak-enabled sandbox attempt failed with LeakSanitizer's explicit ptrace limitation; `sample_sanitized/` retains that failure. The same frozen binary was retried, without disabling leak detection.
- Fresh full exact AL1 engine: OFF d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354; startpos perft5 = 4865609; Kiwipete perft5 = 193690690; whole-executable FMA mnemonic count = 0. Raw evidence and exact build recipe: `full_engine/`.

Release builds use GCC 14.2.0, C++20, `-O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256`. The sanitizer variant uses `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer` with the same architecture, network, and floating-point flags. Release oracle FMA counts are 0. Raw compiler diagnostics are retained; GCC reports an ignored-attributes warning for the FILE RAII deleter type.

## Evidence preservation and review fix

The initial oracle used truncating output streams. The review regression test reproduced six unsafe cases; the fixed oracle validates all paths before creating output and uses exclusive `fopen("wbx")`. Seven native regression tests now pass, covering existing output preservation, direct/symlink/hardlink input aliases, duplicate optional output paths, existing optional outputs, and successful new files. `oracle_io_commands.json` records both runs. The pre-review helper source is retained in `oracle_pre_review.cpp` and its SHA256 matches the original frozen identity; initial results are retained in `current/`. Final rebuilt identities are in `current_final/` and `sample/`.

`source_manifest.json`, per-build `identity.json`, exact command arrays, original logs and raw cp outputs identify the tested bytes. The initial broad source extraction failure due to the sandbox proxy is recorded separately; the full engine source was subsequently fetched and hash-verified in `full_engine/`.

This is Linux cloud correctness and export qualification. It makes no target-Windows-PC, GPU training, NPS, playing-strength, or Elo claim. All CTest results in sibling `native/ctest/` belong to the separately pinned R10 source: 14/15 tests passed, exit 8 with four preserved known diagnostics. No AL1 full-CTest rerun is asserted here.

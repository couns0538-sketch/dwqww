# Independent held-out comparison source review

PASS for the exact compare_holdout.py and test_holdout_report.py hashes in HOLDOUT-REPORT-REVIEW.json. No blocking source finding. This reviewer did not execute the CLI, unit tests, trained-network inference or a heavy data scan; a real comparison result remains pending.

## Authentication and matched evaluation

The recipe verifier requires the bound validation-provenance JSONL hash and count, authentic listed validation-game membership disjoint from known training IDs, matching original generating-engine hash and a source binding of the intended kind. It rejects duplicate game/ply or source-line identities. It replays every requested original source line, validates FEN/ply/bestmove/filter contract, checks exact FEN and row order, STM score and STM outcome against the NPZ, and compares both sparse perspective feature sets without changing their original order. HCE values are explicitly authenticated by prepared-array/probe provenance rather than silently claimed as recomputed.

Both shipped and candidate residual includes are loaded into the same H128 QAT architecture and evaluated on the same validation arrays. Per-row losses use the fixed pure search-teacher probability sigmoid(scoreSTM*2.25/400), HCE-only or correction-only as appropriate, and the shared exact correction clamp/truncation plus combined31871 clamp. Every row participates. Per-row means are checked against the trainer's complete evaluate() metrics at1e-12, and source/network/array/recipe identities are rehashed before fresh output publication. Per-row losses, cluster IDs, counts and network identities are retained.

With --reference-baseline-run supplied, the earlier run must be completed baseline-only with passed integrity and the same complete row count, shipped-net hash, original manifest/snapshot binding, all four validation arrays identical in dtype/shape/value bytes, the identical provenance recipe, and matching HCE/shipped metrics within1e-12. NPZ container-byte identity between differently created directories is not substituted for actual array identity. The switch is optional; without it, the report explicitly says it does not authenticate a prior holdout. The production invocation should supply it.

## Bootstrap review

Whole represented games are sampled with replacement, preserving all selected rows and using the same selected game indices for paired reference/candidate sums. The statistic is ratio(sum losses / sum rows), matching the row-weighted point estimate with unequal game sizes. Positive reference-minus-candidate means lower candidate loss. Percentile endpoints use linear interpolation. Zero-reference relative resamples are not dropped or replaced: the relative interval becomes undefined and the count is reported. Fewer than2 represented games, invalid IDs and nonfinite/negative losses fail. Empty eligible games are explicitly excluded as unrepresented clusters.

The report correctly states these intervals are conditional on the frozen candidate and do not correct selection of the candidate on this same holdout. It does not claim independent generalization confirmation, native inference, Elo, or that the residual term alone is the deployed evaluator.

## Tests inspected

13 test methods cover identity and paired intervals, unequal-size whole-game clusters, zero reference losses, deterministic seeds, invalid/missing identities, authentic ordered recipe replay, wrong hashes and game memberships, row/source/duplicate mismatches, full aggregate agreement, and same-reference array/metric guards. These test sources were read, not executed by this review.

## Candidate-specific probe build recipe (advisory only)

The quoted include in nnue.cpp is resolved relative to that source file before -I directories. Therefore passing a different -I include directory while compiling the original src/nnue.cpp can silently keep the shipped include. Copy only the unchanged nnue.cpp and chosen final include into a NEW outside build directory. Compile that NNUE object and place it BEFORE the immutable core archive on the link line. Do not use --whole-archive or mutate/remove members from the original library. All strong NNUE definitions then come from the explicit candidate object; confirm the link map contains no loaded libforge_core.a(nnue.cpp.o), then run actual candidate parity.

The following is a command template, not an executed build. Replace only FORGE_NNUE_CANDIDATE with the chosen immutable final export. Preserve commands, streams, return codes and input/output SHA-256s when executing.

```bash
set -euo pipefail
FORGE_NNUE_BUILD=/workspace/.cloud-setup/nnue-pipeline-20261023-candidate-probe-attempt1
FORGE_NNUE_CANDIDATE=/absolute/path/to/final/export.inc
mkdir -m 700 -- "$FORGE_NNUE_BUILD"
cp -- /workspace/dwqww/src/nnue.cpp "$FORGE_NNUE_BUILD/nnue.cpp"
cp -- "$FORGE_NNUE_CANDIDATE" "$FORGE_NNUE_BUILD/nnue_weights.inc"
/usr/bin/g++-14 -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto -DFORGE_NNUE_HIDDEN=128 -I /workspace/dwqww/include -c "$FORGE_NNUE_BUILD/nnue.cpp" -o "$FORGE_NNUE_BUILD/nnue-candidate.o"
/usr/bin/g++-14 -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto -DFORGE_NNUE_HIDDEN=128 -I /workspace/dwqww/include /workspace/dwqww/tools/nnue/engine_probe.cpp "$FORGE_NNUE_BUILD/nnue-candidate.o" /workspace/.cloud-setup/see-proof-reuse-native-release/libforge_core.a -pthread "-Wl,-Map,$FORGE_NNUE_BUILD/probe-link.map" -o "$FORGE_NNUE_BUILD/forge_nnue_probe"
```

Before compiling, verify unchanged nnue.cpp SHA86aec39feecf029e73510e7e5fadf9e9878c94744f0380c4149edf04da02cdcd; nnue.hpp SHAd87106d1716388375332ea20e97d9a703c74f479ffa5236c75608b356ab5aace; probe source SHAa4d584955d9cdf1185b6bec6efe884d90babf1a7bbcb79de1b0c40f69b647629; immutable core SHAaed0d79eb7bb2a997ea1ec59605e85dda49e84abacebc549e35b55817cbe2906. Rehash the chosen include and copied include before/after and require identity. A direct candidate probe compile does not build a release engine or establish playing strength.

Then invoke the existing parity runner with BOTH --probe pointing to this candidate executable and --weights pointing to that chosen final include, a new --out directory and --positions2048. Omitting --weights would incorrectly compare against the default shipped include. For the held-out comparison itself, use the final prepared-data directory, unchanged shipped include, chosen candidate include, fresh output,2000 bootstrap draws, seed20261023 and --reference-baseline-run pointing at the genuine earlier baseline run.

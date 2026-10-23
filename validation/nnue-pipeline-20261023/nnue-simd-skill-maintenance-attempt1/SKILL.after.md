---
name: validating-chess-simd
description: Use when changing SIMD or floating-point NNUE code in a UCI chess engine, preparing an x86 Windows executable, or evaluating speed and Elo claims for such a candidate.
---

# Validating chess SIMD

Preserve arithmetic semantics before measuring speed. Establish playing strength with games under equal clocks.

For the Forge reference, see [tested commands and limitations](../../../validation/nnue-avx2-9850x3d/README.md).

## Reproducible reference procedure

1. Record baseline commit, candidate commit/diff, network checksum, compiler version, complete build flags, executable checksums, target CPU and OS. Use existing isolated checkouts; create no worktree unless requested. Build an immutable baseline export and candidate in separate directories with identical compiler options. Never use the cloud CPU's `-march=native` for another person's computer.
2. For floating-point NNUE, preserve clamp operand order, each accumulation lane's sequence, multiplication association, final reduction order, rounding mode, and FTZ/DAZ settings. Keep `-fno-fast-math -ffp-contract=off`. For Ryzen Zen 5, an AVX2 comparison can use `-march=x86-64-v3 -mtune=znver5`; the shipped Zen 5 executable can use `-march=znver5 -mtune=znver5` after target compatibility checks.
3. Compile the same `tools/nnue_snapshot.cpp` against each core. Redirect stdout to separate files and run `cmp` before computing hashes. The stream compares accumulator float bits and integer evaluation outputs across legal walks, all special-move fixtures and 100,000 finite synthetic activations. It does not expose intermediate output-layer float sums or prove equivalence for NaNs.
4. Verify the emitted arithmetic with `python3 tools/check_nnue_simd.py OBJECT_OR_UNSTRIPPED_EXE`. An unchanged SSE build must fail its 256-bit instruction check; the candidate must pass. Run the complete CTest suite with `PYTHONDONTWRITEBYTECODE=1` and preserve logs.
5. Link `tools/search_benchmark.cpp` and `tools/nnue_benchmark.cpp` separately against both cores. Compare per-position depth/nodes/score/bestmove exactly. `benchmark_compare.py` verifies within-engine repeatability, not equality between engines; check cross-engine signatures explicitly. Counterbalance run order for timing experiments, retain raw repetitions and note other VM load. Kernel speed, search NPS and Elo are separate results.

Example differential build (repeat with each build directory):

```sh
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -I include tools/nnue_snapshot.cpp "$BUILD/libforge_core.a" -pthread \
  -o "$BUILD/nnue_snapshot"
"$BUILD/nnue_snapshot" > "$BUILD/nnue-snapshot.bin"
```

## Trained residual networks and handoffs

For Forge's residual H128 network, compare pure HCE, HCE plus the candidate,
and HCE plus the shipped network on identical complete validation data.
Residual-only output is a diagnostic, not the deployed evaluator. Keep STM
labels, the fixed HCE logit offset `HCE * 2.25 / 400`, and network conversion
`logit * 400 / 2.25`; validate exported features and integer scores against the
actual C++ evaluator with the chosen include. A changed network can change the
search tree: freeze its first genuine bench signature, then check repeatability
against that signature rather than the old network's node count.

Assigned game partitions can contain games with zero rows after filtering.
Require retained recipe IDs to be a subset of the assigned partition, match
actual fresh IDs and row counts against the authenticated frozen fresh recipe,
and report zero-retained IDs with their filter reasons. Do not require every
assigned game to retain a row. Legacy game IDs remain unknown and training-only;
FEN counters or file boundaries do not authenticate games.

Before reading independent-audit model losses, freeze the candidate using the
predeclared original-validation rule and record actual changed quantized numeric
`W1/B1/W2/B2` values, include/checkpoint hashes and data identity. A changed header
or include checksum alone does not establish trained weights. Audit results
assess that frozen candidate; they do not select another epoch.

Bind commands, source/net/data hashes, raw streams and actual process exits to
their receipts. Distinguish a failed closure checker from the original producer's
exit. Preserve failed gates and their inputs; use fresh output paths for a
corrected attempt instead of overwriting evidence or changing data to satisfy a
gate. See [NNUE pipeline evidence](../../../validation/nnue-pipeline-20261023/DIAGNOSIS.md).

## Windows and match evidence

Set `LLVM_MINGW_ROOT` to a checksum-verified LLVM-MinGW release. Configure a separate Release build with `-DCMAKE_TOOLCHAIN_FILE=tools/windows-zen5.cmake`. Inspect PE architecture/imports and run the delivered executable's UCI, pondering, legal-search and bench checks. Report Wine and native Windows separately; PE inspection alone is insufficient runtime evidence.

Run a pinned Fastchess A/A calibration before A/B. Freeze settings, openings, hashes and stopping rules. Equal-clock SPRT acceptance supports an improvement over its specified opponent; fixed-node identity and faster inference do not. A positive estimate before the stopping boundary is inconclusive. A claim against Stockfish requires a pinned full-strength opponent (`UCI_LimitStrength=false`), documented resources, audited terminations and complete paired PGNs. Publish the exact tested artifact and evidence, with unresolved checks named.

## Exact-order accumulator loop fusion

Use the actual engine API in `tools/nnue_update_snapshot.cpp`, linked separately
to each frozen actual core. It covers every dirty-count/flag pattern, both
perspectives, legal capture/EP/promotion/castling transitions, distinct and
in-place updates, unchanged parents and finite boundary inputs. Compare the
entire binary stream, including every float bit, evaluation, validity and MXCSR;
retain both original streams. Also run `tools/nnue_snapshot.cpp`: a new driver
does not replace the older independent corpus. Signed zero, subnormals and
rounding cancellation matter. Do not claim coverage for NaN or other rounding
modes unless explicitly added and verified.

Preserve every original per-lane intermediate operation. For remove/remove/add,
compute `((parent - removed0) - removed1) + added`, never combine feature columns
first. Guard the exact dirty pattern and retain all other fallback cases.
Accumulator-array validity alone does not validate a cached output score.

Inspect the complete actual `nnue::update` symbol, using anchored disassembly
headers. An instruction inventory is weaker than tracing the pattern guard to
the fused loop and its store. Preserve compiler flags and prove no FMA. Keep
source-level traffic reductions separate from measured throughput and Elo.

An immutable build export must include `CMakeLists.txt LICENSE bench include
src tests tools`; omitting `bench/` prevents the existing CMake configuration.
Retain failed exports/configure logs and use a new attempt directory. Freeze
source hashes before building, then prove they match the final commit.

Useful evidence: `validation/nnue-update-fusion-20261019/` and
`validation/nnue-capture-fusion-20261019/`. The strict hosted timing profile
39334266771 failed its same-binary noise gate and ran no A/B. Do not retry it or
widen its gate; a separately preregistered equal-clock strength experiment is a
different question and must state that distinction.

## Comparing build objects

Preserve raw archives/member bytes and whole-file hashes. Decode the actual AR
long-name format: GNU `/\n` or COFF NUL terminators, with bounded offsets and
rejection of unknown formats and duplicate/unexpected object members.

Report raw identity first. A timestamp-qualified comparison requires a validated
ordinary AMD64 COFF object (machine `0x8664`, 20-byte header and valid section
table; not PE, bigobj or an unknown layout), equal lengths, and **every byte
outside header TimeDateStamp offsets 4–7 identical**. Retain raw hashes and exact
difference offsets. Never call a timestamp-qualified NNUE object raw bit-exact,
ignore sections/code/data/relocations, or mask additional bytes.

This limited structural evidence supplements arithmetic/search parity and
runtime tests; it does not establish full semantic equivalence. Preserve original
failed parsers/assertions, streams and unknown exit facts. Do not rebuild or
rewrite objects/flags to force matching hashes.

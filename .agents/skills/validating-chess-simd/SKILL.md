---
name: validating-chess-simd
description: Use when changing SIMD or floating-point NNUE code in a UCI chess engine, preparing an x86 Windows executable, or evaluating speed and Elo claims for such a candidate.
---

# Validating chess SIMD

Preserve arithmetic semantics before measuring speed. Establish playing strength with games under equal clocks.

For the Forge reference, see [tested commands and limitations](../../../validation/nnue-avx2-9850x3d/README.md).

The latest explicit user validation/retention contract takes precedence over this workflow; preserve older frozen evidence when applying a newer contract to a new run.

## Reproducible reference procedure

1. Record baseline commit, candidate commit/diff, network checksum, compiler version, complete build flags, executable checksums, target CPU and OS. Use existing isolated checkouts; create no worktree unless requested. Build an immutable baseline export and candidate in separate directories with identical compiler options. Never use the cloud CPU's `-march=native` for another person's computer.
2. For floating-point NNUE, preserve clamp operand order, each accumulation lane's sequence, multiplication association, final reduction order, rounding mode, and FTZ/DAZ settings. Keep `-fno-fast-math -ffp-contract=off`. For Ryzen Zen 5, an AVX2 comparison can use `-march=x86-64-v3 -mtune=znver5`; the shipped Zen 5 executable can use `-march=znver5 -mtune=znver5` after target compatibility checks.
3. Compile the same `tools/nnue_snapshot.cpp` against each core. Redirect stdout to separate files and run `cmp` before computing hashes. The stream compares accumulator float bits and integer evaluation outputs across legal walks, all special-move fixtures and 100,000 finite synthetic activations. It does not expose intermediate output-layer float sums or prove equivalence for NaNs.
4. For Forge, check scoped NNUE emission with `python3 -B releases/forge_sol_pack31_20261025/S05/forge_sol_S05_fmacheck_v3_20261025.py OBJECT_OR_UNSTRIPPED_EXE`. Preserve its exact JSON, including scanned symbols, qualified output bodies and FMA count. It scans all demangled `forge::nnue::` bodies, including outlined helpers and compiler clones, and recognizes the supported output pattern in the public evaluator or `evaluate_values`. The legacy `tools/check_nnue_simd.py` scans only the public evaluator and can accept FMA in an outlined helper; its historical results retain that limited scope. The current checker still requires a recognized 256-bit output pattern and unstripped symbols; it is not a general semantic-equivalence proof or an ISA-independent checker. An unchanged SSE build must fail this width check. Run the complete CTest suite with `PYTHONDONTWRITEBYTECODE=1` and preserve logs.
5. Link `tools/search_benchmark.cpp` and `tools/nnue_benchmark.cpp` separately against both cores. Compare per-position depth/nodes/score/bestmove exactly. `benchmark_compare.py` verifies within-engine repeatability, not equality between engines; check cross-engine signatures explicitly. Counterbalance run order for timing experiments, retain raw repetitions and note other VM load. Kernel speed, search NPS and Elo are separate results.

For each new Forge build, run its required lock `bench 11` as the first engine test, with experimental runtime options OFF and reference settings intact; a mismatch stops every later test/measurement. See the [native gates](../../../tools/windows/zen5_qualify_sol.ps1) and [negative fixtures](../../../tools/windows/tests/test_failure_gates.py).

Classify switches as compile-time defines or runtime UCI options; bind each to its actual source/executable/settings. Compile-time AVX512/alignment switches require separate builds and cannot be disabled through an invented UCI option.

State each checker's accepted ISA, width and symbol scope, and retain its exact result: a 256-bit-only FAIL remains FAIL for an AVX512 build. Report separate ISA-appropriate emitted-code/numerical evidence; never relabel that FAIL as AVX512 PASS.

For a float-locked reference, approximate/int16 inference requires explicit research authorization and its own OFF-default option. An advertised option is insufficient: require the actual active-backend acknowledgement and reject float fallback before attributing ON results.

For that authorized approximate path, use the [actual-core parity driver](../../../tools/nnue_int16_parity.cpp) on at least 100,000 unique legal positions with an explicit uniqueness key; report mean/max/p99 absolute cp error, strict sign flips/zero crossings, preregistered limits, and accumulator/per-worker memory cost including OFF mode. Numerical PASS is not bit-exactness, speed or strength acceptance.

Example differential build (repeat with each build directory):

```sh
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -I include tools/nnue_snapshot.cpp "$BUILD/libforge_core.a" -pthread \
  -o "$BUILD/nnue_snapshot"
"$BUILD/nnue_snapshot" > "$BUILD/nnue-snapshot.bin"
```

## Patch-only source handoffs

Bind each patch to the exact supplied source trees, including test-only merges.
Generate it with `git diff` in the private candidate repository; stage new paths
with intent-to-add so their diffs include `new file mode 100644`. Keep full
context and `a/` / `b/` prefixes. Before compiling, run both
`git apply --check /absolute/candidate.patch` and
`patch -p1 -F0 --dry-run < /absolute/candidate.patch` from a pristine copy of
**each** declared base. Retain commands, exits, original streams and patch/tree
hashes. A GNU patch pass alone does not establish Git application compatibility.
When tests changed in a later handoff, preserve prior results under their exact
old tree identities and qualify the new trees separately.

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

Preserve every failed timed trial, exact exchanges/deadlines, and observer/child CPU evidence, including late observations and missing baselines. Later diagnostics alone do not establish the original cause or replace its failure; keep cause unresolved where evidence is insufficient, and keep any separately authorized fresh preregistered run unpooled with the failed trial.

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

## Large deterministic H256 oracle streams

Use the [actual-core oracle runner](../../../tools/nnue_million_oracle.py) with
both frozen producer executables. For a repeat corpus with retained originals,
pass `--dedup-reference-result /path/to/closed/result.json` and
`--reuse-reference-compression`. Both producers still execute and emit fresh
outputs. Retention reuse requires raw comparisons, independent hashes/counts,
and full canonical decompression through `cmp` against each fresh raw chunk
before linking the immutable archive. Preserve canonical bytes and permissions;
retain failing raw outputs. This saves recompression, not engine computation.
Without a frozen compatible reference, use the independent-compression default.

For a new run under an explicit compact-retention contract, use bounded fresh chunks with identities, counts, coverage, hashes/hash manifests and retained failing chunks; preserve existing frozen streams. The [seeded native protocol](../../../tools/windows/EXPECTED_OUTPUT.md) distinguishes seeds 1..100 from the old single-seed corpus and a hash-manifest digest from raw-concatenation SHA256.

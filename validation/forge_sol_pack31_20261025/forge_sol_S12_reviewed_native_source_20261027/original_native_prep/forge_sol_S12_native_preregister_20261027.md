# S12 serial native validation, prepared 2026-10-27

Status: **SOURCE ONLY. Every C++ compile, main runtime, native regression,
counter measurement and parity result below is UNVERIFIED.** Preparation is
not delivery/acceptance of S12. No performance, Elo or adoption claim.

Root alone grants execution after the actual S11 experiment closes and is
published. A published SHA is a necessary reference, not a CPU lease. Do not
overlap S11/S13/S14 native work, training timing, or any other benchmark. Do not
run this entire document as an unbounded queue. Each invocation has its own
finite grant and checks the assigned core/nice setting. Stop on the first
unexpected failure and preserve the original output; no silent retry.

## Exact source and scope

Use the **single frozen v2** S12 patch at
`/tmp/forge_sol_S12_delivery_prepared_20261026/forge_sol_S12_lazyacc_h256e12_reviewv2_20261026.patch`,
SHA256 `66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d`.
No patch is copied or regenerated here. The old general S12 metadata contains a
v1 candidate search hash. It is not authoritative for candidate code. The new
per-base inventory pins the v2 result projected with GNU `-F0` onto Lprime and
B, with exactly six changed paths and unchanged original inventories.

The baseline already has lazy nearest-ancestor accumulator replay. S12's
bounded change skips physical accumulator/PSQT copies on zero-dirty/null edges,
through valid-ancestor aliases. It preserves float arithmetic, net, evaluation,
search and move ordering. Existing frozen reports already explain the old Job
A counters and the observed 0.976/0.930 ratios; this packet does not retime or
reimplement that investigation.

Original source code commit: `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`.
Net SHA256: `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`;
MD5: `6d22f612c855e17c62d396d32da99ea4`.

Release recipe: pinned GCC14.2, C++20, `-O3 -DNDEBUG -march=x86-64-v3
-mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`.
ASan/UBSan: same ISA/FP/net with `-O2 -g -DNDEBUG
-fsanitize=address,undefined -fno-omit-frame-pointer`.
No PGO/LTO/int16/other feature. Compiler-only CLI has a 4GiB AS cap.
Sanitizer runtime must be a fresh process with unlimited AS for shadow mapping,
leak detection ON, and an owned-subtree RSS guard. One CPU, nice19, jobs1.
Never kill a foreign process. Owned children are reaped and closure recorded.

## Gates and references

Every **new main** first executes exactly `bench 11\nquit\n` without prior UCI,
helper or CTest execution. FIRST is a separate invocation before FULL. Full Std
always uses runtime OFF, including a feature-capable build. It retains all
current tests: Lprime14/B15, exactly four documented KNOWN_FAILURE diagnostics,
no new FAIL/PIN_MISMATCH/error/skip. OFF default, typed UCI default, TT/SMP,
rule50, correction/PSQT, legal witness, ponder/OwnBook tests remain included.

Release OFF and ON fixed references:

| depth | nodes |
|---|---:|
| 11 | 308972 |
| 13 | 745494 |
| 16 | 2460422 |
| 20 | 11901452 |
| 22 | 31111774 |

Release perft5: startpos4865609; kiwipete193690690 using the authoritative
`r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`.
ASan bounded Std/ON uses d11 and perft4 start197281/kiwi4085603, then full
current CTest. The full five depths/perft5 are Release gates; ASan full-depth22
and an additional build-time-OFF ASan build are not claimed or planned.
FMA must be0 in NNUE object, scoped ELF and whole ELF. Compiled-ON FMA evidence
covers the code present in both runtime branches; it is not a separate ON
disassembly. Compiled-OFF has its own main FMA check.

## Baseline reuse eligibility

`forge_sol_S12_bind_arm_20261027.py` verifies existing pristine S11 baseline
evidence, not S11 candidate source or its material-key producer. Release reuse
checks original source/net/compiler/flags/main/current Std, original FIRST and
all fixed bench/perft references plus the completed typed UCI/FMA light checks;
the restored core bytes must equal that exact canonical archive. ASan reuse
checks actual S11 baseline build, FIRST, FULL, raw current full CTest/JUnit,
reference captures, leak/sanitizer environment, FMA and owned closure.

Pinned original receipt list is `forge_sol_S12_baseline_receipt_pins_20261027.json`.
Any changed source/compiler/artifact/profile/status or missing original evidence
blocks reuse. Reuse claims **zero** new main builds, FIRST, Std and JUnit runs.
If reuse fails, stop and diagnose; a separately authorized fresh pristine build
can use the same builder with `--role baseline --feature OFF`. Never relabel
S11's candidate core or slow material oracle as a baseline.

## Commands, one finite invocation at a time

Run from this packet directory. First verify its SHA256SUMS against the hash
published by root. Set only the actual new grant/reference values; placeholders
are not approvals. All output paths below must be NEW, literal descendants of
`/tmp/forge_sol_S12_native_20261027`.

```bash
PREP=/tmp/forge_sol_S12_native_prep_20261027
ROOT=/tmp/forge_sol_S12_native_20261027
CPU=2
GRANT=ROOT_SUPPLIED_NEW_SERIAL_LEASE
S11_SHA=ROOT_SUPPLIED_VERIFIED_40_HEX_PUBLICATION_SHA
BASE=Lprime                 # Repeat independently for B after closure.
cd "$PREP"
sha256sum -c forge_sol_S12_native_SHA256SUMS_20261027.txt
run() { taskset -c "$CPU" nice -n 19 python -B "$@"; }

# Binding is read/hash/parse only, no native execution, no new Std claim.
run forge_sol_S12_bind_arm_20261027.py --reuse-baseline --base "$BASE" --profile Release --out "$ROOT/${BASE}_baseline_Release_arm.json"
run forge_sol_S12_bind_arm_20261027.py --reuse-baseline --base "$BASE" --profile ASAN --out "$ROOT/${BASE}_baseline_ASAN_arm.json"

# Repeat this block for FEATURE=OFF, then ON (Release); each new main gets FIRST.
FEATURE=OFF
BUILD="$ROOT/${BASE}_candidate_Release_${FEATURE}_build"
run forge_sol_S12_build_native_20261027.py --execute --authorization-reference "$GRANT" --s11-published-commit "$S11_SHA" --base "$BASE" --role candidate --feature "$FEATURE" --profile Release --out "$BUILD" --cpu "$CPU" --max-seconds 900
run forge_sol_S12_qualify_native_20261027.py --execute --authorization-reference "$GRANT" --mode FIRST --build-receipt "$BUILD/forge_sol_S12_build_result_20261027.json" --out "${BUILD}_FIRST" --max-seconds 120
run forge_sol_S12_qualify_native_20261027.py --execute --authorization-reference "$GRANT" --mode FULL --build-receipt "$BUILD/forge_sol_S12_build_result_20261027.json" --first-runtime-receipt "${BUILD}_FIRST/forge_sol_S12_runtime_result_20261027.json" --out "${BUILD}_FULL" --max-seconds 600
run forge_sol_S12_bind_arm_20261027.py --build "$BUILD/forge_sol_S12_build_result_20261027.json" --first "${BUILD}_FIRST/forge_sol_S12_runtime_result_20261027.json" --full "${BUILD}_FULL/forge_sol_S12_runtime_result_20261027.json" --out "$ROOT/${BASE}_candidate_Release_${FEATURE}_arm.json"

# Only after the completed ON build/FIRST/FULL above:
ON_ARM="$ROOT/${BASE}_candidate_Release_ON_arm.json"
run forge_sol_S12_feature_qualify_20261027.py --execute --authorization-reference "$GRANT" --arm "$ON_ARM" --out "$ROOT/${BASE}_Release_ON_feature" --cpu "$CPU" --max-seconds 600
run forge_sol_S12_helpers_build_20261027.py --execute --authorization-reference "$GRANT" --arm "$ROOT/${BASE}_baseline_Release_arm.json" --out "$ROOT/${BASE}_baseline_Release_helpers" --cpu "$CPU" --max-seconds 180
run forge_sol_S12_helpers_build_20261027.py --execute --authorization-reference "$GRANT" --arm "$ON_ARM" --out "$ROOT/${BASE}_candidate_Release_helpers" --cpu "$CPU" --max-seconds 180
run forge_sol_S12_helpers_run_20261027.py --execute --authorization-reference "$GRANT" --helper-receipt "$ROOT/${BASE}_baseline_Release_helpers/forge_sol_S12_helpers_build_result_20261027.json" --operation regression --out "$ROOT/${BASE}_baseline_Release_actual_RED" --cpu "$CPU" --max-seconds 120
run forge_sol_S12_helpers_run_20261027.py --execute --authorization-reference "$GRANT" --helper-receipt "$ROOT/${BASE}_candidate_Release_helpers/forge_sol_S12_helpers_build_result_20261027.json" --operation regression --out "$ROOT/${BASE}_candidate_Release_actual_GREEN" --cpu "$CPU" --max-seconds 120
run forge_sol_S12_helpers_run_20261027.py --execute --authorization-reference "$GRANT" --helper-receipt "$ROOT/${BASE}_candidate_Release_helpers/forge_sol_S12_helpers_build_result_20261027.json" --operation counters --out "$ROOT/${BASE}_Release_counter_all5" --cpu "$CPU" --max-seconds 900

CORPUS_MANIFEST=ROOT_SUPPLIED_EXISTING_S09_ORIGINAL_CORPUS_MANIFEST
run forge_sol_S12_alias_run_20261027.py --execute --authorization-reference "$GRANT" --baseline-helpers "$ROOT/${BASE}_baseline_Release_helpers/forge_sol_S12_helpers_build_result_20261027.json" --candidate-helpers "$ROOT/${BASE}_candidate_Release_helpers/forge_sol_S12_helpers_build_result_20261027.json" --corpus-manifest "$CORPUS_MANIFEST" --out "$ROOT/${BASE}_actual_alias_parity" --cpu "$CPU" --max-seconds 600 --arm-seconds 180

# ASan: fresh compiler process, then separate runtime with unlimited AS.
BUILD="$ROOT/${BASE}_candidate_ASAN_ON_build"
run forge_sol_S12_build_native_20261027.py --execute --authorization-reference "$GRANT" --s11-published-commit "$S11_SHA" --base "$BASE" --role candidate --feature ON --profile ASAN --out "$BUILD" --cpu "$CPU" --max-seconds 900
run forge_sol_S12_qualify_native_20261027.py --execute --authorization-reference "$GRANT" --mode FIRST --build-receipt "$BUILD/forge_sol_S12_build_result_20261027.json" --out "${BUILD}_FIRST" --max-seconds 120
run forge_sol_S12_qualify_native_20261027.py --execute --authorization-reference "$GRANT" --mode FULL --build-receipt "$BUILD/forge_sol_S12_build_result_20261027.json" --first-runtime-receipt "${BUILD}_FIRST/forge_sol_S12_runtime_result_20261027.json" --out "${BUILD}_FULL" --max-seconds 600
run forge_sol_S12_bind_arm_20261027.py --build "$BUILD/forge_sol_S12_build_result_20261027.json" --first "${BUILD}_FIRST/forge_sol_S12_runtime_result_20261027.json" --full "${BUILD}_FULL/forge_sol_S12_runtime_result_20261027.json" --out "$ROOT/${BASE}_candidate_ASAN_ON_arm.json"
run forge_sol_S12_feature_qualify_20261027.py --execute --authorization-reference "$GRANT" --arm "$ROOT/${BASE}_candidate_ASAN_ON_arm.json" --out "$ROOT/${BASE}_ASAN_ON_feature" --cpu "$CPU" --max-seconds 300
run forge_sol_S12_helpers_build_20261027.py --execute --authorization-reference "$GRANT" --arm "$ROOT/${BASE}_baseline_ASAN_arm.json" --out "$ROOT/${BASE}_baseline_ASAN_helpers" --cpu "$CPU" --max-seconds 180
run forge_sol_S12_helpers_build_20261027.py --execute --authorization-reference "$GRANT" --arm "$ROOT/${BASE}_candidate_ASAN_ON_arm.json" --out "$ROOT/${BASE}_candidate_ASAN_helpers" --cpu "$CPU" --max-seconds 180
run forge_sol_S12_helpers_run_20261027.py --execute --authorization-reference "$GRANT" --helper-receipt "$ROOT/${BASE}_baseline_ASAN_helpers/forge_sol_S12_helpers_build_result_20261027.json" --operation regression --out "$ROOT/${BASE}_baseline_ASAN_actual_RED" --cpu "$CPU" --max-seconds 120
run forge_sol_S12_helpers_run_20261027.py --execute --authorization-reference "$GRANT" --helper-receipt "$ROOT/${BASE}_candidate_ASAN_helpers/forge_sol_S12_helpers_build_result_20261027.json" --operation regression --out "$ROOT/${BASE}_candidate_ASAN_actual_GREEN" --cpu "$CPU" --max-seconds 120
```

Use `--allow-rewrapped-corpus` only for an explicitly reviewed codec-only S09
recovery; the original raw52,261,200 bytes/SHA/count remain mandatory. The
corpus is not regenerated. This packet intentionally does not auto-select a
random newer corpus manifest.

## Native oracle and counter interpretation

The frozen actual Worker regression must first produce RED on the real pristine
base (exact17 alias/copy assertions only, zero waived float/PSQT/full-eval
failures), then GREEN on the feature-capable candidate. It covers stale sibling
aliases, unevaluated real/null chains, clear/restart, invalid PSQT owners, EP,
both-color castling and underpromotions, capture promotion and NNUE OFF.

The new bounded parity producer constructs **one Worker** per process and never
clears its histories per FEN. It initializes only the physical root/PSQT for
each of the first8,192 sealed original corpus FENs; actual `record_move/null`
must invalidate child frames. First1,024 roots additionally test null-null,
unevaluated real-null replay and alias-to-real sibling overwrite. Every tested
state compares actual Worker evaluation, all512 float words, NNUE integer
output and PSQT against fresh recomputation. One selected state/root is retained
as index/key/score/512 float bits. The baseline/OFF/ON streams must compare every
original decompressed byte, with exact contiguous record/chunk/EOF coverage.
This is bounded8,192-root coverage, **not a million-position result**. Any
native parity failure or missing path/counter proof blocks the candidate.

The existing, final source-bound counter helper records real eight-FEN bench
stats at all five depths, OFF and ON, with exact per-FEN nodes and total
references. It checks OFF updates = ON updates + ON copies avoided and matches
refresh/evaluation/zero-edge work. ON must announce active once and have real
counter changes. The stats expose aggregate refreshes; the eight root refreshes
and aggregate-minus-eight fallback split are explicitly **source-derived**
(patched search.cpp root initialization1450–1452), not separately measured.
Refresh share is the measured rational refreshes/evaluations. No timings from
these correctness runs are speed evidence. A later isolated predeclared ABBA
requires a separate grant after all gates; this packet makes no speed claim.

## Preservation and stop policy

Preserve build/FIRST/FULL/feature/helper/parity receipts, original stdin/stdout/
stderr, JUnit, maps, compiler invocations, source and binary hashes, original
compressed stream chunks and any failures. Keep all failed output directories;
never overwrite and rerun under the same name. Hash raw evidence after closure.
No matches are proposed for this node-identical correctness stage; no PGNs or
Elo estimates exist. Parent alone publishes and verifies raw GitHub readback.

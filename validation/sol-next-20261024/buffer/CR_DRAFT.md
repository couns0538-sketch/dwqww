# CR DRAFT — defensive deferred-capture capacity repair

**d11 precondition FIRST: 308972, PASS for every tested profile**, before subsequent engine tests. Original receipts: `raw/buffer-release-qa/precondition-d11/RESULT.json`, `raw/buffer-assert-on-qa/precondition-d11/RESULT.json`, `raw/buffer-asan-on-qa/precondition-d11/RESULT.json`; the original-array reproducer has its own receipt at `raw/buffer-original-assert/qa/precondition-d11/RESULT.json`.

**Finding: overflow not reproduced on FENs tried; fixed defensively.** The source containment repair and normal-input regression passed their recorded checks; the timed tactical screen is lower for the buffer build and remains an unresolved possible regression. No speed, playing-strength, gate or lock conclusion is made by this draft.

## Source, manifest and build identity

Tested buffer checkpoint: `30e703edc90976b9c59fb22912ddabb3b690658f`, bound by the immutable source-ZIP manifest and `patch-delivery-verification/RECEIPT.md`. Lock: H256 e12 `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`; unchanged network SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. Do not identify these old buffer binaries using the later int16 working tree.

Two distinct `-p1` artifacts exist against f4911f2:

- Minimal buffer-only source/test patch: `../../../releases/sol-next-20261024/buffer_only.patch`, 9605 bytes, SHA256 `32967232826f1fb446ae7651068446926ce37a727ca71b480d5f465efc4bd6ab`; production change is the deferred array, with new CTest registration/test and IDEA_SOURCE documentation.
- Cumulative tested-profile handoff: `../../../releases/sol-next-20261024/buffer_fix.patch`, 26782 bytes, SHA256 `3cf718189340d1b8ea47361e4c8ede0203b39da749938a670a41d50cad19fc6c`. This also retains earlier optional AVX-512/alignment code and the OFF-default `FORGE_COMPLETE_ITERATION_ONLY` guard. It is **not** the minimal four-file buffer-only diff.

Delivered ZIP: `releases/sol-next-20261024/forge-buffer-source.zip`, SHA256 `e05e75180a6e9b2c390fb7711aa6f686b51ac172333ab65670347bbce852fb51`. Both delivered patches apply to exact f4911f2 with `patch --batch --forward --fuzz=0 -p1`, dry-run and real application, all exits 0/no offset/fuzz/rejection. All 34 cumulative core/build files equal the ZIP; all 99 manifest files equal 30e703e, all 89 tracked build-input paths and all four local `.inc` files are present. Receipt and exact operations: `patch-delivery-verification/{RECEIPT.md,RESULT.json,TRACKED_BUILD_INPUTS.json}`. **No fresh rebuild or runtime requalification was performed by that delivery audit**; original frozen-build identities remain the runtime evidence.

Linux, g++ 14.2, Intel Xeon 8573C shared host; no native Ryzen/Windows result. All profiles use H256, `-std=c++20 -ffp-contract=off -fno-fast-math -march=znver5`, warnings `-Wall -Wextra -Wpedantic -Wconversion -Wshadow`. CMake `Threads::Threads` resolves empty on merged glibc: the engine compile/link commands emit **no literal `-pthread`**, a configuration difference from the requested direct command. Windows direct commands and the original 64-slot direct reproducer retain `-pthread`. No frozen binary was rebuilt to alter this. Exact configure/build argv: `buffer-commands.json`; exact emitted compiler flags and link commands: each build's `CMakeFiles/forge_core.dir/flags.make` and `CMakeFiles/forge.dir/link.txt`.

| Profile | Additional actual build settings | forge SHA256 |
|---|---|---|
| Release OFF | `-O3 -DNDEBUG`, static link; AVX512/ALIGN64/COMPLETE_ITERATION_ONLY defaults0 | `dbc2df7403b20f3a767e22e1d53e11716a7ecac702f846bad666973d02306ac4` |
| Assertions flags ON | `-O1 -g1 -DNDEBUG -D_GLIBCXX_ASSERTIONS -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=1`; nonstatic link | `373a3063cd501cfe8342f03d5b905ef316d07cc398939c718edf816abf30e9bc` |
| ASan/UBSan flags ON | `-O1 -g1 -DNDEBUG -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=1 -fsanitize=address,undefined -fno-omit-frame-pointer`; nonstatic link | `7e863dda35eccbf74fedf70a636ea6335593da3eef39e79e6c9509ad6bedf0af` |
| Original 64-slot assertions reproducer | Direct g++ command in `buffer-original-assert-command.json`, O1/g1/NDEBUG, `_GLIBCXX_ASSERTIONS`, AVX512=1, ALIGN64=1, strict FP, pthread | `263e77f6757a673d75604bfd3edb53de5552e773f393158d7c1fb3ff97b1d8d1` |

For example, actual Release configuration was `cmake -S /workspace/dwqww -B /workspace/forge-sol-next-20261024/build-buffer-release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_EXTENSIONS=OFF "-DCMAKE_CXX_FLAGS=-DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5" -DCMAKE_EXE_LINKER_FLAGS=-static`, followed by `cmake --build /workspace/forge-sol-next-20261024/build-buffer-release --parallel 2`; the absolute CMake executable and all other profile commands are preserved in the JSON above. No fast-math was enabled.

## Supplemental strict Release qualification

From the immutable 30e703e ZIP, both new profiles use explicit `-pthread`, static linking, O3/NDEBUG/H256/strict FP/znver5 and `FORGE_COMPLETE_ITERATION_ONLY=0`. Source and original artifacts remain unchanged. Exact source/commands/binary bindings and closed receipts: `strict-release/PROVENANCE.json`, SHA256 `38f1ff033e03c4045b62849372d37d39362f7b99d8afe7a98d7ebee852a8d6b1`.

| Supplemental profile | First d11 and remaining qualification | Artifact identity |
|---|---|---|
| Release OFF, AVX512=0/ALIGN64=0 | First d11 PASS 308972; original all-five/perft/CTest evidence reused by raw-byte identity | Engine exactly original `dbc2df…06ac4`; core `7f942d0d29bc357859d990ba20bbd8d7713e2fffecc341963caa3b942b31ab9e` |
| Release ON, AVX512=1/ALIGN64=1 | First d11 308972, then d13/d16/d20/d22 = 745494/2460422/11901452/31111774; both perft5 values PASS | Engine SHA256 `e69695843a43927882dc1826c7ae27ce36288942f44bffe7ca3b1810ee65ffaf` |

Both supplemental builds retain the same six inherited conversion warnings; bench stderr is empty. No new full CTest was run for the new O3 ON executable: the original O1 assertions-ON and ASan/UBSan-ON full-suite receipts remain distinct. Original CMake metadata above is preserved; the new explicit-pthread builds are additional qualification, not relabeled old commands. No timing inference follows.

## Repair, reachability evidence and regression coverage

The noisy producer is bounded by `MoveList::Capacity=256`. GoodCaptures can defer each original noisy move at most once. The old `std::array<Move,64>` did not contain that producer contract. The repair uses `std::array<Move,MoveList::Capacity>` and a compile-time containment assertion. There is no new switch, pruning/order change or production test hook. Added storage: 192 four-byte Moves, **768 bytes per MovePicker**; performance effects require measurement.

Both supplied FENs were parsed and searched normally to depth3 on the **original 64-slot `_GLIBCXX_ASSERTIONS` engine**; both exited0 without an assertion (`raw/buffer-original-assert/fixed-fens/RESULT.json`, original transcripts retained). The normal CTest census for the repaired build, identical across all three profiles, records:

| Fixture | noisy | SEE-losing / legal SEE-losing | promotions |
|---|---:|---:|---:|
| qa-1 | 72 | 50 / 50 | 0 |
| qa-2 | 68 | 45 / 45 | 0 |
| poisoned pawn | 1 | 1 / 1 | 0 |
| white promotions | 8 | 4 / 4 | 8 |
| black promotions | 8 | 4 / 4 | 8 |

Densest tested supplied FEN (qa-1):
`1Q1bq3/pr1Q1p1R/KQ1n1Q1b/1p1Q1n1Q/BQ1p1Q1r/1p1QpN2/1k1pR2p/5NB1 w - - 0 1`.
Second supplied FEN (qa-2):
`1krQ2b1/8/Q2pQnR1/p1Q3b1/Q1n2QrQ/p1QQpKp1/q1ppR2p/1NB1BN2 w - - 0 1`.

`forge_bad_capture_tests` accepted all five, failures0. It preserves board/FEN/key/history during SEE census and search, checks legal bestmove/PV, and forces the actual SEE-losing poisoned-pawn move `d1d5` through a normal root restriction. The promotion controls include all Q/R/B/N quiet/capture choices for both colors. Evidence: `release-LastTest.log, assert-on-LastTest.log, asan-on-LastTest.log`; source `../../../tests/bad_capture_tests.cpp`.

This is not capacity saturation: noisy72 does not mean 72 entries reached the deferred array; qa-1 has only50 SEE-losing candidates. No >64 SEE-losing normal FEN or overflow was found. The compile-time contract proves declared containment under the existing MoveList contract, not native reachability of the old defect. No parser bypass, private-buffer injection, fuzzer or input generator was used; ASan alone cannot establish absence of an intra-object overrun.

## Bench, perft, full suites and emitted arithmetic

Release T1/H16/OwnBook=false OFF bench d11/d13/d16/d20/d22 = **308972 / 745494 / 2460422 / 11901452 / 31111774**, exactly the lock. Startpos perft5 **4865609**; kiwipete perft5 **193690690**. Assertions-ON and ASan/UBSan-ON each have d11 **308972** then bench13 **745494**, exit0, empty bench stderr. Evidence: `raw/buffer-release-qa/full-signatures-perft/RESULT.json`, `raw/buffer-{assert,asan}-on-qa/bench13/RESULT.json`. The other three depths were not rerun for these O1 flags-ON profiles.

Full Release, assertions-ON and ASan/UBSan-ON CTest each completed **14/15 suites passed**, one failing `forge_tests`, exit8. All have exactly these four FAIL lines:

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 661 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

Logs/actual exits: `raw/buffer-steps/{release,assert-on,asan-on}-ctest/{stdout,result.json}`. ASan/UBSan reported no sanitizer finding; its CTest stderr is the 27-byte `Errors while running CTest` wrapper message, not empty. Environment: `ASAN_OPTIONS=detect_leaks=1:abort_on_error=1`, `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. This closes the recorded flags-ON full-suite and bench13 coverage gap, without calling the full suite all-green.

SIMD checker v2: OFF **PASS** (`buffer-simd-v2-off.stdout`); AVX512+ALIGN64 ON emits exact checker failure `FAIL: NNUE output has no 256-bit vminps` (`buffer-simd-v2-on.stderr`). This is an **ISA-contract mismatch**: the ON float kernel uses 512-bit instructions and the checker requires 256-bit vminps; it is not a v2 PASS. Original symbol-attributed FMA receipts report Forge FMA0 for both OFF and ON. Whole OFF static binary has46 libm log FMAs; ON assertions binary has0 total (`fma-off/summary.json`, `fma-on/summary.json`).

## UCI, null-move coverage, tactics and open fields

The repair adds **no UCI option**. Original banner lines include `Hash` default32, `Threads` default1, `Move Overhead` default10, `Ponder` defaultfalse, `OwnBook` defaulttrue, `Book File`, `Book Depth` default30, `Book Variety` default30, `UseNNUE` defaulttrue, `Clear Hash`. The fixed-input UCI reproducer and WAC disable OwnBook; the new C++ regression uses Searcher directly, where book lookup is absent; `ownbook_regression` exercises both settings. The later `NnueInt16` option does not belong to this buffer artifact. Original UCI transcript: `raw/buffer-original-assert/fixed-fens/qa-1.log`.

Existing full suites include UCI/ponder/OwnBook regression and legal searchmoves/zero-node/promotion/EP/terminal cases. `tests.cpp` also executes depth8 pawn-only null-tries==0 and startpos null-tries>0/null-cutoffs>0 assertions; these did not add FAIL lines. Board null make/unmake and key restoration are checked separately. **Numeric d8 counters PASS:** fresh Searcher(16,1), startpos tries/cutoffs **7/5**, exact pawn-only source fixture `8/8/8/3k4/8/4K3/4P3/8 w - - 0 1` **0/0**. Both completed d8 with legal bestmove/PV, compile/run exits 0 and empty stderr. Correct old exported headers matched the 30e703e ZIP; headers/helper/core/receipt hashes remained unchanged. Original outputs and exact commands: `../int16/null-counters/{BEFORE.json,RESULT.json,buffer.stdout,buffer.stderr}`. No new engine hook or timing measurement.

Paired WAC300 1000ms, T1/H16/OwnBook=false, CPU0, lock / buffer / lock: **276 / 265 / 279** solved, 900/900 legal results, protocol PASS. Originals/settings/binary bindings: `../int16/summaries/wac-buffer/{frozen.json,summary.json,paired-summary.json}`. The middle result is below both references: retain an **unresolved possible regression**, with shared-host variability an alternative rather than an established cause. The result is not Elo and should not be converted into a gain claim.

**Open:** calibrated paired NPS/native PC evidence; ON checker contract gap as reported. The passed source-package/patch audit did not perform a new binary rebuild. No reachable overflow is demonstrated. Source/IDEA_SOURCE provenance is original Forge support code following the user's finding; no external-engine implementation, network/trainer change or match result. This draft makes no full independent CR/CodeRabbit approval claim.

Repository-retained original compiler/link flags: `raw/compiler-flags/{release,assert-on,asan-on}/`. Supplemental strict profiles and exact first-d11/ON five-depth/perft records: `strict-release/RECEIPT.md`, `strict-release/PROVENANCE.json`; original profile metadata remains unchanged. Complete original WAC exchanges are in `../int16/wac-buffer-original.zip`.

# CR DRAFT — H256 `NnueInt16` research, 2026-10-24

**d11 precondition FIRST: PASS, all options OFF = 308972**, before other tests of each build. Release receipt: `raw/release-off-qa/precondition-d11/RESULT.json`; ASan/UBSan receipt: `raw/asan-off-qa/precondition-d11/RESULT.json`.

**STATUS: ISOLATED RESEARCH — numerical PASS, Linux NPS NOISE; not an accepted candidate for performance or playing strength.** This is an evidence draft, not full CR approval, a speed-gain claim, gate/lock recommendation or Elo result. Remaining runtime/platform/profile limits are listed below.

## Identity, route and build

- Frozen delivered source: `074102419c90c6b3725cd83c172e1ec22a2d8203`. Initial implementation was isolated WIP `e7ae15f075c12c55b1e02e4426b5046ea5669977`; the tested engine/core hashes below remain unchanged. Lock: H256 e12 `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`.

- Same binary, runtime OFF/ON. Release SHA256: `61f3753f8f66ec5b9ee2d43d0f3156b3bc1fedf32fc7da46582354a04c49e509`; ASan/UBSan: `5fb88d17f54a67534e2671d2b354e05c648e91ac965afec75a85a5289f5b994a`. Linked Release core: `118fd17d5a84c29b71677eb3cabf6c8dd62a6477962020fc4686febd2bc9c430`.
- Network unchanged: `src/nnue_weights.inc` SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. No net/trainer change or matches.
- Linux, g++ 14.2, shared Intel Xeon 8573C; **not** native Ryzen/Windows evidence. Actual Release core flags: `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5`; link uses `-static`. CMake `Threads::Threads` resolves to empty flags on this merged-glibc platform: **no literal `-pthread` appears in the emitted engine compile/link commands**, the original configuration difference from the requested direct command. Windows direct commands retain `-pthread`. The original profile and its metadata remain unchanged; the separate strict reproduction below closes the delivered-artifact flag difference. Exact configure/build argv: `build-commands.json`; compiler/link receipts: `raw/build-flags/{release-flags.make,release-link.txt}`. ASan/UBSan uses `-O1 -g1 -DNDEBUG`, address/undefined sanitizers and halt-on-error settings; exact argv/env retained with those steps.
- **Strict `-pthread` reproduction PASS:** separate `build-int16-strict-pthread` emits literal `-pthread` in core flags and `-static -pthread` in link.txt. Its forge and libforge_core.a compare raw-byte equal (Python raw-byte equality and matching SHA256) to the original SHA61f375…e509/core118fd…c430. First d11=308972, then all remaining OFF depths and both perft5 values passed. Evidence: `strict-pthread/BYTE_IDENTITY.json`, `strict-pthread/commands.json`, `strict-pthread/qa/{precondition-d11,full-signatures-perft}/RESULT.json`. This adds reproducibility evidence without relabeling the original NPS build or rerunning timing.
- Runtime implementation binding: `SOURCE_FREEZE.json` covers `nnue.hpp`, `nnue.cpp`, `nnue_int16.inc`, `uci.cpp`, and the parity tool. Delivered ZIP `releases/sol-next-20261024/forge-int16-research-source.zip`: **1,310,139 bytes**, SHA256 `f7a145738b36cf4ebb7ec460cf93e480453535084db572b14ffdd0385302d103`. Cumulative `int16_fix.patch` against exact f4911f2: **236353 bytes**, SHA256 `0a9be1a59c500619b52f458015ebaedcbdf00235fba6bb5e21d9272ed2553f73`.
- **Independent delivery audit PASS:** real GNU patch dry-run and application, `--fuzz=0 -p1`, both exits 0/no offsets/fuzz/rejections. All **105 source files** compare patched tree = ZIP = frozen Git blobs, with corresponding Git executable modes; ZIP Unix modes match exactly. ZIP has 106 members including generated `SOURCE_MANIFEST.json`. All 95 tracked build/source inputs and four legacy `.inc` files plus new integer include are present; only three generated tracked `__pycache__/*.pyc` caches are excluded. Network stays locked. Exact commands/stdout/exits, comparisons and preserved consumer-check failures: `delivery-independent/{RECEIPT.md,RESULT.json}`. No archive-based rebuild or engine rerun was performed by this audit; the strict reproduction above is separate.

## Behaviour and source review

Exact new UCI line: `option name NnueInt16 type check default false`. Existing controls are `UseNNUE`, `Hash`, `Threads`, `OwnBook`; searches below use UseNNUE=true, Hash=16, Threads=1, OwnBook=false unless stated. Activation prints `info string NnueInt16 active`. Unsupported representation stays on float and prints `info string NnueInt16 unavailable; using float`; invalid values are rejected. `setoption` first stops/joins search, then changes mode and clears TT. Unsupported-net fallback is verified by source read; an actual nonrepresentable-net exercise is **PENDING**.

Original implementation derives scales from Forge's supplied weights and H128 implementation; see `IDEA_SOURCE.md`. No external-engine code/constants/tables were copied. Weights are int16, accumulators int32. Clipping is [0,4096], rounded square scale 8192. H256 positive/negative output bounds, +2,510,422,016 / −2,198,339,584, exceed int32. Each 16-hidden group is sign-extended before cross-group accumulation and final int64 reduction; the output scale is retained. Eligibility rejects unsupported scales/grid bounds/widths without aborting.

Memory tradeoff: separate integer storage adds **2048 bytes per H256 accumulator**, including OFF, or 278,528 bytes across 136 search-stack entries per worker (~272 KiB). Float weights remain available alongside the integer table. Unchanged OFF nodes do not establish unchanged cache behaviour or performance.

## Recorded gates

Bench is T1/H16/OwnBook=false. Each ON row changes only `NnueInt16`; legacy optional build flags remain at their defaults.

| Mode | d11 | d13 | d16 | d20 | d22 |
|---|---:|---:|---:|---:|---:|
| OFF | 308972 | 745494 | 2460422 | 11901452 | 31111774 |
| NnueInt16 ON | 335382 | 850773 | 3130100 | 10757244 | 27884195 |

OFF startpos perft5 **4865609**, kiwipete perft5 **193690690**: PASS. Evidence: `raw/release-off-qa/full-signatures-perft/RESULT.json`; ON: `ON-bench13-16/RESULT.json` and `ON-bench11-20-22/RESULT.json` (activation acknowledged, exit0, empty stderr). ON changes the search tree; node differences are not a strength or speed result.

Synthetic overflow-bound unit: **PASS**, exact int64 totals +2,510,422,016 / −2,198,339,584 exceed signed32, with integer/oracle/float outputs +13305 / −11642cp. Source and core bound to the same tested engine; exit0, empty stderr (`output-boundary/RESULT.json`). These are output-layer unit inputs, not FENs or additional parity positions.

Release and ASan/UBSan full CTest: **14/15 suites passed; one failing suite, `forge_tests`, containing these exact four FAIL lines in each build**:

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 661 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

Logs: `raw/build-test-steps/release-ctest/stdout`, `raw/build-test-steps/asan-ctest/stdout`. These are not four failed CTest suites or an all-green suite. ASan/UBSan ON bench13 = **850773**, activation acknowledged, exit0 and empty stderr. Six ON d10 searches over three positions at T1/T2 completed with legal bestmoves and no sanitizer report (`ASAN-ON-bench13/RESULT.json`, `ASAN-ON-smoke/RESULT.json`).

**100,000-FEN parity PASS:** mean |cp diff| **0.0147**, max **1**, p99 **1**; fixed limits mean≤2/max≤30 met. 1470 differ; raw-net/full-static strict sign flips 0/0, zero-vs-nonzero 13/3. Fresh/incremental lanes, independent int64 output oracle, tags, unchanged parents and in-place checks: zero mismatches. Actual special-move/null coverage passed. Seed20261024; corpus SHA256 `e8a35483ced1a41e607fc5c277cdd800449eea1d55833de38ab10c216af7b842`; originals and bindings: `parity/RESULT.json`.

**Bestmove sensitivity:** 6 changes in **32/32 cold depth13 OFF/ON pairs**. Fresh Searcher(16,1), explicit mode checks and TT/history/cache clear each side; exact corpus indices 0,3125,…,96875, no eligibility skips. Every bestmove/PV passed actual Board legality checks; all searches reached d13; exits0, empty stderr. Exact FENs/results: `d13-bestmove/quant-bestmove-selected.tsv`, `d13-bestmove/quant-bestmove-results.jsonl`, `d13-bestmove/quant-bestmove-summary.json`. This is a stated subset, not 100,000 depth13 searches or strength evidence.

**Numeric null counters PASS:** cold T1/H16 d8, startpos tries/cutoffs **7/5** in both OFF and ON; pawn-only **0/0** on `8/8/8/3k4/8/4K3/4P3/8 w - - 0 1`. All four searches completed d8 with legal bestmove/PV; compile/run exits 0, empty stderr, bound headers/core unchanged (`null-counters/BEFORE.json`, `null-counters/RESULT.json`). Opening book is unused by the direct API.

**Emitted arithmetic:** `SIMD/v2.stdout` PASS for retained float output path. Read-only integer review confirms `vpmulhrsw`/`vpmaddwd`, signed `vpmovsxdq` before loop-carried `vpaddq`, and 64-bit final reduction. **0 FMA across all 18 anchored NNUE symbols**; the whole static binary has 46 attributed libm log FMAs. Evidence: `integer-SIMD-review.md and integer-SIMD-review.json`, `SIMD/fma/summary.json`. Public evaluate is a runtime dispatcher; old checker assumptions about instructions inside that symbol do not directly qualify this design. Combined AVX-512/int16 qualification is **PENDING**. No CodeRabbit CLI run or full CodeRabbit approval is claimed.

## Tactical trial, performance and open handoff fields

- First WAC300 1000ms OFF/ON/OFF trial: **FAILED / INCOMPLETE**, 492 retained result rows, watchdog failure at WAC.193; observer/engine gap ~13s. Cause remains **UNRESOLVED**. Preserve `summaries/wac-int16/FAILURE.json`, `FAILURE_DIAGNOSIS.json`, `INCOMPLETE_AUDIT.json`; no complete paired score and no pooling. Three isolated OFF/ON/OFF diagnostic cases returned near0.991s; they did not reproduce the fault and **do not rescue the failed trial**.
- Fresh full quiet trial2: **PASS, 900/900 legal results**, closed16:47:57UTC, CPU0, same frozen binary/settings and first-fault stopping rule. OFF_A1 **274/300**, B_ON **271/300**, OFF_A2 **278/300**; answer-match counts are tactical observations. Evidence: `WAC_FRESH_QUIET_2_PREDECLARED.json`, `summaries/wac-int16-fresh-quiet-2/summary.json` and `paired-summary.json`. This separate complete trial does not repair, replace or pool the original failed trial; its root cause remains unresolved.
- Predeclare timestamp correction: its frozen quiet-condition text says heavy work closed before 16:07:32, but the diagnostic actually closed 16:23:55, still before fresh launch 16:34. Preserve the original predeclare unchanged; the correction receipt is retained in `CLARIFICATIONS.json`. This corrects provenance wording without attributing the earlier fault to host or engine.
- **Paired NPS Linux dry run: COMPLETE / NOISE.** Same frozen original engine61f375…e509, six A/A palindrome blocks and fourteen ABBA blocks, 80 processes. Faster **8/14**, slower6/14; median **+0.4396913%**, mean **−1.2059303%**, A/A band **21.4671442%**. The protocol completed, but gain criteria were not met. Closed17:09:18UTC; `NPS-Linux-dry-run/RESULT.json` retains every per-pair percentage. No Windows/Ryzen speed or Elo result; native PC qualification and whole-engine phase split remain unmeasured.
- **OPEN:** runtime unsupported-representation exercise; native Windows/Ryzen qualification; whole-engine phase profiling; combined AVX-512 stage3 + int16 qualification; full independent CR approval and performance/playing-strength acceptance. No gate, lock, match or Elo recommendation.

## Additional retained lifecycle and publication evidence

ASan/UBSan T2 mid-search ON/OFF transitions PASS: observed infinite searches, stopped/joined before readiness, ON active acknowledgement, legal subsequent finite d6 searches; actual engine/runner exits0, empty stderr, frozen ASan binary unchanged. Exact exchanges and controller source: `ASAN-midsearch-mode/`, `tools/asan_mode_lifecycle.py`. `clear_hash()` clears TT and every worker evaluation cache after mode changes; search invalidates stack accumulators. No new source change was needed after these checks.

Complete WAC originals are in `wac-int16-original.zip`, `wac-int16-fresh-quiet-2-original.zip` and `diagnostic-wac193-original.zip`, with roundtrip-verified manifests. Numerical originals include `parity/corpus.fen.gz`. `NPS-root-audit.json` independently rechecks all87 process records,80 timed samples and20 pairs; no repeat or pooling.

Actual UCI advertisement from the first Release gate:

```text
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name Move Overhead type spin default 10 min 0 max 1000
option name Ponder type check default false
option name OwnBook type check default true
option name Book File type string default <empty>
option name Book Depth type spin default 30 min 0 max 100
option name Book Variety type spin default 30 min 0 max 100
option name UseNNUE type check default true
option name NnueInt16 type check default false
option name Clear Hash type button
```

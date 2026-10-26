# fc_nnue_h256_e12_ep12_ep10base — H256 net (run e, epoch 12) on the locked ep10 source base

Status: **UNPROVEN. No Elo or strength claim.** Built on the box by Engine Coder, 2026-10-23.

## What changed
Only `src/nnue_weights.inc` (verified with `diff -rq` against the locked ep10 tree `/workspace/forge-coder/fc_nnue_ep10_1ab50b2d`, excluding build_release/artifacts; artifacts/diff_rq.txt). Everything else (src, include, tests, bench, tools, CMakeLists.txt) is the ep10 tree's source. IDEA_SOURCE.md is rewritten for this candidate.
- Net: /workspace/chess-tools/nnue/forge_resid/resid_h256_e12_e_ep12.inc, md5 **6d22f612c855e17c62d396d32da99ea4**, sha256 74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b (HiddenSize 256, FORGE_NNUE_RESIDUAL 1, from Engine NNUE).
- Replaces ep10 net md5 da65098ce0612b7f18706547b0a57c84 (H128). The ep10 tree itself was not touched (its nnue_weights.inc md5 re-checked unchanged).
- Net holdout-loss claims are Engine NNUE's (teacher 0.004679, b0.6 0.014534 vs ep10 0.004701 / 0.014740); not verified here, not strength evidence.

## Exact build
    cd /workspace/forge-coder/fc_nnue_h256_e12_ep12_ep10base
    nice -n 19 cmake -S . -B build_release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 \
      "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
    nice -n 19 cmake --build build_release -j1
g++-14, Release, -j1, niced. Build clean (6 pre-existing -Wconversion warnings in search.cpp, same as ep10 tree). Binary: build_release/forge, **sha256 e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b**.
`tools/check_nnue_simd.py` on nnue.cpp.o: PASS (256-bit clamp/multiply/add, no FMA).

**Windows / drop-in note:** any Windows build MUST pass `-DFORGE_NNUE_HIDDEN=256` in the compiler flags (macro default is 128; there is no CMake option). Without it the static_asserts in the .inc fail the compile (shape mismatch), so a wrong build cannot silently succeed. Otherwise use the same toolchain/flags as the ep10 Windows build (see /workspace/forge-coder/WINDOWS_BUILD_nnue_candidates.md); only the net file and this flag differ.

## Tests
- perft 5 startpos = 4865609 (correct).
- ctest: 13/14 pass; forge_tests fails with exactly the 4 known ep10 lines (same failure type; the WAC 001 score text is 661 here vs 662 on ep10 — still "below 31997"):
  - FAIL: WAC 001 expected g3g6 got f6h5
  - FAIL: WAC 001 score 661 below 31997
  - FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion (x2, incl. mirror)
  No other failure, no blocker. Tests not edited. (artifacts/ctest.log)
- UCI smoke (artifacts/uci_smoke.log): uciok, 4 depth-8 positions legal, 40-ply self-play at depth 5, 0 illegal moves, clean quit after bestmove.

## Bench (Threads=1, Hash=16, nice 19, pinned core 5; artifacts/bench.log)
| depth | nodes (H256 e12 ep12) | ep10 locked nodes (for reference) |
|---|---|---|
| 11 | 308972 | 315955 |
| 13 | 745494 | 851522 |
| 20 | 11901452 | 12374513 |
| 22 | 31111774 | 22765028 |
Node counts differ from ep10 because the eval differs (expected for a different net).

## NPS timing vs locked ep10 binary (box only; never pool with PC numbers)
ep10 binary: /workspace/forge-coder/fc_nnue_ep10_1ab50b2d/build_release/forge, sha256 f94f6778ab8422e98af27ce1265af8c34caff7422bdf81d804d703fb6cfac639. Bench depth 20, Threads=1 Hash=16, alternating pairs (order flips), nice 19, taskset core 5, one process at a time, run only when integer 1-min load <= 5 (other crew matches were running on the box, load 5.4-6.1 during runs).
| run | pairs | ep10 mean NPS | H256 mean NPS | ratio H256/ep10 mean / median / min–max / sd |
|---|---|---|---|---|
| run2 (clean, headline) | 8 | 1936308 | 1626482 | 0.840 / 0.840 / 0.807–0.860 / 0.018 |
| run1 (load-contended, pair 7 outlier 0.696) | 8 | 1827410 | 1515337 | 0.831 / 0.844 / 0.696–0.904 / 0.063 |
H256 is about 16% lower NPS than ep10 (ratio ~0.84, both runs agree; run1 kept for transparency, not discarded). Note bench20 node counts differ, so NPS ratio is not time-to-depth or strength. Files: artifacts/timing_bench20_pairs_run1_loaded.csv, timing_bench20_pairs_run2.csv, timing_summary.txt, pair_bench.sh, summarize_timing.py.

## Gate note (for QA)
Opponent for any gate = the **locked ep10 tree** (/workspace/forge-coder/fc_nnue_ep10_1ab50b2d, net md5 da65098c…, bench d11 315955, d13 851522, d20 12374513, d22 22765028), NOT forge-strength/base-ep10 (that is the runb net). Candidate must identify as bench d11 308972 / d13 745494 / d20 11901452 / d22 31111774 (Threads=1 Hash=16) before gating; if the PC build differs, the -DFORGE_NNUE_HIDDEN=256 flag was probably missed. Candidate side: no setoption needed (net-only change; no UCI options added). Because NPS is ~16% lower, gate on games only (QA's 1000-game gain-route, no pooling); do not infer anything from loss numbers or NPS.

## Artifacts
artifacts/: diff_rq.txt, changed_files.txt/.sha256, build.log, ctest.log, bench.log, check_nnue_simd.log, uci_smoke.log (+ uci_smoke_proper.py), binary_sha256.txt, timing csv/summary/scripts.

## Lock-adoption checklist: re-record Job C pins (20261025)

1. Record the new engine and network SHA256, source revision and build flags.
2. From the tree root, run `bash tools/rerecord_pins.sh build_release/forge --out NEW_FOLDER`
   (`tools/rerecord_pins.py` must sit next to the .sh). By default it checks the documented
   lock pins and exits 1 with `PIN_OBSERVATION_MISMATCH` if any differ; add `--observe-only`
   for a new net, which prints `PIN_OBSERVATION_RECORDED (n of 3 match documented pins)`.
   It prints WAC001 at Hash8/depth12 and both promotion mirrors at Hash1/depth1,
   using Threads1 and OwnBook=false. It records observations and edits no pins.
3. Compare WAC move/score/depth/PV with the exact `f6h5/661/d12` pin, and compare
   promotion king moves/PV/depth with `c6d7` and `c3d2` at depth1 (score>100).
4. A mismatch remains a failure. Review the new outcomes, retain the original
   mate and rook expectations, and re-record pins in tests/tests.cpp plus the
   maintained known-failure record FORGE_KNOWN_TEST_FAILURES.md (lock pack
   files/08_status/) only through a separate reviewed change.
   Never replace exact661 with a score floor. Re-run mutation controls.

## h256_e12+buffix (appended 2026-10-25, QA)
This tree is the h256_e12 lock plus Sol's bad-capture buffer fix: MovePicker `bad_captures_` grows from 64 to `MoveList::Capacity` entries with a `static_assert`, and a new test `tests/bad_capture_tests.cpp` (CMake target `forge_bad_capture_tests`, test build only, not part of the engine exe). Bench is identical to the lock (d11/13/16/20/22 = 308972/745494/2460422/11901452/31111774). Apply with `patch -p1 < fc_sol_buffix_h256e12_vs_lock.patch` (sha256 9ce56b3d…) on the lock source. No Elo or speed claim; adoption as base is decided by QA's PC d13/d16 nps ABBA (forge-hashes/QA_PC_ABBA_buffix_h256e12_20261025.md).


## S08 opt-in profiling (ADVICE; compile default OFF)

Configure with `-DFORGE_PROF=ON` only for the profiling executable. It adds one
UCI check option `Profile`, default false. `setoption name Profile value true`
profiles ordinary `go` searches; `bench_prof 20` explicitly profiles the same
eight FENs and fixed-depth search/clear sequence as `bench 20`. Plain `bench`
continues to use its normal unprofiled local Searcher. All profile lines precede
the unchanged final bench summary or bestmove. Compile OFF removes the added
fields, includes, calls, implementation source, option and command branch.

Counts cover Worker::search entry through return only; FEN loading, board setup
and other work outside that window are excluded. NNUE refresh/forward and HCE
counts are actual function entries inside that window, not timing estimates.
Zero refreshes do not show that refresh code is dead. Picker counts are executed
stage cases (including fallthrough), not elapsed time. Pruning checks are actual
condition evaluations; searches/prunes/reductions count their taken branches.
An event's denominator is printed explicitly. Multiple moves can be tested per
node, so opportunities per node may exceed100%; no opportunities means unknown.

Each Searcher owns its bank. Worker-local TLS scopes restore previous contexts
on exit, including disabled and nested independent searches. Requested enabling
is atomic and snapshotted once before worker launch. Workers only add relaxed
atomic uint64 values. Reset occurs before launch and external snapshot/reset
operations require the Searcher quiescent, as clear/resize already do. No added
heap allocation occurs in make/unmake or per-event hooks. uint64 arithmetic wraps
modulo2^64; a sticky overflow flag also covers aggregation. Any wrapped run must
be discarded for frequency analysis. No arbitrary infinite-search bound is claimed.

Use fixed depth or node limits and fresh ucinewgame/hash/history per corpus
position. Counter overhead makes wall-time comparisons unsuitable for strength
or speed conclusions. The requested2,000 distinct WAC/STS positions are not all
provided: the real WAC300 suite supplies300 unique boards;1,700 remain missing,
and no genuine STS corpus was found. Do not pad with duplicate WAC, opening-book
or training positions. Any300-position result must be labelled a limited screen.

Source-level OFF-token/placement checks and behavioral C++ fixtures accompany
the patch. Native OFF executable identity, ON five-depth reference nodes, full
required tests, sanitizer checks and measured frequencies remain unverified until
run under the frozen validation protocol. Instrumentation is not a playing-strength
change and authorizes no gate/promotion rule change.

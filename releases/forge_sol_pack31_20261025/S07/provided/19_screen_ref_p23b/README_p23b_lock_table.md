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


---

# p23b_refutlmr_h256 — P23 RefutLmr, narrowed trigger: killers only when r >= 5 (OFF by default)

Base: h256_e12 lock (net md5 6d22f612, exe e3df99cd). Also applies to h256_e12+buffix (see below).
Status: UNPROVEN — no Elo claim. Rework of p23_refutlmr_h256_v2 (patch ef929ef9), which failed the crew
deep-node screen (RefutLmr=1, MinR 4: d22 38241769 = +22.9%; WAC300 1 s 283/281/283 OFF/ON/OFF).

## What changed vs v2
Only the default of `RefutLmrMinR` (4 -> 5) and its comment; code paths are identical (interdiff shipped).
Tunables (all inert while RefutLmr = 0):
- `RefutLmr` 0..4 (default 0 = off): 1 = both killers; 2 = killers + counter move; 3 = as 2 but only at
  non-cut nodes; 4 = first killer only.
- `RefutLmrPlies` 1..2 (default 1): plies taken off the LMR reduction r.
- `RefutLmrMinR` 0..8 (default 5): only applied when r (after all other LMR adjustments) is >= this.

## Deep-node screen (existing tunables, Plies=1; lock 308972/745494/2460422/11901452/31111774)
| variant | d11 | d13 | d16 | d20 | d22 | d22 vs lock |
|---|---|---|---|---|---|---|
| m1 r4 (v2) | 291046 | 717175 | 2438867 | 11617492 | 38241769 | +22.9% FAIL |
| **m1 r5 (p23b)** | 311855 | 745052 | 2594099 | 10785772 | 22307140 | **-28.3%** (d16 +5.4%) |
| m1 r6 | 308972 | 745496 | 2481357 | 9733344 | 26744723 | -14.0% |
| m1 r7 | 308972 | 745494 | 2460422 | 11492871 | 26108437 | -16.1% |
| m3 r4 | 308972 | 742485 | 2904577 | 12329780 | 30666489 | -1.4% (d16 +18.1% FAIL) |
| m3 r5 | 308972 | 745494 | 2466996 | 13399246 | 30794672 | -1.0% |
| m3 r6 | 308972 | 745494 | 2460422 | 11904471 | 33068574 | +6.3% |
| m3 r7 | 308972 | 745494 | 2460422 | 11904445 | 32027921 | +2.9% |
| m4 r4 | 288554 | 820740 | 2728035 | 12269234 | 30035394 | -3.5% (d13 +10.1% FAIL) |
| m4 r5 | 308972 | 745506 | 2366147 | 10516257 | 29359505 | -5.6% |
| m4 r6 | 308972 | 745494 | 2460426 | 10250343 | 24154132 | -22.4% |
| m4 r7 | 308972 | 745494 | 2460422 | 11904442 | 30619329 | -1.6% |

## Paired WAC300 (x_wacnew.epd, core 4, nice 19, one exe 199f6235, OFF first and last; tactics only, not Elo)
| run | 1000 ms | 100 ms |
|---|---|---|
| OFF_a | 283 | 255 |
| **m1 r5** | **284** | 254 |
| m1 r6 | 282 | 255 |
| m4 r6 | 287 | 255 |
| m3 r5 | 283 | 255 |
| OFF_b | 283 | 256 |
Single session; the +4 at 1 s is one sample, not a strength claim.

## Gate
Primary: `setoption name RefutLmr value 1` (defaults RefutLmrMinR=5, RefutLmrPlies=1; sending them explicitly
is harmless). Crew choice (DR/CR): MinR 5 clears the deep screen (d22 -28.3%, d16 +5.4%; CR's independent
bench matches these numbers) and 1 s WAC300 ON 284 >= OFF 283/283. 100 ms was 254 vs 255/256 (within noise).
Option-live proof: ON bench 11 = 311855 vs OFF 308972 (the exe accepts unknown option names silently, so
a d11 equal to OFF would mean the option was not applied).
PC precondition: bench 11 with RefutLmr=1 must print exactly 311855 nodes (OFF 308972).
Node trend: d20 -9.4%, d22 -28.3% (shrinks with depth), so any H1 should be confirmed at a longer TC.
Tuning steps only if the primary reaches H1 (or fallbacks after H0, in this order): RefutLmr=4 with
RefutLmrMinR=6 (first killer only; WAC300 1 s 287, but inert at d11/d13, live from d16 = 2460426),
then RefutLmr=1 with RefutLmrMinR=6.

## Files
src/search.cpp (tunables, table entries, MovePicker::refutation_kind, LMR adjustment),
include/forge/search.hpp (externs). No new test (option-live bench + OFF bit-identity).

## Base compatibility
Applies with `patch -p1` to a fresh h256_e12 lock copy and to a fresh h256_e12+buffix copy
(lock + buffer_only.patch sha256 32967232…); see the handoff for the buffix-base bench.

# Forge 6.4 — UCI clock-origin correctness repair integrated on work branch
20 October 2026 UTC. Applies ONLY to work branch `forge/6.4-hourly-20261019`, not the immutable baseline release or main. Parent `06c581895708a6eb9ff26b380d818f72f7bd9ebf`.

## Source-level problem
Before this fix, `src/uci.cpp` accepted `go` then spent time joining a previous worker, parsing UCI limits and creating a new thread, while the match clock advanced. The engine instead started its search clock on entering `Worker::search`. Any thread-admission delay therefore extended effective wall-clock thinking by the entire delay. This could contribute to time forfeits. It has not been proven to be the sole root cause of the previous specific Candidate timeout.

## Change
A `SearchLimits.start_time` optional steady clock point receives the UCI `go` receipt timestamp for finite time or movetime searches, excluding infinite and ponder; direct `Searcher` calls and node/depth analysis remain unchanged. `Worker::search` uses this origin when supplied. Existing pondering rebase behavior remains unchanged. Search pruning, NNUE, TT tag repair, move rules and the version are unchanged. Source changed: `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`.

## Actual native verification *before* integration (disposable CMake builds)
GitHub Actions `39382802396` **SUCCESS** on Ubuntu 24.04, GCC 13.3.0, 20 October 2026 06:51 UTC. Source experiment: `06c581895708a6eb9ff26b380d818f72f7bd9ebf`. Baseline Release CTest 4/4 PASS; patched candidate Release CTest 4/4 PASS, including UCI and ponder regression. Verified SHA-256 of native binaries:
- baseline unpatched: `2f16d32dcb9242c35ca38e32d83d4354566587f868b547d620b2709a65515b6e`.
- patched candidate: `7d760af0bb0d3f2baaf0205301b866851fde9e760f01b94599bba0d2ed94d04e`.
- LD_PRELOAD shim: `0ac7caa62cbc6e28aed3f6b077795a08e611acef4cb1a7269097856a77e43a2c`.

An artificial 440 ms `pthread_create` admission delay produced real-engine UCI results:
| Trial | First info reported time | End-to-end bestmove wall time | Move |
|---|---:|---:|---|
| pre-fix `go movetime 1200` | 0ms | 1630.492ms | d2d4 |
| scoped fix `go movetime 1200` | 440ms | 1190.489ms | e2e4 |
| scoped fix `go depth 1` | 0ms | 440.890ms | e2e3 |

These are actual compiled Forge engines under controlled *artificial* worker admission, not fastchess games. Candidate returns within the requested movetime inclusive of the admission delay; baseline consumes ~440 ms beyond it. The changed move is expected from different allotted search time; it does not establish a chess strength difference.

Native probe had 3/3 normal UCI exits, valid bestmove records, raw JSONL journals and matching SHA hashes. Artifact ZIP `12245898445` 26 original entries, SHA-256 `00e625ae021f34abe93731e371c3bbf54edc844d8eab28caec22000eba3c301a`, URL https://github.com/couns0538-sketch/dwqww/actions/runs/39382802396/artifacts/12245898445.

The earlier CI `39382382647` failed only because its probe hit the embedded opening book; both its CMake builds and 4/4+4/4 CTests passed. Its original failed record retained: https://github.com/couns0538-sketch/dwqww/actions/runs/39382382647/artifacts/12245034489.

## Next validation
This integration commit's CI reruns both complete source trees (real work-branch candidate vs patch-reversed disposable pre-fix copy) with the same admission-delay test and CTest. No Windows/Ryzen runtime is claimed. This fix does not address arbitrary OS scheduling pauses *during* active search, an absolute deadline for the runner, a blocked output stream, or actual root-cause proof for the original timeout.

The TT verification-tag candidate remains `correctness_verified_strength_blocked`; first match stopped after **6 games / 3 pairs / 1 Candidate timeout** and has no H0/H1 boundary. Do not resume/pool that failed experiment. TT playing-strength gain = **unproven**, no new games this cycle. Any replacement SPRT must be separately preregistered at equal time and frozen hashes, and positive improvement requires real native H1. This cycle's code is a *timing correctness* repair, not proof of +Elo.

The original metadata-bearing raw match archive remains blocked from public publication; none of its bytes were uploaded via this validation workflow.

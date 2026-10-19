# Coherent shared transposition-table candidate

The accepted development reference is `9108d012526be80c6d163f7cab684e6acd9abf8d`.
This experiment preserves the later isolated underpromotion candidate source
`f6f0a00b2f98a7a9f117790e2c8f19a340b6769f`; its published parent checkpoint is
`842c02ef432f730d7083e3c22d36a5f3cc5d5184`. Neither has an accepted Elo gain.

## Hypothesis and observed failure

Unsynchronized plain TT fields allow C++ data races and inconsistent entry
payloads during SMP search. Entry snapshots copied under striped mutexes can
remove this correctness defect. Synchronization may cost speed, so correctness,
single-thread tree identity, overhead and strength must be reported separately.

The actual four-thread UCI engine, not just a table model, reproduced a TSan
write/read race in `TranspositionTable::store`/`probe`. The unmodified baseline
was exported and built with GCC14.2, Debug plus `-O1 -g -fsanitize=thread
-fno-omit-frame-pointer -fno-pie -fno-fast-math -ffp-contract=off`, linked with
`-fsanitize=thread -no-pie`. With Threads4, Hash1, OwnBook=false and
`go nodes 200000`, TSan halted with exit66 before bestmove. Original stderr and
exact commands must remain in the evidence directory. This is a correctness
failure; it is not a match result.

## Minimal implementation

- Copy a full entry under the cluster's one-of-1024 striped locks. No shared
  entry pointer may escape to search callers.
- Keep an opaque owner/key/epoch/cluster/slot handle. Store under the same lock
  into the exact probe-selected slot, preserving old single-thread replacement
  behavior when recursive searches overwrite the slot in between.
- Preserve existing score/depth/generation/move admission rules. Lock hashfull.
- Reject default, foreign, wrong-key and lifecycle-stale handles. Clear,
  resize, new_search and destruction still require all workers/readers joined.
  Allocate replacement storage before publishing a resized table.
- Port existing tests and add coherent tuple, delayed store, replacement,
  snapshot immutability, invalid handle and concurrent reader/writer regressions.

## Gates and decision

Run normal CTest/perft/UCI/pondering first; run the real table stress and actual
multithreaded engine under TSan, including stop/join/clear/resize/thread-change
cycles. Compare matching-platform single-thread cold/warm search outputs and
bench signatures with the exact source parent. Investigate any divergence.
Use ASan/UBSan for storage/lifecycle checks where the runtime supports it.

After correctness passes, freeze Release binaries and counterbalance repeated
1/2/4-thread runs on the same allocated CPUs. Save raw process wall/CPU timing,
nodes and settings; do not call a loaded VM result a Ryzen result. Do not start
more timed Wine/VM strength pilots: earlier attempts failed on scheduling and
clock limits. Equal-clock SPRT on stable native hardware remains required for
promotion. Fixed-node matches can assess a separately labelled search-quality
question, but cannot prove equal-clock gain. Preserve slow or inconclusive
results, and retain the accepted branch unchanged until sufficient validation.

# GrokChess 1.7.50 — stale Lazy-SMP completion contamination (2026-10-20 08:15 CEST)

This is an **isolated compiled-JavaScript research candidate**, not a released TypeScript change. Source: 2026-10-20 07:10 validated checkpoint, `grokchess/src-genclear/dist-v1.7.50`. The authoritative TypeScript source is not present; source maps contain no `sourcesContent`.

## New reproduction
`searchLazySmp` resolves after thread 0 finishes and a bounded helper grace period. The persistent helper can still be running when the next UCI `go` begins. Its previous `done` message is seen by **both** the original search's listener and the next search's listener, because listeners match only `threadId`, not the originating search. A previous legal helper move can then override the current main worker's move.

Deterministic fake-worker harness (same actual `search/smp.js` module, worker scheduling simulated): original generation-retirement candidate produced `r1=e2e4, r2=d2d4`, erroneously accepting the prior search helper's `d2d4`; assertion failed. This is a controlled scheduling reproduction, not evidence of a naturally occurring incorrect move.

## Minimal repair and evidence
Add a monotonic `jobId` to every search job, echo it in worker `info` and both `done` branches, ignore messages whose `jobId` differs in the search's listener. This prevents stale result acceptance while retaining time-bounded helper grace.

With the same deterministic schedule, patched candidate produced `r1=e2e4, r2=e2e4` and the regression passed. Node.js v22.16.0 (Linux) movegen 36/36, perft 25/25; depth 9 219,323 nodes, depth 10 286,029 nodes; Threads=2 3/3 depth-8 UCI positions passed. No speed/Elo improvement claimed.

## Limitations
Old helpers may still occupy a persistent worker and delay the next queued job; job IDs fix **message contamination**, not helper lifecycle, time forfeits, or UCI mutation races. This candidate also includes the preceding unmerged TT coherence, nonblocking write and bundle-generation retirement fixes. It must be implemented in the matching TypeScript source and tested on Windows before merging. Do not merge the broad `forge/ci-evidence-gzip` PR as a substitute.

Complete tested distribution, baseline, harness, logs, patch and SHA256 manifest are in conversation artifact `forge-grokchess-hourly-20261020-0815-jobid.zip` (not yet mirrored into this branch).

Coordination: inspected Forge head `ec013151` (Sol's UCI go-clock-origin standalone model/review patch; not an engine change), plus tester `a9f14bab`. Avoided altering any Sol branch. Hosted NNUE Forge 6.4.11 vs 6.4.9 previously ended 427W/1194D/427L, no SPRT acceptance.
# IDEA_SOURCE — S13 TtChildPrefetch (TT prefetch at every key change; 64-byte TT bucket)

IDEA_SOURCE: Sol's S13 preparation on branch `forge/sol-pack31-20261025` (head 17aa0cae),
`validation/forge_sol_pack31_20261025/forge_sol_S13_source_prepared_20261026/forge_sol_S13_ttprefetch_20261026.patch`
(sha256 cc3efc9659a00e2b2da8c4853f7c1c2f601e95e16e1805bc2cbf8cc4b91a249a). Its four production files are ported
verbatim (commit 8557326e; `git apply` and GNU `patch -F0` both reproduce them byte for byte on the lock tree).
The job text (crew S13 handoff): prefetch the TT bucket at every key change (make, null move, qsearch) and
static_assert that a bucket is one 64-byte line.

Sol's idea notes (from the patch's IDEA_SOURCE.md/README.md hunks, kept here instead of the root files):
- Forge itself already prefetches the TT bucket after the qsearch and main-search make and already asserts
  `sizeof(TTCluster) == 64` (with `alignas(64)`); reading its null-move and ProbCut recursion identified the two
  remaining child entry paths, which this adds.
- Own C++ implementation; the requested-option / per-search worker snapshot pattern follows earlier Forge
  experiment plumbing. No code, tuned constants or parameter values from another engine.
- The isolated build switch `FORGE_S13_TT_CHILD_PREFETCH` and the UCI option `TtChildPrefetch` both default OFF.
  No TT layout, move order, evaluation value or network change.

Technique background: issuing a software prefetch for the transposition-table entry of the position just
reached, so the memory access overlaps the work before the probe, is a widely used, generic engine technique
(here only extended to the two make paths that lacked it). Probe test (tests/tt_prefetch_probe_tests.cpp)
written after Sol's `forge_sol_S13_worker_prefetch_probe_20261026.cpp` diagnostic design.

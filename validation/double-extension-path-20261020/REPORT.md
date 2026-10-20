# Actual double-extension path RED/GREEN investigation

The real frozen Forge 6.4.13 source `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`
reproduces stale search-path accounting. An isolated **unapplied** source repair
eliminates every observed mismatch with the same independent instrumentation.
No production file, Git branch or accepted engine was modified by this worker.

| Actual bench11 counter | Frozen baseline | Isolated proposal |
| --- | ---: | ---: |
| children | 292878 | 292878 |
| single_extensions | 6520 | 6520 |
| double_extensions | 184 | 184 |
| singular_attempts | 930 | 930 |
| same_ply_changed | 151 | 0 |
| single_parent_mismatch | 159 | 0 |
| actual_vs_true_path_mismatch | 5038 | 0 |
| null_parent_path_mismatch | 691 | 0 |
| probcut_parent_path_mismatch | 313 | 0 |
| incoming_parent_path_mismatch | 4138 | 0 |
| eligibility_mismatch | 0 | 0 |

Both uninstrumented baseline and both instrumented variants finish normally at
**419798 nodes**. The exact same 292878 selected children and 184 real double
extensions occur. Seven mismatch counters fall to zero. There is no observed
threshold-eligibility difference in this bounded workload, no demonstrated
budget above seven, and no performance, NPS or Elo gain. Timings in raw logs are
diagnostic only. No larger workload was needed or executed.

The shadow is independent of real SearchStack counters: it starts at zero,
propagates unchanged through null/ProbCut, adds one only for the actual selected
extension=2 edge, and stays at the same incoming count through same-ply
verification. PVS/LMR re-searches reuse the same child edge. Quiescence never
reenters main search. All eleven instrumentation insertion blocks are
mechanically identical in RED and GREEN; reconstructing the RED diagnostic
from frozen baseline is byte-exact. No diagnostic assignment changes search
conditions, SearchStack fields or returned scores.

The ordinary real-engine trace includes a legal checking single extension
`c3b2` at ply9/depth2, in
`r3k2r/p2p1pb1/BB3np1/q7/4P3/2p2Q1p/PPP2PPP/R3K2R b KQkq - 0 5`:
current outgoing counter1 versus parent/true incoming count0. Another branch
loses a true path count2 and propagates1. Null and ProbCut inherit stale
outgoing counts before the move-loop assignment. These FENs are internal path
witnesses; starting a new search from one FEN resets its history/budget. The
reproducible regression workload is the complete preserved bench11 input.

The proposal captures the inherited budget at main-search entry before null or
ProbCut recursion, resets the frame, uses that stable local for eligibility,
and assigns it plus `(extension == 2)` for every actual move. It restores the
baseline after both same-ply singular and high-depth null verification. The
latter restore prevents a failed null verification from leaving a double
extension count for the subsequent ProbCut branch. Thresholds, margins and
selectivity parameters remain unchanged. See `proposed-unapplied.patch`.

GREEN recompiles only changed search.cpp with exact frozen compile flags,
replaces search.cpp.o in a copied baseline core, and relinks the frozen UCI
object using original link flags. All six other archive members are verified
byte-identical. Source, baseline bytes, UCI object and resulting engine/core
hashes are frozen and unchanged. This is a diagnostic experiment, not a full
candidate Release/ASan/TSan or strength acceptance.

One unchanged assertion fails RED with exit1 and passes GREEN with exit0;
`RED-GREEN-ASSERTIONS.json` records both commands. Independent python-chess
checks passed1623 assertions across541 RED trace rows and288 assertions across
96 GREEN rows: valid FENs, legal actual moves and each reported mismatch's
arithmetic. An initial auditor assumed Move::none formats as0000; Forge's raw
diagnostic sentinel is a1a1. That failed auditor attempt is retained and the
checker now handles explicit no-move event types. Original traces are unchanged.
Compiler output retains existing halfmove int-to-uint16 conversion warnings;
both compiles succeeded. No sanitizer or warning option was suppressed.

Next: after the parent finishes clock validation, apply only the proposed
production change on a new isolated candidate; repeat the unchanged invariant
oracle with full source provenance, meaningful regression tests and all required
correctness/sanitizer checks. A deeper bounded workload should exercise the
high-depth null-verification path and the limit itself before claiming those
branches dynamically covered. Then run a fresh, preregistered paired equal-time
SPRT if justified. Keep this source and all failed approaches intact.

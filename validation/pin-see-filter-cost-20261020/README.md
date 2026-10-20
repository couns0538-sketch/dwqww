# Isolated exact SEE filter mask

The forbidden-origin mask preserves the frozen 6.4.15 reference behavior and
shows lower source-level king-filter lookup work on the bounded bench. This
is an isolated prototype result; measured speed and integration acceptance
remain unproven.

DESIGN.md is the original source-only proposal and proof snapshot.
mask.patch changes only the per-candidate king-safety filter. The reference is
source 8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad; the original Release core hash
is 27c8db2caf860c868dbece61a4de0b8121a5d696b846a96e4f7aa2439498ea97.
The core and complete original source export remained unchanged. Only
board.cpp.o differs in copied candidate archives. Production and Git were
not edited by this experiment.

Uninstrumented actual Board API output is byte-identical over the immutable
300-case prototype corpus, four supplemental cases, and 12 coverage controls:
316 rows and 6,320 fixed-threshold answers, including SEE values, legality, and
complete first recapture lists. Both inherited promotion limitations remain
-400 against oracle -1200. This is exact reference parity, not a claim of
universal minimax SEE correctness.

Diagnostics were added only after that semantic gate. Instrumented API
outputs still match the uninstrumented reference byte-for-byte. The candidate
shadow-compared 3,614 complete surviving attacker masks against the actual
reference helper, using 1,275 individual shadow queries, with zero mismatches.
All same-value candidate origins were included.

One serial depth-11 bench capture was run per instrumented build, with a
10-second operational guard each. The dedicated driver reuses UCI bench's
exact eight FENs, Searcher(16), one thread, per-position clearing, and exclusive
TT access, and prints actual per-position depth, nodes, score, best move, and
legal PV. Those stdout files are byte-identical, totaling 385,792 nodes.
Search and NNUE objects were reused unchanged; neither was recompiled.

| Filter work in the eight-position bench | Reference | Mask |
| --- | ---: | ---: |
| SEE calls | 462,049 | 462,049 |
| Visited exchange plies | 426,149 | 426,149 |
| Non-king candidate origins | 371,702 | 371,702 |
| Surviving non-king origins | 369,479 | 369,479 |
| Full per-origin king queries | 371,702 | 0 |
| Occupied bishop/rook queries | 742,109 | 0 |
| Empty-board bishop/rook lookups | 0 | 474,626 |
| Between-ray classifications | 0 | 49,015 |
| Each pawn/knight/king attack test | 371,702 | 237,313 |

These are diagnostic operation counts, with scope limited to the SEE filter.
Reference helper counters were active only around its primary candidate loop.
Candidate shadow queries were counted separately during API verification and
were disabled in both bench runs. Instrumentation itself changes execution
cost and was not used for a performance comparison.

The reduction in occupied-board attack queries and repeated non-slider tests
supports the proposed mechanism. Costs per operation differ, and some
single-candidate positions may require more between work. No wall-time, NPS,
Elo, match, or Ryzen/Windows speed claim follows. Recorded durations exist
only for operational guards and the 120-second engine-execution budget.
Total actual API/bench execution was 5.067148 seconds.

semantic-record.json and diagnostics-attempt1/record.json preserve every
command, exit status, timeout, stdout/stderr hash, source identity, core member
hash, and counter result. All execution phases succeeded. One artifact-writing
tool syntax error occurred before tool execution and is preserved separately
in artifact-write-attempt1.json; it ran no compiler or engine and wrote no files.
INDEPENDENT-AUDIT.md records a separate source/output audit. Full source TARs,
plain and diagnostic Board sources, objects, copied cores, diagnostic
executables, drivers, immutable inputs, and raw outputs are included in
complete-evidence.zip.

archive-manifest.json maps every archived artifact to its SHA-256. The
archive-verification receipt sits outside the ZIP to avoid self-referential
hashing. Root should review the bounded result before any source integration
and require the appropriate full correctness gates for an applied candidate.

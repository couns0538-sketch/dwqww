# One actual qsearch causal pair

PASS. At the actual qsearch SEE gate of -40, source16 skipped legal Qb1xb8;
source17 accepted and searched it from the same pre-gate state. This is one
forced-position correctness diagnostic, with no claim about best-move choice,
speed, or playing strength.

The frozen parent position was:

    1br3k1/2P5/2K5/8/8/8/8/1Q6 b - - 0 1

Each fresh process received OwnBook=false, Threads=1, Hash=16, ucinewgame,
isready, and exactly `go depth 1 searchmoves g8h8`. Default NNUE/options were
otherwise retained. Both actual root bestmoves were g8h8, as forced by the
protocol. The legal oracle established b1b8 as the child's only legal noisy
move and a +300 same-target material exchange after optional legal recaptures,
including promotion. That material oracle does not predict the engine score.

Both actual trace entries recorded ply1, outside check, alpha/static_eval578,
beta32001, futility_base738, and the same child FEN. Neither was skipped by
futility. The captured Bishop contributes300 to that futility test, so the
observed SEE gate was reached before a search decision.

| Actual build | SEE at -40 | Actual target branch | Depth1 score | Nodes | PV |
| --- | --- | --- | --- | --- | --- |
| Source16 | fail | SKIP_SEE; no target search | -578 | 2 | g8h8 |
| Source17 | pass | SEARCH_ENTER and SEARCH_RETURN, target score859 | -859 | 3 | g8h8 b1b8 |

The source17 returned target score859 raised the White child's alpha from578.
The corresponding root score changed under the negated qsearch result. The
forced move and shallow search establish a real pruning-path consequence;
they do not establish which move a deeper unrestricted search would choose.

`PROTOCOL.json` and `PREPARATION-RECEIPT.json` froze the witness, expected gate,
scripts, source/header/core hashes, and stopping rule before compilation or
engine execution. Root explicitly sent `17 QSEARCH TRACE CLEAR`. One common
outside-only search.cpp object was compiled with the original Release flags,
serially; two copies of the original frozen cores replaced only search.cpp.o.
All headers and production files remained unchanged. The two original cores
differ only in board.cpp.o; their NNUE object hashes match. Each executable
uses its matching original UCI object, preserving its version label.

The patch adds precise diagnostic getters/output and stores the original SEE
predicate once. The qsearch branch, thresholds, ordering, and evaluation are
unchanged except for diagnostic output. Source16's and source17's actual Board
objects supply the SEE behavior. The build emitted existing halfmove-clock
conversion warnings, preserved in compile-trace-search.stderr; compilation
and all link/archive-member operations exited0.

The pair had one invocation per build and no retry. Each shared one 10-second
startup-through-quit response guard. Both exited0, both owned process groups
were empty after cleanup, and aggregate engine budget accounting was
0.470357753 seconds against the30-second cap. These durations serve only to
verify the operational bound. Raw engine NPS/time fields remain in the
transcripts and provide no performance comparison.

`attempt1/` preserves both executable/core copies, the one compiled object,
all command stdout/stderr, complete UCI input/output, trace output, event
records, member hashes, parsed observations, and result. `originals/` preserves
both original cores/UCI objects/flags and source/header snapshots. The outside
working source/include copies are byte-identical and fully represented here.

`POST-RUN-VERIFY.json` records18 passing checks, including all external
source/header/core/UCI/flag originals unchanged, frozen driver/fixture/source
hashes, exactly one depth1 info line per build, no build/engine failure,
budgets, empty process groups, and common trace/NNUE member identity. A second
read-only agent independently inspected the raw traces and confirmed the
causal branch and both depth1 results; its receipt is preserved separately.
There were no engine failures or additional engine/build attempts to omit.
The initial system-Python dependency probe lacked chess; preparation used
the existing /workspace/.cloud-setup/venv Python and succeeded once. Two
later read-only cat commands used nonexistent trace-suffixed log names;
the existing source16.stderr/source17.stderr logs were subsequently read.

The source17 repair remains a guarded promotion-recapture SEE improvement.
LVA/lsb attacker choice and optional-stop SEE approximation remain. This pair
does not make the helper a universal exact exchange minimax solver or prove
the absence of other search errors. No further engine runs are proposed here.

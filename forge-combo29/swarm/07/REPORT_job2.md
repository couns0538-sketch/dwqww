# REPORT — seat 07, area 7, job 2: the empty `searchmoves` root and search.cpp:2640

## What was asked / the answer / how sure

**Asked:** close the `bestmove 0000` question properly: (1) prove whether search.cpp:2640 is
real UB using a debug STL or a bounds-checked wrapper; (2) establish intended behaviour for
three `searchmoves` cases; (3) write a text patch that makes the line safe and reports the case
honestly; (4) confirm the patch changes nothing measurable.

**Answer:** line 2640 is **not** UB — it is unreachable with an empty `root_candidates`, because
search.cpp:2253 returns early whenever the root is empty. My earlier code-reading suspicion is
REFUTED (FINDINGS 07-R1). What is real is a different, milder defect: when `searchmoves` names no
legal root move, the engine emits a full set of depth lines reading `score cp 0 nodes 0`, which any
GUI or harness parses as "this position is a drawn 0-node position", even though the engine has
already computed that the cause is the restriction (search.cpp:2210). Patch
`job2/searchmoves_empty_root.patch.txt` withdraws those lines for exactly that case and nothing else.

**How sure:** high on the negative (two independent instruments, each with its own positive
control, both below). High on the patch's no-change claim (honesty pins identical, per-case
bestmove/score/PV/node-count comparison automated and asserted). Medium-low on how much the
`score cp 0` line matters to a real GUI — I did not test any GUI, only that the line is emitted.

## Honesty numbers

Base build (commit 6b98f217, GCC 13.3.0, plain CMake Release, x86-64-v4), job0/raw/summary.txt:
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

Patched build (same source plus job2/searchmoves_empty_root.patch.txt, applied with
`patch -p1 --fuzz=0`, exit 0), job2/raw_patched_honesty/summary.txt:

| check | required | patched build |
|---|---|---|
| bench 11 | 312866 | 312866 |
| bench 13 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 |

sha256 of the patched exe: 70892782538b24fb57dfb4cbc95d7e308990f4bebb54315d03837b0f0fb4db5c.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| debug-STL build that would catch an empty `front()` | done | job2/raw_dbg/, build flags in this report | built (`-D_GLIBCXX_ASSERTIONS -D_GLIBCXX_DEBUG` + ASan/UBSan, `nm -C \| grep -c __asan_` = 35); **no abort** on any case |
| positive control that the debug STL detector fires | done | job2/detector_control.cpp (+ built binary `detector_control`), run below | aborts with "attempt to access an element in an empty container", exit 134 — the detector is not blind |
| reachability proof that line 2640 is executed at all | done | /tmp/reach (scratch copy, marker on 2640), raw in job2/raw_reach/ | `REACHED-LINE-2640 root_candidates=20` on a normal search; **never** on any searchmoves case |
| three requested `searchmoves` cases | done | job2/cases_searchmoves.txt, driven by job2/uci_drive.py | table below |
| text patch making the case honest | done | job2/searchmoves_empty_root.patch.txt | applies `patch -p1 --fuzz=0`, exit 0 |
| patch changes no node count | done | job2/raw_patched_honesty/summary.txt | all four pins equal |
| patch changes no bestmove where a legal root exists | done | job2/compare_searchmoves.py over raw_dbg vs raw_patched | every assertion held, exit 0 |

## The three asked cases (S14, Threads 1, Hash 16, ASan+UBSan+debug STL build)

| case | command | bestmove | last depth line | nodes |
|---|---|---|---|---|
| no legal name, board HAS legal moves | `position startpos` + `go depth 4 searchmoves e2e5` | `0000` | `info depth 4 ... score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` | 0 |
| one legal name | `position startpos` + `go depth 6 searchmoves e2e4` | `e2e4` | `info depth 6 seldepth 6 score cp -1 nodes 438 ... pv e2e4 c7c5 d2d3 e7e6 c2c3` | 438 |
| two names, one legal | `position startpos` + `go depth 6 searchmoves e2e4 e2e5` | `e2e4` | same 438-node line, same PV | 438 |

The two-name case is bit-identical to the one-name case in score, PV and node count: the illegal
name is dropped by the intersection at search.cpp:2204-2209 and costs nothing.

Also measured, and the reason my first categorisation was wrong: `position fen 7k/5Q2/6K1/8/8/8/8/8
b - - 0 1` is **stalemate**, not a restriction case — python-chess reports 0 legal moves. Its
`nodes 0` line is the pre-existing dead-root answer that Opus already listed as known, so the patch
deliberately leaves it alone. My automated checker caught my own mislabel and refused to pass;
that is the assertion working as intended (job2/compare_searchmoves.py, first run).

## Findings

**07-F1 (NEW).** `searchmoves` naming no legal root move, on a board that does have legal moves,
answers a fabricated `score cp 0 nodes 0` depth line before `bestmove 0000`. The engine knows the
cause — `result.restricted_root_empty` is set and an info string is printed — but the depth lines
claim a search that never happened.
Show it again:

    cd forge-combo29/swarm/07/job2 && python3 -u uci_drive.py <exe> cases_searchmoves.txt /tmp/x 60
    # read /tmp/x/sm_illegal_startpos.json -> last_info: "info depth 4 ... score cp 0 nodes 0 ... pv"

**07-R1 (correction of my own earlier note).** search.cpp:2640 is not an empty-container read.
Show it again: job2/raw_reach/ has the marker run; job2/raw_dbg/ has the debug-STL run that aborts
on nothing.

## Why the patch is what it is

The engine already distinguishes the cases at search.cpp:2210
(`root_restricted_ && !legal.empty() && root_candidates.empty()`). The defect is that this
information stops at an info string and the depth loop at 2259 runs anyway, reporting whatever
`score` was initialised to. The patch returns before that loop **only** when that same predicate
holds: it reuses the existing detection rather than inventing a new one, prints no score at all
(an absent line cannot be misparsed, whereas `score cp 0` is a claim), and leaves `best_move`
none so the UCI layer still answers `bestmove 0000` — no protocol change, no GUI regression. The
dead-root and drawn-root paths are untouched by construction, which is why the stalemate case and
all three legal-root cases keep byte-identical scores, PVs and node counts.

## Suspicions, not proven

- Whether `bestmove 0000` should arguably be an error answer for a restriction case at all. I did
  not change it: UCI has no error reply for `go`, and Opus's list already treats `0000` as the
  engine's normal answer on a position without legal moves. Making it an error would need a
  protocol decision, not a bug fix.
- The `nps 0` / `time 0` fields on a patched legal-root search in job2/raw_patched (the depth line
  is identical apart from timing). I read this as the patch not touching timing at all and the
  harness's `isready` boundary resetting the clock, but I did not prove it beyond noting the node
  counts are exact.

## What I did NOT do

- Did not build a TSan variant for this job (not needed for a single-threaded control-flow fix).
- Did not test any chess GUI, only the UCI text.
- Did not change `bestmove 0000` itself, per the paragraph above.
- Did not re-run set O or set G with the patch; the pins plus the six-case comparison are the
  evidence of no change.

## What I am NOT sure about

- The exact reason the debug-STL and reachability runs produced no abort on `sm_illegal_only`: I
  believe it is the early return at 2253, and the marker experiment supports that, but I did not
  single-step a debugger to show the branch being taken.

## Times

See job2/stamps.txt.

## Last command outputs

`git status --short` and `ls` of the job folder are in the final block of STATUS.md for this push.

# REPORT — seat 07, job 3: check of seat 17's finding S-F2

## What was asked / the answer / how sure

**Asked:** (area 7, cycle step 2a) check a NEW finding by another seat that nobody has checked
yet, reproducing it from its command file, with a harness of my own.

**Answer:** checked **17-S-F2**, which claims `src/search.cpp:2640` reads `front()` of an EMPTY
`MoveList` when `root_candidates` is empty but legal moves exist. **REFUTED.** Line 2640 never
executes with an empty root, because search.cpp:2253 returns early whenever
`root_candidates.empty()`. The *symptom* 17-S-F1 describes (an illegal `bestmove 0000` after
`searchmoves`) is real, and I measured it myself; the *cause* is not a `front()` on an empty list
but the fabricated `score cp 0 nodes 0` depth line emitted at search.cpp:2259. That is my 07-F1.

**How sure:** high. Both instruments carry their own positive control in this same report, so
"nothing happened" means the code path does not exist rather than that the detector is blind.

## Honesty numbers

Base build, job0/raw/summary.txt: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
perft 5 = 4865609. The two builds used here are the same source with extra flags:
`build-dbg` (`-D_GLIBCXX_ASSERTIONS -D_GLIBCXX_DEBUG -fsanitize=address,undefined`,
`nm -C | grep -c __asan_` = 35) and `/tmp/reach/build-dbg` (same plus a stderr marker at 2640).

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read 17-S-F2's own command file | done | `git show FETCH_HEAD:forge-combo29/swarm/17/job1/finding_searchmoves.py` | it is a *symptom* script; the S-F2 cause claim is a `sed`/code-reading claim with no test |
| harness of my own (never a copy) | done | job3/cases_17sf2.txt + job3/check_17SF2.py, driving job2/uci_drive.py | every `go` is followed by reading until `bestmove` |
| instrument A: container check | done | job3/raw_dbg/, verdict in check_17SF2.py stdout | **no abort on any case** |
| instrument A positive control | done | job2/detector_control.cpp (compiled with the same flags) | aborts: "attempt to access an element in an empty container", exit 134 |
| instrument B: reachability marker | done | job3/reach_2640.py over /tmp/reach/build-dbg, raw in job3/raw_reach2/ | **0 hits with size 0**; positive control fires at size 20 |
| instrument B positive control | done | case `control_plain_nodes` in cases_17sf2.txt | `REACHED-LINE-2640 root_candidates=20` |
| guard precondition (marker really in the binary) | done | reach_2640.py runs `strings` first and exits if absent | marker present; script refuses to report otherwise |

## What the engine actually answers (ASan + debug STL build, S14, Threads 1, Hash 16)

| case | command | bestmove | depth line | nodes |
|---|---|---|---|---|
| 17's empty-root case | `position startpos` + `go depth 5 searchmoves e7e5` | `0000` | `info depth 5 seldepth 5 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` | 0 |
| garbage name | `position startpos` + `go depth 5 searchmoves zzzz` | `0000` | same 0-node line | 0 |
| legal control | `position startpos` + `go depth 5 searchmoves e2e4` | `e2e4` | `info depth 5 seldepth 5 score cp 23 nodes 252 ... pv e2e4 c7c5 c2c3 e7e6` | 252 |
| mate position | `... b KQkq - 0 4` + `go depth 5 searchmoves a7a6` | `0000` | 0-node line | 0 |
| black to move, White's move named | `... b KQkq - 0 1` + `go depth 5 searchmoves e2e4` | `0000` | 0-node line | 0 |
| empty list | `position startpos` + `go depth 5 searchmoves` | `0000` | 0-node line | 0 |

## Why 2640 is unreachable-empty (the mechanism, with lines)

    search.cpp:2203  MoveList root_candidates;            // filled by the restriction intersection
    search.cpp:2210  result.restricted_root_empty = root_restricted_ && !legal.empty() && root_candidates.empty();
    search.cpp:2253  if (root_candidates.empty() || root_drawn) { ... return result; }   // <-- the guard
    search.cpp:2459  if (!result.pv.empty()) result.best_move = result.pv.front();
    search.cpp:2640  if (result.best_move.is_none()) result.best_move = root_candidates.front();

Every path that reaches 2640 has passed 2253 with a non-empty `root_candidates`. The marker run
confirms this empirically: the only hit in the whole matrix is `go nodes 5`, where the search stops
before any iteration publishes a PV, so 2460 leaves `best_move` none and 2640 fills it in from a
root that is (correctly) size 20.

That last observation is a small extra: line 2640 is what makes `go nodes 5` answer `a2a3`, the
first legal move in generation order — consistent with seat 27's S-F2, which I have not checked.

## Findings

**07-C1 — REFUTES 17-S-F2, CONFIRMS the symptom of 17-S-F1.** In FINDINGS.md.
Show it again:

    cd forge-combo29/swarm/07/job3 && python3 -u reach_2640.py /tmp/reach/build-dbg/forge /tmp/reachcheck
    # expects: control_plain_nodes marker hits=1 sizes=[20]; all s17_* cases 0 hits
    python3 -u check_17SF2.py /agent/repos/base/forge-combo29/build-dbg/forge /tmp/dbgcheck
    # expects: aborted False on every case

## Suspicions, not proven

- I did not examine seat 17's own build or flags, so I cannot say whether their `front()` claim came
  from a build whose `root_candidates` could actually be empty (e.g. an older commit). I refuted the
  claim against 6b98f217, the commit the brief pins.

## What I did NOT do

- Did not re-check 17-S-F1's GUI-facing argument (whether a GUI should treat `0000` as an error).
- Did not check seat 27's S-F2 (`go nodes` below one iteration), only noticed that 2640 explains it.

## What I am NOT sure about

- Whether 2640 can be reached with an empty root on any input at all. I covered the searchmoves
  family, mate/stalemate roots and the node-budget path; I did not exhaustively enumerate
  `MultiPV` + `searchmoves` + clock combinations.

## Times

See job3/stamps.txt.

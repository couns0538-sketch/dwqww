# REPORT — seat 07, job 5: settling seat 01 vs. seat 07 on search.cpp:2640

## What was asked / the answer / how sure

**Asked:** seats 01 and 07 make contradictory claims about search.cpp:2640. Settle it with the
marker instrument; quote raw marker output; note that ASan silence is not evidence either way;
record the resolution in FINDINGS naming seat 01; report one line to the coordinator.

**Answer:** **seat 01's claim does not hold, mine does.** Line 2640 is never reached with an empty
`root_candidates`, because search.cpp:2253 returns first. The `bestmove 0000` comes from
`best_move` legitimately staying `none` (the UCI layer renders a none move as `0000`), not from a
garbage `Move` read out of a `front()` on an empty list.

**How sure:** very high. The instrument is a single binary with a marker on **both** branches, so
whichever path executes announces itself. Seat 01's exact commands fire the 2253 marker and never
the 2640 marker, and the 2640 marker is proven able to fire in the same binary.

## The instrument

`/tmp/branch` = 6b98f217 plus two stderr markers, nothing else:

    search.cpp:2253  if (root_candidates.empty() || root_drawn) {
    +    std::cerr << "MARK-2253-EARLY-RETURN root_candidates=" << root_candidates.size()
    +              << " legal=" << legal.size() << " restricted=" << int(result.restricted_root_empty)
    +              << " drawn=" << int(root_drawn) << std::endl;
    search.cpp:2640  if (result.best_move.is_none()) {
    +    std::cerr << "MARK-2640-GUARD-TRUE root_candidates=" << root_candidates.size() << std::endl;
         result.best_move = root_candidates.front();

Built plain RelWithDebInfo with g++-13, no sanitizers (a sanitizer is irrelevant to which branch
runs, and would only slow the marker down). Driver: job2/uci_drive.py, which never pipelines a
command behind `go`.

## Raw marker output (verbatim, from job5/raw/*.err)

| case | command | MARK-2253 fired | MARK-2640 fired | bestmove |
|---|---|---|---|---|
| s01_c1_plain_control | `go depth 2` | no | no | `d2d4` |
| s01_c2_searchmoves_no_names | `go searchmoves depth 2` | **yes**, `root_candidates=0 legal=20 restricted=1 drawn=0` | no | `0000` |
| s01_c3_one_legal_name | `go searchmoves e2e4 depth 2` | no | no | `e2e4` |
| s01_c4_not_a_move | `go searchmoves a1a1 depth 2` | **yes**, `root_candidates=0 legal=20 restricted=1 drawn=0` | no | `0000` |
| s01_c5_illegal_pair | `go searchmoves e2e5 depth 2` | **yes**, `root_candidates=0 legal=20 restricted=1 drawn=0` | no | `0000` |
| s01_c6_restricted_illegal_only | `go searchmoves e7e5 depth 2` | **yes**, `root_candidates=0 legal=20 restricted=1 drawn=0` | no | `0000` |
| s01_c7_two_legal | `go searchmoves e2e4 d2d4 depth 2` | no | no | `d2d4` |
| s01_c8_marker_positive_control_nodes | `go nodes 5` | no | **yes**, `root_candidates=20` | `a2a3` |

The last row is the positive control: it proves the 2640 marker in this very binary is capable of
printing, so the absence of 2640 lines in rows 2, 4, 5 and 6 means the branch was not taken, not
that the instrument was dead. Rows 1, 3 and 7 are the controls showing plain and legal-restricted
searches reach neither marker.

## On ASan silence

Seat 01 is right that "ASan reported nothing" proves nothing here, and I do not use it as proof.
An out-of-range read into a mapped slot need not trap. The disagreement was therefore never
settleable by sanitizers, which is why both seats' sanitizer observations are set aside and only
the branch markers are used. (For the record, my earlier debug-STL run also produced no abort, and
I likewise do not treat that as the proof — see the note below.)

## Why 2640 cannot see the empty list, in lines

    2203  MoveList root_candidates;                 // filled by the searchmoves intersection
    2210  result.restricted_root_empty = root_restricted_ && !legal.empty() && root_candidates.empty();
    2253  if (root_candidates.empty() || root_drawn) { ... return result; }  // <-- fires, marker proves it
    2459  if (!result.pv.empty()) result.best_move = result.pv.front();
    2640  if (result.best_move.is_none()) result.best_move = root_candidates.front();

Every path to 2640 has already passed 2253 with a non-empty root. `best_move` being `none` at 2640
happens on the `go nodes 5` path, where no iteration publishes a PV — and there the root is
size 20, exactly as the control shows.

## One correction to my own earlier evidence

My 07-C1 line leaned partly on a debug-STL build not aborting. Given seat 01's correct point that
sanitizer/abort silence is weak evidence, the load-bearing evidence is now the two-branch marker
run in this report (07-C2). The 07-C1 conclusion is unchanged and now rests on the stronger
instrument; the debug-STL non-abort is retained only as consistent supporting observation.

## Findings

**07-C2 — REFUTES seat 01's S-C3 (2640 half), AGREES on the ASan method point.** In FINDINGS.md.
Show it again:

    cd forge-combo29/swarm/07/job5 && python3 -u ../job2/uci_drive.py /tmp/branch/build/forge cases_s01.txt /tmp/x 60
    grep -E "MARK-" /tmp/x/*.err

## What I did NOT do

- Did not attempt to build seat 01's exact binary or flags; the claim is about 6b98f217's control
  flow, so it is refuted at the pinned commit.
- Did not change `bestmove 0000` semantics; that stays the patch's business (07-F1), not this check.

## Times

See job5/stamps.txt.

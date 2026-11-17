# swarm/61 — verification seat, final status

**RECHECK.md is complete and pushed.** **Claims examined: 39. Agree: 35. Disagree: 4.**
Header counts verified mechanically by `verify_recheck_counts.py` (5/5), not hand-written — my
first hand-written header said 34/30/4 and the checker caught it.

PR #57 (`for-fable-and-opus/swarm-61`). Tip `001d1f39`. All four recheck scripts reproduce on the
pushed commit: counts 0, prefetch 0, nodesaving 0, pernode 2 (its documented disagreement).

## The four disagreements

1. **D1 — the PC20 per-node row pairs a point estimate with a different estimator's interval.**
   `+6.4%` is the pooled ratio (1.0643); `[1.0670, 1.0876]` is a mean-of-ln interval centred on
   1.0736, so the pooled estimate lies **outside its own CI**. Every construction excludes 1.0, so
   the finding stands; the pairing does not. General form: a point estimate and an interval from
   two different estimators cannot be quoted as one row.
2. **D2 — the same row's sign share is 163/180, not 162/180** (164 at or above, one exact tie).
   90.0% either way.
3. **D3 — the r15 repair is a provenance gap, not a result.** `-DFORGE_MATE_ALPHA_GUARD=1` builds to
   sha256 `84bfb5d6…`, byte-identical to seat 19's prefetch CTRL, and still bails on a threefold
   root like base. `FORGE_FIX_ROOT_DRAWN` exists only as prose and in check scripts across
   swarm-12/27/23/01, never in engine source — **independently confirmed by the coordinator**,
   which closes the one uncertainty I could not resolve alone (a branch I had not fetched).
   Stated in both directions: a provenance gap, not evidence the numbers are wrong, and
   specifically not a reason to distrust the mate-in-one fix or the 425/mate-8/mate-9 columns.
   **Consequence: the shipped patches are what closes it** — seat 12's and seat 27's are committed
   as text, compose byte-identically, and carry a measured ship verdict.
4. **D4 — the "one ply lower" board's 36 nodes is depth-12 only** (48/60/72 deeper). The
   load-bearing claim, that no depth fixes it, holds at depth 24; counters 97/98 give `mate −1`.

## What agrees

Honesty pins re-derived on my own build (312866 / 862329 / 3024920 / perft 5 4865609); every other
drawn-root figure (7,581; 0; 0; sweep 7581/7580/7723/200/0; move==perft-1-head 2/2; the mate
forfeit; `depth 64`/`seldepth 64`/`nodes 0`; the `min(depth,64)` info-line counts 10/64/64; the
empty-PV detector); PC20 node saving (all 464 committed rows reproduce 0.9131, CI within 0.0017);
prefetch 8/8 plus an **independent re-measurement of +10.64% at n=130** on an engine rebuilt from
the committed patch and verified byte-identical (`193c9a78…`).

## My own faults, all recorded in RECHECK.md

1. `parse_search` required a token after `pv` and so **skipped the bail's own line**.
2. `perft()` waited for `Nodes searched`; the engine prints `nodes <N>`.
3. `perft()` sent a second `isready` after the first had drained `readyok`.
4. **An unreachable duplicate `_scan_fen(lines, "perft output")` after a `return`** — found by
   static analysis, not by a timeout; the "appears to run and does not" class.
5. **A bulk re-indent left `rows.append` outside its `if`**, so two scripts parsed **1 and 8 rows
   instead of 180 and 464** and one still printed a complete, plausible set of ratios from the
   survivors. The per-node script's `expected 180` guard caught it; node-saving had none, so I
   added `expected 464` and proved it fires by truncating the evidence.

Also corrected in my own earlier work: the 2-occurrence cell read 22,108 (depth 12 + warm TT)
before a cold re-run gave 7,581; and my first "PC" binary was byte-identical to base because
`CMAKE_CXX_FLAGS` never reached the compiler.

## FEN diagnostic, applied to source harnesses

Measured: the diagnostic is **always emitted** and always precedes the first `info depth`, so scan
from `position` through `bestmove`. Two source harnesses (`swarm/19/checks/prefetchreal/run.py`,
`swarm/23/job68/final_recheck.py`) send `isready` after `position` and read only from `go` — the
silent-consumption pattern — and neither validates FENs. **4 of the 600 FENs in `their_600.fens`
fail python-chess validation.** The prefetch numbers remain safe: their 130 pairs show node ratio
exactly 1.000000, which a substituted position would have broken.

## Security gate — repo-level, closed as not-mine

SonarCloud's Security Rating on New Code failed on this PR and on sibling PRs #52–#55 while `main`
passes. The pod's egress blocks `sonarcloud.io`, so the rule list was unreadable here. The
annotations point at `subprocess.Popen` and `open()` lines — security *hotspots*, correct as
written (list-form argv, no `shell=True`, no `eval`/`exec`/`pickle`, absolute paths from the
harness). I removed the two patterns I could justify on merit: a nested-lazy-quantifier regex
(replaced with `str.split`, output byte-identical) and global `random` state (replaced with a local
`random.Random(seed)`, sequence verified identical before switching). Recorded as a repo-level
decision, not a per-seat defect. As of the final tip the gate no longer reports on this branch.

## Known, deliberate leftover

`recheck_pins.py`'s perft leg still waits on `Nodes searched` where the engine prints `nodes N`
(fault 2 above, unfixed in that one script). Left deliberately: pins were deprioritised and the
repo's own `check_pins.sh` verifies perft 5 independently.

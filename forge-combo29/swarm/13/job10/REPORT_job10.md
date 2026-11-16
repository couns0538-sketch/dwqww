# REPORT_job10 — reproduction attempt for another seat's "under-reported mate at go nodes 20000"

## What was asked
Another seat reported that at `go nodes 20000` on endgame boards the engine claims a mate distance
its own PV does not deliver — **2 of 14 boards**. My harness already verifies that a mate claim
resolves in exactly the claimed plies, so the coordinator asked me to run it over my 21 mate positions
and the 6 lost ones at `go nodes 20000` specifically, with repetitions, and report whether any
under-report appears.

## The answer
**No under-report appears: 0 of 200 mate claims, over 270 runs on 27 boards, in both disciplines.**

| | result |
|---|---|
| boards | 27 (21 job-9 mate positions + 6 job-9b lost positions) |
| budget | `go nodes 20000` only |
| repetitions | 5 per board per discipline |
| runs | 270 (135 fresh-process, 135 shared-process) |
| runs producing a mate claim | 200 |
| runs producing a cp score | 70 |
| **under-reported or wrong mate claims** | **0** |
| boards affected | 0 |

Because my result is clean where theirs was not, the useful conclusion is a **bound**, not a
contradiction: their two boards are not among my 27, so the defect is specific to particular positions
rather than a general failure of the mate path at that budget. Two other differences also apply, and I
list them honestly below rather than claiming their finding is wrong.

## Two disciplines, because warm state is the obvious suspect
Seat 10 established that two identical searches in one process give different node counts on this
engine, so a *warm* run is exactly the mechanism that could make a claim outrun its own PV. I therefore
ran each board twice over:

- **FRESH** — a new engine process per search (135 runs).
- **SHARED** — one process for the whole list, `ucinewgame` between searches (135 runs).

Both were clean. Additional findings from comparing them:

| check | result |
|---|---|
| per-board result unstable across the 5 reps | **0 of 54** board×discipline groups |
| groups whose node count varied across reps | **0 of 54** |
| boards where FRESH and SHARED disagreed on the answer | **0 of 27** |

So on these boards, at this budget, with PC20/Threads 1/Hash 16, the mate path is deterministic and
insensitive to process reuse.

## How sure
High that no under-report exists **on my 27 boards**. The detector is proven able to fail
(`CONTROL_UNDERREPORT.md`, through the same `judge()` function):

| plant | verdict | expected | correct |
|---|---|---|---|
| P0 real claim (mate 2, PV mates at 3) | delivered | delivered | yes |
| A claim mate 1 when the PV needs 3 plies | UNDER_REPORTED | UNDER_REPORTED | yes |
| B PV truncated to 1 ply | UNDER_REPORTED | UNDER_REPORTED | yes |
| C empty PV | UNDER_REPORTED | UNDER_REPORTED | yes |
| D PV with an illegal first move | UNDER_REPORTED | UNDER_REPORTED | yes |
| E a cp score is not a mate claim | no_mate_claim | no_mate_claim | yes |

**A control mistake I made and fixed:** my first version of this control used a mate-in-1 board, where
"claim mate 1 with a PV that mates at ply 1" is genuinely correct, so three of the six cases were
indistinguishable and reported as failures. I had picked a board where the plants could not be told
apart — the same class of error as the wrong-predicate mistake in job 9b, and I only caught it because
the control disagreed with itself. Re-run on a mate-in-2 board, all six cases are correct.

## Why the difference from their finding is plausible (not a refutation)
I am **not** claiming their result is wrong. Three concrete differences could explain a clean result
here and a defect there:

1. **Different boards.** Theirs are endgame boards they found the defect on; mine are elementary
   king-and-piece mates plus 6 lopsided G positions. If the defect needs a particular geometry, my set
   would not contain it.
2. **Different budget interaction.** At 20,000 nodes my boards are almost all trivial to solve — the
   engine reports `mate 1`/`mate 2` at high depth because the ending is simple. A mate claim that
   outruns its PV is more likely where the mate is *hard* to find at that budget.
3. **Their build/settings may differ.** Mine is PC r15 under PC20 with MateAlphaGuard on.

So the honest statement is: **their finding stands unrefuted by my data; my data bounds it to boards
other than these 27, and shows it is not a general property of `go nodes 20000` on endgame positions
under PC20.**

## Settings and build
PC r15 sha256 `068f0927...`, `-DFORGE_MATE_ALPHA_GUARD=1`; PC20 in full (Threads 1, Hash 16, S14 +
the six), option names validated against the exe's `uci` list, `isready`/`readyok` after every
`setoption`, `quit` only after `bestmove`.

## Findings
- S-F13: **no under-reported mate** at `go nodes 20000` on 27 endgame/mate boards: 200 mate claims in
  270 runs (135 fresh-process, 135 shared-process), **0** claims whose own PV failed to deliver, 0
  boards affected, and full determinism (0 of 54 board×discipline groups varied across 5 reps, 0 node
  count variation, 0 fresh-vs-shared disagreement). This does not refute the other seat's 2-of-14
  result; it bounds it to boards other than these. Reproduce:
  `cd forge-combo29/swarm/13/job10 && python3 underreport.py ~/b/pc/forge boards27.json out 5 20000`
  then `python3 control_underreport.py ~/b/pc/forge boards27.json out 5 20000`.

## Suspicions, not proven
- If the under-report needs a *hard* mate at 20,000 nodes, my boards are the wrong material: they are
  solved almost immediately. A better test would use endgame boards where the correct mate distance is
  large (mate in 8+), which my exhaustive reference cannot verify cheaply. I am flagging that as the
  most likely reason my set came back clean.

## What I did NOT do
- **I did not test their 14 boards** — I do not have them. That is the one experiment that would settle
  it, and it needs their position list.
- No budgets other than 20,000 (the coordinator specified that one).
- No mate distances deeper than 3 in the reference set (the exhaustive verifier is expensive), so a
  "hard mate" scenario is under-represented.

## What I am NOT sure about
- With 27 boards of mostly elementary endings, a clean sweep is weak evidence about *hard* positions
  even though it is strong evidence about *these* positions.
- The shared discipline uses `ucinewgame` rather than a truly warm table, so it is "partially warm";
  a fully warm run (no `ucinewgame`) was not tested here and is the one variant most likely to differ.

## Files
`underreport.py` (harness), `control_underreport.py` + `CONTROL_UNDERREPORT.md` (Rule-1 control),
`boards27.json` (the 27 boards), `out/underreport.json` (all 270 rows), `stamps.txt`.

## Last command output

```
$ ls
boards27.json
CONTROL_UNDERREPORT.md
control_underreport.py
out
REPORT_job10.md
stamps.txt
underreport.py
```

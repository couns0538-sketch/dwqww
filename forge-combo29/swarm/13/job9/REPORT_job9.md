# REPORT_job9 — mate scores on the PC's real path (closes a gap I named in job 7)

## What was asked
Not asked by the coordinator; this closes a limit I stated myself in job 7: *"all 12 positions
scored cp, none mate, so the mate-score path at these budgets is untested here."*

## The answer
**57 positive mate claims, and every single one is real and exact.**

| property | result |
|---|---|
| positions | 21 (14 mate-in-1, 3 mate-in-2, 2 mate-in-3, 2 deliberate no-mate controls) |
| budgets | 20,000 / 50,000 / 250,000 under PC20, Threads 1, Hash 16 |
| runs | 63 |
| runs producing a `mate` score | 57 |
| **claims NOT delivered by the engine's own PV** | **0** |
| **PV mate distance differing from python-chess's** | **0** |
| illegal bestmoves | 0 |
| mate score changed between budgets | 0 positions |

Every `mate M` claim was delivered by the move sequence the engine itself printed, in exactly the
right number of plies: `mate 1` at ply 1, `mate 2` at ply 3, `mate 3` at ply 5. The two deliberate
no-mate controls stayed `cp` at all three budgets, so the engine does not manufacture a mate score
where no forced mate exists.

## How sure
High, and the check is proven able to fail (`CONTROL_MATES.md`, run through the same functions):

| plant | check says delivered? | should be? | correct |
|---|---|---|---|
| P0 the real claim (mate 2) against the real PV (mates at ply 3) | yes | yes | correct |
| A claim of mate 1 when the PV needs 3 plies | no | no | correct |
| B PV truncated to 1 ply | no | no | correct |
| C PV with an illegal first move | no | no | correct |
| D no PV at all | no | no | correct |

## The reference values are computed, not assumed
Each position's true mate distance comes from an exhaustive python-chess search
(`build_mates.py`): for each candidate, the smallest N such that every defence is mated within N
plies, confirming the bound at N, N−2, … Only confirmed positions were kept. So "mate 2 delivered at
ply 3" is a comparison against a computed ground truth, not against the engine's own opinion.

## Settings and build
PC r15 sha256 `068f0927...`, `-DFORGE_MATE_ALPHA_GUARD=1`; **PC20** in full (Threads 1, Hash 16, S14
+ the six), option names validated against the exe's `uci` list, `isready`/`readyok` after each
`setoption`, fresh process, `quit` only after `bestmove`.

## Findings
- S-F11: on the PC's real path (PC r15, PC20, Threads 1, Hash 16) at all three match budgets, every
  reported mate score is **delivered by the engine's own PV in exactly the claimed number of plies**:
  57/57 positive claims correct, 0 distance disagreements with python-chess, 0 illegal bestmoves, and
  no mate score changed between 20,000 / 50,000 and 250,000 nodes. Two no-mate positions correctly
  stayed `cp`. This closes job 7's stated gap (job 7 saw only cp scores). Reproduce:
  `cd forge-combo29/swarm/13/job9 && python3 build_mates.py positions.json && python3 mates_run.py
  ~/b/pc/forge out 20000,50000,250000` and `python3 control_mates.py`.

## Suspicions, not proven
- None. This is a clean result.

## What I did NOT do
- Negative mate scores (the engine being mated) were not systematically exercised: one candidate
  position was built for it but python-chess found no forced mate from it within the bound, so it was
  dropped rather than reported as a test. My `mate < 0` handling therefore has **no coverage**, and I
  am saying so rather than implying the sign convention is verified.
- Mates deeper than 3 (5+ plies) are not represented; the exhaustive reference gets expensive.
- Only 21 positions, all elementary king-and-piece endings, not middlegame mates.

## What I am NOT sure about
- Elementary endings are the easiest case for a mate score: the search finds them almost immediately
  (depth 64 reported, i.e. it sees the mate outright). A mate-score bug that needed a deep,
  heavily-pruned search would not be exposed here.
- The `MateAlphaGuard` option is on under PC20, and I have not compared against it off, so I cannot
  say whether the guard is what makes these exact.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
build_mates.py
CONTROL_MATES.md
control_mates.py
mates_run.py
out
positions.json
REPORT_job9.md
stamps.txt
```

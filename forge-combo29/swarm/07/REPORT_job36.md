# REPORT — seat 07, job 36: the 100-position differential, and why its zero is a real result

## What was asked / the answer / how sure

**Asked:** the 100-case base-vs-PC differential, every move difference with its isolating switch.

**Answer:** **there are no differences.** 0 of 100 positions differ at depth 12 under identical
settings. The isolating machinery was built and is tested, but it had nothing to isolate. That zero is
itself the finding, and it is consistent with the four-leg result from the other direction.

**How sure:** high, because the instrument is proven able to see a difference (1 of 1 on a known
case), so this is a measured zero rather than a blind one.

## Result

    100 positions, depth 12, Threads 1, Hash 16, OwnBook false, base vs PC under IDENTICAL settings
    stage 1: 0 of 100 positions differ (0.0%)
    absent answers: none

Raw: job36/raw/diff100.json (every position, both answers).

## The control that makes the zero mean something

    $ diff100.py base pc 8/P6k/8/8/8/8/8/K7-w.fen ...
      DIFF   0 base a1a2/cp 1067/21093  pc a7a8q/cp 1124/36405
    stage 1: 1 of 1 positions differ (100.0%)

The same script, same code path, same settings reports the difference it is built to find. A 12-position
run through the identical path also completed cleanly. So "0 of 100" is not the instrument being blind.

## Why zero is the right answer, not a disappointment

The four `FORGE_FIX_*` switches that the PC patch adds are aimed at **special states**:

| switch | the state it fires on |
|---|---|
| `FORGE_FIX_ROOT_DRAWN` | a root that is a third repetition or has passed the 50-move counter |
| `FORGE_FIX_GO_PARSE` | a `go` line where a keyword is taken as another keyword's value |
| `FORGE_FIX_BARE_KING_*` | endings where one side has a bare king |
| `FORGE_FIX_HARD_LIMIT_EMERGENCY` | a hard time limit already passed before the search starts |

Set O at depth 12 is **ordinary middlegame positions**. None of those states occurs, so none of the
fixes fires, so the trees are identical. That is not an accident of my sample; it is the design.

This is the same fact as **07-C30** seen from the other end: `PC+S14 = base+S14 = 9,500,069`, exactly
equal, on all 200 positions. Two independent measurements, one aggregate and one per-position with
controls, agree.

**What it tells the owner:** the PC patch's value is in the special states it fixes (a drawn root now
searched, a bare-king ending not mis-reduced, a malformed `go` not misparsed), **not** in changing how
ordinary positions are searched. If the owner wants better play in ordinary positions, the lever is the
**options** — and per 07-C32 that lever is almost entirely `TtPruneV2`.

## The isolation machinery, built and tested but unneeded here

`diff100.py --variant NAME=PATH` re-runs each differing position against scratch builds carrying one
`FORGE_FIX_*` switch alone and names the switch that reproduces the PC answer. I built all three
variants (`/tmp/var_ROOT_DRAWN`, `/tmp/var_HARD_LIMIT_EMERGENCY`, `/tmp/var_BARE_KING_LMR_CAP`, each
with exactly one switch set and the others off) and verified the approach worked in job33/07-C29, where
it isolated the one real difference. With 0 differences there was nothing for it to name; the code is
in place and tested for the next seat.

## Findings

**07-C33** in FINDINGS.md.

## Suspicions, not proven

- That the patches would show differences on **game positions from the owner's real match files**,
  particularly late endgames and drawn positions — which is precisely where the fixes are aimed and
  precisely the path file 6 says is worth most. Set O is not that sample. This is a strong candidate
  for the next 12 hours' work rather than a gap in this result.

## What I did NOT do

- Did not run the differential on bare-king or drawn-repetition positions at depth 12 (those are where
  a difference is *expected*, and finding one there would be confirmation rather than news).
- Did not look for differences at depths other than 12.

## What I am NOT sure about

- Whether "0 of 100 at depth 12" holds at depth 20 or with node budgets. A deeper search may reach the
  bare-king or drawn-root states inside the tree, where a fix could change the answer. I flagged it
  rather than guess.

## Times

See job36/stamps.txt.

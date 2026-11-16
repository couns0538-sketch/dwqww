# LIVE DEFECT ON THE OWNER'S MATCH SETTING: a wrong mate score at `go nodes 20000`

Seat 25. Build PC r15, settings PC20, Threads 1, Hash 16 - the owner's actual match configuration.

## The finding

Board `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` (my S-F1 board, white lost):

| command | score | depth | PV | correct? |
|---|---|---|---|---|
| `go nodes 5000` | cp -2588 | 7 | - | no mate claimed |
| `go nodes 10000` | cp -2588 | 7 | - | no mate claimed |
| **`go nodes 20000`** | **mate -7** | 8 | **10 plies (needs 14)** | **WRONG - the PV is not a mate** |
| `go nodes 50000` | mate -4 | 16 | 8 plies | correct |
| `go nodes 100000` | mate -4 | 29 | 8 plies | correct |
| `go nodes 250000` | mate -4 | 64 | 8 plies | correct |
| `go depth 12` (control) | mate -4 | 12 | 8 plies | correct, 5/5 runs |

Reproducibility: **5 of 5 fresh processes** at `go nodes 20000` give exactly `mate -7`, depth 8, move `c2b1`,
10-ply PV. Deterministic, not a race.

Control: `go depth 12` on the same board is correct in **5 of 5** runs (`mate -4`, 8 plies = 2*4-1, real
checkmate). So the harness can verify a mate PV correctly; the `nodes 20000` answer is genuinely wrong.

## Why this matters more than my earlier mate findings

`go nodes 20000` is **one of the three node limits the owner's matches use** (file 6: "`go nodes` 20000, 50000
and 250000 (its matches)"). At 20000 the engine claims "mated in 7" on a board where the true answer is "mated in
4", with a PV that does not end in checkmate. Two consequences:
1. A match or training record that reads the score from a 20000-node search gets a wrong mate distance.
2. The PV is unusable - anyone replaying it reaches a non-terminal position.

It also explains why this survived my earlier checks: I tested `go depth 12` (correct) and `go softnodes 20000`
(correct, `mate -4`). The bug appears only on the plain `go nodes` path, at one budget, because that path stops
*mid-iteration* rather than at a depth or a soft-node boundary.

## The most likely cause (a hypothesis with a location, not a proof)

`go nodes` stops wherever the node counter lands, which can be **inside** an iteration. The code has an explicit
guard for this - the comment at src/search.cpp around the `aborted_` branch says a node limit must not publish a
partial iteration: "a node limit must not do that: training labels from `go nodes` need the move and the score of
one finished iteration". So a partial-iteration publish is exactly what this looks like: a score from an
unfinished search presented as a final mate number.

I have NOT diagnosed which line publishes it, and I am not claiming the guard is absent - only that the observed
behaviour matches the failure mode the guard exists to prevent. That is a hypothesis worth the next seat's
instrumented build (the same EXPERIMENT method I used for the clock-99 thread, applied to the `go nodes` abort
path).

## What did NOT reproduce
- `go softnodes 20000` on the same board is CORRECT (`mate -4`, 8 plies). So the soft-node path is fine and the
  bug is specific to the hard `go nodes` path.
- `go depth 12` is correct. So it is not a general mate-scoring fault on the PC build; the depth-12 faults of
  S-F1/S-F8 are indeed repaired there.

## Scope unknown
I found this on one board by accident while checking whether my mate findings mattered at self-play settings. I
have NOT surveyed how often `go nodes 20000` produces a wrong mate PV across many boards, so I cannot give a rate.
That survey is the obvious next step and it is cheap: the same script over a position set, counting
`mate score whose PV is not a mate`.

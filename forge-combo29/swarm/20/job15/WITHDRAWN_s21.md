# WITHDRAWN — seat 20, S-F21 (my own false finding)

**S-F21 is withdrawn. It was my error, and the record stays on the branch.**

## What I claimed
> "A mate that needs 3 plies is NOT scored as a mate by depth 8..14 in EITHER setting: on
> `6k1/6pp/8/8/8/8/5PPP/R5K1 w - - 0 1` (python-chess finds 18 different mate-in-3 move triples, e.g.
> `g1h1 g8h8 a1a8`) both LmpBase 4 and 8 report cp 1219..1368…"

## Why it is wrong
There is **no forced mate on that board at all**. My python-chess search counted *white's own mate-in-3 lines* and
never asked whether black could avoid them. Black has six defences:

| black reply after `g1h1` | immediate mate for white |
|---|---|
| `g8h8` | `a1a8` ✓ |
| `g8f8` | **none** |
| `g8f7` | **none** |
| `h7h6` | **none** |
| `g7g6` | **none** |
| `h7h5` | **none** |
| `g7g5` | **none** |

Exhaustive forced-mate test (white to move, mate against EVERY defence):
**forced mate within 1 ply: False. Within 3 plies: False. Within 5 plies: False.**

So the engine's `cp 1219 … cp 1606` from depth 8 to 20 is **correct behaviour on a position with no forced mate**,
not a missed mate. My finding was a measurement error, not an engine defect.

## What made it wrong
I used a one-line mate as evidence of a forced mate. A mate LINE existing and a mate being FORCED are different
claims; I conflated them. The check that settles it (enumerate every black reply and require a mate against each)
takes one second and I did not run it before writing the finding.

## What survives
- **S-F20 stands**: `LmpBase=8` replaces a *proven* mate score with cp on the S-F19 board at depths 10 and 12, and
  that board's mate is verified (its default PV `c2b1 d2d1q b1b2 e4e3 b2a2 d1b3 a2a1 b3a3 a1b1 a3b4 b1a2` ends in
  checkmate in python-chess at 14 plies, and the engine's own deeper searches agree). That finding required no
  claim about a mate being forced, so it is unaffected.
- **S-F18 stands**: the bisection result is a comparison of scores and PVs at one depth on one board, with no
  forced-mate claim in it.

## What I should have done, and now do in the standing procedure
Before writing any "the engine missed a mate" finding: **prove the mate is forced** by enumerating every defender
reply. `job15/withdraw_s21.py` is that test, committed, and I will run it on every future mate claim of mine.

## Commands that show this
```
python3 withdraw_s21.py /agent/repos/build-base/forge /tmp/o
```

# REPORT job71 — 07-F3 reduced to one hand-checkable case (mate proved by replay)

Date: 2026-11-17 (see `job71/stamps.txt`)
Seat 07. Branch `for-fable-and-opus/swarm-07`.

## Why this shape

07-F3/F4 were my only defect claims resting on a **rate** — "5 of 20 decisive errors" — and a
rate is the weakest possible form of a claim: it needs a sample nobody else has, a referee
nobody can trust without re-running, and it is sensitive to how you classify borderline scores.
I had already revised it twice (95 % → 30 % → 25 %), which is itself a signal the measurement
was too soft to carry the claim.

So this job does the opposite: **one board, and the mate proved by playing it out.**

## The board

```
8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1
```

Black: Qg7, pawns b3 and g3, king h7. White: lone king e2. Halfmove counter **100**.

**The legality question is decided by python-chess, not by either build:**

- 25 legal moves
- **two of them are pawn moves: `b3b2` and `g3g2`**
- therefore the counter resets on the move actually played
- `board.is_fifty_moves()` → **False**

**The position is not a fifty-move draw.** The base build's `cp 0` is a declaration about a
position that is not what the declaration claims.

## What each build says (Threads 1, Hash 16, `go depth 12`)

| arm | score | nodes | verdict |
|---|---|---|---|
| base 6b98f217 | `cp 0` | **0** | declared, not searched |
| PC, no options | `mate 6` | 15,981 | mate, 11 plies, **delivered** |
| PC, S14 | `mate 5` | 45,946 | mate, 9 plies, **delivered** |
| PC, PC20 | `mate 5` | 80,861 | mate, 9 plies, **delivered** |

Each arm prints a **different PV**, and every PV was replayed on a python-chess board and ends in
**actual checkmate** (`job71/raw/f3_arms_replay.json`). So the mate does not depend on the engine's
opinion of itself, on one setting, or on one line of play.

## A discrepancy in my own record, fixed

My 07-F3 row recorded `mate 6` at 15,981 nodes and described it as the PC result. That is the
**no-options** arm. Under the owner's PC20 settings the same board gives `mate 5` at 80,861.
Both are correct; my row cited one arm without naming its regime, which is exactly the
half-citation 07-C72 warns about. Corrected in the row.

## The rule this job is really about

**A refutation-grade instance beats a rate nobody can re-check.** The 6-of-20 rate requires
trusting a depth-12 re-search as referee; this case requires trusting nothing but the FEN, two
pawn moves, and a nine-ply line any board can play. When a claim has been revised downward twice,
the honest move is not a third rate — it is to find the one instance that does not need a rate.

## Files

- `job71/verify_f3.py` — the whole argument, re-runnable
- `job71/raw/verify_f3.json` — base vs PC20, PV replay, python-chess legality
- `job71/raw/f3_arms.json`, `job71/raw/f3_arms_replay.json` — three regimes, three PVs, all mate
- `job71/stamps.txt`

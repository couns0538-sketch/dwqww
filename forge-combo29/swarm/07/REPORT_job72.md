# REPORT job72 — which of my two faults is actually live on the PC build

Date: 2026-11-17 (see `job72/stamps.txt`)
Seat 07. Branch `for-fable-and-opus/swarm-07`.

## The question

Both my confirmed engine faults were demonstrated on the **base tree** — the old code, not the
branch the owner is shipping. A fault that only exists on the base tree is a historical note. So:
**do they survive on PC r15, and does the settings regime matter?**

Two builds × three regimes (none / S14 / PC20) × two faults = 12 cells, fresh process each,
Threads 1, Hash 16.

## Fault A — 07-F1's fabricated report

`go depth 12 searchmoves a1a8` on startpos: the move list contains no legal move, so the engine
reports without searching.

```
base/none    fabricated=12   pc/none    fabricated=12
base/S14     fabricated=12   pc/S14     fabricated=12
base/PC20    fabricated=12   pc/PC20    fabricated=12
```

**All six arms, identical: 12 lines (one per depth) and `bestmove 0000` throughout.** Not a base
defect, not a settings defect — **unfixed code on the branch the owner ships.** This is the one that
needs the shared-path patch.

## Fault B — the fifty-move declaration

Board `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1`. python-chess: 25 legal moves, **two pawn moves
(`b3b2`, `g3g2`)**, `is_fifty_moves()` **False** — not a fifty-move draw.

| arm | searched | score |
|---|---|---|
| base/any | **no** | `cp 0`, 0 nodes |
| pc/none | yes | `mate 6`, 15,981 |
| pc/S14 | yes | `mate 5`, 45,946 |
| pc/PC20 | yes | `mate 5`, 80,861 |

**The base answers `cp 0`/0 nodes in all three regimes; the PC build searches in all three and finds
mate.** `FORGE_FIX_ROOT_DRAWN` works and is settings-independent.

## The conclusion that matters

**Of my two confirmed engine defects, only one is live on the PC build.** 07-F3/F4 are *not* an
outstanding task — they are the justification for a fix that is already in the tree, and reporting
them as open would have sent the owner looking for work that is done. That is a reporting error I was
about to make, and it was only visible by testing the ship build instead of the base.

The general point: **"I found a defect" and "there is work to do" are different claims**, and the
second one requires testing the build that will actually run. A defect on the base tree is evidence
*for* a patch, not evidence of remaining work.

## Files

- `job72/pc_live.py` — both faults, both builds, three regimes, one harness
- `job72/raw/pc_live.json` — the 12 cells with verbatim score lines
- `job72/stamps.txt`

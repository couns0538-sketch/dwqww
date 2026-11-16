# job 10, items 1 and 2 — independent verdict, and the correction I must make

## CORRECTION FIRST (the coordinator is right and my job-9 sentence was wrong)

My job-9 report said "the base build scores the same two moves cp -1145 / cp -1174 and plays the better one", and used
that to argue the PC build was specifically at fault. **That sentence does not hold as a general claim**, and it was
produced by a settings mismatch of my own making: I measured the PC build under **PC20** but the base build under
**DEFAULT options**. Re-measured properly (`correction_check.txt`):

| settings | free choice (depth 18) | c6d6 alone | c6c7 alone |
|---|---|---|---|
| base, DEFAULT options | **c6d6**, cp -1112, 106,668 nodes (5/5 runs identical) | cp -1132 | cp -1157 |
| base, **S14** | **c6c7, mate -20**, 212,662 nodes | cp -1192 | mate -22 |

Under the PC's own search settings the **base tree makes the same wrong-move choice**. The other seat's numbers
(cp -1192, mate -22, mate -20) reproduce exactly on my machine under S14. So:
- **Withdrawn**: "the base build ranks them sanely" / "plays the better one", and the framing that this is a PC-build
  regression. It is **pre-existing in the shared search**, triggered by the S14/PC20 search settings.
- **Unchanged**: S-F16's core observation, because it was measured inside ONE build at ONE settings regime (PC build
  under PC20 plays a move it scores as a forced loss). That self-contradiction does not depend on any cross-build
  comparison.

## Item 1: independent verdict — by play-out, not by engine scores

`playout155.py`: after forcing each candidate move with python-chess, both sides are played by the engine and
python-chess decides the result. Engine scores are ignored entirely.

Engine: base build, S14 search settings (the 17 options that exe actually lists; the 5 PC20-only options are reported
as not sent), Threads 1, Hash 16, `go depth 12`, fresh process per move.

```
options sent: 17; not present in this exe and therefore NOT sent: ['CuckooRep', 'HistRework', 'TtPruneV2', 'CorrHistV2', 'MateAlphaGuard']

pair 1: c6d6 22 plies (black mates)   c6c7 20 plies (black mates)
pair 2: c6d6 22 plies (black mates)   c6c7 20 plies (black mates)
pair 3: c6d6 22 plies (black mates)   c6c7 20 plies (black mates)
```

**Verdict, decided by python-chess's rules and not by any score: `c6d6` is the better move.** Both moves lose (the
position is materially lost: lone white king against K+R+B+N), but c6d6 survives 22 plies and c6c7 survives 20, in
all three paired repeats, deterministically.

This matches the search's own verdict (c6d6 cp -1142..-1192 versus c6c7 mate -11..-22) — so the engine's evaluation is
right about which move is worse and its move choice is still wrong. That is the defect, stated without any cross-build
comparison.

## Item 2: is it resource-limited? (hash and depth tested)

Under S14, base build, depth 18, free choice:

| Hash | free choice |
|---|---|
| 16 | c6c7, mate -20, 212,662 nodes |
| 64 | c6c7, mate -20, 212,662 nodes |
| 256 | c6c7, mate -20, 212,662 nodes |
| 1024 | c6c7, mate -20, 212,662 nodes |

Byte-identical at every hash size — **the table is not the constraint here**.

| depth | free choice |
|---|---|
| 18 | c6c7, mate -20, 212,662 nodes |
| 19 | c6c7, mate -20, 236,252 |
| 20 | c6c7, mate -20, 262,671 |
| 21 | c6c7, mate -20, 343,379 |
| 22 | c6c7, mate -16, 429,922 |

**Depth does not rescue it either** — c6c7 at every depth to 22, and the score improves toward the truth (mate -16) while
the move stays wrong.

So on this position the choice is not sensitive to hash size or to an increased depth budget. That argues against a
pure "resource-limited search failure" in the sense of "give it more nodes and it will find it"; something about the
ordering at the root keeps the bad move first. The other seat's node asymmetry (21.4M for the correct move versus
407k for the wrong one) is consistent with this: the correct move needs a much deeper search to be PROVEN better, and
at equal depth the engine stops before paying that price. That is a real and different mechanism from "not enough
hash", and naming it needs the instrumented build (item 3 of the coordinator's list, next).

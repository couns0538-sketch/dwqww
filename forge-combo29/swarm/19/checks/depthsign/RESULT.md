# 19-C66 — 19-C44's "+3 ply at 20k" was 8× overstated per position, and half of all pairs are exact ties

## Result
PC r15 vs base, Threads 1, Hash 16, **130 real positions** (19-C44 used **six**):

| budget | PC20 deeper | **TIE** | shallower | ply sum | **ply/position** | wins/decided |
|---|---|---|---|---|---|---|
| `nodes 20000` | 44 | **65 (50.0 %)** | 21 | +8 | **+0.062** | **67.7 %** |
| `nodes 50000` | 46 | **55 (42.3 %)** | 29 | +4 | **+0.031** | **61.3 %** |

**19-C44's original: +3 ply over six positions = +0.500/position.** At n=130 the same comparison gives
**+0.062** — **an eight-fold overstatement of the per-position effect**, from the same six-position small-sample
failure that has recurred throughout this record.

## My three predictions, and how they did
1. **"Tie fraction 50–75 %"** → **50.0 %** at 20k. **Correct at the bound, and the mechanism was right: depth is an
   integer, so at a fixed node budget the two engines very often report the same number.** Trap 20 arriving on a
   different quantity, exactly as I expected.
2. **"+0.05 to +0.25 ply/position, and 19-C44 overstated the size"** → **+0.062**. **Correct.** The prediction
   worked here because I applied my own history rather than a mechanism intuition.
3. **"wins/decided 55–70 % for PC20"** → **67.7 %** at 20k, **61.3 %** at 50k. **Correct.**

## What the honest form of 19-C44 is now
**NOT** "PC20 reaches +3 ply at 20k". **The defensible statement is:**
> **At a fixed node budget PC20 reaches the same depth as S14 on about half of positions, deeper on about a third,
> and shallower on about a sixth — so it is deeper-or-equal on ~84 % of positions while averaging only +0.06 ply.**

**PC20 is not "deeper"; it is "rarely shallower".** Those are different claims and the second is what the data
supports.

## The caveat that survives
**The median depth difference is exactly 0.0 at both budgets**, with a small positive mean. So the effect lives
entirely in the tail of positions where PC20 gains a ply, while the typical position is unchanged. Anyone using
"+3 ply" to argue PC20 searches meaningfully deeper should use the share, not the sum.

Note also **depth range 7–64** — the 64s are the mate-inflated counters identified earlier in this run (19-C59's
finding that decided positions report inflated depth). Both engines hit them together, so they contribute ties and
do not bias the direction, but they are why the range looks absurd.

# The fifty-move root fault: bounded four ways, all resting on seat 07's original finding

seat 19 · area 9. Four independent angles on one fault. **Seat 07 found the fault (07-F4 → 07-C38 → 07-C75 →
07-C76); my contribution is the threshold precision, the settings-independence, the fix-side comparison, and the
severity measurement.**

## The fault, in one sentence

On the base tree, a root with halfmove counter **≥ 100** is declared drawn **without any search**, so the engine
returns an arbitrary first move instead of playing the position.

## The three-angle bound (the form for the FINAL)

> **Below counter 100 it cannot fire. At 100 and above it always fires, and the substitute move is not merely
> unscored — it is wrong. On PC r15 it never fires, under either settings regime.**

## 1. Threshold: exactly counter 100 (19-C37)

Mate-in-1 board `6k1/5ppp/8/8/8/8/5PPP/R5K1 w`, `go depth 12`, Threads 1, OwnBook false:

| counter | base 6b98f217 | PC r15 |
|---|---|---|
| 0, 50, 98, **99** | 252 nodes, **`mate 1`**, `a1a8` | 252 nodes, `mate 1`, `a1a8` |
| **100**, 101, 150, **9999** | **0 nodes, `cp 0`, `f2f3`** | 252 nodes, `mate 1`, `a1a8` |

**The 99 → 100 step is the cleanest demonstration:** one half-move of counter turns a *found mate* into a
*fabricated quiet move*. Testing at **9,999** as well as 100/101 is what makes "every counter at or above 100"
solid rather than extrapolated. This confirms seat 21's 21-F9 threshold claim exactly.

## 2. Settings-independent (19-C38)

The **same sweep under PC20** (all fifteen options: CuckooRep, HistRework 2, TtPruneV2, CorrHistV2,
MateAlphaGuard, OwnBook false, Hash 16) gives **byte-identical** results — every node count, every score, every
move. **So the fault lives in the drawn-root shortcut itself, not in any tunable: no configuration the owner can
send avoids it on the base build.**

## 3. The fix works, at every counter (19-C36)

PC r15 **searches** the counter-100 roots the base answers with 0 nodes:

| board | base | PC r15 |
|---|---|---|
| `8/6qk/8/8/8/1p4p1/4K3/8 b` | **0 nodes, `cp 0`** | **15,981 nodes, `mate 6`** |
| `6k1/5ppp/8/8/8/8/5PPP/R5K1 w` | **0 nodes, `cp 0`** | **252 nodes, `mate 1`** |
| `r3k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R3K2R w` | **0 nodes, `cp 0`** | **4,899 nodes, `cp 0`** |

`FORGE_FIX_ROOT_DRAWN` does what its name says — unlike `FORGE_FIX_ABORT_PUBLISH`, which defaults to 0 and does
not cover its own case (19-F25/19-F28).

## 4. Severity: a playing fault, not a reporting one (19-C39)

Counter 0 (real search) vs counter 100 (shortcut), same engine, `go depth 12`:

| board | counter 0 | counter 100 | nodes |
|---|---|---|---|
| `6k1/5ppp/8/8/8/8/5PPP/R5K1` | **`a1a8` (`mate 1`)** | **`f2f3` (`cp 0`)** | 252 → **0** |
| `r3k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R3K2R` | **`e1c1`** (castling, `cp 21`) | **`a2a3`** (`cp 0`) | 30,842 → **0** |
| `4k3/8/8/8/8/8/4P3/4K3` | **`e1f2` (`cp 369`)** | **`e2e3` (`cp 0`)** | 12,712 → **0** |

**It throws away a mate, loses castling rights, and gives up a three-pawn advantage — with zero nodes of work.**
Seat 07's 07-F4 reported "5 losses masked, 1 win thrown away"; this adds *why* the masked results were decisive
rather than marginal.

## 5. My error inside this, kept

The first severity attempt appended `- 0 1` to a FEN that already contained a counter, producing an **invalid
FEN**. All three boards then returned `e2e4` — **including from a KPvK ending, which cannot be right.**
**Three identical answers across three unrelated boards was the tell.** Same family as the "too clean" pattern:
uniform results across unrelated inputs mean the *input*, not the engine.

## 6. Attribution

- **Fault found, mechanism located, rate measured, and self-corrected twice: seat 07** (07-F4 → C38 tightened its
  own rate downward with a deeper reference → C75 reduced it to one hand-checkable case → C76 made it mechanical
  and 20-of-20). **That chain is the best self-correction I have seen in this swarm.**
- **Threshold at exactly 100: shared with seat 21's 21-F9**, confirmed precisely here.
- **My contribution: the threshold precision sweep, the settings-independence, the fix-side comparison, and the
  severity measurement.**

## 7. Files

`checks/fifty/RESULT.txt`, `counter_sweep.txt`, `threshold_pc20.txt`, `severity.txt`.

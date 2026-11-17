# RESOLUTION of the 389-vs-505 on the repetition door — seat 08, with a label defect found in my own script

Seat 27 reproduced my drawn-root matrix and flagged one number it could not reconcile: it measures PC **505 nodes** on
the repetition door where I reported **389**. The coordinator's reading was that 389 is S14-on-PC-r15 and 505 is
PC20.

**The coordinator's diagnosis of the CAUSE is right — the two figures are different option sets — but the LABEL
direction is the reverse of what was assumed, and the error is mine.** I checked rather than agreeing.

## The measurement, all four cells on the same board and move list

`g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8` (threefold), `go depth 4`:

| build | options | bestmove | nodes |
|---|---|---|---|
| base 6b98f217 | **S14 only** | a2a3 | **0** |
| **PC r15** | **S14 only** | d2d4 | **505** |
| PC r15 | PC20 (all 22) | d2d4 | **389** |
| v3 build | PC20 | d2d4 | 389 |

**So `505` is PC r15 under S14-ONLY and `389` is PC r15 under PC20 — seat 27's figure is the S14-only one, and mine was
the PC20 one.** Both are correct; they are different configurations measured on the same build, and the base cell
(`a2a3`, **0 nodes**) is identical in both harnesses, which is what proves the harnesses are otherwise the same.

## The defect in MY script, which is the real finding here
`pc20/check_repetition_root.py` names its option list **`S14`** but that list **contains the five PC20 switches**
(`CuckooRep`, `HistRework`, `TtPruneV2`, `CorrHistV2`, `MateAlphaGuard`) plus `OwnBook false`. So the script's own
variable name says S14 and its behaviour is PC20. **I then wrote "both builds, S14" into the finding line by trusting
the variable name rather than reading the list** — which is exactly the failure this run has been documenting all
night, and exactly the rule the coordinator has now put in one line:

> **A bare node figure names no search.**

**How the label was wrong matters more than that it was wrong:** I did not mis-measure anything. I read a variable
called `S14`, believed it, and published its name. The figure was right; its configuration was misdescribed.

## The fix, applied
The finding line for 08-C34 now states the full option list beside the figure: **"PC r15, S14 only, no PC20 switches"**
— and I have added the PC20 cell beside it so the two configurations are both visible rather than one substituted for
the other. Any reader can now reproduce either.

## What seat 27's other results add
- Its **counting convention** nearly made it reject my threefold claim: counting *returns to start* by move gives 2,
  where the initial position is occurrence **#1**, so the third occurrence is the second return. **That is a real trap
  and its preflight refusing to measure rather than producing a false refutation is the correct behaviour** — the same
  discipline as my own plant failing on the S-F22 board rather than lowering the threshold. A convention that
  undercounts by one would have refuted a true claim.
- Its severity reading matches my `a1b1` cell: **the base build loses an available mate**, not merely a worse move.
  Two independent harnesses agreeing on the severity, not just the count.

## The transferable line
**A node count is not a fact until it carries its configuration.** In this block I published a correct number with a
wrong label because I trusted a variable name — and the disagreement it caused cost another seat's time. The rule now
applies to my whole findings file: every node figure states its build AND its full option set.

## Show it again

    # the four cells above, one line each
    printf 'uci\n<option list>\nsetoption name Threads value 1\nsetoption name Hash value 16\nisready\nucinewgame\nisready\nposition startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8\nisready\ngo depth 4\n' | <exe>

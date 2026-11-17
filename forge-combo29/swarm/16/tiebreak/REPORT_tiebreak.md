# REPORT_tiebreak — ATTEMPT at the stated next step: score-based order with a mirror-invariant tie-break

> **THIS WAS AN ATTEMPT AT A FIX, AND IT DID NOT WORK FULLY. It is reported because the negative is what a reader
> needs before trying the same thing.** The full canonicalisation of S-F35 achieves symmetry by DISCARDING the
> tuned ordering, which costs strength. The obvious remedy is to keep the score-based ordering and break only TIES
> by a mirror-invariant key. **That reaches 7 of 15 cases, not 15 of 15.**

## The result

```
build                          pairs equal (5 positions x 3 depths)
base PC r15                             3 of 15
score-based + canonical TIE-BREAK       7 of 15
full canonicalisation (S-F35)          15 of 15
```

Per case, against both references:

```
 d |     base A/m |   tiebreak A/m | equal |  fullcanon A/m | equal
 1 |        67/74 |          65/65 |   YES |          68/68 |   YES
 2 |      164/135 |        161/157 |   no  |        133/133 |   YES
 3 |      256/407 |        243/234 |   no  |        219/219 |   YES
 1 |      155/165 |        163/163 |   YES |        156/156 |   YES
 2 |      217/226 |        223/224 |   no  |        218/218 |   YES
 3 |      289/295 |        293/293 |   YES |        288/288 |   YES
 1 |        87/75 |          87/75 |   no  |          79/79 |   YES
 2 |      141/129 |        141/129 |   no  |        133/133 |   YES
 3 |      219/209 |        220/210 |   no  |        214/214 |   YES
 1 |        12/12 |          12/12 |   YES |          12/12 |   YES
 2 |        32/32 |          32/32 |   YES |          34/34 |   YES
 3 |      174/166 |        177/169 |   no  |        132/132 |   YES
 1 |        20/20 |          20/20 |   YES |          20/20 |   YES
 2 |        67/42 |          43/43 |   YES |          64/64 |   YES
 3 |      140/107 |        164/163 |   no  |        143/143 |   YES
```

## Why it cannot work, and this is the useful part

**A tie-break only acts when two moves have EXACTLY equal scores.** The asymmetry, however, arises when two moves
have *different* scores on the two sides — or the same score but with a different set of moves explored before
them. Two mechanisms defeat the tie-break:

1. **Score ties are rare.** In most nodes the picker is not choosing between equal scores at all, so the tie rule is
   never consulted; the list order has already decided which move is examined first among *unequal* scores through
   the ordering's own dynamics (TT hit, SEE, history), and that ordering is not mirror-invariant.
2. **Even with equal scores, the canonical key only reorders the EQUAL group.** The set of moves reaching equal
   scores can itself differ between the two sides, because earlier nodes used order-dependent pruning.

So the tie-break reduces the asymmetry (3 → 7 of 15) without removing it. **Removing it requires the list ORDER to
correspond, which is what full canonicalisation does and what costs the strength.**

## What this means for the stated next step

In `REPORT_mirror_order.md` I wrote that a real fix would need "an ordering that is both score-based and
mirror-invariant — score every move, then break ties by the canonical key". **This experiment tests exactly that
formulation and shows it is insufficient.** The correct statement is narrower:

- **Symmetry** requires order correspondence at every tie AND at the pruning decisions (LMR, futility, SEE
  thresholds) that consume move order — not just at the final score comparison.
- **Strength** requires the tuned ordering.

Those two requirements collide at the pruning decisions, not at the tie-break. So there is no cheap
"score-then-canonical-tiebreak" fix, and the honest conclusion is that **the diagnostic (S-F35) is the deliverable;
a strength-preserving symmetry fix is not something I can produce, and the collision above is the reason.**

**How sure:** high on the counts (cold, Threads 1, PC20-equivalent base options, three builds compared in the same
run). High on the mechanism explanation: point 1 is directly observable in the data — most pairs that stay unequal
have DIFFERENT node totals, which cannot come from a tie rule.

## Honesty numbers

```
base      /home/ubuntu/builds/bld-pc/forge      none 312866 / S14 242796 / PC20 278024  (all match file 5)
tiebreak  /home/ubuntu/builds/bld-tbk/forge     = PC r15 + EXPERIMENT_tiebreak.patch.txt
          -DFORGE_EXPERIMENT_TIEBREAK_CANON=1   EXPERIMENT: bench pins not claimed (the tie rule changes the tree)
fullcanon /home/ubuntu/builds/bld-mirord3/forge = S-F35's build, for reference
settings  Threads 1, Hash 16, OwnBook false, cold per search
```

Patch is TEXT only: `EXPERIMENT_tiebreak.patch.txt`, applies with `patch -p2`. The switch defaults to 0, so a
build of this patch without the flag is the PC engine unchanged. Note: when the switch is ON the AVX2 lane
shortcut in `pick_best` is compiled out, so the scalar tie rule governs — otherwise an equal-scored group inside a
4-lane chunk would still take the first-in-lane.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| tie-break switch implemented (score order preserved) | done | `EXPERIMENT_tiebreak.patch.txt` | builds, applies clean |
| 5 positions x 3 depths vs base and full-canon | done | `raw_tiebreak.txt` | 3 / 7 / 15 of 15 |
| explain why it cannot reach 15 | done | this report | ties are rare; unequal-score order still leaks |
| a formulation that satisfies both goals | NOT produced | — | the collision is at pruning decisions, not ties |

## Findings

`S-F36 | 6 | the "score-based order with a mirror-invariant tie-break" fix — the cheap version of S-F35's canonicalisation — does NOT achieve symmetry: it reaches 7 of 15 cases against the base build's 3, while full canonicalisation reaches 15 of 15. The reason is structural: a tie-break acts only when two moves score EXACTLY equal, whereas the asymmetry also arises among UNEQUAL scores through order-dependent pruning (LMR, futility, SEE thresholds), which a tie rule never touches. So the diagnostic (S-F35) is the deliverable and a strength-preserving symmetry fix collides at the pruning decisions, not at the tie-break | tiebreak/raw_tiebreak.txt tiebreak/EXPERIMENT_tiebreak.patch.txt | NEW |`

## Suspicions, not proven

- That no ordering-only fix can satisfy both goals. I have shown one plausible formulation fails and given the
  mechanism; I have not proven impossibility.

## What I did NOT do

- Did not try a formulation that also canonicalises the pruning decisions, which is where the collision is. That
  would be a much larger change to the search and it is the honest next step if anyone wants a real fix.
- Did not measure strength (games), only node counts and symmetry.

## Times

`tiebreak/stamps.txt`, every line a `date -u`.

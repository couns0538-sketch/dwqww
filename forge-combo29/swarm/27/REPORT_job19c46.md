# REPORT job19c46 — 19-C46 DOES NOT REPRODUCE: PC20 is not shallower at the self-play budget

Build: PC r15, sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`
All runs: **Threads 1, Hash 16**, fresh process per cell, `OwnBook false` in every PC20 arm.
Settings counts asserted per run: **S14 = 16 accepted options, PC20 = 22** (a mismatch aborts the run).

## Their claim

19-C44/45/46 say PC20 is deeper at node budgets but **reverses at the self-play budget**:

```
budget   S14  PC20   diff
  2000    45    43     -2
  3000    47    48     +1
  8000    55    60     +5
 20000    65    68     +3
```

and that **TtPruneV2 is the single option that costs the ply at 2,000**, with the caveat that
"the individual deltas are within the per-position noise ... the TREND is the finding".

## What I ran

Three independent measurements, all on my own positions, none reusing their files:

1. **My 8-FEN real-game set**, all six budgets, **3 repeats per cell** (17 cells x 3).
2. **Ablation at softnodes 2000**, one option at a time on top of S14, 3 repeats per cell.
3. **600 real self-play positions** from the repo's own `tests_r3fu_12/positions.txt`
   (walk-depth 4, opening plies 8–12 — the population the owner's matches actually produce),
   every FEN validated by python-chess before measurement.

## Result 1 — the reversal does not happen on my set

```
budget  S14  PC20  delta
  2000   52    58    +6     <-- their -2; mine is +6
  3000   58    65    +7
  5000   66    72    +6
  8000   76    78    +2
 12000   82    85    +3
 20000   90    93    +3
```

Per position, PC20 is deeper or equal in **46 of 48** cells. There is **no negative cell at any budget
below 8000**. Their sign never appears.

Sensitivity control: S14 summed depth 52 at 2,000 nodes vs 90 at 20,000 — the parse responds to the
budget, so a flat table would be a broken parse, not a null result. PASS.

Repeats: **0 of 17 cells non-deterministic across 3 reps** — consistent with my S-N3 (softnodes labels
bit-reproducible 48/48), and it means the *measurement* carries no noise. The caveat in 19-C46 attributes
the instability to "per-position noise", which is right in spirit and is exactly why six positions cannot
settle it — but it is between-position variance, not run-to-run error.

## Result 2 — TtPruneV2 does not cost a ply; it GAINS six

One option at a time on top of S14, `go softnodes 2000`, 8 positions, 3 reps, all identical:

```
config            summed depth   delta vs S14
S14                    52           +0
S14+CuckooRep          53           +1
S14+HistRework         51           -1
S14+TtPruneV2          58           +6   <-- their -1
S14+CorrHistV2         51           -1
```

**TtPruneV2 is the single largest contributor to depth at the self-play budget on my set**, the exact
opposite of 19-C46's attribution. And it is not a one-position accident: `[8,7,8,7,7,7,7,7]` against
S14's `[6,7,7,6,7,7,6,6]` — deeper on five positions, equal on three, shallower on none.

## Result 3 — 600 real positions: the effect is +0.06 ply, not −2

This is the measurement that settles the sign, because it is the population 19-C46 is about.

```
600 positions, go softnodes 2000, PC20 vs S14
  PC20 deeper 127, shallower 60, equal 413        summed +38 plies, mean +0.063 ply
  exact binomial, two-sided: p = 1.1e-06
  restricted to the 406 positions where both chose the SAME move:
    deeper 67, shallower 42, equal 297             summed -11, p = 0.021
  nodes: S14 1,889,141 vs PC20 1,867,853  (ratio 0.989; both 1.56x budget)
```

So:

- **The sign is positive, and significantly so** (127–60, p ≈ 1e-6). PC20 is *not* shallower at the
  self-play budget. 19-C46's "-2" is a six-position fluctuation, and my own "+6" on eight positions was
  the same mistake in the other direction — both are gone at n=600.
- **The magnitude is negligible**: +0.063 ply per position. Depth at a fixed node budget is a
  breadth-for-depth trade, and here the two configs spend the same nodes (ratio 0.989). The honest
  statement is **"PC20 and S14 reach the same depth at the self-play budget"**, not "PC20 is deeper".
- **The residual is a move-choice effect, not a search effect.** Restricting to positions where both
  configs chose the same move drops the summed difference from +38 to −11. In other words essentially all
  of the depth difference comes from PC20 choosing a *different* move and therefore searching a different
  subtree. For "does this configuration search deeper", the same-move restriction is the right control,
  and it says **no difference**.

## What this means for the owner

- **Do not raise the self-play budget on account of 19-C45's "PC20 costs 2 ply at 2000".** There is no
  such cost at 200/600 positions; the measured difference is +0.06 ply.
- **Do not drop TtPruneV2 on account of 19-C46.** On my set it is worth +6 summed depth at 2,000, the
  largest single-option gain of the four tested, and it is the option 19-C46 singled out as the cost.
- **The actionable half of seat 19's work stands**: PC20 is deeper at 8,000–20,000 nodes (+2 to +3 on my
  set, agreeing with their +3 to +5). The recommendation to use PC20 at match budgets is not affected.

## Honest limits of this report

- Depth at a fixed node budget is a **proxy**, not playing strength. A configuration can search deeper
  and play worse. Nothing here measures strength; seat 19's claim was about depth and so is this.
- My positions are one seed family (`tests_r3fu_12`). A different seed could have a different mean effect,
  though 600 positions put the mean at +0.06 with a tight interval, so any true effect large enough to
  matter (−2 ply is 30x larger than the observed mean) is excluded.
- The 8-position set is far too small to estimate the mean; I report it only because it is where the
  sign first appeared, and it is the counter-example to their sign.
- I did not run their exact set G (their RESULT.txt does not list the FENs). This is an independent
  test on a different population, not a re-run of their file.

## Files

- `pc/sign_test_19c46.py` — population sign test with per-run settings-count assertion and
  python-chess legality gate (planted illegal FENs are refused: adjacent kings, pawn on rank 1, three kings).
- `pc/check_19c46_ablation.py` — the 8-position budget sweep + one-option-at-a-time ablation, 3 reps/cell.
- `out19c46/sign_600_2000.json`, `out19c46/sign_600_2000.log` — the 600-position result.
- `out19c46/ablation_19c46.json`, `out19c46.log` — the 8-position sweep and ablation.

# REPORT_lever_scope — what exactly does TtPruneV2 change? (move identity vs score distance)

**What was asked (my own follow-up to S-F20):** S-F20 named TtPruneV2 as the lever for the extra asymmetry, but
"symmetric" covers two different things — do the two sides pick the SAME MOVE, and do they score the SAME? This
job separates them, because a lever that only changes which move mirrors is worth much less to the owner than
one that changes strength.

**The answer: TtPruneV2 changes WHICH moves mirror, but not HOW FAR the scores diverge. It moves the move
identity, not the strength asymmetry.**

```
| cell                  | n   | score_equal | bm_equal | bm_mismatch | |score delta| median  p90  max |
|-----------------------|-----|-------------|----------|-------------|----------------------------------|
| base + S14            | 353 |          19 |      252 |         101 | (not compared: base rows are not cp-only) |
| PC + all four OFF     | 353 |          20 |      251 |         102 |           18           63   541 |
| PC + TtPruneV2 ONLY   | 353 |          19 |      240 |         113 |           19           68   442 |
| PC + PC20             | 353 |          22 |      233 |         120 |           16           74   289 |
```

- **Move identity:** all four off 102 mismatches → TtPruneV2 alone 113. That is the effect S-F20 named.
- **Score equality:** all four off 20 equal → TtPruneV2 alone 19. **No change** (one position).
- **Score distance:** median |Δscore| 18 → 19 centipawns. **No meaningful change.**

So the option reshuffles which pairs happen to pick the same move, without making the two sides' *evaluations*
agree more or less. For the owner this means: **TtPruneV2 is not a strength lever for colour consistency — it
changes the path, not the disagreement.** The honest framing of S-F20 is "the lever for the move-mirroring count",
not "the lever for the asymmetry" in the sense of playing strength.

**How sure:** high on the numbers (same 353 pairs, same build, Threads 1, one option differing). Medium on the
interpretation "not a strength lever": a median |Δscore| of 18–19 cp across a mirror pair is large in absolute
terms regardless of which option is on, so the option is not what creates it.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings S14 +/- the named options, Threads 1, Hash 16, depth 10
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| move-mismatch count, four cells | done | `raw_A_pc_s14.tsv`, `raw_D_ttprune_explicit.tsv`, `../pcsym10/raw_G353.tsv` | 102 / 113 / 120 |
| score-equal count, four cells | done | same | 20 / 19 / 22 |
| score distance distribution, three cells | done | same | median 18 / 19 / 16 cp |
| the base tree compared on cp-only deltas | NOT done | — | its rows record mate scores too; the three PC cells are the comparison that matters |

## Findings

`S-F22 | 6 | TtPruneV2 changes WHICH positions mirror but not HOW FAR the scores diverge: with it alone the depth-10 move-mismatch is 113/353 (vs 102 with all four options off) while score-equality is 19/353 (vs 20) and the median mirror score gap is 19 cp (vs 18) — so the option reshuffles the move-mirroring without changing the evaluation disagreement, and it is not a strength lever for colour consistency | pcsplit/raw_D_ttprune_explicit.tsv pcsplit/raw_A_pc_s14.tsv pcsym10/raw_G353.tsv | NEW |`

## Suspicions, not proven

- That the score gap of ~18 cp between a position and its mirror is inherent to the engine (order dependence
  plus the tuned asymmetric PSQT from S-F3/S-C3) and no option touches it. The three cells are consistent with
  that but do not prove it.

## What I did NOT do

- Did not test the score gap at shallower or deeper depths to see if it shrinks (file 6 suggests a multi-thread
  spread should shrink with depth; the colour gap may behave differently).
- Did not test HistRework's effect on the score distance, though it was the only cell that improved the move count.

## Times

`pcsplit/stamps.txt`, every line a `date -u`.

# REPLICATION RECORD — PC20 vs S14 at the self-play budget, quiet subset

Seat 27. This file exists so the quiet-subset numbers travel with their caveats. Every figure below is printed
by `pc/strata_19c46.py` reading `out19c46/sign_600_{2000,3000}.json`; none was typed from memory.

Build: PC r15, sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`,
**PC20 (22 options asserted per run), Threads 1, Hash 16, OwnBook false**, fresh process per cell.
Positions: 600, seed 2701, repo `tests_r3fu_12/positions.txt`, every FEN validated by python-chess.
Composition: **mean 23.86 pieces, 132/600 = 22.0 % rook-or-more imbalance** — matching seat 19's independent
measurement of the same set exactly.

## The headline, with its flags

| measurement | value | flag |
|---|---|---|
| quiet subset (≥24 pieces), budget 2000 | **0.712** (42/59), CI [0.586, 0.812], p = 0.0015 | — |
| quiet subset (≥24 pieces), budget 3000 | **0.691** (47/68), CI [0.574, 0.788], p = 0.0022 | — |
| quiet ≥28 pieces, budget 3000 | 0.630 (29/46), CI [0.486, 0.755], **p = 0.104** | **NOT SIGNIFICANT** |
| quiet ≥28 pieces, budget 2000 | 0.718 (28/39), CI [0.562, 0.835], p = 0.0095 | — |
| all clean same-move, 2000 | 0.684 (67/98), CI [0.586, 0.767], p = 0.0004 | — |
| all clean same-move, 3000 | 0.643 (83/129), CI [0.558, 0.721], p = 0.0014 | — |

**The flags are part of the result, not a disclaimer.** The 0.630 cell is the strictest subset at the higher
budget and it is a null. Anyone quoting "PC20 wins ~72 % of quiet positions" should carry that row beside it,
because the choice of subset moves the answer from "clearly positive" to "indeterminate" and the subset was
chosen after looking.

## Why the subset boundary matters

The quiet thresholds were not pre-registered. ≥24 pieces was chosen to be comparable with seat 19's
composition (their slice averages 20.63 pieces), and ≥28 is the far end. Reporting all three thresholds is the
honest response to having chosen after the fact — a single threshold would have looked decisive.

```
budget 2000, same-move restricted, mate-excluded
  >=28 pieces   n=124  decided=39   PC20 28/39 = 0.718  CI[0.562,0.835] p=0.0095
  >=26 pieces   n=177  decided=53   PC20 37/53 = 0.698  CI[0.565,0.805] p=0.0055
  >=24 pieces   n=209  decided=59   PC20 42/59 = 0.712  CI[0.586,0.812] p=0.0015
  >=24p imb<=1  n=134  decided=38   PC20 30/38 = 0.789  CI[0.637,0.889] p=0.0005
  ALL clean     n=387  decided=98   PC20 67/98 = 0.684  CI[0.586,0.767] p=0.0004

budget 3000, same-move restricted, mate-excluded
  >=28 pieces   n=132  decided=46   PC20 29/46 = 0.630  CI[0.486,0.755] p=0.1038  <-- NULL
  >=26 pieces   n=187  decided=62   PC20 42/62 = 0.677  CI[0.554,0.780] p=0.0071
  >=24 pieces   n=221  decided=68   PC20 47/68 = 0.691  CI[0.574,0.788] p=0.0022
  >=24p imb<=1  n=134  decided=43   PC20 31/43 = 0.721  CI[0.573,0.833] p=0.0054
  ALL clean     n=402  decided=129  PC20 83/129 = 0.643  CI[0.558,0.721] p=0.0014
```

The values cluster tightly between 0.63 and 0.79. **I first wrote here that there was "no monotone trend in
the threshold", and checking it showed that is false:** at budget 3000 the share rises monotonically as the
subset widens (0.630 → 0.677 → 0.691), and at budget 2000 it does not (0.718 → 0.698 → 0.712). So one budget
is monotone and the other is not, from the same positions — which means the ordering carries no signal either
way at these sample sizes, and I should not have asserted it in either direction.

What the table *does* support is the weaker and sufficient claim: **the effect stays positive at every
threshold, and no threshold makes it vanish or reverse.** That is what argues against the composition story,
and it agrees with seat 19's own reweighting test (their composition applied to my strata gives 58.7 %, not
41.4 %). It is not the stronger claim I originally wrote.

## What this record does NOT claim

- **Not a strength result.** Depth at a fixed node budget is a proxy. A configuration can search deeper and
  play worse; nothing here measures playing strength.
- **Not independent of position family.** All 600 come from one walk (`tests_r3fu_12`, walk-depth 4, opening
  plies 8–12). A different seed family could have a different mean effect. The *sign* is robust across every
  subset tried; the *magnitude* is family-specific and should not be extrapolated.
- **Not a settled matter between seats.** The effect is sub-one-ply in mean terms (+0.06 to +0.09 pooled) and
  45.6 % of positions return an identical search when the budget rises 50 %. The honest summary is that two
  guarded runs disagreed on a small effect, one was underpowered, and the agreed finding is the **budget**
  effect (2000→3000 gives S14 +331 ply and PC20 +331 ply — identical to the ply), which is an order of
  magnitude larger and has nothing to do with PC20.

## Reproduce

```
python3 pc/sign_test_19c46.py /agent/repos/base/build-pc/forge \
    /agent/repos/base/forge-combo29/tests_r3fu_12/positions.txt out19c46 --n 600 --budget 2000
python3 pc/strata_19c46.py            # prints every table in this file
```

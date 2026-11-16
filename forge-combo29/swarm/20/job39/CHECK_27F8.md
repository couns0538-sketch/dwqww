# seat 20 — job 39: seat 27's S-F8 chain at Threads 1 — the qualitative claim holds, the quoted numbers are a
# DIFFERENT SETTINGS REGIME, and the sign is unstable exactly as their own S-F8b says

Queue short-list entry. Seat 27's S-F8: "the restriction also changes the SCORE the engine reports. Startpos,
depth 12, **S14**: `go depth 12` gives cp 30 / 56720 nodes, `searchmoves e2e4` gives cp 23 / 26329,
`searchmoves e2e4 d2d4` gives cp 23 / 16770, all playing e2e4."

All rows below: `Threads 1`, fresh process per run, 3 runs per cell, startpos, `go depth 12`.

## The finding that matters most: their "S14" numbers are actually DEFAULT-settings numbers

| settings | `go depth 12` unrestricted |
|---|---|
| **no setoption at all** | `e2e4` / **`cp 30`** / **`56720` nodes** |
| `Threads 1` + `Hash 16` only | `e2e4` / `cp 30` / `56720` nodes |
| **S14 (all 14 options)** | `d2d4` / **`cp 24`** / **`22459` nodes** |

`cp 30 / 56720 nodes` is exactly the **default-settings** answer — the same figure seat 19 published for a plain
`go depth 12`. Under real S14 the unrestricted answer is `d2d4 / cp 24 / 22459`. So S-F8's headline triple is a
comparison of **restricted-S14 searches against an unrestricted-DEFAULT search**, and the 7 cp "gap" it reports is
partly a settings mismatch, not a restriction effect.

This is precisely the regime rule of Opus's file 4 (pins are default numbers, sums are S14 numbers). I did **not**
accuse seat 27 of anything: their line says "S14", so the label is what is wrong, and the correction is one line.

## The qualitative claim DOES hold, in both directions

| build | command | bestmove | score | nodes |
|---|---|---|---|---|
| base + S14 | `go depth 12` | d2d4 | cp 24 | 22,459 |
| base + S14 | `… searchmoves e2e4` | e2e4 | **cp 28** | 15,392 |
| base + S14 | `… searchmoves e2e4 d2d4` | e2e4 | **cp 28** | 28,909 |
| PC r15 + PC20 | `go depth 12` | d2d4 | cp 25 | 21,600 |
| PC r15 + PC20 | `… searchmoves e2e4` | e2e4 | **cp 32** | 15,577 |
| PC r15 + PC20 | `… searchmoves e2e4 d2d4` | **d2d4** | **cp 24** | 19,755 |

- A `searchmoves` restriction **changes the reported score** on both builds (24 / 28 / 28 vs 25 / 32 / 24).
- **The sign is unstable**: on the base tree the restricted score is 4 cp HIGHER than unrestricted; seat 27's S-F8b
  reports it 4–8 cp LOWER depending on `IirDepth`. I reproduce their instability, not their specific numbers.
- **On the PC build the two-move restriction returns the unrestricted move and a near-identical score**
  (d2d4 / cp 24 vs cp 25), i.e. the effect is much smaller there — worth knowing, and not something seat 27 tested
  (their work predates the PC build being available).

## Verdict
- **CONFIRMS** the substance of S-F8/S-F8b (a restriction perturbs the score, and the perturbation is not
  explained by IIR alone) on the base tree and on the PC build, `Threads 1`.
- **CORRECTS** the quoted numbers: `cp 30 / 56720` is the DEFAULT-settings unrestricted answer, not S14.
- **ADDS**: on the PC build under PC20 the effect nearly vanishes for the two-move restriction.
- S-F8 remains **OPEN** as they say; I have not found the third cause either.

## Limits
- Startpos only, one depth, one position; `Threads 1` only.
- I did not build their `searchmoves_iir.PARTIAL.patch.txt`, so I cannot say whether their IIR patch recovers what
  they report.
- 3 runs per cell; every cell was identical across its 3 runs, so the numbers above are stable at Threads 1.

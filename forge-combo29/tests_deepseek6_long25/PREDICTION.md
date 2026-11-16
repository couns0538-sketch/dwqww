# deepseek6 long 25 — PREDICTION (written before the first build command)

Item (file 7, long 25): **Depth 14 rows on O for V, CED 8 alone, T1 and T2** (known: S14 depth 14 on O =
21,812,100).

Model: DeepSeek V4.1 Flash 1017. Time written: see `stamps.txt`, first line.

## Configurations (definitions fixed here so the report cannot redefine them)

| tag | configuration |
|---|---|
| S14 | the fourteen options of the standing text at their S14 values (pin 21,812,100 at depth 14) |
| V | S14 + `CheckExtensionDepth 8` + `LmrGiveCheck 0` + `LmrInCheck 0` |
| CED8 | S14 + `CheckExtensionDepth 8`, nothing else changed |
| T1 | B_FINE at `LmrFine 1` + `LmrFineHistory 1` + `LmrRoundF 512`, S14 options unchanged |
| T2 | B_FINE at `LmrFine 1` + `LmrFineHistory 1` + `LmrRoundF 0`, S14 options unchanged |

Builds needed, three: (i) plain base 6b98f217 for S14/CED8 and, with the B10 `ChecksLmr` patch (d33b27ca) that
carries both check options, for V; (ii) the kimi5 `LmrFine` patch (sha256 f7bf3f43…) alone for T1/T2. The B10
patch is the source the known V sums were measured on (my long 18), so V must come from it, not from kimi5's
`LmrGiveCheck` (0e5b0375…, redundant with it).

## Predictions, each with the range that kills it

**P1 — the S14 pin.** S14 at depth 14 on O sums to **21,812,100** exactly. Kill range: any other sum. This is a
pin, not a guess: a different sum means the wrong binary and the whole item stops there.

**P2 — CED 8 at depth 14 on O = 16,900,000 ± 900,000.** Reasoning: at depth 12, CED 8's O sum is 9,015,167
against S14's 9,500,069 (ratio 0.9490). An extension that deepens the tree costs nodes, but CED 8's *net* effect
is a smaller tree at 12; extrapolating a depth-12 ratio to depth 14 is the weak step, so the range is wide on
purpose. Kill range: outside 16.0 M to 17.8 M kills P2.

**P3 — V at depth 14 on O = 16,000,000 ± 900,000, and V < CED 8.** At depth 12 V/CED8 = 8,565,026/9,015,167 =
0.9501. Kill ranges: V outside 15.1 M to 16.9 M kills P3's level; V not strictly below CED 8 at depth 14 kills
P3's ordering.

**P4 — the depth-14 ratios are CLOSER to 1 than the depth-12 ratios, for both V and CED 8.** i.e.
V₁₄/S14₁₄ > 0.9017 and CED8₁₄/S14₁₄ > 0.9490. Reasoning: the extension adds a ply of search at checked nodes,
and its relative saving should shrink as the base search gets deeper and the check rate per node falls. This is
the prediction I am least sure of, and it is the interesting one: if it fails, the extension gets *more*
valuable with depth, which is a stronger result than anything in my long 18. Kill range: either ratio at or
below its depth-12 value kills P4 for that arm.

**P5 — T1 and T2 at depth 14 on O bracket S14, with T2 above and T1 below.** Depth-12 anchors: T2 11,915,365
(1.2542 × S14), T1 10,170,054 (1.0705 × S14). Prediction: T2₁₄ ∈ [23.0 M, 30.0 M] and T1₁₄ ∈ [21.0 M, 25.5 M],
with T1₁₄ < T2₁₄. Kill ranges: outside those bands, or T1 ≥ T2, kills P5.

**P6 — T1 at depth 14 is below S14's ratio-implied value only if RoundF's effect grows with depth.** Explicitly:
T1₁₄/S14₁₄ ∈ [0.96, 1.22]. Kill range: outside kills P6.

**P7 — best-move churn against S14 at depth 14 is smaller than at depth 12 for all four configurations.**
Depth-12 churn (my long 18 and long 21 rows) was: V 141 of 200, CED8 133, T1 143, T2 143 against S14. Prediction:
each of the four is **≤ 130 of 200** at depth 14, because a deeper search converges. Kill range: any value above
130 kills P7 for that configuration.

**P8 — the run cost.** One depth-14 O run (200 positions, Threads 1, Hash 16) takes 150–900 s on this 4-core VM,
so five runs fit inside the item's 60-minute budget only if they are run in parallel two at a time with each
process single-threaded. Kill range: if a single run exceeds 1200 s I say so and run them serially, reporting the
part done.

## What would make me report "not done"
A build that does not reproduce the four honesty pins, or a run that refuses an option name (the engine's line
goes into the report and that configuration is "refused", not guessed). A depth-14 run I cannot finish inside
the budget becomes the first step of the next item, said plainly in the report.

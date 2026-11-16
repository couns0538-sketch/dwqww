# seat 20 — check of seat 06's S-F1 (`eval` is exactly colour-symmetric)

Verdict: **CONFIRMS seat 06's S-F1** — and only after correcting a convention error of my own that first produced
120 false asymmetries.

Raw: `out_symmetry.txt` (the pasted run), `check_s06f1b.json` (every pair as data), `convention.txt` (the
measurement that fixed the sign convention), `out_check_WRONG_convention.txt` (my first, wrong run, kept on
record). Script: `check_s06f1b.py`.

## The convention, established before judging anything

| board | side to move | `eval` |
|---|---|---|
| `4k3/8/8/8/8/8/8/QQQQK3` (4 white queens) | white | hce 4211 nnue 228 total 4439 |
| same board | black (illegal, but parsed) | hce -4182 nnue 662 total -3520 |
| `qqqqk3/8/8/8/8/8/8/4K3` (4 black queens) | black | hce 4211 nnue 228 total 4439 |

So `eval` is **side-to-move relative**: the same advantage reads the same number whoever holds it. Colour symmetry
therefore means `eval(position) == eval(mirror(position))`, **not** the negation. My first script asserted the
negation and "found" 120 asymmetries that were entirely my error; that run is kept as
`out_check_WRONG_convention.txt` rather than deleted.

## The result (120 positions x 3 configurations = 360 pairs)

| config | pairs | symmetric | asymmetric | max abs diff (hce / nnue / total) |
|---|---|---|---|---|
| default | 120 | **120** | 0 | 0 / 0 / 0 |
| `UseNNUE false` | 120 | **120** | 0 | 0 / 0 / 0 |
| `DeadMaterial true` | 120 | **120** | 0 | 0 / 0 / 0 |

Positions: 60 from my own seeded legal walk (`Random(2001)`, one every 5 plies) + 60 from the shared O set
(`tests_kimi5_job3/first200.fens`, first 60), read from `O_first60.fens` which is committed with this check.

Controls, both passing:
- the same position evaluated twice: equal (`84/32/116` both times);
- a deliberately DIFFERENT position: `116` vs `-52`, so the harness sees a change and is not blind.

## Why this matters
A checker that assumes left-right or colour symmetry of `eval`, or that "corrects" a mirrored score by negating,
will misread the engine. Seat 06's finding is the safe statement: **the static eval is exactly colour-symmetric
under the engine's own side-to-move convention.**

## Where my predictions went
Predictions 1 and 2 held once the convention was right. Prediction 3 held (`UseNNUE false` changes the numbers —
hce-only values differ from nnue-loaded ones across the sample; the configs are genuinely different).
Prediction 4 held (`DeadMaterial` is a real check option; confirmed in the `uci` answer). Prediction 5 was
**not testable under the right convention** — since hce and nnue are both exactly symmetric, there is no asymmetry
to attribute to either — and I do not claim it.

## What I did NOT do
- I did not reproduce seat 06's exact 8,103 pairs or their four configs exactly (they had a "dead-material set"
  position list; I used `DeadMaterial true` over my positions instead).
- I did not test in-check positions in depth; my sample contains few, and `incheck` is printed but I did not
  stratify on it.
- I did not test left-right symmetry (that is seat 06's S-F3/S-F4, a different axis).

## What I am NOT sure about
- Whether the equality survives positions where the side to move is in check for one board and not the other
  (impossible for a true mirror, so this should be vacuous, but I did not build such a case deliberately).

## Commands that show it again
```
python3 check_s06f1b.py /agent/repos/build-base/forge /tmp/o forge-combo29/swarm/20/job9/O_first60.fens
printf 'uci\nisready\nposition fen 4k3/8/8/8/8/8/8/QQQQK3 w - - 0 1\neval\nquit\n' | ./forge
printf 'uci\nisready\nposition fen qqqqk3/8/8/8/8/8/8/4K3 b - - 0 1\neval\nquit\n' | ./forge
```

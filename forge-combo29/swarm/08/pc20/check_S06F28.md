# CHECK of seat 06's S-F28 — the four PC20 switches do not cause the colour-mirror asymmetry — seat 08

Their finding:
> S-F28: "the FOUR NEW PC20 SEARCH SWITCHES do NOT cause the asymmetry: on the PC r15 build with the same 353 pairs at
> depth 10/Threads 1, switches OFF (S14 only) gives 102/353 = 28.9 % bestmoves ... the base tree's 28.6 % within a
> point — and switches ON gives the same rate."

## Verdict: CONFIRMS, at a smaller sample (60 pairs per config)

My own harness (`check_s06f28.py`): for each position and its **colour mirror** (`board.mirror()`), `go depth 10`,
then check whether the two bestmoves are mirror-equivalent and whether the scores are equal. Base and PC builds,
Threads 1, Hash 16, `OwnBook false` everywhere.

| config | pairs | bestmoves not mirrored | rate | scores unequal | rate |
|---|---|---|---|---|---|
| base 6b98f217, S14 (reference) | 60 | 14 | **23.3 %** | 60 | **100 %** |
| **PC r15, S14 only (four switches OFF)** | 60 | 16 | **26.7 %** | 60 | **100 %** |
| **PC r15, S14 + the four switches ON** | 60 | 21 | **35.0 %** | 58 | 96.7 % |
| PC r15, PC20 full bundle | 60 | 21 | **35.0 %** | 57 | 95.0 % |

| their question | my measurement |
|---|---|
| the asymmetry is present on the PC build at a rate like the base tree's | **yes — 26.7 % (PC, switches off) against 23.3 % (base)** |
| turning the four switches ON does not cause it | **yes — 35.0 % against 26.7 %, a difference of +8.3 points, well inside the ±12-point interval a 60-pair sample allows at a ~30 % rate** |
| the score asymmetry is near-total on every config | **yes — 96.7–100 % unequal scores on all four configs, including the base build** |

So the direction of their conclusion holds: **the four search switches do not account for the colour-mirror
asymmetry**, which is present at essentially the same level with them off, and near-totally present in the SCORES on
every configuration including the base tree.

## What I do NOT claim
- **Not a reproduction of their counts.** 60 pairs against their 353; my rates (23.3 / 26.7 / 35.0) are not their
  numbers (28.6 / 28.9). I am checking the LEVEL of the rate and the OFF-vs-ON difference, not their exact figures.
- **The ON rate is nominally higher (+8.3 points).** With 60 pairs that is inside noise, so I do not call it an
  effect — but I also cannot exclude one, and I say so rather than reporting "identical".
- I did not test the six possible individual-switch combinations; I tested the four together (their claim) and the
  full PC20 bundle for reference.

## Why this check was worth making
It is the one finding in seat 06's list that would tell the owner something actionable about the PC build's settings:
whether turning on the four new search switches introduces a colour asymmetry. The answer is no — the asymmetry is
there either way, and it is near-total in the scores even on the base tree, so it is not a PC20 artefact.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s06f28.py /tmp/s06f28.txt

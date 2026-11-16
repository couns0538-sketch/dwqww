# REPORT — seat 07, job 39: tightening the fifty-move rate with a deeper reference

## What was asked / the answer / how sure

**Asked:** take the 6 decisive plus the 10 inconclusive fifty-move positions, run the reset-counter
reference at depth 16 or 18 instead of 12, and report how many of the 10 become decisive — tightening
"6 of 20" toward the truth.

**Answer:** **the rate gets smaller, not larger: 5 of 20 (25 %), with 1 of 20 a thrown-away win.** None
of the 10 inconclusive positions became decisive at depth 18, and one position that *was* decisive at
depth 12 turned out to be a **depth-12 artefact**.

**How sure:** higher than 07-F4, because I ran depths 12/16/20/24 on the positions that matter and the
classification is stable from 18 upward. Thresholds (±300 cp or any mate) were fixed in the script
**before** the run so the number could not be read generously after the fact.

## The measurement

Reference = the same board with the halfmove counter set to **0**, so the fifty-move rule cannot mask
the result. Base build, Threads 1, Hash 16, OwnBook false.

| # | depth 12 | depth 16 | depth 20 | depth 24 | reading |
|---|---|---|---|---|---|
| 0 | cp −1601 | cp −1789 | **mate −16** | **mate −9** | decisive loss, real |
| 4 | cp −942 | cp −1067 | cp −1159 | cp −1284 | decisive loss, real |
| 7 | cp −477 | cp −84 | cp −70 | **cp −52** | **artefact** — not decided |
| 10 | cp 2950 | **mate 4** | mate 4 | mate 4 | decisive **win**, real |
| 11 | cp −1039 | cp −1178 | cp −1225 | cp −1354 | decisive loss, real |
| 13 | cp −963 | cp −1056 | cp −1163 | cp −1256 | decisive loss, real |
| 17 | cp 0 | cp 0 | cp 0 | cp 0 | genuinely drawn |
| 5 | cp −6 | cp 0 | cp 0 | cp 0 | genuinely drawn |
| 8 | cp −46 | cp 0 | cp 18 | cp −15 | noise, not decided |
| 15 | cp −49 | cp −73 | cp −46 | cp −49 | noise, not decided |

At depth 18 across all twenty: **DECISIVE-WIN 1, DECISIVE-LOSS 4, INCONCLUSIVE 15**.
Of the 14 inconclusive at depth 12: **0 became decisive**.

## The rate, tightened

| version | decisive base error | thrown-away win | status |
|---|---|---|---|
| my first pass | "19 of 20 (95 %)" | — | **withdrawn**, conflated losses with wins |
| 07-F4 (depth 12) | 6 of 20 (30 %) | 1 of 20 | superseded |
| **this job (depth 18–24)** | **5 of 20 (25 %)** | **1 of 20** | current |

**Two directions of correction, and they are worth separating:**

- **One case left** (position #7): a −477 that collapsed to −52 by depth 24. Deeper search *removed* a
  claimed base error. Reporting only the depth-12 number would have overstated the case.
- **The real cases got stronger** (#0 → mate −9, #10 → mate 4 stable): deeper search made the genuine
  errors clearer, so the surviving five are solid.

## What this means for the root-drawn switch

On this sample the switch prevents **one game-losing outcome in twenty**, plus four corrected
draw-from-lost declarations that cost nothing. That is the honest worth, and it is **narrower** than
either of my earlier figures. Whether that justifies the switch is the owner's call; my job was to give
the right number, and it is 5/20 with 1/20 consequential.

## Findings

**07-C38** in FINDINGS.md (which supersedes 07-F4's rate and records both corrections).

## Suspicions, not proven

- That position #7's −52 would resolve to a draw at even greater depth. It is heading that way
  (−477 → −84 → −70 → −52), so I read it as decided-draw, but I did not run depth 30.
- That the four masked losses are typical of real fifty-move positions — they come from stripped G
  positions with the counter forced to 100, a synthetic population.

## What I did NOT do

- Did not run all twenty at depth 24 (only the ten that mattered); the other ten were already stable
  at 12 and 18.
- Did not go beyond depth 24.

## What I am NOT sure about

- Whether any of the 10 stable-inconclusive positions would become decisive at depth 30+. Their scores
  are flat across 12→18 and, for the sampled ones, flat to 24, which is evidence of a genuine draw, not
  proof.

## Times

See job39/stamps.txt.

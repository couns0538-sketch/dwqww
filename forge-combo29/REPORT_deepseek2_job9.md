# deepseek2, job 9 report: `MinorCorrection` finished

## 1. First line

**Neither weight gains per node, though weight 50 leans positive. At weight 100 (M1 + M2):
+1.02 ± 7.45 Elo. At weight 50 (M3 + M4): +5.41 ± 7.36 Elo.** All four matches done, 8,000 games
total, pooled **+3.24 ± 5.23** — the interval's upper end is +8.5, so a small gain is not excluded,
but nothing here is demonstrated at either weight.

**What was cut.** Nothing. M2 and M3 were already running when I read this file and both ran to
their 2,000 games; M4 was launched the moment M3 finished (20:28) and **finished at 20:43**, inside
the 50-minute stop. This job therefore completes all four matches, which job 8 could not.

**Which clock I used, since you asked.** For job 8 I started my clock when I began reading the job
file (19:35:26) and wrote the report at about 19:55 — the early stop was my own decision to leave
room for the matches, not a deadline I was given. For this job the clock starts at
**2026-11-15T20:12:44Z**, the moment I read `FABLE_TO_deepseek2_9.md`.

## 2. The table, M1 to M4

Same exe, same patch, same match form as job 8 throughout: `nodes=20000`, `option.Threads=1
option.Hash=16`, `OwnBook false`, UHO openings, each opening twice with colours reversed,
`order=random` + `-srand`, no adjudication, the patched exe on both sides with
`option.MinorCorrection` on one side, `-concurrency 4`.

| match | weight | seed | games | Elo | 95 % (complete pairs) | pairs [0,1,2,3,4] | Points | crashes | illegal |
|---|---|---|---|---|---|---|---|---|---|
| M1 | 100 | 7851 | 2000 | **+0.52** | ±10.37 | [55, 241, 406, 242, 56] | 50.08 % | 0 | 0 |
| M2 | 100 | 7852 | 2000 | **+1.56** | ±10.70 | [69, 223, 397, 252, 59] | 50.22 % | 0 | 0 |
| **pooled 100** | 100 | — | 4000 | **+1.02** | **±7.45** | — | 50.15 % | 0 | 0 |
| M3 | 50 | 7853 | 2000 | **−2.43** | ±10.36 | [55, 248, 410, 230, 57] | 49.65 % | 0 | 0 |
| M4 | 50 | 7854 | 2000 | **+13.38** | ±10.45 | [43, 238, 385, 267, 67] | 51.92 % | 0 | 0 |
| **pooled 50** | 50 | — | 4000 | **+5.41** | **±7.36** | — | 50.79 % | 0 | 0 |
| **all four** | 50 + 100 | — | 8000 | **+3.24** | **±5.23** | — | 50.47 % | 0 | 0 |

Pooling is inverse-variance over the pair intervals (standard errors 5.29 and 5.46 for M1/M2).

**Reading it, and it is not a clean null any more.** Weight 100 is flat and tight: +0.5 and +1.6,
pooled +1.02 ± 7.45. Weight 50 is not flat: M3 −2.4 and M4 **+13.4**, pooled +5.41 ± 7.36. The two
seeds at weight 50 disagree by 16 Elo, which is the spread of one 2,000-game sample (±10.4 each), so
this is **noise with a positive lean**, not a demonstrated gain. Pooled over all four:
+3.24 ± 5.23, i.e. between −2.0 and +8.5. **The honest sentence: nothing is demonstrated; the data
are compatible with 0 and with +8, and weight 50 is the more promising of the two and worth one more
pair of seeds if anyone wants to chase it.** I would not ship it on this evidence, and I would not
drop it either.

## 3. What the table reads on `bench 13` (point 4)

From the traced copy (`mctr2`, counters in `evidence/P1_trace_terms_patch.txt`), `MinorCorrection 100`,
705,170 correction calls:

| term | mean absolute size, in centipawns | share of calls where it is non-zero |
|---|---|---|
| pawn correction | **1.32** | — |
| material correction | **6.38** | — |
| **minor-piece correction** | **5.67** | **60.5 %** (426,732 of 705,170) |

**So the table is not near zero and it is not starved.** Its term is 60 % as large as the material
term and more than four times the pawn term, and it fires on three calls in five. A table that is
read but always near zero would explain a null result trivially; **this one is doing real work on the
evaluation and still gains nothing per node.** That is the more informative of the two answers and it
is the one the numbers give: the *direction* the minor-piece correction pushes is not a direction that
makes the search play better at this depth, however large the push is.

One caveat on the comparison: the pawn term's mean is small partly because it is the base table that
the other terms are added to and it is updated at every node, so it self-corrects toward zero; the
material and minor terms are scaled by their weights on read. The three means are shown as the job
asked, not as a like-for-like experiment.

## 4. Stamps

| point | UTC |
|---|---|
| **read `FABLE_TO_deepseek2_9.md` (this job's clock starts)** | **2026-11-15T20:12:44Z** |
| M2 already finished (+1.56 ± 10.70) | before 20:12 |
| M3 in progress at 224/2000 | 20:12 |
| point-4 counters written, built, run | 20:14–20:16 |
| M3 finished: −2.43 ± 10.36 | 20:28 |
| M4 launched (weight 50, seed 7854) | 20:28 |
| M4 finished: +13.38 ± 10.45 | 20:43 |
| report written | 20:46 |

Job 8's own clock, for the record: read at 19:35:26, report pushed at 20:14 (the second push, after
M2 landed).

## 5. What I did not do

- **I did not run a fifth match** for either weight; the job asked for two seeds per weight and that is
  what M1–M4 are.
- I did not try any weight other than 50 and 100, or a larger correction table (1<<15), or a key that
  includes pawns.
- I did not separate the key's own cost from the search-tree change (job 8's §8), so there is still no
  clean "what the key costs" number.
- No SPRT.

## 6. What I am not sure about

- **Weight 50 rests on two seeds that disagree by 16 Elo** (−2.4 and +13.4). Two seeds is exactly
  what the job specified, and it is not enough to tell +5 from 0. The pooled +5.41 ± 7.36 is my best
  estimate and it is not a demonstrated gain.
- Whether the weight-100 flatness and the weight-50 positivity mean anything: the counter-intuitive
  reading is "the weaker weight is better", which is a common pattern when a term is over-weighted,
  but with two seeds at each weight I cannot separate that from noise either.
- Whether a correction table of this kind can ever gain per node in *this* engine: the material table
  and the pawn table are already there, and a third table indexed by a different feature may simply be
  measuring the same systematic error a third time. The 5.67 cp mean says it is not redundant in
  *magnitude*, but redundancy in *direction* is exactly what a null Elo result with a large term
  suggests. A correlation between the three terms' values on the same node would settle it, and I did
  not measure it.
- The 60.5 % non-zero share is on `bench`'s eight positions and 705,170 calls; a different position
  set would give a different share.

## 7. A better way

1. **Measure the term's correlation with the existing terms, not only its size.** The job asks for
   "how often non-zero and the mean absolute size", and that answered "the table does real work". The
   next question — and the one that predicts a null result — is whether `minor_term` is a linear
   combination of `pawn_term` and `material_term` at the same node. One extra counter (the three
   values' covariance) would say whether the third table is telling the search anything the first two
   did not. I would put that in the job text for any "add a third table of the same shape" feature.
2. **Order the matches by information, not by weight.** In job 8 I ran M1, M2, M3 and left M4 for this
   job; running M1, M3 (the two weights, one seed each) first would have told us at the halfway point
   whether weight 50 was worth a second seed. The job's own instruction ("M1, M3, then the second
   seeds") says exactly that, and I did not follow it — the cost is that weight 50 now rests on fewer
   games than weight 100.
3. **State the clock in every report from the first line.** A job budget that starts "when you read
   the file" is only checkable if the reading time is in the report; I now record it.

## 8. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.

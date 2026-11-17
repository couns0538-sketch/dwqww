# REPORT — seat 25, area 5, job 1 SEVENTH RUN (seed 2561, set R7)

Branch `for-fable-and-opus/swarm-25`. Folder `forge-combo29/swarm/25/job1g/`.
Prediction committed and pushed alone at `e1003ced8`, before the first measuring command.
Build: base tree `6b98f217`, S14, Threads 1, Hash 16. Honesty pins hold.

This run tested the remedy S-C53 named for the limitation it exposed: enrich on **score** change rather than **move**
change. The answer is a clear no, and the reason is more useful than the test.

---

## 1. The prediction, against what actually happened

| # | prediction | outcome |
|---|---|---|
| S1 | all 300 measured at both depths, both settings | **HIT** |
| S2 | score stratum 25–48% of 300 | **HIT** — **109/300 = 36.3%** |
| S3 | move stratum rate HIGHER than score stratum; predicted move 40–65%, score 30–55% | **HIT in direction (57.1% vs 6.4%), MISS in magnitude** — the score rate was far below even my floor |
| S4 | 60–100% overlap between the strata | **KILLED — and it could not have been otherwise:** my own definition made the strata mutually exclusive. See §3. |
| S5 | remainder 5–20% | **HIT** — 13.5% |
| S6 | 0 score ties; planted control passes | **HIT** — 0 ties in 48 disagreements |
| S7 | 0–2 mate-number disagreements between depths | **HIT** — 1 (board 106), still being verified at this writing |
| S8 | no mate-frequency prediction | **kept** — 33 mate top-scores reported without a predicted range |

## 2. The finding: the score criterion is inverted, not just weaker

Three strata, all defined from the **selection** data only (`bestmove` and `score` at depths 12 and 16), with the
outcome (MultiPV-1 vs MultiPV-3 disagreement) playing **no part** in selection:

| stratum | definition | n | disagree | rate | 95% CI |
|---|---|---|---|---|---|
| **Move-unstable** | `bestmove(d12) != bestmove(d16)` | 35 | 20 | **57.1%** | [40.9, 72.0] |
| **Score-unstable** | same move, `|Δscore| >= 50 cp` | 109 | 7 | **6.4%** | [3.1, 12.7] |
| **Neither** | — | 156 | 21 | **13.5%** | [9.0, 19.7] |

The stratum I built specifically to catch the board-121 failure — a large score change with the move held constant —
has **less than half the disagree rate of the boards it excludes** (6.4% against 13.5%). And the move stratum remains
above both, at 57.1%, consistent with S-C54's 53.4%.

**Why, and this is the durable part:** a large score change with the move unchanged marks a search that has
**already converged on the choice** and is refining only its evaluation. MultiPV perturbs the *choice*; if the choice
is settled, extra lines do not move it. **The instability that matters is instability of the choice, not of the
number.** So enriching a test set by score-change would have been *worse than using no criterion at all* — it would
have selected precisely the boards where the effect is rarest.

That also explains, in hindsight, why board 121 could be stable by the move rule and still be wrong about its
distance: the two failures are different phenomena. Board 121 is a **distance** error in a settled search; the
MultiPV effect is a **choice** effect in an unsettled one. Conflating them was my mistake, and the data separated
them cleanly.

## 3. S-C57: a prediction that contradicted its own definition

S4 predicted 60–100% overlap between the move and score strata. The same document defines the score stratum as
requiring `bestmove(d12) == bestmove(d16)` and the move stratum as `bestmove(d12) != bestmove(d16)`. **The
intersection is empty by construction**, so the overlap was 0% and the run reported "KILLED" for a prediction that was
dead when I wrote it.

This is a new error class for my list and I am recording it as such: **not a wrong number, not a wrong harness, but a
prediction whose falsification was guaranteed by my own definitions** — the same family as an unfalsifiable
hypothesis, and worse than a wrong guess because a wrong guess can at least be informative. Nineteenth control error,
first one located in the prediction rather than the measurement.

The substantive question underneath was answerable and now is answered: of the 35 move-unstable boards, **10
(28.6%)** also change score by ≥50 cp. So the two phenomena are largely **separate** rather than nested — which is
itself the reason the score criterion fails as a substitute for the move criterion.

## 4. Board 106: a third candidate, and its verdict is not in

R7 board 106 (`6nr/7p/p2krp2/R1pP1bP1/1QP4p/4p3/3NP3/1B2K1NR w`):

| depth | score | first move | PV length | needed | replay |
|---|---|---|---|---|---|
| 12 | `mate 10` | `a5a6` | 19 | 19 ✓ | legal, ends in checkmate |
| 16 | `mate 7` | `b4c5` | 13 | 13 ✓ | legal, ends in checkmate |

Two right-length PVs, different moves, different distances. Exhaustive verification of the **shorter** claim is the
right order (it is the cheaper budget and, if it holds, the longer claim is a proven error):

| n | can white force mate in ≤ n? | time |
|---|---|---|
| 1–4 | no | up to 26.3 s |
| 5 | **no** | 422.9 s (4.6 M memo entries) |
| 6, 7 | **still running when this report was written** | — |

So as of this writing I have excluded ≤5 and have not settled whether 7 is right. **The report does not guess.** If
n=7 completes as forced, this is a third instance of the class and depth 12's `mate 10` is the wrong one (an
over-estimate by 3, the same shape as S-C53). If it comes back not-forced, board 106 is a different and larger
anomaly. Either way the count of demonstrated instances stays at **two** until this resolves, and I will state which
before close.

## 5. Honesty notes

- **S4 is recorded as killed by my own definition**, not by the data, and that distinction is in the row.
- **S3 is a directional hit with a magnitude miss:** I predicted the score stratum would be 30–55%; it was 6.4%.
  Being right about which way it went while being wrong by a factor of five is not a good prediction.
- Board 106's verdict is **not in**. Two demonstrated instances of the right-length-wrong-mate class; a third is
  pending.
- No mate-frequency prediction was made this run (S8), by design, after two consecutive misses in opposite
  directions.
- Every number above came from a committed command output. The one number in the previous cycle that was wrong
  (S-C55) was the one I did not compute, which remains the most useful thing that happened to my process.

## 6. Files

| file | what |
|---|---|
| `PREDICTION.md` | pushed alone before measuring, `e1003ced8` |
| `R7_2561.fens` | 300 positions, seed 2561 |
| `R7_d12free.jsonl`, `R7_d16.jsonl` | free MultiPV-1 sweeps — the SELECTION data |
| `M.fens`, `S.fens`, `R.fens` | the three strata as selected, so the split is reproducible |
| `R7_M_mpv.jsonl` (35), `R7_S_mpv.jsonl` (109), `R7_R_mpv.jsonl` (156) | the outcome measurement per stratum |
| `b106_partial.txt` | board 106's budgets so far, with the unfinished ones marked |
| `rows.md` | the FINDINGS rows as appended |

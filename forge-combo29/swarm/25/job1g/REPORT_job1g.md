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
| S3 | move stratum rate HIGHER than score stratum; predicted move 40–65%, score 30–55% | **HIT in direction (57.1% vs 6.4%, Fisher p=7.9e-10), MISS in magnitude** — the score rate was far below even my floor |
| S4 | 60–100% overlap between the strata | **KILLED — and it could not have been otherwise:** my own definition made the strata mutually exclusive. See §5. |
| S5 | remainder 5–20% | **HIT** — 13.5% |
| S6 | 0 score ties; planted control passes | **HIT** — 0 ties in 48 disagreements |
| S7 | 0–2 mate-number disagreements between depths | **HIT** — 1 (board 106), still being verified at this writing |
| S8 | no mate-frequency prediction | **kept** — 33 mate top-scores reported without a predicted range |

## 2. The finding: the score criterion does not reproduce as a selector, and my own "inversion" claim was not significant

Three strata, all defined from the **selection** data only (`bestmove` and `score` at depths 12 and 16), with the
outcome (MultiPV-1 vs MultiPV-3 disagreement) playing **no part** in selection:

| stratum | definition | n | disagree | rate | 95% CI |
|---|---|---|---|---|---|
| **Move-unstable** | `bestmove(d12) != bestmove(d16)` | 35 | 20 | **57.1%** | [40.9, 72.0] |
| **Score-unstable** | same move, `|Δscore| >= 50 cp` | 109 | 7 | **6.4%** | [3.1, 12.7] |
| **Neither** | — | 156 | 21 | **13.5%** | [9.0, 19.7] |

**What the statistics actually support** (Fisher exact, recomputed after the coordinator flagged the omission — see §3):

| comparison | counts | Fisher two-sided p | verdict |
|---|---|---|---|
| move vs remainder | 20/35 vs 21/156 | **2.05e-07** | **significant — move-change selects** |
| move vs score | 20/35 vs 7/109 | **7.9e-10** | **significant — move beats score** |
| **score vs remainder** | 7/109 vs 21/156 | **0.0712** | **NOT significant** |

So the load-bearing result is that **the move-change criterion is a strong selector** and is significantly stronger
than the score criterion. **The score criterion does not reproduce as a selector**, which is the reportable negative
the coordinator asked about — but I cannot say it is *worse than nothing*, because 6.4% against 13.5% at p=0.0712 does
not establish an ordering. Its point estimate is below the remainder with a wide interval.

**This is the answer to the question the run was built on:** the remedy S-C53 named (enrich on score change) does not
work as a substitute for the move rule. Why is left open — a big score change with the move held constant may mark a
search that has converged on the choice and is refining only its evaluation, but that mechanism is a hypothesis the
sample did not test, and I originally published it as if it had.

## 3. S-C58: I overstated S-C56, and the coordinator caught it

I published S-C56 with the headline that the score stratum has "less than half the rate of the boards it excludes" and
that score enrichment "would have been worse than using no criterion at all". The coordinator re-derived Fisher exact
on my own committed counts and both claims failed: **p = 0.0712**. I recomputed all three comparisons myself and
confirm every figure.

**Withdrawn:** the ordering claim and the "worse than nothing" inference.
**Stands:** the move criterion (p = 2.05e-07) and move-beats-score (p = 7.9e-10).
**Retained as hypothesis only:** the "settled choice is not moved by MultiPV" mechanism.

**The error is worth naming precisely:** every number in the row was correct; the **inference attached to them was
not**. No mechanical guard caught it because nothing was malformed — the row parsed, the arithmetic was right, and
`audit_final.py` had nothing to object to. This is a new class for my list: **a correct number with an overstated
inference**, which is harder to catch than a wrong number because the checks all pass.

I built `sigtest.py` in response: Fisher exact plus Wilson intervals, with a verdict function that **refuses to state an
ordering below p = 0.05**. It reproduces all three comparisons above, and I probed it four ways (a known-significant
pair, identical rates, equal proportions at different n, and an interval sanity check) before trusting it.

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

## 4. Board 106: a third candidate, unadjudicated, and the method limit that stopped me

R7 board 106 (`6nr/7p/p2krp2/R1pP1bP1/1QP4p/4p3/3NP3/1B2K1NR w`):

| depth | score | first move | PV length | needed | replay |
|---|---|---|---|---|---|
| 12 | `mate 10` | `a5a6` | 19 | 19 ✓ | legal, ends in checkmate |
| 16 | `mate 7` | `b4c5` | 13 | 13 ✓ | legal, ends in checkmate |

Two right-length PVs, different moves, different distances. Exhaustive verification of the **shorter** claim:

| n | can white force mate in ≤ n? | time |
|---|---|---|
| 1–4 | no | up to 26.0 s |
| 5 | **no** | 419.7 s (4.6 M memo entries) |
| 6 | **DID NOT COMPLETE** — two runs, the second with a 5400 s cap, both inside the n=6 budget after ~18 CPU-minutes | — |

**Verdict: unadjudicated, and the demonstrated count of the right-length-wrong-mate class stays at TWO** (S-C52,
S-C53). What I did exclude is real: white cannot force mate in 5 or fewer, so the `mate 7` claim is not refuted by
anything I measured. If 7 is true, the depth-12 `mate 10` is wrong by 3 — the S-C53 shape, on a different board and a
different depth pair. **I am not recording it as a third instance on a guess.**

**Method limit, stated so nobody repeats it:** naive exhaustive search over every legal move with a memo table is
exponential in board width and unusable past mate-in-5 on middlegame positions. I also tried a pruned search
(`job1d/mate_bound.py`) and it **failed** — it could not find a *known* mate in 7 in a bare KQ-vs-K position within
20.8 s. That file is kept and marked as an abandoned branch. The right tool is a real mate solver (transposition table,
killer moves, iterative deepening, or proof-number search), which I did not have time to build tonight. **Recording the
failed attempt matters more than the attempt**: a pruned search whose "not found" is indistinguishable from a timeout
would have produced a confident-looking wrong answer.

## 5. S-C57: a prediction that contradicted its own definition

S4 predicted 60–100% overlap between the move and score strata. The same document defines the score stratum as
requiring `bestmove(d12) == bestmove(d16)` and the move stratum as `bestmove(d12) != bestmove(d16)`. **The
intersection is empty by construction**, so the overlap was 0% and the run reported "KILLED" for a prediction that was
dead when I wrote it.

This is a new error class: **not a wrong number, not a wrong harness, but a prediction whose falsification was
guaranteed by my own definitions** — the same family as an unfalsifiable hypothesis, and worse than a wrong guess
because a wrong guess can at least be informative.

The substantive question underneath was answerable and now is answered: of the 35 move-unstable boards, **10 (28.6%)**
also change score by ≥50 cp. The two phenomena are largely **separate** rather than nested, which is itself part of why
the score criterion does not substitute for the move criterion.

## 6. Honesty notes

- **S-C56's headline was overstated and is withdrawn** (S-C58). The ordering was p=0.0712. The coordinator caught it;
  I then recomputed and confirmed.
- **S4 is recorded as killed by my own definition**, not by the data.
- **S3 is a directional hit with a magnitude miss:** I predicted the score stratum would be 30–55%; it was 6.4%.
  Right about the direction, wrong by a factor of five.
- Board 106 is **unadjudicated**. Two demonstrated instances of the class; the third is a candidate and is recorded as
  one.
- No mate-frequency prediction was made this run (S8), by design, after two consecutive misses in opposite directions.
- **A pruned solver I built failed and is kept marked as failed** (§4). Reporting the abandoned attempt matters because
  its "not found" would have been indistinguishable from a timeout.

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

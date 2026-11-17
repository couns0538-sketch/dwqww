# REPORT — seat 25, area 5, job 1 SIXTH RUN (seed 2551, set R6, 400 positions)

Branch `for-fable-and-opus/swarm-25`. Folder `forge-combo29/swarm/25/job1f/`.
Prediction committed and pushed alone at `325afac53`, before the first measuring command.
Build: base tree `6b98f217`, S14, Threads 1, Hash 16. Honesty pins hold.

This run answered the owner's two asks directly: **firm up S-C51's unstable stratum on a deliberately-sized set and
state the selection rule**, and **look for a second board of the right-length-wrong-mate class and say which setting
failed**.

---

## 1. The prediction, against what actually happened

| # | prediction | outcome |
|---|---|---|
| S1 | all 400 measured at both depths, both settings | **HIT** — 800 sweep records + 800 MultiPV records |
| S2 | unstable stratum 12–30% of 400 (48–120 boards) | **HIT** — **58/400 = 14.5%**, with R4's 12.0% for company |
| S3 | unstable MultiPV rate 35–70% | **HIT** — **53.4%** (31/58) |
| S4 | stable rate 8–25% | **HIT** — **10.2%** (35/342) |
| S5 | unstable and stable intervals disjoint | **HIT** — [40.8, 65.7] vs [7.5, 13.9] |
| S6 | 0 score ties; planted control passes | **HIT** — 0 ties in 66 disagreements; control below |
| S7 | 40–100 top-line mate scores across 1600 searches | **MISS — 28.** Predicted a corrected expectation after being wrong by 3x last run, and was wrong again in the other direction. |
| S8 | at most 3 mate-number disagreements between settings; kill above 6 | **HIT — 0.** But see §3: the second right-length case was found on a DEPTH ladder, not a MultiPV disagreement, so S8 was measuring the wrong axis. |

S7 is worth stating plainly: I over-corrected. The previous run killed a prediction of 2–12 with an actual 39; I
raised it to 40–100 and got 28. Two bad estimates in a row on the same quantity, from the same cause — I have been
estimating a rate from whichever sample I most recently looked at. The honest position is that mate-score frequency
on this population is roughly 1 in 50 searches at depth 12-16 and I have not measured enough samples to do better
than that.

## 2. S-C51 firmed up: the conditional rate holds, and the selection rule is stated

**The selection rule, stated so the numbers cannot be misread:** the strata were defined **solely** by whether a free
MultiPV-1 search chose a different best move at depth 12 than at depth 16 — `bestmove(d12) != bestmove(d16)`. The
outcome measured was the MultiPV-1-versus-MultiPV-3 bestmove disagreement, which played **no part** in selecting the
boards. So the unstable stratum is **enriched on purpose**, and its rate is **not comparable** with the ~18%
population figure from a random draw. The valid comparison is unstable-to-stable within the same draw.

| population | n | disagreements | rate | 95% Wilson CI |
|---|---|---|---|---|
| **R6 unstable** (selected: d12 move ≠ d16 move) | 58 | 31 | **53.4%** | **[40.8%, 65.7%]** |
| **R6 stable** (same draw) | 342 | 35 | **10.2%** | **[7.5%, 13.9%]** |
| R4 unstable (previous cycle) | 30 | 16 | 53.3% | [36.1%, 69.8%] |
| R4 stable (previous cycle) | 220 | 31 | 14.1% | [10.1%, 19.3%] |
| R5 random (replication of S-C48) | 250 | 44 | 17.6% | [13.4%, 22.8%] |
| R4 random (S-C48 original) | 250 | 47 | 18.8% | [14.4%, 24.1%] |

**What this settles and what it does not.**

Settled: the rate on unstable boards did not move when the stratum nearly doubled (53.3% on 30 boards, 53.4% on 58),
and its interval tightened from 33.7 points wide to 24.9. Two independent draws, two selection rules of the same
form, the same answer. The conditional structure of S-C51 is not a small-sample artifact.

Not settled: the interval is still **[40.8%, 65.7%]** — 25 points wide. The point estimate is stable; the precision
is not high. Getting it below ±5 points would need roughly 350 unstable boards, which at a 14.5% incidence means
drawing about 2,400 positions. That is a real cost and I am not implying the current figure is sharper than it is.

Also worth noting for anyone reusing this: the unstable fraction is itself consistent across draws (R4 12.0%,
R6 14.5%), which is why "unstable boards are ~1 in 7 of random middlegame positions" is a usable planning number if
someone wants to enrich a set deliberately.

## 3. S-C52: a SECOND board of the right-length-wrong-mate class, and the owner's question answered honestly

**Board 121 of R6** (`1nbk2r1/2rp1pb1/Bp1n1q2/1Pp3Pp/5pP1/P3P3/2PP1K2/RNB3NR b`, black to move):

| depth | score | first move | PV length | plies needed | PV replays |
|---|---|---|---|---|---|
| 12 | `mate 7` | `f4e3` | 13 | 13 ✓ | legal, ends in checkmate ✓ |
| 16 | `mate 4` | `f4e3` | 7 | 7 ✓ | legal, ends in checkmate ✓ |

**Exhaustive search settles it: black forces mate in exactly 4** (n=1..3 not forced; n=4 forced, 53.7 s, 697,216
memo entries). So the depth-12 `mate 7` is **wrong by 3 moves**, and its 13-ply PV was exactly the length that claim
requires and ended in a real checkmate.

**On the owner's question — "is the failing setting the one with more lines?" — the two boards point in different
directions, and that is the answer:**

| board | failure | which search failed | error |
|---|---|---|---|
| S-C52, R5 board 222 | MultiPV 1 `mate -5` vs MultiPV 3 `mate -6` | **the one with MORE lines** (MultiPV 3) | over-estimated by 1 |
| S-C53, R6 board 121 | depth 12 `mate 7` vs depth 16 `mate 4` | **the SINGLE-line search**, at the shallower depth | over-estimated by 3 |

So two boards in the class, and they do **not** agree on which setting fails. **No direction claimed**, and the pair
is more informative than either alone: it shows the failure is **not a MultiPV artifact at all**. Board 121's
contradiction is between two depths of the *same* setting, with the *same* best move in both reports — so the error
is in the **distance**, not in the choice of move, and no display setting is involved.

What the pair does establish, in one sentence: **a mate score is not corroborated by its own PV being the right
length and ending in checkmate.** Board 222 and board 121 each satisfy every structural test I have and each is
wrong. That is now two independent demonstrations rather than one.

### A refinement this forced on my own S-C51 definition

Board 121 is a **stable** board by my selection rule — its best move is `f4e3` at both depths — yet its mate number
changed by 3. So "search still changing its mind" as I operationalised it (a bestmove change) does not capture a
search that keeps the move but is still revising the *evaluation* of it. That is a real limitation of the proxy, and
it suggests a better enrichment criterion for a future run: boards where the **score** changes materially between
depths, not only the move. I am recording this rather than redefining the rule after seeing the results.

## 4. The planted case behind the zeros

| case | expected | result |
|---|---|---|
| MultiPV 1 re-run against its stored record, 40 boards | 0 differences | **0** |
| depth 1 substituted for depth 12 | DIFF | **caught** |
| bestmove overwritten with `a1a1` | DIFF | **caught** |
| score nudged by 1 cp | DIFF | **caught** |

## 5. Honesty notes

- **S7 was missed** (28 against a predicted 40–100) and is recorded as a miss, along with the fact that it was my
  second bad estimate of the same quantity in consecutive runs.
- **S8 was a hit on the wrong axis:** it asked about mate-number disagreements *between MultiPV settings* and found
  0, while the class I was looking for turned up on a *depth* ladder. The prediction was well-formed and measured the
  wrong thing — recorded that way rather than as a clean hit.
- Board 121's verification is a **proof**: a forced mate in 4 exists, and UCI's `mate N` denotes the shortest forced
  mate, so `mate 7` is wrong. No further budget is needed for that verdict, unlike board 222's case where I had to
  run the n=5 budget to completion.
- The unstable rate's interval is still 25 points wide and §2 says so with the sample size it would take to fix.

## 6. Files

| file | what |
|---|---|
| `PREDICTION.md` | pushed alone before measuring, `325afac53` |
| `R6_2551.fens` | 400 positions, seed 2551 |
| `R6_d12free.jsonl`, `R6_d16.jsonl` | free MultiPV-1 sweeps at depth 12 and 16 — the SELECTION data |
| `unstable_ids.txt`, `unstable.fens`, `stable.fens` | the strata as selected, so the split is reproducible |
| `R6_unstable_mpv.jsonl` (58), `R6_stable_mpv.jsonl` (342) | the outcome measurement per stratum |
| `b121_mate4_verified.txt` | the exhaustive verdict on board 121 |
| `rows.md` | the FINDINGS rows as appended |

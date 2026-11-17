# REPORT — seat 25, area 5, job 1 FOURTH RUN (seed 2531, set R4)

Branch `for-fable-and-opus/swarm-25`. Folder `forge-combo29/swarm/25/job1d/`.
Prediction committed and pushed alone at `2f0e799c7`, before the first measuring command.
Build: base tree `6b98f217`, S14, Threads 1, Hash 16 (all commands below run the release build at
`~/build/release/forge`). Honesty pins re-checked for this build: 312866 / 862329 / 3024920 / 4865609.

---

## 1. The prediction, against what actually happened

| # | prediction | outcome |
|---|---|---|
| S1 | 250 searches complete | **HIT** — 250 records written |
| S2 | 0 PVs with an illegal move | **HIT** — 254 PVs replayed on a real board, 0 illegal, 0 empty |
| S3 | mate scores seen: 5–20 (kill outside [2,30]) | **NEAR MISS** — 4 at depth 12. Inside the kill range I declared, outside the range I expected. Written down as a near miss, not as a hit. |
| S4 | mate PVs not ending in mate: 0–2 | **HIT** — 4 of 4 ended in checkmate with the right length |
| S5 | depth-20 mate number never LONGER than depth-12 | **HIT** as stated (0 longer). **But see §2: this was not the test I thought it was.** |
| S6 | no mate vanishes at greater depth | **HIT** — 0 vanished |

S5 and S6 are hits in the sense that their kill conditions did not fire on 250 boards. That is the whole of
what they establish, and §2 is why I am not treating the pair as support for anything larger.

## 2. The one board where the answer changed, and what it turned out to be

Board 103 of R4 (`2r1n1r1/3b2p1/2Ppp3/B2n2kp/R2PB1P1/4P2P/1P6/4KQR1 w - - 0 36`) reported:

| depth | bestmove | score | PV length |
|---|---|---|---|
| 12 | `g4h5` | `mate 6` | 11 |
| 13 | `g4h5` | `mate 6` | 11 |
| 14 | `h3h4` | `mate 4` | 7 |
| 15–20 | `h3h4` | `mate 4` | 7 |

On its face this is exactly the phenomenon my S-C32 mechanism said does not happen: a mate distance falling
from 6 to 4 as depth rises. **It is not. The distance did not fall; the engine changed which move it preferred.**
Both halves of that were measured separately, and neither depends on the other:

1. **Per move, pinned by `searchmoves`, the number is constant at every depth.** `g4h5` reports `mate 6` at
   depths 12, 14, 16 and 20 with an identical 11-ply PV each time. `h3h4` reports `mate 4` at depths 12, 14 and
   20 with an identical 7-ply PV. Neither move's distance shrinks. (`searchmoves_probe.py`.)
2. **At one fixed depth, MultiPV decides which of the two is reported as best.** At depth 12 with everything
   else identical, MultiPV 1 reports `mate 6` / `g4h5`, and MultiPV 3 reports `mate 4` / `h3h4` as its first
   line with `mate 6` / `g4h5` demoted to second. So the shorter mate was **available at depth 12** — the
   MultiPV-1 search simply did not return it.

So the ladder's apparent fall is a **move-choice change**, and the move-choice change is itself an artifact of
the MultiPV setting. That second half is the part I did not expect and did not predict.

## 3. Ground truth from outside the engine

`matesolve3.py` is an independent brute-force solver (no engine code, python-chess only, exhaustive over every
legal move with both sides playing optimally). Its semantics are written out in the file header because two
earlier versions of it disagreed on this very board; the third is consistent and its self-check includes a
consistency assertion (`solve(fen)` must equal the best `solve_after(fen, move)` over legal moves).

| question | answer |
|---|---|
| after `h3h4`, smallest forced mate | **mate 4** — agrees with the engine exactly |
| after `g4h5`, smallest forced mate within the budget searched | **NOT ESTABLISHED** — see §4 |
| is the `mate 4` PV a genuinely forced mate of 7 plies? | **YES** — every defender reply at plies 2, 4 and 6 still loses (`pv_truth.py`) |

So the engine's `mate 4` on this board is correct, and its PV is a proof, not just a legal line. The engine did
**not** overestimate the mate it eventually chose.

## 4. What I did NOT establish, stated as a limit

**Whether `g4h5` forces mate in 6.** The `searchmoves g4h5` probe shows the engine reports `mate 6` there at every
depth 12, 14, 16 and 20, but the independent solver has not finished the budget that would confirm it.

What the solver *did* complete, and this is a real result rather than an absence:

| budget (total moves after `g4h5`) | independent verdict | time |
|---|---|---|
| mate in ≤ 2 | not forced | 0.0 s |
| mate in ≤ 3 | not forced | 0.1 s |
| mate in ≤ 4 | not forced | 8.2 s |
| mate in ≤ 5 | **not forced** | 451.5 s (6.07 M memo entries) |
| mate in ≤ 6 | **NOT RUN TO COMPLETION** — killed at the 3000 s cap | — |

So the honest statement is a **one-sided bound: `g4h5` does not force mate in 5 or fewer, which is consistent with
the engine's `mate 6` but does not prove it.** The engine's number requires exactly 6, and my run excludes 5 and
below. Confirming 6 needs the m=5 budget to finish, which was still climbing when the time cap hit and had already
reached ~1.8 GB of memo table; I stopped it rather than risk the machine.

Until that finishes, the honest statement is: *the engine reports `mate 6` after `g4h5`, the independent solver has
excluded every distance of 5 or less, and the exact distance is unverified.* No claim in this report depends on it,
and the §2 conclusion (the ladder's drop is a change of move rather than a shortening) does not need it — that
conclusion rests on the pinned `searchmoves` ladder and on the verified `mate 4`, both of which stand on their own.

Note also that the engine's own `mate 6` PV after `g4h5` differs between MultiPV 1 and MultiPV 3
(`f1f7 d5e7 g1g6 h6h7 g6g7 h7h6 g7h7 h6g5 f7f4` versus `g1g6 h6h7 f1f7 e8f6 g6f6 h7h8 f6h6 g7h6 f7h7`), so at most
one of those two lines can be the same move sequence; both are 11 plies. This is a second reason not to treat
either as verified.

## 5. The size of the MultiPV effect on this set (independent of the mate question)

On all 250 R4 boards, MultiPV 1 versus MultiPV 3, fresh process for each configuration, at each of two depths:

| measurement | depth 12 | depth 16 |
|---|---|---|
| different top-line score | **47 / 250 (18.8%)** | **41 / 250 (16.4%)** |
| different bestmove | **47 / 250** | **41 / 250** |
| differing bestmoves that are score TIES | **0** | **0** |
| top-line mate scores | 4 in both configurations | 6 in both configurations |
| mate-number disagreements | 1 (board 103) | 0 |

Three things follow, and the third is the one that matters for the owner's pipeline:

1. **Every disagreement is a real search difference, not bookkeeping.** In both depth families the count of
   differing bestmoves exactly equals the count of differing scores, with **zero** ties. Two searches that
   merely broke a tie would produce equal scores; these do not.
2. **It does not wash out with depth.** 18.8% at depth 12, 16.4% at depth 16. If this were a shallow-search
   artifact, raising the depth should dissolve it; it barely moves. So "run deeper and the MultiPV setting
   stops mattering" is false on this evidence.
3. **Most of it is small, but the tail is large.** Among the centipawn disagreements the score gap is median
   **15 cp** at depth 12 and **21 cp** at depth 16, but 5 (depth 12) and 7 (depth 16) boards disagree by more
   than **100 cp**, and the largest gaps are **452 cp** and **315 cp**. So the practical harm is not "19% of
   moves are slightly different" — it is that roughly 2-3% of positions get a materially different evaluation
   depending on a display setting.

| measurement | depth 12 | depth 16 |
|---|---|---|
| centipawn-gap median among disagreements | 15 cp | 21 cp |
| gap > 100 cp | 5 boards | 7 boards |
| gap > 300 cp | 1 board | 1 board |
| largest gap | 452 cp | 315 cp |

### Which setting is actually better? Measured, not assumed (S-C50)

The disagreement count says the two settings differ. It says nothing about which is right. So for all 47
disagreements I scored **both candidate moves** at depth 20, each pinned with `searchmoves` — so neither candidate
gets the free search's preference, and the comparison is move against move from an identical position.

| verdict at reference depth 20 | boards |
|---|---|
| MultiPV 1's move is stronger | **27** |
| MultiPV 3's move is stronger | **20** |
| equal | 0 |
| unscored | 0 |

A two-sided sign test on 27/47 gives **p = 0.38**. That is a coin flip, and I am not claiming a direction. What the
same run does establish is the *size*: among the 46 centipawn-scored pairs the median gap is **43 cp**, **18** exceed
50 cp, **12** exceed 100 cp, and **none are equal**.

So the honest summary of the whole MultiPV thread is: **the setting moves the answer on ~19% of random middlegame
positions, the disagreements are substantial, and neither setting is the accurate one.** MultiPV is a second sample
from an equally good search, not a correction. A pipeline that wants the stronger move has to spend depth (as this
reference does) or breadth; turning on extra lines does not buy accuracy.

**Ceiling:** depth 20 pinned is a stronger judge than depth 12, but it is still a search and not the truth. Where
depth 20 is itself wrong, the verdict inherits the error — and depth 20 sits below the depth-24 region where S-F8's
score changed again. This is a measurement about which of two moves a deeper search prefers, not a proof about
either move's true value.

### A confound I checked and then discarded

At depth 12 the MultiPV-1 answer matched the depth-16 answer on 88.0% of boards and the MultiPV-3 answer on
80.0%. That comparison is **not usable as evidence**: the depth-16 reference is itself a free (MultiPV-1)
search, so it favours MultiPV 1 by construction. I report the numbers only to say that I computed them and do
not rely on them. The disagreement-rate stability above is the sound version of the same question.


## 6. What this means for the owner, in one paragraph

A training pipeline that reads the engine's `info` line as "the best move and its score" is reading the result
of a search whose *move choice* depends on a display setting. On 47 of 250 positions at depth 12 (41 at depth 16),
MultiPV 1 and MultiPV 3 disagree about the best move and about its score; on one of those, they disagree about the
mate distance by two moves. **Neither setting is more accurate** (27 vs 20 at a deeper reference, p=0.38), so there is
no rule of the form "MultiPV > 1 is better". The safe statement is the narrower and more useful one: a score or a mate
number is a property of the search that produced it, MultiPV is part of that search, and the disagreements are large
enough (median 43 cp) that a pipeline should fix the setting and record it, rather than expecting the choice not to
matter.

## 7. Honesty notes

- S3 was declared with a kill range wider than my expectation, and the real value (4) fell outside my
  expectation but inside the kill range. I am recording that as a near miss rather than dressing it as a hit.
- I wrote **four** wrong "known answers" into `matesolve2.py`/`matesolve3.py` selfchecks tonight (a back rank
  that was mate in one rather than two, a ladder that was mate in one, a queen line that was mate in one, and a
  budget off-by-one that made every correct PV look unforced). All four were mine, all four were caught by
  running the check, none by reading it. This is now the eleventh instance of the pattern in STATUS.md.
- The `g4h5` distance is not verified (§4). No claim in this report depends on it.
- The 250 boards are random-game positions at one depth on one build. This is a measurement of the MultiPV
  effect on that population, not a claim about all positions or all depths.

## 8. Files

| file | what |
|---|---|
| `PREDICTION.md` | written and pushed before measuring |
| `R4_2531.fens` | 250 positions, seed 2531 |
| `R4_mates.jsonl` | depth-12 records, plus depth-20 for every depth-12 mate |
| `R4_mpv.jsonl` | MultiPV 1 and MultiPV 3 at depth 12, 250 boards |
| `run_mates.py`, `depth_sweep.py`, `choice_trace.py`, `searchmoves_probe.py`, `mpv_compare.py` | the measuring harnesses |
| `matesolve2.py`, `matesolve3.py`, `pv_truth.py` | independent solvers (matesolve3 is the current one) |
| `ladder.py` | depth ladder with PV replay |

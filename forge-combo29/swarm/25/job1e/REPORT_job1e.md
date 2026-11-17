# REPORT — seat 25, area 5, job 1 FIFTH RUN (seed 2541, set R5)

Branch `for-fable-and-opus/swarm-25`. Folder `forge-combo29/swarm/25/job1e/`.
Prediction committed and pushed alone at `52c3da2ad`, before the first measuring command.
Build: base tree `6b98f217`, S14, Threads 1, Hash 16. Honesty pins hold: 312866 / 862329 / 3024920 / 4865609.

---

## 1. The prediction, against what actually happened

| # | prediction | outcome |
|---|---|---|
| S1 | 250 records for both configurations | **HIT** — 250 records, both settings in every one |
| S2 | R5 disagreement rate 10–25% (kill outside [5%, 35%]) | **HIT** — **44/250 = 17.6%** against R4's 47/250 = 18.8% |
| S3 | R4's 30 unstable boards disagree MORE often than R5's random boards; predicted 25–60% | **HIT, and much harder than predicted** — **53.3%** (16/30) vs 17.6% |
| S4 | 0 differing bestmoves with equal scores | **HIT** — 0 of 44 |
| S5 | 2–12 top-line mate scores across the 500 searches; kill above 25 | **KILLED — 39.** I predicted rarity and got ~8% of searches reporting mate. Recorded as a kill, not softened. |
| S6 | no NEW board shows a fall with the MOVE unchanged | **NOT TRIGGERED** — the one mate-number disagreement found (board 222) is between two settings at one depth, not a depth ladder |
| S7 | planted-case control still passes | **HIT** — see §4 |

S5 is a genuine kill and worth saying plainly: mate scores on a "random middlegame" population are not rare, they
are roughly 1 in 12 searches at depth 12 on this set. R5 has 20 boards carrying a top-line mate in at least one
configuration, against 4 such boards in R4. My earlier samples (4, 4, 6) made me predict 2–12 and I was wrong by a
factor of about three.

## 2. The finding: the disagreement rate is conditional, not flat

S-C48 measured a flat ~19%. This run shows that number is an **average over two very different populations**.

I split the R4 boards by whether depth 12 and depth 16 chose the same best move — a board where they differ is a
board where the search is still changing its mind — then compared the MultiPV disagreement rate in each stratum:

| population | disagreements | rate | Wilson 95% CI |
|---|---|---|---|
| R4 **unstable** boards (d12 move ≠ d16 move) | **16 / 30** | **53.3%** | [36.1%, 69.8%] |
| R4 **stable** boards (d12 move = d16 move) | 31 / 220 | 14.1% | [10.1%, 19.3%] |
| R5 **random** (replication of S-C48) | 44 / 250 | 17.6% | [13.4%, 22.8%] |
| R4 random (S-C48 original) | 47 / 250 | 18.8% | [14.4%, 24.1%] |

The unstable and stable intervals do not overlap. Two things follow.

**First, the replication is real.** R5 is a fresh seed, drawn the same way, measured the same way, and lands within
1.2 percentage points of R4. S-C48's number is not an artifact of one seed.

**Second, and this is the useful part: the flat rate hides the mechanism.** A display setting can only change the
answer where the answer is not settled. On a position the engine has resolved, MultiPV changes the best move about
1 time in 7; on a position where the search itself is still flipping between moves, it changes the best move **more
often than not**. So "MultiPV changes the answer on ~19% of positions" is true and misleading — the same sentence is
"about half the time, on exactly the positions where you most needed the engine to be right".

That second reading is what a pipeline should act on: the positions to distrust are the near-horizon ones (which is
S-F29's depth-18 finding arriving from a different direction), and MultiPV is not a way to rescue them.

## 3. A mate-number disagreement where both PVs are textbook-valid

R5 board 222 (`2r1k1n1/4p1bQ/1P2B1pp/2pp1pN1/pn3PPP/1RPPP3/1B6/1N2KR2 b`, black to move), depth 12:

| setting | score | first move | PV length | PLY length needed |
|---|---|---|---|---|
| MultiPV 1 | `mate -5` | `b4d3` | 10 | 10 ✓ |
| MultiPV 3 | `mate -6` | `g8f6` | 12 | 12 ✓ |

**Both PVs replay to checkmate at exactly their claimed length**, from two different first moves, at the same depth,
on the same position. At most one of these can be correct. This matters beyond the disagreement count because it is
the **exact shape my own S-C31 recorded as 0 occurrences**: the "right-length-not-mate" class, where the PV is the
right length but proves a *different mate* than the score claims. S-C31's filter catches every SHORT-PV failure I
have seen; it cannot catch this, and S-C31 said so in the abstract. This is the first concrete instance.

I have now annotated the S-C31 row in FINDINGS.md to record that its blind spot has moved from hypothetical to
demonstrated, without changing what the filter claims to do.

### What the independent solver established about board 222

`claimcheck.py` resolves the attacker from the **sign** of the score (`mate -5` means the side to move is being
mated, so the attacker is the other side) and then asks the exhaustive question directly:

| n | can white force mate in ≤ n? | time |
|---|---|---|
| 1 | no | 0.0 s |
| 2 | no | 0.1 s |
| 3 | no | 2.1 s |
| 4 | **no** | 27.3 s (356 k memo entries) |
| 5 | **was still running when this report was written** | — |

So `mate -5` is **not supported by the evidence I have**: white cannot force mate in 4 or fewer, and whether it can
in exactly 5 was not settled before I wrote this. If n=5 completes as *forced*, then `mate -5` is true and it is the
MultiPV-3 `mate -6` that is wrong (a mate six moves away reported where five sufficed). If n=5 is *not forced*, both
engine reports are wrong. I am not guessing which; the run is the answer and it is not in yet.

**One methodological error caught here, mine:** three of my own solver entry points had the attacker wrong in
different ways. `matesolve2.checkpv` assumed the side to move was the attacker, so every negative-mate PV reported
nonsense (it asked the losing side to force a mate). `solve_after_incremental` assumed the first move was played by
the defender, which is false when the side to move is the one being mated. `claimcheck.py` replaces all of it: one
place, sign-resolved, printed explicitly in its output so a reader can check the assumption rather than trust it.

## 4. The planted case behind the zero (S4)

S4 predicted zero score ties among the disagreements. A zero needs a planted case:

| case | expected | result |
|---|---|---|
| MultiPV 1 re-run against its own stored record, 40 boards | 0 differences | **0** |
| depth 1 substituted for depth 12 | DIFF | **caught** |
| bestmove overwritten with `a1a1` | DIFF | **caught** |
| score nudged by 1 cp | DIFF | **caught** |

The comparison reports differences when differences exist, so the 0 ties is a measurement of the engine.

## 5. Honesty notes

- **S5 was killed** and is recorded as killed. I predicted 2–12 mate scores and got 39.
- Board 222's true distance is **unknown** at this writing (§3). The report states it that way.
- The unstable/stable split is defined by a d12-vs-d16 move change — one operational proxy for "search in flux",
  not the same thing as S-F29's depth threshold. The unstable stratum is 30 boards, so its interval is wide.
- Three of my solver tools had the attacker wrong before `claimcheck.py` replaced them; the errors are listed in §3
  because they would each have produced a false defect report if trusted.

## 6. Files

| file | what |
|---|---|
| `PREDICTION.md` | written and pushed before measuring |
| `R5_2541.fens` | 250 positions, seed 2541 |
| `R5_mpv_d12.jsonl` | MultiPV 1 and 3 at depth 12, 250 boards, both settings |
| `rows.md` | the FINDINGS rows as appended |
| `../job1d/claimcheck.py` | the authoritative mate-claim checker (sign-resolved) |
| `../job1d/R4_mpv.jsonl`, `R4_mates.jsonl`, `R4_d16.jsonl` | the R4 data the stratification uses |

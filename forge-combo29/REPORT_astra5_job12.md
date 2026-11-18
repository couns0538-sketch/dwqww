# Astra5 job 12 — the quiet-mate guard at 80,000 nodes

## 1. Step 0

The r15d guard executable retained its job 8 SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. Each bench and perft result came from a fresh process using the built-in evaluation. [Step 0 transcripts](astra5/job12/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
| --- | --- | --- | --- |
| defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Fastchess reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The UHO book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, and `nproc` returned 5. [Build and input checks](astra5/job12/build.txt)

## 2. K12 — equal settings

At 80,000 nodes per move, the two games in each of the 10 opening pairs followed the same move list and scored 1–1. The pentanomial was 0 / 0 / 10 / 0 / 0. [PGN audit](astra5/job12/K12/pgn-audit.txt) · [Opening pairs](astra5/job12/K12/pairs.tsv)

## 3. C12 — unequal node budgets

With 40,000 nodes per move against 80,000, side A scored 14–46–40. Its Elo estimate was -115.23 [-168.05, -62.40]. The upper endpoint was below zero, passing C12’s control. [Pair records](astra5/job12/C12/pairs.tsv) · [Elo calculation](astra5/job12/C12/elo.txt)

## 4. Frozen prediction

C12 ended at 21:14:24Z. Commit `4ef9f2cb9f708710554af8e3bc047c38519c60c5` contained only the forecast and was pushed at 21:15:06Z. Fastchess launched M3 at 21:15:17Z. [Prediction](astra5/job12/prediction.txt) · [Step times](astra5/job12/stamps.txt)

> I used the two 2,000-node seeds and four 20,000-node seeds from jobs 8, 9 and 11. Their pooled estimates were +1.56 and +3.69 Elo, and the 20,000-node seed estimates spanned -4.78 to +7.82. With 300 opening pairs per new seed, I expect considerable uncertainty. I kept a small positive forecast and used the same range for both seeds.

| Match | Forecast Elo | Inclusive range | Observed Elo | Grade |
| --- | --- | --- | --- | --- |
| M3 | +4 | -14 to +22 | -1.16 | inside range, sign missed, point missed |
| M3b | +4 | -14 to +22 | -3.47 | inside range, sign missed, point missed |

## 5. Match results

Both sides ran the same r15d binary with PC20, the built-in evaluation, Threads 1, Hash 16 and OwnBook false. Each A-side option check reached `readyok`. Fastchess used random UHO openings, reversed colors within each pair, ran four concurrent games at fixed nodes per move, and capped games at 300 moves. [Match commands, PGNs and transcripts](astra5/job12)

The original UHO book was the source for each match. Fastchess’s seeded order was retained among eligible openings. The selector excluded every earlier starting position from the 12 PGNs of jobs 8, 9 and 11, plus earlier job 12 matches. It also rejected repeats within each match. Its conservative exclusion key used placement, side to move and castling rights, so changing the en-passant field or move counters could not reintroduce an opening. All 660 opening pairs played in this job used distinct keys and none overlapped the earlier games. [PGN overlap check](astra5/job12/opening-overlap.txt) · [Seeded selection and exclusions](astra5/job12/K12/opening-selection.txt)

For seed 7344, the candidate at shuffled rank 180 had appeared in job 11, M2c round 176. The selector skipped it. [Excluded candidate](astra5/job12/M3b/skipped-opening.txt)

| Match | NullMateGuard A vs B | Nodes A / B | Seed | Games | A W–L–D | Pentanomial | Elo [95%] | Same moves / pairs | Endings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [K12](astra5/job12/K12.pgn) | 0 vs 0 | 80,000 / 80,000 | 7341 | 20 | 4–4–12 | 0 / 0 / 10 / 0 / 0 | +0.00 [+0.00, +0.00] | 10/10 | 8 / 12 / 0 |
| [C12](astra5/job12/C12.pgn) | 0 vs 0 | 40,000 / 80,000 | 7342 | 100 | 14–46–40 | 10 / 19 / 15 / 5 / 1 | -115.23 [-168.05, -62.40] | 0/50 | 60 / 40 / 0 |
| [M3](astra5/job12/M3.pgn) | 2 vs 0 | 80,000 / 80,000 | 7343 | 600 | 149–151–300 | 6 / 60 / 168 / 62 / 4 | -1.16 [-15.61, +13.30] | 3/300 | 300 / 300 / 0 |
| [M3b](astra5/job12/M3b.pgn) | 2 vs 0 | 80,000 / 80,000 | 7344 | 600 | 140–146–314 | 5 / 68 / 161 / 60 / 6 | -3.47 [-18.36, +11.42] | 3/300 | 286 / 314 / 0 |

The five pentanomial bins count opening pairs in which A scored 0, ½, 1, 1½ or 2 points. “Same moves” counts pairs whose two games followed the same move list. Endings are checkmate / draw by rule / 300-move limit. The interval treats an opening pair as one observation. [Calculation](astra5/job12/formula.txt)

## 6. POOL80 and the reading

> POOL80 = every COMPLETE 80,000-node match of this job (pentanomial counts added; a cut match is left out and named). BETTER when POOL80's interval lies wholly above 0 AND M3 alone has a positive Elo; WORSE when it lies wholly below 0 AND M3 alone has a negative Elo; LEVEL otherwise. Also print one row per node count: the pools at 2,000 and 20,000 nodes from jobs 8, 9 and 11 (counts added) and POOL80, each with games, Elo and interval.

| Nodes per move | Included guard matches | Seeds | Games | Pooled pentanomial | Elo [95%] |
| --- | --- | --- | --- | --- | --- |
| 2,000 | M1, M1b | 2 | 4,000 | 6 / 72 / 1834 / 74 / 14 | +1.56 [-0.99, +4.12] |
| 20,000 | M2, M2b, M2c, M2d | 4 | 3,200 | 29 / 253 / 1018 / 255 / 45 | +3.69 [-2.34, +9.72] |
| 80,000 | M3, M3b | 2 | 1,200 | 11 / 128 / 329 / 122 / 10 | -2.32 [-12.69, +8.06] |

**POOL80 measured -2.32 Elo with a 95% interval of [-12.69, +8.06].** M3 alone measured -1.16 Elo. The interval includes zero. The declared reading is **LEVEL**. All scheduled 80,000-node guard matches finished. [Pool evidence](astra5/job12/pools.md)

## Facts

The 80,000-node pooled estimate (-2.32 Elo) was lower than the 20,000-node estimate (+3.69 Elo). At 80,000 nodes, the games within a pair followed identical move lists in 3 of 300 pairs on seed 7343 and 3 of 300 pairs on seed 7344. [Pool comparison](astra5/job12/pools.md) · [Job 12 pair records](astra5/job12)

## Suspicions

The openings may differ in how often the guard encounters a mating threat. The three pooled point estimates vary both the node budget and the opening sample.

## What I did not do

I did not run the different budgets on the same openings or trace individual guard decisions during these matches.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; node counts other than 2,000, 20,000 and 80,000; time controls; a real net.

## What I am not sure about

A changed move list shows a difference in play. It leaves open which quiet-mate test first changed the continuation or which change affected the eventual score.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job12`.

```text
A  forge-combo29/REPORT_astra5_job12.md
M  forge-combo29/astra5/job12/stamps.txt
forge-combo29/astra5/job12:
C12
C12.meta
C12.out
C12.pgn
K12
K12.meta
K12.out
K12.pgn
M3
M3.meta
M3.out
M3.pgn
M3b
M3b-admission.txt
M3b.meta
M3b.out
M3b.pgn
all-openings-audit.txt
audit.py
build.txt
effective-configuration-checks.txt
formula.txt
fresh_openings.py
match-table.md
opening-overlap.txt
paired_elo.py
pool-independent.txt
pool.py
pools.md
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job12/C12:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job12/K12:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job12/M3:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job12/M3b:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt
skipped-opening.txt

forge-combo29/astra5/job12/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
```

# Astra5 job 13 — comparing the guard implementations in play

## 1. Step 0

The r15d guard executable retained its job 8 SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. Each bench and perft result came from a fresh process using the built-in evaluation. [Step 0 transcripts](astra5/job13/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
| --- | --- | --- | --- |
| defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Fastchess reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The UHO book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, and `nproc` returned 5. [Build and input checks](astra5/job13/build.txt)

## 2. Part A — reference guard versus fast guard

NullMateGuard 1 and 2 played from both colors at 20,000 nodes per move on seed 7351. The two games followed the same complete move list in **100 of 100 pairs**. Side A, the reference guard, scored 57–57–86.

The replay found no first differing move in these pairs. Values 1 and 2 agreed throughout this sample of games at a fixed node budget. This comparison did not measure runtime.

The per-round record and both game scores are available for every pair. [Part A readback](astra5/job13/A13/part-a.txt) · [Shared move list for each identical pair](astra5/job13/A13/same-lines.tsv) · [Pair scores](astra5/job13/A13/pairs.tsv) · [PGN](astra5/job13/A13.pgn)

## 3. K13 — identical engines

At 80,000 nodes per move, all 10 opening pairs followed identical move lists and scored exactly 1–1. The pentanomial was 0 / 0 / 10 / 0 / 0. [PGN audit](astra5/job13/K13/pgn-audit.txt) · [Pair records](astra5/job13/K13/pairs.tsv)

## 4. Frozen prediction

K13 ended at 21:52:48Z. Prediction commit `d5a6389d6b75ad3492bab23d7ff7424c2288511e` contained only the forecast and was pushed at 21:53:00Z. Fastchess launched M3c at 21:53:18Z. [Frozen forecast](astra5/job13/prediction.txt) · [Step times](astra5/job13/stamps.txt)

> I used the match results from jobs 8, 9, 11 and 12, and reviewed job 10's search counts. The two earlier 80,000-node seeds scored -1.16 and -3.47 Elo. Their pooled -2.32 Elo gets the most weight because it uses the same node budget. Both new seeds use the same forecast and range.

| Match | Forecast Elo | Inclusive range | Observed Elo | Grade |
| --- | --- | --- | --- | --- |
| M3c | -2 | -18 to +14 | +1.16 | inside range, sign missed, point missed |
| M3d | -2 | -18 to +14 | -8.11 | inside range, sign matched, point missed |

## 5. Match results

Both sides of every match ran the same r15d binary with PC20, the built-in evaluation, Threads 1, Hash 16 and OwnBook false. Each A-side option check reached `readyok`. Fastchess used random UHO openings, reversed colors within each pair, ran four concurrent games at fixed nodes per move, and capped games at 300 moves. [Match commands, PGNs and transcripts](astra5/job13)

For job 13 the selector retained seeded UHO order among eligible openings. All 710 job 13 openings were distinct and absent from the 16 earlier match PGNs, even when treating boards with the same placement, side to move and castling rights as the same opening regardless of en-passant field and move counters. [Actual PGN overlap](astra5/job13/opening-overlap.txt) · [Selection audit](astra5/job13/A13/opening-selection.txt)

Seed 7353 skipped a position that job 9 had played in M1b round 727. Seed 7354 skipped one from job 8, M2 round 283. [Seed 7353](astra5/job13/M3c/skipped-opening.txt) · [Seed 7354](astra5/job13/M3d/skipped-opening.txt)

The table covers all matches from jobs 8, 9, 11, 12 and 13. Job 10 counted search events and played no games. [Job 10 report](REPORT_astra5_job10.md)

| Match | NullMateGuard A vs B | Nodes A / B | Seed | Games | A W–L–D | Pentanomial | Elo [95%] | Same moves / pairs | Endings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [K8](astra5/job8/K8.pgn) | 0 vs 0 | 2,000 / 2,000 | 7311 | 100 | 34–34–32 | 0 / 0 / 50 / 0 / 0 | +0.00 [+0.00, +0.00] | 50/50 | 68 / 32 / 0 |
| [C8](astra5/job8/C8.pgn) | 0 vs 0 | 10,000 / 20,000 | 7312 | 200 | 15–130–55 | 42 / 34 / 21 / 3 / 0 | -227.56 [-271.40, -183.71] | 0/100 | 145 / 55 / 0 |
| [M1](astra5/job8/M1.pgn) | 2 vs 0 | 2,000 / 2,000 | 7313 | 2,000 | 675–654–671 | 2 / 35 / 912 / 42 / 9 | +3.65 [-0.09, +7.39] | 546/1000 | 1329 / 671 / 0 |
| [M2](astra5/job8/M2.pgn) | 2 vs 0 | 20,000 / 20,000 | 7314 | 800 | 239–221–340 | 2 / 63 / 262 / 61 / 12 | +7.82 [-3.59, +19.22] | 21/400 | 460 / 339 / 1 |
| [K9](astra5/job9/K9.pgn) | 0 vs 0 | 2,000 / 2,000 | 7321 | 100 | 35–35–30 | 0 / 0 / 50 / 0 / 0 | +0.00 [+0.00, +0.00] | 50/50 | 70 / 30 / 0 |
| [C9](astra5/job9/C9.pgn) | 0 vs 0 | 10,000 / 20,000 | 7322 | 200 | 21–115–64 | 28 / 43 / 24 / 5 / 0 | -177.22 [-214.44, -139.99] | 0/100 | 136 / 64 / 0 |
| [M1b](astra5/job9/M1b.pgn) | 2 vs 0 | 2,000 / 2,000 | 7323 | 2,000 | 691–694–615 | 4 / 37 / 922 / 32 / 5 | -0.52 [-4.01, +2.97] | 555/1000 | 1385 / 615 / 0 |
| [M2b](astra5/job9/M2b.pgn) | 2 vs 0 | 20,000 / 20,000 | 7324 | 800 | 245–230–325 | 10 / 56 / 254 / 69 / 11 | +6.52 [-5.78, +18.81] | 18/400 | 475 / 325 / 0 |
| [K11](astra5/job11/K11.pgn) | 0 vs 0 | 20,000 / 20,000 | 7331 | 50 | 10–10–30 | 0 / 0 / 25 / 0 / 0 | +0.00 [+0.00, +0.00] | 25/25 | 20 / 30 / 0 |
| [C11](astra5/job11/C11.pgn) | 0 vs 0 | 10,000 / 20,000 | 7332 | 200 | 11–116–73 | 32 / 43 / 23 / 2 / 0 | -202.63 [-240.13, -165.13] | 0/100 | 127 / 73 / 0 |
| [M2c](astra5/job11/M2c.pgn) | 2 vs 0 | 20,000 / 20,000 | 7333 | 800 | 232–220–348 | 6 / 72 / 240 / 68 / 14 | +5.21 [-7.41, +17.84] | 21/400 | 452 / 348 / 0 |
| [M2d](astra5/job11/M2d.pgn) | 2 vs 0 | 20,000 / 20,000 | 7334 | 800 | 213–224–363 | 11 / 62 / 262 / 57 / 8 | -4.78 [-16.66, +7.11] | 19/400 | 437 / 362 / 1 |
| [K12](astra5/job12/K12.pgn) | 0 vs 0 | 80,000 / 80,000 | 7341 | 20 | 4–4–12 | 0 / 0 / 10 / 0 / 0 | +0.00 [+0.00, +0.00] | 10/10 | 8 / 12 / 0 |
| [C12](astra5/job12/C12.pgn) | 0 vs 0 | 40,000 / 80,000 | 7342 | 100 | 14–46–40 | 10 / 19 / 15 / 5 / 1 | -115.23 [-168.05, -62.40] | 0/50 | 60 / 40 / 0 |
| [M3](astra5/job12/M3.pgn) | 2 vs 0 | 80,000 / 80,000 | 7343 | 600 | 149–151–300 | 6 / 60 / 168 / 62 / 4 | -1.16 [-15.61, +13.30] | 3/300 | 300 / 300 / 0 |
| [M3b](astra5/job12/M3b.pgn) | 2 vs 0 | 80,000 / 80,000 | 7344 | 600 | 140–146–314 | 5 / 68 / 161 / 60 / 6 | -3.47 [-18.36, +11.42] | 3/300 | 286 / 314 / 0 |
| [A13](astra5/job13/A13.pgn) | 1 vs 2 | 20,000 / 20,000 | 7351 | 200 | 57–57–86 | 0 / 0 / 100 / 0 / 0 | +0.00 [+0.00, +0.00] | 100/100 | 114 / 86 / 0 |
| [K13](astra5/job13/K13.pgn) | 0 vs 0 | 80,000 / 80,000 | 7352 | 20 | 6–6–8 | 0 / 0 / 10 / 0 / 0 | +0.00 [+0.00, +0.00] | 10/10 | 12 / 8 / 0 |
| [M3c](astra5/job13/M3c.pgn) | 2 vs 0 | 80,000 / 80,000 | 7353 | 600 | 146–144–310 | 7 / 56 / 172 / 58 / 7 | +1.16 [-13.65, +15.96] | 1/300 | 290 / 310 / 0 |
| [M3d](astra5/job13/M3d.pgn) | 2 vs 0 | 80,000 / 80,000 | 7354 | 600 | 152–166–282 | 10 / 63 / 164 / 57 / 6 | -8.11 [-23.49, +7.28] | 3/300 | 318 / 280 / 2 |

The five pentanomial bins count opening pairs in which A scored 0, ½, 1, 1½ or 2 points. “Same moves” counts pairs whose two games followed the same move list. Endings are checkmate / draw by rule / 300-move limit. The interval treats an opening pair as one observation. [Calculation](astra5/job13/formula.txt)

## 6. POOL80 and the reading

> POOL80 = every COMPLETE 80,000-node match of jobs 12 and 13 (pentanomial counts added; a cut or missing match is left out and named). BETTER when POOL80's interval lies wholly above 0 AND M3c alone has a positive Elo; WORSE when it lies wholly below 0 AND M3c alone has a negative Elo; LEVEL otherwise. Also the row per node count of job 12 (2,000 / 20,000 / 80,000 nodes, every complete seed of jobs 8, 9, 11, 12 and 13 added).

| Nodes per move | Included guard matches | Seeds | Games | Pooled pentanomial | Elo [95%] |
| --- | --- | --- | --- | --- | --- |
| 2,000 | M1, M1b | 2 | 4,000 | 6 / 72 / 1834 / 74 / 14 | +1.56 [-0.99, +4.12] |
| 20,000 | M2, M2b, M2c, M2d | 4 | 3,200 | 29 / 253 / 1018 / 255 / 45 | +3.69 [-2.34, +9.72] |
| 80,000 | M3, M3b, M3c, M3d | 4 | 2,400 | 28 / 247 / 665 / 237 / 23 | -2.90 [-10.34, +4.55] |

**POOL80 measured -2.90 Elo with a 95% interval of [-10.34, +4.55].** M3c alone measured +1.16 Elo. The interval includes zero. The declared reading is **LEVEL**. All scheduled 80,000-node guard matches finished. [Pool evidence](astra5/job13/pools.md)

## Facts

The completed 80,000-node seeds gave M3 -1.16, M3b -3.47, M3c +1.16, M3d -8.11 Elo. They contributed 4 equal-sized seed samples to the pooled result. [Match scores and seed counts](astra5/job13/match-table.md)

## Suspicions

At a fixed node budget, two implementations can play the same moves while spending different amounts of time checking for mate. Replaying a common node budget does not estimate that time difference.

## What I did not do

I did not benchmark the two predicate implementations here or run equal-time matches.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; node counts other than 2,000, 20,000 and 80,000; time controls; a real net.

## What I am not sure about

The paired PGNs establish how the tested games unfolded. They leave open whether an untested position would distinguish the two guard implementations, and which quiet-mate guard decisions affected a game’s score.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job13`.

```text
A  forge-combo29/REPORT_astra5_job13.md
M  forge-combo29/astra5/job13/stamps.txt
forge-combo29/astra5/job13:
A13
A13.meta
A13.out
A13.pgn
K13
K13.meta
K13.out
K13.pgn
M3c
M3c.meta
M3c.out
M3c.pgn
M3d
M3d-admission.txt
M3d.meta
M3d.out
M3d.pgn
all-openings-audit.txt
audit.py
build.txt
effective-configuration-checks.txt
formula.txt
fresh_openings.py
match-table.md
opening-overlap.txt
paired_elo.py
part_a.py
pool-independent.txt
pool.py
pools.md
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job13/A13:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
part-a.txt
pgn-audit.txt
same-lines.tsv

forge-combo29/astra5/job13/K13:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job13/M3c:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt
skipped-opening.txt

forge-combo29/astra5/job13/M3d:
elo.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt
skipped-opening.txt

forge-combo29/astra5/job13/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
```

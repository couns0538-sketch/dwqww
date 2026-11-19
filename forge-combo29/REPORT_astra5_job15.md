# Astra5 job 15 — the second clock seed for the quiet-mate guard

## 1. Step 0

Step 0 passed. `nproc` returned 5, and fastchess ran 3 concurrent games. The r15d executable retained its job 8 SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. Each bench and perft result came from a fresh process using the built-in evaluation. [Step 0 transcripts](astra5/job15/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
| --- | --- | --- | --- |
| defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Fastchess reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The UHO book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Build and input checks](astra5/job15/build.txt)

## 2. C15 — unequal clocks

With 5+0.05 against 10+0.1 and guard 0 on both sides, A scored 15–72–113 over 200 games in 100 complete opening pairs. Its estimate was -101.84 [-129.27, -74.41] Elo. The upper endpoint was below zero, passing C15. [PGN audit](astra5/job15/C15/pgn-audit.txt) · [Paired Elo](astra5/job15/C15/elo.txt)

## 3. Frozen prediction

C15 ended at 23:45:45Z. Commit `c6e22f650fe6d33d79022b50dda454abd48fdc26` contained only the prediction and was pushed at 23:45:56Z. Fastchess launched T1b at 23:45:57Z. [Forecast](astra5/job15/prediction.txt) · [Step times](astra5/job15/stamps.txt)

> I used jobs 8 through 14. The earlier clock seed was cut after 55 pairs and estimated -15.80 Elo with a wide interval. I gave that same-clock sample some weight and moved the forecast toward the smaller fixed-node estimates. The range allows for substantial sampling error in another time-limited seed.

| Match | Forecast Elo | Inclusive range | Observed Elo | Grade |
| --- | --- | --- | --- | --- |
| T1b (incomplete) | -7 | -36 to +22 | +9.15 | inside range, sign missed, point missed on completed pairs only |

## 4. Clock match results

Both sides used the r15d guard executable, PC20, the built-in evaluation, Threads 1, Hash 16 and OwnBook false. Fastchess ran three concurrent games and applied a 300-move limit. At 10+0.1, each player started with ten seconds and gained one tenth of a second per move. Each opening was scheduled with colors reversed. All 157 starting positions in this job’s scored PGNs were distinct and absent from the 22 earlier match PGNs. Two additional opening positions had games in progress when the run stopped. The seed reconstruction also found both of those positions to be fresh. [Actual opening check](astra5/job15/T1b/opening-overlap.txt) · [Seeded selection](astra5/job15/C15/opening-selection.txt)

| Match | NullMateGuard A vs B | Time control A / B | Seed | Scored / scheduled games | A W–L–D | Pentanomial | Elo [95%] | Endings (mate / rule draw / move limit / A time losses / B time losses) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C15](astra5/job15/C15.pgn) | 0 vs 0 | 5+0.05 / 10+0.1 | 7371 | 200 / 200 | 15–72–113 | 8 / 48 / 37 / 7 / 0 | -101.84 [-129.27, -74.41] | 87/113/0/0/0 |
| [T1b (incomplete)](astra5/job15/T1b.pgn) | 2 vs 0 | 10+0.1 / 10+0.1 | 7372 | 114 / 600 | 29–26–59 | 0 / 10 / 34 / 13 / 0 | +9.15 [-19.49, +37.78] | 55/59/0/0/0 |
| [T1 (incomplete) · job 14](astra5/job14/T1.pgn) | 2 vs 0 | 10+0.1 / 10+0.1 | 7362 | 110 / 600 | 20–25–65 | 0 / 15 / 31 / 8 / 1 | -15.80 [-47.86, +16.25] | 45/65/0/0/0 |

The five pentanomial bins count color-reversed opening pairs in which A scored 0, ½, 1, 1½ or 2 points. Game endings and points in the table count only complete pairs. The job 14 row is the earlier measured clock seed. [Paired Elo calculation](astra5/job15/formula.txt) · [Job 14 audit](astra5/job14/T1/pgn-audit.txt)

**C15.** Fastchess logged 200 completed games and the PGN audit found 200 game records. The score uses 200 games from 100 complete opening pairs. Every completed game was scored. Across all completed runner records, A lost 0 on time and B lost 0. [Coverage](astra5/job15/C15/coverage.txt) · [PGN audit](astra5/job15/C15/pgn-audit.txt)

**T1b (incomplete).** Fastchess logged 114 completed games and the PGN audit found 114 game records. The score uses 114 games from 57 complete opening pairs. Every completed game was scored. The match stop was recorded at 00:06:33Z. The cutoff was 00:07:12Z. Each retained pair had both PGN results, agreeing runner results and both game-end timestamps before that cutoff. The game IDs that started without a scored finish were 115–117. Across all completed runner records, A lost 0 on time and B lost 0. [Coverage](astra5/job15/T1b/coverage.txt) · [PGN audit](astra5/job15/T1b/pgn-audit.txt)

The first poll found the job at 23:17:12Z and the claim was recorded at 23:17:43Z. Fifty minutes from first read gave 00:07:12Z, earlier than 00:07:43Z from the recorded claim. The runner used the earlier cutoff and looked for the first whole-pair boundary within its final 40 seconds. [Job receipt](astra5/job14/job15-polls.txt) · [Claim and step times](astra5/job15/stamps.txt) · [Match controller](astra5/job15/run_match.py)

## 5. Declared clock pool beside the fixed-node pools

> POOLT = job 14's T1 plus T1b (counts added; a cut or missing match is left out and named): BETTER when its interval lies wholly above 0 AND T1b alone has a positive Elo; WORSE when wholly below 0 AND T1b alone negative; LEVEL otherwise. As description: POOLT beside the node-count pools of jobs 8 to 13. More than 5 losses on time in T1b or C15: say so beside every reading (the clock then measures the machine, not the engines).

| Limit, both sides | Included measured seeds | Games in pool | Pentanomial | Guard 2 vs 0 Elo [95%] |
| --- | --- | --- | --- | --- |
| 2,000 nodes per move | M1, M1b | 4,000 | 6 / 72 / 1834 / 74 / 14 | +1.56 [-0.99, +4.12] |
| 20,000 nodes per move | M2, M2b, M2c, M2d | 3,200 | 29 / 253 / 1018 / 255 / 45 | +3.69 [-2.34, +9.72] |
| 80,000 nodes per move | M3, M3b, M3c, M3d | 2,400 | 28 / 247 / 665 / 237 / 23 | -2.90 [-10.34, +4.55] |
| 10+0.1 per side (POOLT) | none | 0 | — (empty pool) | unavailable |

**POOLT — LEVEL under the “otherwise” clause only.** The excluded seeds were T1 (incomplete), T1b (incomplete). No match completed all 300 pairs, so the pool contains 0 games and has no Elo estimate or 95% interval. The formal label supplies no evidence that the guards have equal strength. [Clock pool](astra5/job15/pools.md) · [Seed eligibility](astra5/job15/eligibility.tsv) · [Fixed-node pools](astra5/job13/pools.md)

## Facts

T1 (incomplete) supplied 55 of 300 scheduled pairs and measured -15.80 [-47.86, +16.25] Elo. T1b (incomplete) supplied 57 of 300 scheduled pairs and measured +9.15 [-19.49, +37.78] Elo. The clock matches allowed the engine to choose how much search time to spend per move. The earlier matches fixed the node budget per move. [Clock and fixed-node comparison](astra5/job15/pools.md)

## Suspicions

Opening choice, time management and changes in which moves the guard searches could each affect the individual clock results.

## What I did not do

I did not measure seconds per node or profile the calls made by the guard.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; time controls other than 10+0.1; a real net.

## What I am not sure about

The observed game scores cannot distinguish the contribution of search changes, their cost per move, and variation between opening samples.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job15`.

```text
A  forge-combo29/REPORT_astra5_job15.md
M  forge-combo29/astra5/job15/stamps.txt
forge-combo29/astra5/job15:
C15
C15.meta
C15.out
C15.pgn
T1b
T1b.meta
T1b.out
T1b.pgn
all-openings-audit.txt
audit.py
build.txt
clock_results.py
effective-configuration-checks.txt
eligibility.tsv
formula.txt
fresh_openings.py
independent-clock-pool.txt
independent-pooled-results.txt
match-table.md
opening-overlap.txt
paired_elo.py
pools.md
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job15/C15:
coverage.txt
cutoff.txt
effective-clock.txt
elo.txt
game-readback.tsv
games.tsv
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job15/T1b:
coverage.txt
cutoff.txt
effective-clock.txt
elo.txt
game-readback.tsv
games.tsv
launch-decision.txt
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job15/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
```

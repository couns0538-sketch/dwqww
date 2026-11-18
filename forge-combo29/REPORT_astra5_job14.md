# Astra5 job 14 — the quiet-mate guard on the clock

## 1. Step 0

The r15d guard executable retained its job 8 SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. Each bench and perft result came from a fresh process using the built-in evaluation. [Step 0 transcripts](astra5/job14/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
| --- | --- | --- | --- |
| defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Fastchess reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The UHO book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, and `nproc` returned 5. Fastchess ran 3 concurrent games. [Build and input checks](astra5/job14/build.txt)

## 2. C14 — unequal clocks

With 5+0.05 against 10+0.1 and guard 0 on both sides, A scored 25–76–99 over 200 games in 100 complete opening pairs. Its estimate was -90.59 [-120.04, -61.15] Elo. The upper endpoint was below zero, passing C14. [PGN audit](astra5/job14/C14/pgn-audit.txt) · [Paired Elo](astra5/job14/C14/elo.txt)

## 3. Frozen prediction

C14 ended at 22:55:19Z. Commit `cfcfc398bc6a799e5f5326e51c5185744feb23ee` contained only the prediction and was pushed at 22:55:32Z. The launcher read the verified forecast SHA before starting T1 in that same second. [Launch receipt](astra5/job14/T1/launch-decision.txt) [Forecast](astra5/job14/prediction.txt) · [Step times](astra5/job14/stamps.txt)

> I used the fixed-node results of jobs 8 through 13. The measured guard did not establish an advantage at any of the three node budgets. I forecast a small loss on equal clocks because the guard checks additional moves, with a wide range for the unknown time cost and the number of pairs that finish before the cutoff.

| Match | Forecast Elo | Inclusive range | Observed Elo | Grade |
| --- | --- | --- | --- | --- |
| T1 (incomplete) | -4 | -25 to +17 | -15.80 | inside range, sign matched, point missed on completed pairs only |

## 4. Clock match results

Both sides used the r15d guard executable, PC20, the built-in evaluation, Threads 1, Hash 16 and OwnBook false. Fastchess ran three concurrent games and applied a 300-move limit. At 10+0.1, each player started with ten seconds and gained one tenth of a second per move. Each opening was scheduled with colors reversed. All 155 starting positions observed in this job were distinct and absent from the 20 earlier match PGNs. [Actual opening check](astra5/job14/T1/opening-overlap.txt) · [Seeded selection](astra5/job14/C14/opening-selection.txt)

| Match | NullMateGuard A vs B | Time control A / B | Seed | Games scored | A W–L–D | Pentanomial | Elo [95%] | Endings (mate / rule draw / move limit / A time losses / B time losses) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C14](astra5/job14/C14.pgn) | 0 vs 0 | 5+0.05 / 10+0.1 | 7361 | 200 | 25–76–99 | 6 / 52 / 30 / 11 / 1 | -90.59 [-120.04, -61.15] | 101/99/0/0/0 |
| [T1 (incomplete)](astra5/job14/T1.pgn) | 2 vs 0 | 10+0.1 / 10+0.1 | 7362 | 110 / 600 | 20–25–65 | 0 / 15 / 31 / 8 / 1 | -15.80 [-47.86, +16.25] | 45/65/0/0/0 |

The five pentanomial bins count color-reversed pairs in which A scored 0, ½, 1, 1½ or 2 points. The endings columns count games in those complete pairs. [Paired Elo calculation](astra5/job14/formula.txt)

**C14.** Fastchess logged 200 completed games and the PGN audit found 200 game records. The score uses 200 games from 100 complete opening pairs. Every completed game was scored. Across all completed runner records, A lost 0 on time and B lost 0. [Coverage](astra5/job14/C14/coverage.txt) · [PGN audit](astra5/job14/C14/pgn-audit.txt)

**T1 (incomplete).** Fastchess logged 110 completed games and the PGN audit found 110 game records. The score uses 110 games from 55 complete opening pairs. Every completed game was scored. The cutoff was 23:17:00Z. The controller stopped at 23:16:20Z, the first complete-pair boundary in its final 40-second window. Games 111–113 were in progress and had no result. Each retained pair had both PGN results, agreeing runner results and both game-end timestamps before that cutoff. Across all completed runner records, A lost 0 on time and B lost 0. [Coverage](astra5/job14/T1/coverage.txt) · [PGN audit](astra5/job14/T1/pgn-audit.txt)

## 5. Clock reading and fixed-node results

> T1 BETTER when its interval lies wholly above 0, WORSE when wholly below 0, LEVEL otherwise. As description: T1 beside the node-count pools of jobs 8 to 13 (2,000 / 20,000 / 80,000 nodes). More than 5 losses on time in T1 or C14: say so beside every reading (the clock then measures the machine, not the engines).

| Limit, both sides | Matches | Scored games | Pentanomial | Guard 2 vs 0 Elo [95%] |
| --- | --- | --- | --- | --- |
| 2,000 nodes per move | M1, M1b | 4,000 | 6 / 72 / 1834 / 74 / 14 | +1.56 [-0.99, +4.12] |
| 20,000 nodes per move | M2, M2b, M2c, M2d | 3,200 | 29 / 253 / 1018 / 255 / 45 | +3.69 [-2.34, +9.72] |
| 80,000 nodes per move | M3, M3b, M3c, M3d | 2,400 | 28 / 247 / 665 / 237 / 23 | -2.90 [-10.34, +4.55] |
| 10+0.1 per side | T1 (incomplete) | 110 / 600 | 0 / 15 / 31 / 8 / 1 | -15.80 [-47.86, +16.25] |

**T1 (incomplete) — LEVEL.** Only the 55 completed opening pairs enter the displayed interval. Guard 2 scored −15.80 Elo, with a 95% interval from −47.86 to +16.25. [Paired comparison](astra5/job14/pools.md) · [Historical fixed-node pools](astra5/job13/pools.md)

## Facts

T1 (incomplete) used 55 complete opening pairs. The previous fixed-node pools used 4,000, 3,200 and 2,400 scored games respectively. The clocks governed available thinking time and allowed the number of nodes per move to vary. [Clock and node comparison](astra5/job14/pools.md)

## Suspicions

The guard can change both the moves searched and the work spent checking a null cutoff. Time management, openings and their interaction with search could all affect the clock score.

## What I did not do

I did not profile the engine or measure seconds per node in either clock match.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; time controls other than 10+0.1; a real net; one seed only.

## What I am not sure about

The match score alone cannot separate per-node cost, changes in search behavior and opening-sample variation. The fixed-node comparison uses different openings and search limits.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job14`.

```text
A  forge-combo29/REPORT_astra5_job14.md
M  forge-combo29/astra5/job14/stamps.txt
forge-combo29/astra5/job14:
C14
C14.meta
C14.out
C14.pgn
T1
T1.meta
T1.out
T1.pgn
all-openings-audit.txt
audit.py
build.txt
clock_results.py
effective-configuration-checks.txt
formula.txt
fresh_openings.py
independent-pooled-results.txt
match-table.md
opening-overlap.txt
paired_elo.py
pools.md
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job14/C14:
coverage.txt
effective-clock.txt
elo.txt
game-readback.tsv
games.tsv
opening-overlap.txt
opening-preflight.txt
opening-selection.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job14/T1:
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
skipped-opening.txt

forge-combo29/astra5/job14/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
```

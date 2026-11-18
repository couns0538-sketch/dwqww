# Astra5 job 11 — four opening seeds at 20,000 nodes

## 1. Step 0

The r15d guard executable retained its job 8 SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. Each bench and perft result came from a fresh process using the built-in evaluation. [Step 0 transcripts](astra5/job11/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
| --- | --- | --- | --- |
| defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Fastchess reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The UHO book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, and `nproc` returned 5. [Build and input checks](astra5/job11/build.txt)

## 2. K11 — identical engines

All 25 opening pairs replayed the same move list with colors reversed and scored 1–1 at 20,000 nodes per move. The pentanomial was 0 / 0 / 25 / 0 / 0. [Pair-by-pair audit](astra5/job11/K11/pgn-audit.txt)

## 3. C11 — unequal node budgets

The side with 10,000 nodes per move scored 11–116–73 against the side with 20,000. Its estimate was -202.63 [-240.13, -165.13] Elo. The upper endpoint was below zero, passing the C11 control. [Control audit](astra5/job11/C11/pgn-audit.txt) · [Elo calculation](astra5/job11/C11/elo.txt)

## 4. Frozen prediction

C11 ended at 20:54:51Z. Prediction commit `abf04af0849580d4777eb8272fa3af2708f19efb` was pushed alone at 20:55:26Z, before the M2c launch at 20:55:39Z. [Forecast](astra5/job11/prediction.txt) · [Step times](astra5/job11/stamps.txt)

> I used the +7.82 and +6.52 Elo estimates and paired uncertainty from jobs 8 and 9 to set both ranges, shrinking the predicted points toward zero. The forecast does not distinguish the two new random seeds.

| Match | Forecast Elo | Inclusive range | Observed Elo | Grade |
| --- | --- | --- | --- | --- |
| M2c | +4 | -7 to +15 | +5.21 | inside range, sign matched, point missed |
| M2d | +4 | -7 to +15 | -4.78 | inside range, sign missed, point missed |

## 5. Match results

Both sides used the verified r15d guard executable, PC20, the built-in evaluation, Threads 1, Hash 16 and OwnBook false. Fastchess selected random UHO openings and repeated each with colors reversed, with four games running concurrently. Node budgets are per move. Each A-side preflight reached `readyok`. [Job 8](astra5/job8) · [Job 9](astra5/job9) · [Job 11](astra5/job11)

| Match | NullMateGuard A vs B | Nodes A / B | Seed | Games | A W–L–D | Pentanomial | Elo [95%] | Endings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [K8](astra5/job8/K8.pgn) | 0 vs 0 | 2,000 / 2,000 | 7311 | 100 | 34–34–32 | 0 / 0 / 50 / 0 / 0 | +0.00 [+0.00, +0.00] | 68 / 32 / 0 |
| [C8](astra5/job8/C8.pgn) | 0 vs 0 | 10,000 / 20,000 | 7312 | 200 | 15–130–55 | 42 / 34 / 21 / 3 / 0 | -227.56 [-271.40, -183.71] | 145 / 55 / 0 |
| [M1](astra5/job8/M1.pgn) | 2 vs 0 | 2,000 / 2,000 | 7313 | 2,000 | 675–654–671 | 2 / 35 / 912 / 42 / 9 | +3.65 [-0.09, +7.39] | 1329 / 671 / 0 |
| [M2](astra5/job8/M2.pgn) | 2 vs 0 | 20,000 / 20,000 | 7314 | 800 | 239–221–340 | 2 / 63 / 262 / 61 / 12 | +7.82 [-3.59, +19.22] | 460 / 339 / 1 |
| [K9](astra5/job9/K9.pgn) | 0 vs 0 | 2,000 / 2,000 | 7321 | 100 | 35–35–30 | 0 / 0 / 50 / 0 / 0 | +0.00 [+0.00, +0.00] | 70 / 30 / 0 |
| [C9](astra5/job9/C9.pgn) | 0 vs 0 | 10,000 / 20,000 | 7322 | 200 | 21–115–64 | 28 / 43 / 24 / 5 / 0 | -177.22 [-214.44, -139.99] | 136 / 64 / 0 |
| [M1b](astra5/job9/M1b.pgn) | 2 vs 0 | 2,000 / 2,000 | 7323 | 2,000 | 691–694–615 | 4 / 37 / 922 / 32 / 5 | -0.52 [-4.01, +2.97] | 1385 / 615 / 0 |
| [M2b](astra5/job9/M2b.pgn) | 2 vs 0 | 20,000 / 20,000 | 7324 | 800 | 245–230–325 | 10 / 56 / 254 / 69 / 11 | +6.52 [-5.78, +18.81] | 475 / 325 / 0 |
| [K11](astra5/job11/K11.pgn) | 0 vs 0 | 20,000 / 20,000 | 7331 | 50 | 10–10–30 | 0 / 0 / 25 / 0 / 0 | +0.00 [+0.00, +0.00] | 20 / 30 / 0 |
| [C11](astra5/job11/C11.pgn) | 0 vs 0 | 10,000 / 20,000 | 7332 | 200 | 11–116–73 | 32 / 43 / 23 / 2 / 0 | -202.63 [-240.13, -165.13] | 127 / 73 / 0 |
| [M2c](astra5/job11/M2c.pgn) | 2 vs 0 | 20,000 / 20,000 | 7333 | 800 | 232–220–348 | 6 / 72 / 240 / 68 / 14 | +5.21 [-7.41, +17.84] | 452 / 348 / 0 |
| [M2d](astra5/job11/M2d.pgn) | 2 vs 0 | 20,000 / 20,000 | 7334 | 800 | 213–224–363 | 11 / 62 / 262 / 57 / 8 | -4.78 [-16.66, +7.11] | 437 / 362 / 1 |

The five pentanomial bins count pairs in which A scored 0, ½, 1, 1½ or 2 points. Endings give checkmate / draw by rule / 300-move limit. Each Elo interval uses opening pairs as the observations. [Paired Elo method](astra5/job11/formula.txt)

## 6. POOL20 and the reading

> POOL20 = every COMPLETE 20,000-node match of jobs 8, 9 and 11 (pentanomial counts added; a cut or missing match is left out and named). The pooled Elo with its 95 % interval from the pooled counts. BETTER when POOL20's interval lies wholly above 0 AND M2c alone has a positive Elo; WORSE when it lies wholly below 0 AND M2c alone has a negative Elo; LEVEL otherwise ("level at 20,000 nodes in N seeds"). Also print every seed's Elo side by side, both node counts.

| Nodes per move | First seed Elo | Second seed Elo | Third seed Elo | Fourth seed Elo |
| --- | --- | --- | --- | --- |
| 2,000 | 7313 (M1) **+3.65** | 7323 (M1b) **-0.52** | — | — |
| 20,000 | 7314 (M2) **+7.82** | 7324 (M2b) **+6.52** | 7333 (M2c) **+5.21** | 7334 (M2d) **-4.78** |

POOL20 adds the five opening-pair bins for M2, M2b, M2c, M2d before recalculating Elo and its interval. All four measured 20,000-node matches were complete.

| Guard A vs B | Nodes per move | Seeds | Games | Pooled pentanomial | Elo [95%] | M2c Elo |
| --- | --- | --- | --- | --- | --- | --- |
| 2 vs 0 | 20,000 | 4 | 3,200 | 29 / 253 / 1018 / 255 / 45 | +3.69 [-2.34, +9.72] | +5.21 |

The pooled 95% interval was **+3.69 [-2.34, +9.72] Elo**. It includes zero. The declared reading is **LEVEL — level at 20,000 nodes in 4 seeds**. [Pool readback](astra5/job11/pools.md)

## Facts

At 20,000 nodes, 3 of the 4 completed seed estimates were positive. The two earlier 2,000-node seeds totaled 4,000 games and gave +1.56 [-0.99, +4.12] Elo. Job 11 added games at 20,000 nodes only. [Job 11 seed estimates](astra5/job11/pools.md) · [Job 9 pools](astra5/job9/pools.md)

## Suspicions

Some openings may give the quiet-mate guard more opportunities to affect play. Identifying them would require tracing games from those opening pairs.

## What I did not do

This job tested the guard at a fixed node budget and the built-in evaluation. It did not measure equal-time play or trace guard activations inside the games.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; other node counts; time controls; a real net.

## What I am not sure about

The PGNs identify wins, losses and draws. They leave open which individual game results can be attributed to a quiet-mate threat found by the guard.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job11`.

```text
A  forge-combo29/REPORT_astra5_job11.md
M  forge-combo29/astra5/job11/stamps.txt
forge-combo29/astra5/job11:
C11
C11.meta
C11.out
C11.pgn
K11
K11.meta
K11.out
K11.pgn
M2c
M2c.meta
M2c.out
M2c.pgn
M2d
M2d-admission.txt
M2d.meta
M2d.out
M2d.pgn
audit.py
build.txt
effective-configuration-checks.txt
formula.txt
match-table.md
paired_elo.py
pool-independent.txt
pool.py
pools.md
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job11/C11:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job11/K11:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job11/M2c:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job11/M2d:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job11/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
```

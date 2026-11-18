# Astra5 job 8 — does the exact quiet-mate guard play better?

## 1. Step 0

The r15d guard executable from job 7 matched its original SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. A fresh UCI process advertised `option name NullMateGuard type spin default 0 min 0 max 2`. Each control below used a fresh process and the built-in evaluation. [Gate transcripts](astra5/job8/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
|---|---:|---:|---:|
| Defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

The local build of official fastchess tag `v1.8.3-alpha` reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The full UHO opening book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. The host reported five logical CPUs to `nproc`. [Controller build](astra5/job8/build.txt) · [Book and engine identities](astra5/job8/step0/identities.txt)

## 2. K8 — identical engines

All 50 opening pairs scored exactly 1–1. Their two games had identical move lists and opening FENs after swapping colors. The pentanomial was 0 / 0 / 50 / 0 / 0. Zero variance among these paired scores gives the control its zero-width interval. [PGN audit](astra5/job8/K8/pgn-audit.txt)

## 3. C8 — unequal node budgets

The 10,000-node side scored 15–130–55 against the 20,000-node side over 200 games. Its Elo was -227.56 [-271.40, -183.71]. The estimate was below the −100 Elo threshold and the interval’s upper end was below zero. [Control Elo](astra5/job8/C8/elo.txt)

## 4. Frozen prediction

The forecast was pushed alone at `2ed49628ad5ba08ded3234d1dc41f0c46bb47592` after C8 and before M1. [Prediction](astra5/job8/prediction.txt)

| Match | Forecast, Elo | Range | Observed Elo | Grade |
|---|---:|---|---:|---|
| M1 | +2 | -8 to +12 | +3.65 | Inside range, positive sign matched, point missed |
| M2 | +1 | -13 to +15 | +7.82 | Inside range, positive sign matched, point missed |

## 5. Match results

Both sides used the job 7 r15d guard binary, PC20, built-in evaluation, Threads 1, Hash 16 and OwnBook false. The only difference in C8 was its node budget. M1 and M2 varied only the guard. Fastchess ran four games concurrently with fixed nodes per move and a 300-move cap. It used no clock or score-based resignation or draw adjudication. It selected random UHO openings and repeated each with colors reversed. Each match had a fresh A-side UCI option check.

| Match (seed) | Guard A vs B | Nodes A / B | Games | A W–L–D | Pentanomial | Elo [95%] | Endings |
|---|---|---:|---:|---:|---|---|---|
| [K8](astra5/job8/K8.pgn) (7311) | 0 vs 0 | 2,000 / 2,000 | 100 | 34–34–32 | 0 / 0 / 50 / 0 / 0 | +0.00 [+0.00, +0.00] | 68/32/0 |
| [C8](astra5/job8/C8.pgn) (7312) | 0 vs 0 | 10,000 / 20,000 | 200 | 15–130–55 | 42 / 34 / 21 / 3 / 0 | -227.56 [-271.40, -183.71] | 145/55/0 |
| [M1](astra5/job8/M1.pgn) (7313) | 2 vs 0 | 2,000 / 2,000 | 2,000 | 675–654–671 | 2 / 35 / 912 / 42 / 9 | +3.65 [-0.09, +7.39] | 1329/671/0 |
| [M2](astra5/job8/M2.pgn) (7314) | 2 vs 0 | 20,000 / 20,000 | 800 | 239–221–340 | 2 / 63 / 262 / 61 / 12 | +7.82 [-3.59, +19.22] | 460/339/1 |

Endings are mate / draw by rule / 300-move limit. The five pentanomial bins count pairs where A scored 0, ½, 1, 1½ or 2 points. Elo and its 95% interval use the paired-opening calculation from the pinned fastchess source. Each interval is the estimate plus or minus fastchess’s unrounded margin. [Calculation](astra5/job8/formula.txt)

## 6. Reading

> Both matches are exploratory, one seed each: no verdict. A match whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it; otherwise the row reads "level alone at this node count" (an idea is never closed on one result alone). A cut match gives no reading.

**M1** — level alone at this node count.

**M2** — level alone at this node count.

## Facts

At 2,000 nodes, 546 of 1,000 color-reversed pairs had identical move lists. At 20,000 nodes, 21 of 400 pairs did. The guard and baseline split the points in 912 and 262 pairs respectively. K8 reproduced the control openings move for move. In the measured matches the guard changed the course of games even when the two games of a pair split the points. [M1 pair records](astra5/job8/M1/pairs.tsv) · [M2 pair records](astra5/job8/M2/pairs.tsv)

M2 was admitted after M1 finished. The M1/C8 throughput estimate was 6 minutes 19 seconds, with more than 40 minutes left before the cutoff. [Admission calculation](astra5/job8/M2-admission.txt)

## Suspicions

The guard may change a continuation well before the game ends. Establishing which intervention helped or hurt would require tracing the first diverging move in those paired games.

## What I did not do

I used one fixed seed at each measured node count. The PC’s own engine and network were outside this run.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; other node counts; time controls; a real net (net768 is made up and not used here).

## What I am not sure about

A guard can change moves on selected positions while a single opening sample leaves its effect on game score unresolved. These games do not identify which quiet-mate checks, if any, caused an individual result.

## Pre-commit inventory

`git status --short` followed by `ls -R forge-combo29/astra5/job8` produced this output.

```text
A  forge-combo29/REPORT_astra5_job8.md
M  forge-combo29/astra5/job8/stamps.txt
forge-combo29/astra5/job8:
C8
C8.meta
C8.out
C8.pgn
K8
K8.meta
K8.out
K8.pgn
M1
M1.meta
M1.out
M1.pgn
M2
M2-admission.txt
M2.meta
M2.out
M2.pgn
audit.py
build.txt
formula.txt
paired_elo.py
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job8/C8:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job8/K8:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job8/M1:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job8/M2:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job8/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
identities.txt
pc20.txt
uci.txt
```

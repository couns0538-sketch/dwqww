# Astra5 job 9 — the quiet-mate guard across two opening seeds

## 1. Step 0

The r15d guard executable retained its job 8 SHA-256, `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. Its UCI listing contained `option name NullMateGuard type spin default 0 min 0 max 2`. Each bench and perft result came from a fresh process using the built-in evaluation. [Step 0 transcripts](astra5/job9/step0)

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
| --- | --- | --- | --- |
| defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Fastchess reported `fastchess alpha 1.8.3 20261107-d7b47e8`. The UHO book matched SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, and `nproc` returned 5. [Build and input checks](astra5/job9/build.txt)

## 2. K9 — identical engines

The two games in each of the 50 color-reversed opening pairs followed identical move lists. Every pair scored 1–1, giving pentanomial counts 0 / 0 / 50 / 0 / 0. K8 also replayed all 50 openings move for move. [K9 audit](astra5/job9/K9/pgn-audit.txt) · [K8 audit](astra5/job8/K8/pgn-audit.txt)

## 3. C9 — half the node budget

At 10,000 versus 20,000 nodes, A scored 21–115–64 and measured -177.22 [-214.44, -139.99] Elo. Its upper endpoint was below zero, satisfying the C9 rule. C8 had already passed both job 8 thresholds at -227.56 [-271.40, -183.71] Elo. [C9 calculation](astra5/job9/C9/elo.txt) · [C8 calculation](astra5/job8/C8/elo.txt)

## 4. Frozen prediction

Prediction commit `91e384d5dd621bd0d0dc7aa78ce1125c26b04acc` contained only the forecast. C9 ended at 20:32:19Z and the prediction push was recorded at 20:32:46Z. Fastchess launched M1b at 20:32:53Z. [Frozen text](astra5/job9/prediction.txt)

> I used job 8's positive point estimates and the widths of its paired intervals, moving both predicted points closer to zero for the independent seeds.

| Match | Predicted Elo | Inclusive range | Observed Elo | Grade |
| --- | --- | --- | --- | --- |
| M1b | +2 | -7 to +11 | -0.52 | inside range, sign missed, point missed |
| M2b | +3 | -10 to +16 | +6.52 | inside range, sign matched, point missed |

## 5. Match results

Both sides used r15d, PC20, the built-in evaluation, Threads 1, Hash 16 and OwnBook false. Fastchess drew random UHO openings with each seed and played each opening with colors reversed. Each match used fixed nodes per move, four concurrent games and a 300-move limit. Each A-side option check reached `readyok`. The command and configured options appear in each match’s `.meta` file. [Job 9 match evidence](astra5/job9) · [Job 8 match evidence](astra5/job8)

| Match | NullMateGuard A vs B | Nodes A / B | Seed | Games | A W–L–D | Pentanomial | Elo [95%] | Endings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [K9](astra5/job9/K9.pgn) | 0 vs 0 | 2,000 / 2,000 | 7321 | 100 | 35–35–30 | 0 / 0 / 50 / 0 / 0 | +0.00 [+0.00, +0.00] | 70 / 30 / 0 |
| [C9](astra5/job9/C9.pgn) | 0 vs 0 | 10,000 / 20,000 | 7322 | 200 | 21–115–64 | 28 / 43 / 24 / 5 / 0 | -177.22 [-214.44, -139.99] | 136 / 64 / 0 |
| [M1](astra5/job8/M1.pgn) | 2 vs 0 | 2,000 / 2,000 | 7313 | 2,000 | 675–654–671 | 2 / 35 / 912 / 42 / 9 | +3.65 [-0.09, +7.39] | 1329 / 671 / 0 |
| [M1b](astra5/job9/M1b.pgn) | 2 vs 0 | 2,000 / 2,000 | 7323 | 2,000 | 691–694–615 | 4 / 37 / 922 / 32 / 5 | -0.52 [-4.01, +2.97] | 1385 / 615 / 0 |
| [M2](astra5/job8/M2.pgn) | 2 vs 0 | 20,000 / 20,000 | 7314 | 800 | 239–221–340 | 2 / 63 / 262 / 61 / 12 | +7.82 [-3.59, +19.22] | 460 / 339 / 1 |
| [M2b](astra5/job9/M2b.pgn) | 2 vs 0 | 20,000 / 20,000 | 7324 | 800 | 245–230–325 | 10 / 56 / 254 / 69 / 11 | +6.52 [-5.78, +18.81] | 475 / 325 / 0 |

Pentanomial bins count openings where A scored 0, ½, 1, 1½ or 2 points across the pair. Endings are checkmate / draw by rule / 300-move limit.

## 6. Two-seed pools and reading

> For each node count: POOL = job 8's match plus job 9's match at that node count (pentanomial counts added; a cut or missing match is left out and named). The pooled Elo with its 95 % interval from the pooled counts. BETTER when the pooled interval lies wholly above 0 AND the job 9 match alone has a positive Elo; WORSE when the pooled interval lies wholly below 0 AND the job 9 match alone has a negative Elo; LEVEL otherwise ("level at this node count in two seeds"). Also print, as description, the job 8 and job 9 Elo side by side.

| Nodes per move | Job 8 Elo | Job 9 Elo | Pooled games | Pooled pentanomial | Pooled Elo [95%] | Reading |
| --- | --- | --- | --- | --- | --- | --- |
| 2,000 | +3.65 | -0.52 | 4,000 | 6 / 72 / 1834 / 74 / 14 | +1.56 [-0.99, +4.12] | LEVEL — level at this node count in two seeds |
| 20,000 | +7.82 | +6.52 | 1,600 | 12 / 119 / 516 / 130 / 23 | +7.17 [-1.22, +15.55] | LEVEL — level at this node count in two seeds |

Both pools contain two completed seeds. I added the five bin counts across seeds. With $N=\sum_i n_i$ pairs and $x_i=i/4$, the mean score is $p=\sum_i n_i x_i/N$ and its standard error is $s=\sqrt{\sum_i n_i(x_i-p)^2}/N$. For $L(p)=400\log_{10}(p/(1-p))$, fastchess reports $L(p)$ and the symmetric margin $[L(p+qs)-L(p-qs)]/2$, where $q$ is the 97.5th percentile of the standard normal distribution. [Calculation](astra5/job9/formula.txt) · [Pooled record](astra5/job9/pools.md)

## Facts

At 2,000 nodes, the numbers of color-reversed pairs with identical move lists were 546 of 1,000 on seed 7313 and 555 of 1,000 on seed 7323. At 20,000 nodes, the numbers of color-reversed pairs with identical move lists were 21 of 400 on seed 7314 and 18 of 400 on seed 7324. [Job 8 pair records](astra5/job8) · [Job 9 pair records](astra5/job9)

## Suspicions

Opening choice may affect how often the guard changes a game. The paired scores and move lists identify candidate games for a trace.

## What I did not do

I did not replay the games with tracing to identify the first refused null cutoff.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; other node counts; time controls; a real net.

## What I am not sure about

These games leave open whether a score change came from finding a mating threat or from a later change in move ordering. Both effects can follow a refused cutoff.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job9`.

```text
A  forge-combo29/REPORT_astra5_job9.md
M  forge-combo29/astra5/job9/stamps.txt
forge-combo29/astra5/job9:
C9
C9.meta
C9.out
C9.pgn
K9
K9.meta
K9.out
K9.pgn
M1b
M1b.meta
M1b.out
M1b.pgn
M2b
M2b-admission.txt
M2b.meta
M2b.out
M2b.pgn
audit.py
build.txt
effective-configuration-checks.txt
formula.txt
match-table.md
paired_elo.py
pool.py
pools.md
prediction.txt
run_match.py
stamps.txt
step0

forge-combo29/astra5/job9/C9:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job9/K9:
elo.txt
pairs.tsv
pgn-audit.txt

forge-combo29/astra5/job9/M1b:
elo.txt
pairs.tsv
pgn-audit.txt
two-seed-readback.txt

forge-combo29/astra5/job9/M2b:
elo.txt
pairs.tsv
pgn-audit.txt
two-seed-readback.txt

forge-combo29/astra5/job9/step0:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
uci.txt
```

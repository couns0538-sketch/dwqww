# Astra5 job 21 — NullMateGuard with NullThreatVerify

## 1. Step 0 and match setup

The job 12 executable passed all five known answers in fresh processes. Without setoptions, benches 11 and 13 returned 312,866 and 862,329 nodes, and perft 5 returned 4,865,609. With PC20 and the built-in evaluation the two benches returned 278,024 and 587,276. The executable SHA-256 was `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. `nproc` returned 5, and match concurrency was 4. The runner identified itself as `fastchess alpha 1.8.3 20261107-d7b47e8`. [Build, runner, book and net identities](astra5/job21/step0/build.txt) · [Gate receipts](astra5/job21/step0/gates.txt)

The option declaration was printed exactly as follows. [UCI transcript](astra5/job21/step0/uci.txt)

```text
option name NullThreatVerify type check default false
```

In another fresh process, PC20 + net768 accepted lowercase `true` for NullThreatVerify. The handshake reached `readyok` with the net active and checksum `30ab43b4ba5db5f3`. It produced no unknown-option or invalid-value line. Bench 13 returned **3,853,966 nodes**, compared with the 4,275,906-node baseline, so the option reached the search. [Complete handshake and changed bench](astra5/job21/step0/PC20-net768-NullThreatVerify-true-bench-13.txt)

The three schedules shared no opening positions. Selection excluded 11,815 previously used position keys, including self-play roots and earlier started rounds missing from the PGNs. The schedules list the one-based source book line for each round. [Opening history](astra5/job21/openings/history.txt) · [C21 original line numbers](astra5/job21/openings/C21-lines.tsv) · [B1 original line numbers](astra5/job21/openings/B1-lines.tsv) · [B2 original line numbers](astra5/job21/openings/B2-lines.tsv)

## 2. C21 passed

C21 varied only the node allowance. A searched 10,000 nodes and B searched 20,000, both on PC20 + synthetic net768 with NullMateGuard 0 and NullThreatVerify false. Across 100 complete pairs, A scored -217.35 [-271.11, -163.59] Elo. The 95% upper endpoint was below zero, so the control passed before the forecast was frozen. [C21 paired audit](astra5/job21/C21/pgn-audit.txt) · [C21 setup and times](astra5/job21/C21.meta)

## 3. Frozen prediction and grades

The single-file prediction was pushed at 01:37:24Z. B1’s first PGN game started at 01:37:49Z. The ranges used the guard-alone evidence from jobs 8–15 and allowed for uncertainty about adding verification. [Frozen prediction](astra5/job21/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/e81425e361ba1ab861c0c38358458c4ef651b1bc)

**B1.** The forecast was +2 Elo, range -12 to +16. The observed +4.63 Elo matched the predicted sign and fell inside the range. Its difference from the point estimate was +2.63 Elo.

**B2.** The forecast was -2 Elo, range -14 to +10. The observed +2.32 Elo missed the predicted sign and fell inside the range. Its difference from the point estimate was +4.32 Elo.

## 4. Paired match results

The settings column gives NullMateGuard + NullThreatVerify for each arm. B1 and B2 compare the bundle on A with both options off on B. All matches used the same executable, PC20, synthetic net768, Threads 1, Hash 16 MiB and OwnBook false. Fastchess reversed colors for each opening and enforced the 300-move limit without resign or draw adjudication.

Pentanomial bins count A’s 0, ½, 1, 1½ and 2 points per opening pair. Elo and its symmetric 95% interval follow fastchess’s logistic calculation from the pair distribution. Each game contributes to exactly one ending category.

| Match | Settings (A / B) | Nodes (A / B) | Seed | Games | A W–L–D | Pentanomial | Elo [95%] | Endings (mate / rule / 300-move) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C21](astra5/job21/C21.pgn) | 0 + false / 0 + false | 10,000 / 20,000 | 7391 | 200 | 30–141–29 | [52, 17, 23, 6, 2] | -217.35 [-271.11, -163.59] | 171 / 29 / 0 |
| [B1](astra5/job21/B1.pgn) | 2 + true / 0 + false | 20,000 / 20,000 | 7392 | 1,200 | 526–510–164 | [102, 83, 230, 67, 118] | +4.63 [-13.60, +22.86] | 1036 / 164 / 0 |
| [B2](astra5/job21/B2.pgn) | 2 + true / 0 + false | 2,000 / 2,000 | 7393 | 1,200 | 338–330–532 | [34, 119, 283, 133, 31] | +2.32 [-10.53, +15.16] | 668 / 532 / 0 |

All three schedules completed. The last PGN game ended at 01:47:17Z, before the 02:22:00Z playing cutoff. [Match start, end and checkpoint times](astra5/job21/stamps.txt)

## 5. Declared reading

**LEVEL.** B1 scored +4.63 [-13.60, +22.86] Elo from 600 complete opening pairs. Its 95% interval included zero.

> B1 decides: BUNDLE BETTER when its interval lies wholly above 0; BUNDLE WORSE when wholly below 0; LEVEL otherwise. B2 is description beside it (the PC's self-play depth). A cut B1 is read only on its whole pairs and named "cut". What follows from it (ours, not your work): BETTER = a question for the PC on its own net after its tune; WORSE or LEVEL = the guard is put aside as "level alone and in its bundle with NullThreatVerify, under these settings".

B2 is descriptive at 2,000 nodes. Its estimate was +2.32 [-10.53, +15.16] Elo.

## Facts

The PGN opening, colors, result and ending matched the individual runner completion record for every counted game. Pairs with identical move lists were C21 0/100, B1 1/600, B2 53/600. [C21 paired audit](astra5/job21/C21/pgn-audit.txt) · [B1 paired audit](astra5/job21/B1/pgn-audit.txt) · [B2 paired audit](astra5/job21/B2/pgn-audit.txt)

The search checks the quiet-mate guard on the null-move child. A remaining eligible fail-high can then trigger NullThreatVerify’s second search on the real position. [Source and option semantics](astra5/job21/review/bundle-semantics.txt)

## Suspicions

The two options may affect largely different positions. These games do not count how often either choice changed a cutoff.

## What I did not do

Only the joint configuration was measured against the baseline. There was no NullThreatVerify-only match or timed match.

**What this cannot see**, in the job’s words

> the PC's own net, compiler and processor; the PC's tuned values (its tune is still running); NullThreatVerify alone (only the bundle is played); time controls.

## What I am not sure about

The match cannot separate the two options’ contributions or determine how their interaction would affect games with the PC’s trained net.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job21`.

```text
A  forge-combo29/REPORT_astra5_job21.md
M  forge-combo29/astra5/job21/stamps.txt
forge-combo29/astra5/job21:
B1
B1.meta
B1.out
B1.pgn
B2
B2.meta
B2.out
B2.pgn
C21
C21.meta
C21.out
C21.pgn
audit
build.txt
driver
openings
prediction.txt
review
stamps.txt
step0

forge-combo29/astra5/job21/B1:
B1-config.json
B1-cutoff.txt
B1-effective-audit.txt
B1-live-options.txt
B1-opening-readback.txt
controller.txt
coverage.txt
games.tsv
legality.txt
live-traffic.txt
pairs.tsv
pgn-audit.txt
prefix-receipt.txt
reading.txt
replay.tsv
score.tsv
settings-check.txt
verified.txt

forge-combo29/astra5/job21/B2:
B2-config.json
B2-cutoff.txt
B2-effective-audit.txt
B2-live-options.txt
B2-opening-readback.txt
controller.txt
coverage.txt
games.tsv
legality.txt
live-traffic.txt
pairs.tsv
pgn-audit.txt
prefix-receipt.txt
reading.txt
replay.tsv
score.tsv
settings-check.txt
verified.txt

forge-combo29/astra5/job21/C21:
C21-config.json
C21-cutoff.txt
C21-effective-audit.txt
C21-live-options.txt
C21-opening-readback.txt
controller.txt
coverage.txt
games.tsv
legality.txt
live-traffic.txt
pairs.tsv
pgn-audit.txt
prefix-receipt.txt
reading.txt
replay.tsv
score.tsv
settings-check.txt
verified.txt

forge-combo29/astra5/job21/audit:
audit.py
grade.py
live.py
monitor.py
reading.txt
runstage.py
stage-summary.tsv
stats_seed.py

forge-combo29/astra5/job21/driver:
check_effective.py
checkpoints.py
finish_check.py
run_match.py
stage.py

forge-combo29/astra5/job21/openings:
B1-lines.tsv
B1-opening-preflight.txt
B1-skips.tsv
B2-lines.tsv
B2-opening-preflight.txt
B2-skips.tsv
C21-lines.tsv
C21-opening-preflight.txt
C21-skips.tsv
check_pgn.py
history-sources.tsv
history.txt
prepare.py
skip_sources.py
skipped-history.tsv

forge-combo29/astra5/job21/review:
bundle-semantics.txt
check-config.py
check-opening-lines.py
opening-crosscheck.txt

forge-combo29/astra5/job21/step0:
PC20-bench-11.txt
PC20-bench-13.txt
PC20-net768-NullThreatVerify-true-bench-13.txt
build.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt
pc20.txt
uci.txt
```

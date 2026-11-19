# Astra5 Job 25 — r15d and kF with two and four search threads

## 1. Step 0 passed

The host reported `nproc 5`. Both executables matched their Job 16 hashes and passed all five pins in fresh processes. Default benches 11 and 13 returned 312,866 and 862,329 nodes and perft 5 returned 4,865,609 on each build. With PC20 and synthetic net768, the benches returned 882,074 and 4,275,906. Both network checks logged `NNUE v3 active` and the load checksum `30ab43b4ba5db5f3`. Fastchess was the same official Linux 1.8.3-alpha release as in Job 24. Part A used the unchanged first 30 lines of that job's 234-position EPD. Each four-field EPD received the standard FEN clocks `0 1`. [Identities and opening hashes](astra5/job25/build.txt) · [Fresh pin transcripts](astra5/job25/step0)

## 2. All three controls passed

- **KA1** matched on all 30 positions. With Threads 1, all eight repeats and both builds agreed on last depth, score, nodes, PV and bestmove. [Position-by-position check](astra5/job25/audit-A/KA1.tsv)
- **CA2** passed on 30 of 30 positions per build. Each position produced more than one last-info node count over eight two-thread repeats. The required minimum was 15. [Variation counts](astra5/job25/audit-A/CA2.tsv)
- **KC1** passed all 20 rounds. Each color swap reproduced the complete move list and gave each build one point. kF scored 20 wins, 20 losses and zero draws. [Paired moves](astra5/job25/audit-C/C1/pairs-independent.tsv)

## 3. Prediction graded

The prediction was committed alone and pushed after KA1, CA2 and KC1. A2 had been collected, and its node-bound comparison remained blinded until that push. For A2 plus A4 the forecast was 0–0 over-budget searches per build. Both recorded zero in 480 searches. The forecast for C2 plus C4 was 0–0 endings outside the rules of chess. All 200 games ended by a named rule, so that range held. kF earned 56.5 points out of 120 in C2 (47.08%), inside the 40%–60% interval. [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/0a089ef6ec51cda7e53d3eaa632d71f93322eb64) · [Prediction and measured start times](astra5/job25/chronology.txt)

## 4. Part A — single searches

Each row covers 30 positions × eight repeats in one persistent engine process. Before every `go nodes 100000` the driver sent `ucinewgame`, waited for `readyok` and sent the FEN. The maximum uses every UCI info line. The checker tested each `bestmove` against python-chess 1.11.2's legal moves and measured the go-to-bestmove interval on a monotonic clock. [Per-search raw references](astra5/job25/audit-A/final/search-readback.tsv) · [Independent check](astra5/job25/audit-A/qa)

| Build | Threads | Searches | Info lines | Largest nodes reported | Searches above 100,064 | Missing bestmove within 60 s | Illegal bestmoves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| r15d | 1 | 240 | 2,664 | 97,985 | 0 | 0 | 0 |
| kF | 1 | 240 | 2,664 | 97,985 | 0 | 0 | 0 |
| r15d | 2 | 240 | 2,463 | 99,395 | 0 | 0 | 0 |
| kF | 2 | 240 | 2,453 | 98,842 | 0 | 0 | 0 |
| r15d | 4 | 240 | 2,263 | 99,711 | 0 | 0 | 0 |
| kF | 4 | 240 | 2,266 | 97,621 | 0 | 0 | 0 |

## 5. Part C — whole games

Both sides used PC20, net768, Hash 16 and `go nodes 50000`. The fixed seed was 2500001 for each tournament. Each opening was repeated with colors reversed. The endings below use fastchess's labels and W–L–D is from kF's side. [Tournament plan](astra5/job25/C/run-plan.tsv) · [PGN and log audit](astra5/job25/audit-C/method.txt)

| Run | Threads | Rounds | Concurrency | Started | Finished | Endings | kF W–L–D | Problem lines |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| [C1](astra5/job25/C/C1/fastchess.log) | 1 | 20 | 3 | 40 | 40 | 24 Black mates, 16 White mates | 20–20–0 | 0 |
| [C2](astra5/job25/C/C2/fastchess.log) | 2 | 60 | 2 | 120 | 120 | 60 Black mates, 8 Draw by 3-fold repetition, 1 Draw by fifty moves rule, 51 White mates | 52–59–9 | 0 |
| [C4](astra5/job25/C/C4/fastchess.log) | 4 | 40 | 1 | 80 | 80 | 43 Black mates, 2 Draw by 3-fold repetition, 1 Draw by fifty moves rule, 34 White mates | 38–39–3 | 0 |

**CC2 passed.** The paired games had different move lists in 60 of 60 rounds. There were no fastchess lines naming an illegal move, lost connection, stall or time loss in C1, C2 or C4. [C2 paired moves](astra5/job25/audit-C/C2/pairs-independent.tsv) · [C4 paired moves](astra5/job25/audit-C/C4/pairs-independent.tsv)

## 6. Declared reading

**HOLDS WITH THREADS.** On both builds, every measured two- and four-thread search returned a legal bestmove within 60 seconds and every info line stayed within 100,064 nodes. Every C2 and C4 game finished by a specified rule of chess. [First-case checks](astra5/job25/audit-A/final/first-cases.txt) · [C2 game audit](astra5/job25/audit-C/C2/summary-independent.json) · [C4 game audit](astra5/job25/audit-C/C4/summary-independent.json)

## 7. For the record

Each row gives the median and inclusive range of the last completed info line across 240 searches. Root move variation counts positions with more than one bestmove across their eight repeats. [Spread data](astra5/job25/audit-A/final/spread.tsv)

### r15d

| Threads | Last depth, median [range] | Last nodes, median [range] | Positions with varying bestmove |
| ---: | --- | --- | ---: |
| 2 | 10 [9–13] | 64,077.5 [11,857–99,395] | 27/30 |
| 4 | 9 [8–12] | 61,013.5 [16,601–99,711] | 28/30 |

### kF

| Threads | Last depth, median [range] | Last nodes, median [range] | Positions with varying bestmove |
| ---: | --- | --- | ---: |
| 2 | 10 [9–12] | 61,190.5 [20,149–98,842] | 27/30 |
| 4 | 9 [8–12] | 62,045.0 [18,094–97,621] | 24/30 |

### Most frequent kF moves by position

The table lists every tied kF mode. “Yes” means r15d played each listed move at least once in its eight repeats. For these samples, all tied modes were either present together or absent together. [Counts for every move](astra5/job25/audit-A/final/modes.tsv)

| EPD line | Threads 2 kF mode(s) | Seen in r15d | Threads 4 kF mode(s) | Seen in r15d |
| ---: | --- | --- | --- | --- |
| 1 | `c1f4` | Yes | `c1f4` | Yes |
| 2 | `b2b4` | Yes | `b2b4` | Yes |
| 3 | `e2e3` | Yes | `d1d4` | Yes |
| 4 | `d1b3` | Yes | `d1b3` | Yes |
| 5 | `d1a4` | Yes | `e4e5` | Yes |
| 6 | `b2b4` | Yes | `d1d4` | Yes |
| 7 | `e1c1` | Yes | `e1c1` | Yes |
| 8 | `h2h3` | Yes | `h2h3` | Yes |
| 9 | `e2e4` | Yes | `e2e4` | Yes |
| 10 | `d1d4` | Yes | `d1d4` | Yes |
| 11 | `e1d2` | Yes | `e1d2` | Yes |
| 12 | `d1b3` | Yes | `d1a4` | Yes |
| 13 | `h2h4` | Yes | `h2h4` | Yes |
| 14 | `f3e5` | Yes | `f3e5` | Yes |
| 15 | `d1e1` | Yes | `d1e1` | Yes |
| 16 | `g1h1` | Yes | `d4b5,f2f3` | Yes |
| 17 | `g5f6` | Yes | `g5f6` | Yes |
| 18 | `d3h7` | Yes | `e1d2` | No |
| 19 | `d1c2` | Yes | `d1c2` | Yes |
| 20 | `g5e6` | Yes | `g5e6` | Yes |
| 21 | `c2c4` | Yes | `c2c4` | Yes |
| 22 | `g2g3` | Yes | `d1a4` | Yes |
| 23 | `d1d4` | Yes | `d1d3,h1g1` | No |
| 24 | `g5f6` | Yes | `g5f6` | Yes |
| 25 | `e1f2` | Yes | `e1f2` | Yes |
| 26 | `e1e2` | Yes | `e1e2` | Yes |
| 27 | `e3c5` | Yes | `e1e2` | Yes |
| 28 | `d4f3` | Yes | `d4b5` | No |
| 29 | `e1e2` | Yes | `e1e2` | Yes |
| 30 | `d4c6` | Yes | `g5f6,h2h4` | Yes |

### Paired game outcomes

The pentanomial bins count rounds in which kF earned 0, ½, 1, 1½ or 2 points across the color swap.

| Run | kF W–L–D | Pentanomial |
| --- | --- | --- |
| C2 | 52–59–9 | [17, 3, 22, 6, 12] |
| C4 | 38–39–3 | [8, 2, 21, 1, 8] |

## Facts

At two threads, r15d and kF each varied their bestmove on 27 of 30 positions. At four threads the counts were 28 and 24, respectively. At two threads every kF modal move appeared among r15d's replies. At four threads the exceptions were EPD lines 18, 23 and 28. [Position-level modes and tie rules](astra5/job25/audit-A/final/modes-summary.txt)

## Suspicions

The spread is consistent with workers reaching shared search-table entries in different orders. The runs measured the reported searches and moves. No access trace isolated the cause of an individual divergence. kF's fast single-worker node-stop shortcut requires one worker; the multithread configuration uses the publication and shared-count path. [Source hashes and lines](astra5/job25/audit-A/source-note.txt)

## What I did not do

WHAT THIS CANNOT SEE: a memory error that changes no move and no count (that needs checking builds, another helper's job); more than 4 threads; cases too rare for 480 searches and 200 games; the PC's own build (clang 23 for Windows, its profile) and its trained net; play on the clock with several threads.

## What I am not sure about

The UCI logs bound the node counts the engines reported. They do not independently count visits after the last completed iteration. Eight repeats give a sample of possible bestmoves at each position. The kF point shares describe these openings with a synthetic net and do not establish playing strength.

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job25
 A forge-combo29/REPORT_astra5_job25.md
M  forge-combo29/astra5/job25/stamps.txt
forge-combo29/astra5/job25:
A
C
audit-A
audit-C
build.txt
chronology.txt
prediction.txt
stamps.txt
step0

forge-combo29/astra5/job25/A:
A1
A2
A4
CA2.txt
KA1.txt
controls.py
launch.sh
search_driver.py
search_maxima.py
summaries.tsv

forge-combo29/astra5/job25/A/A1:
kF
r15d

forge-combo29/astra5/job25/A/A1/kF:
maxima.tsv
progress.txt
run.meta
searches.tsv
uci.log

forge-combo29/astra5/job25/A/A1/r15d:
maxima.tsv
progress.txt
run.meta
searches.tsv
uci.log

forge-combo29/astra5/job25/A/A2:
kF
r15d

forge-combo29/astra5/job25/A/A2/kF:
maxima.tsv
progress.txt
run.meta
searches.tsv
uci.log

forge-combo29/astra5/job25/A/A2/r15d:
maxima.tsv
progress.txt
run.meta
searches.tsv
uci.log

forge-combo29/astra5/job25/A/A4:
kF
r15d

forge-combo29/astra5/job25/A/A4/kF:
maxima.tsv
progress.txt
run.meta
searches.tsv
uci.log

forge-combo29/astra5/job25/A/A4/r15d:
maxima.tsv
progress.txt
run.meta
searches.tsv
uci.log

forge-combo29/astra5/job25/C:
C1
C2
C4
part_c.py
read_c.py
run-plan.tsv

forge-combo29/astra5/job25/C/C1:
argv.json
fastchess.log
games.pgn
games.tsv
inputs.json
issues.txt
pairs.tsv
receipt.json
summary.json

forge-combo29/astra5/job25/C/C2:
argv.json
fastchess.log
games.pgn
games.tsv
inputs.json
issues.txt
pairs.tsv
receipt.json
summary.json

forge-combo29/astra5/job25/C/C4:
argv.json
fastchess.log
games.pgn
games.tsv
inputs.json
issues.txt
pairs.tsv
receipt.json
summary.json

forge-combo29/astra5/job25/audit-A:
CA2.tsv
KA1.tsv
audit25.py
final
first_cases.py
qa
source-note.txt
source_note.py

forge-combo29/astra5/job25/audit-A/final:
first-cases.txt
modes-summary.txt
modes.tsv
search-readback.tsv
spread.tsv
summary.tsv
threshold-cases.tsv

forge-combo29/astra5/job25/audit-A/qa:
A1-forensics.txt
A2-forensics.txt
A4-forensics.txt
uci_forensics.py

forge-combo29/astra5/job25/audit-C:
C1
C2
C4
all-independent.tsv
audit_c25.py
method.txt
threaded-prediction-independent.txt

forge-combo29/astra5/job25/audit-C/C1:
games-independent.tsv
pairs-independent.tsv
problems-independent.tsv
summary-independent.json

forge-combo29/astra5/job25/audit-C/C2:
games-independent.tsv
pairs-independent.tsv
problems-independent.tsv
summary-independent.json

forge-combo29/astra5/job25/audit-C/C4:
games-independent.tsv
pairs-independent.tsv
problems-independent.tsv
summary-independent.json

forge-combo29/astra5/job25/step0:
build.txt
job22-comparison.txt
kF
pc20.txt
r15d

forge-combo29/astra5/job25/step0/kF:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job25/step0/r15d:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```

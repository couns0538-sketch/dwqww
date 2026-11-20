# grok2 seat 042

Arm 2, id B1b, source seat 080, branch for-fable-and-opus/grok-080, commit e778c1358711c0571e8f5cc4df87083cce98e03a, switch IdeaB1. Model Grok 4.7. exe P is /agent/repos/work/build/forge. exe B is /agent/repos/base/build/forge.

## Patch

sha256 of ~/arm.patch, which is the file fetched as forge-combo29/grok/080/idea.patch.txt:

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm table's sha256. FETCH_HEAD was e778c1358711c0571e8f5cc4df87083cce98e03a. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both succeeded before the build. A later `--check` fails because those hunks are already applied. `git -C /agent/repos/work diff --stat` now:

```
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

The work tree HEAD is still 6b98f2170a3210e71beed04bbd2553972c253ed7. No engine source was committed.

Build: CMake Release, `/usr/bin/g++` (GCC 13.3.0), default `-march=x86-64-v4`. `/usr/bin/c++` is Clang 18 and failed to link libstdc++, so it was not used. The CPU flags include avx512 and bmi2, so FORGE_PORTABLE was left off. CMake reported `The CXX compiler identification is GNU 13.3.0`.

## Honesty

Fresh process per line, no setoption. `python3 read_runs.py honesty` on the raw transcripts:

```
info string bench depth 11 nodes 312866 time 163 nps 1919423
nodes 312866
info string bench depth 13 nodes 862329 time 431 nps 2000763
nodes 862329
info string bench depth 16 nodes 3024920 time 1471 nps 2056369
nodes 3024920
nodes 4865609
```

exe B and exe P both gave those four node counts (312866, 862329, 3024920, 4865609). The known honesty numbers are those four.

## O runs

`python3 read_runs.py orun` on the raw transcripts. Table values are sum 9500069 and first three 41311 / 24872 / 28574 for exe B; IdeaB1 false identical to B; IdeaB1 true sum 9748678, first three 17841 / 25977 / 43905, 200 differ.

```
=== B ===
sum 9500069
first3 41311 24872 28574
=== P off vs B ===
sum 9500069
first3 41311 24872 28574
differ 0
identical True
=== P on vs B ===
sum 9748678
first3 17841 25977 43905
differ 200
identical False
```

Options in the .meta files: the S14 list in the brief's order, then Threads 1, Hash 16, then IdeaB1 false or true on exe P only. exe B was not sent IdeaB1.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both sha256 values match the brief. Seat 042 took every 90th line starting at line 42 (`wc -l ~/mine.epd` was 29245). The last 300 lines were ctl.epd. Chunks used the top: 15 chunks times 250 openings is lines 1-3750.

## C-ARRIVE

`grep -c "setoption name IdeaB1 value true" ~/arrive.log` printed 20. `grep -c -E "unknown option|invalid value|No such option" ~/arrive.log` printed 0. The 20 log lines around the first switch setoption are in arrive_check.txt. fastchess accepted `engine=true`.

## C-HALF

`python3 ~/games_tsv.py pool FULL` on half.tsv, also saved as half_pool.txt:

```
side FULL: games 400 W-L-D 238-26-136 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 38, 90, 65] Elo +205.04 95% [+178.56, +233.85]
```

FULL (20000 nodes) against HALF (10000 nodes), switch false on both. +205.04 is above +20.

## Pool

15 chunks, 7500 games. `python3 ~/games_tsv.py pool ON` wrote POOL.txt:

```
side ON: games 7500 W-L-D 1940-1999-3561 pairs 3750 (openings not in exactly 2 games: 0)
ptnml [172, 954, 1564, 881, 179] Elo -2.73 95% [-7.90, +2.43]
```

Each chunk_*.tsv is 500 lines. Each chunk_*.out contains one `Finished match`. `grep -c -E 'adjudicat|resign'` on every chunk_*.out printed 0. fastchess was not given -draw, -resign, -maxmoves, or -tb.

## Suspicions, not proven

The point estimate is -2.73 Elo for IdeaB1 on versus off. The 95% interval includes 0. I do not treat that as a proven loss.

Every games_tsv row has Termination `normal` (counted on chunk 6: 500 normal). The fastchess .out files still name mates and rule draws. I did not find an adjudication string. I have not proved that `normal` is only used for games that played to a chess ending, only that the .out files say so and the adjudication flags were not passed.

## What I did NOT do

No pull request. No commit of an engine source file, an exe, a net, or a PGN. No second patch. No portable build. No option from the patch except IdeaB1. No chunk after minute 95. No kill of fastchess: chunk 15 finished at 2026-11-20T15:00:28Z and play.sh then printed `minute 95: no new chunk`. The channel fetch found no forge-combo29/soak_all/FABLE_TO_grok2_*.md, so nothing from the channel changed the run. The last 300 lines of mine.epd were not played.

## What I am NOT sure about

I am not sure the morning O-run sent Threads and Hash before the S14 options. This run sent S14, then Threads 1, then Hash 16, then the switch. The node counts still matched the table.

I am not sure a Clang build would have matched. The compiler that produced these numbers is GCC 13.3.0.

The first harness called select on a buffered pipe and stalled after `id name`. A reader thread replaced that, and the honesty and O-run numbers above are from the replacement. I am sure of those files. I am not sure the stalled attempt wrote a partial transcript; the committed honesty files are the successful runs.

The `ls -la` below was taken after this report file existed and immediately before the status text was appended, so the listed size of REPORT.md does not include the status section.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/042/stamps.txt
?? forge-combo29/grok2/042/POOL.txt
?? forge-combo29/grok2/042/REPORT.md
?? forge-combo29/grok2/042/RESULT.txt
```

## ls -la

```
total 2724
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2231 Nov 20 13:33 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56253 Nov 20 14:32 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51350 Nov 20 14:32 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56436 Nov 20 14:37 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 14:37 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56763 Nov 20 14:43 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51572 Nov 20 14:43 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56139 Nov 20 14:49 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51435 Nov 20 14:49 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56742 Nov 20 14:55 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51533 Nov 20 14:55 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  55961 Nov 20 15:00 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51467 Nov 20 15:00 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56446 Nov 20 13:43 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51344 Nov 20 13:43 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56373 Nov 20 13:48 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51469 Nov 20 13:48 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56284 Nov 20 13:54 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51280 Nov 20 13:54 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56461 Nov 20 13:59 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51321 Nov 20 13:59 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56703 Nov 20 14:05 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51313 Nov 20 14:05 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56784 Nov 20 14:10 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51392 Nov 20 14:10 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56322 Nov 20 14:15 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51339 Nov 20 14:15 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56068 Nov 20 14:21 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51412 Nov 20 14:21 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56309 Nov 20 14:26 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 14:26 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:37 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46856 Nov 20 13:37 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:37 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1043 Nov 20 13:37 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42288 Nov 20 13:37 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:28 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:28 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5284 Nov 20 13:28 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5284 Nov 20 13:28 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5286 Nov 20 13:28 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:28 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5497 Nov 20 13:28 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1027 Nov 20 13:37 match.sh
-rw-r--r-- 1 ubuntu ubuntu    782 Nov 20 13:28 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281677 Nov 20 13:28 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 13:28 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281915 Nov 20 13:28 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    815 Nov 20 13:28 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 283171 Nov 20 13:28 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   1391 Nov 20 13:30 o_summary.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:37 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   2138 Nov 20 13:25 read_runs.py
-rw-r--r-- 1 ubuntu ubuntu   6122 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    805 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   6835 Nov 20 13:28 uci_harness.py
```

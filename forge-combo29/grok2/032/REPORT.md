# Seat 032, arm 2 (B1b)

Arm 2, source seat 080, branch for-fable-and-opus/grok-080, commit e778c1358711c0571e8f5cc4df87083cce98e03a. SWITCH IdeaB1. exe P is the base commit 6b98f2170a3210e71beed04bbd2553972c253ed7 plus that patch. exe B is the base commit with no patch. GCC 13.3.0, Release, default -march=x86-64-v4. The CPU has avx512 and bmi2, so FORGE_PORTABLE was left off.

## Patch sha256 and git apply

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch && git apply ~/arm.patch` in the work tree exited 0. The work tree diff after apply:

```
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

No engine source was committed.

## Honesty numbers

Fresh process, no setoption. Nodes from the saved stdout:

```
honesty_B_bench11.txt info string bench depth 11 nodes 312866 time 163 nps 1919423
honesty_B_bench13.txt info string bench depth 13 nodes 862329 time 433 nps 1991521
honesty_B_bench16.txt info string bench depth 16 nodes 3024920 time 1424 nps 2124241
honesty_B_perft5.txt nodes 4865609
honesty_P_bench11.txt info string bench depth 11 nodes 312866 time 163 nps 1919423
honesty_P_bench13.txt info string bench depth 13 nodes 862329 time 432 nps 1996131
honesty_P_bench16.txt info string bench depth 16 nodes 3024920 time 1444 nps 2094819
honesty_P_perft5.txt nodes 4865609
```

Known pins: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match. honesty=ok.

## Three O runs

`o_table.py` read the raw transcripts. Pasted summary lines:

```
SUMMARY B sum 9500069 first 41311 24872 28574
SUMMARY OFF sum 9500069 first 41311 24872 28574 differ 0
SUMMARY ON sum 9748678 first 17841 25977 43905 differ 200
```

Arm table, run (1): sum 9500069, first three 41311 / 24872 / 28574. Run (2): equal to (1) on all 200. Run (3): sum 9748678, first three 17841 / 25977 / 43905, 200 differ. The pasted lines are those integers. Every position row is in o_table_out.txt.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

2632036 lines. Both hashes match the brief. book=ok. Seat 032 takes every 90th line of that file, starting at line 32. The last 300 lines were the controls and were not used in the chunks.

## C-ARRIVE and C-HALF

arrive_check.txt, the two counts:

```
grep -c setoption name IdeaB1 value true: 20
grep -c unknown option|invalid value|No such option: 0
```

20 is at least 1, and the refusal count is 0. arrive=ok.

C-HALF, pasted `games_tsv.py pool FULL` on half.tsv:

```
side FULL: games 400 W-L-D 236-33-131 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 11, 37, 90, 62] Elo +194.34 95% [+167.93, +222.96]
```

FULL's Elo is +194.34, above +20. PASS. half_elo=+194.34.

## POOL.txt and chunks

17 chunks, each 500 games, 8500 games. `wc -l chunk_*.tsv` total was 8500. Pasted POOL.txt:

```
side ON: games 8500 W-L-D 2238-2251-4011 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [211, 1027, 1789, 1010, 213] Elo -0.53 95% [-5.43, +4.36]
```

## suspicions, not proven

A pool of the first 6500 games, printed while play was still going, was Elo -0.91 with an interval that included 0. That was a partial count. The result above is the full 8500.

One PGN header from chunk 17 has Termination "normal" and Result "0-1". fastchess stdout for the matches names mates and draws. A count of lines matching adjudicat, resign, or maxmoves across chunk_1.out through chunk_17.out was 0. fastchess wrote config.json in the repository root with resign.enabled false and draw.enabled false. match.sh does not pass -draw, -resign, or -maxmoves. I do not have a proof that "Termination normal" means anything other than fastchess's own header word.

## what I did NOT do

No pull request. No engine source committed. The patch lives only in the work tree outside the seat branch. No exe, no PGN, no net, and no config.json committed. IdeaB1_Lanes, IdeaB1_Fade, IdeaB1_Scale, and IdeaB1_Cap were never sent. The last 300 openings were not played in the chunks. Arm 10 was not used. No force-push, and no write to any branch but for-fable-and-opus/grok2-032. No FABLE_TO_grok2 file was on the handoff branch at the fetches.

## what I am NOT sure about

From chunk 8 onward, the commit and the channel fetch were done by ~/commit_chunks.sh: sleep 240, commit a chunk only when its tsv has 500 lines and its .out is present, push, fetch the handoff branch. I started it so a repeated check would not drop a chunk. The pushes are the "chunks N" lines in stamps.txt. I did not watch every fetch by hand. No channel file was present at the fetches the script logged.

RESULT.txt uses id=B1b because that is the name on the arm 2 row. If id was meant to be the model, the seat file says Grok 4.7.

## times: see stamps.txt

STEP 1 stamp is 2026-11-20T13:22:02Z. play.sh printed "minute 95: no new chunk" after chunk 17. Chunk 17's stamp in play.log is 2026-11-20T14:57:59Z. Nothing was killed at minute 103.

## git status --short

```
 M forge-combo29/grok2/032/stamps.txt
?? config.json
?? forge-combo29/grok2/032/POOL.txt
?? forge-combo29/grok2/032/REPORT.md
?? forge-combo29/grok2/032/RESULT.txt
```

## ls -la

```
total 3004
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2245 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56119 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56021 Nov 20 14:27 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51513 Nov 20 14:27 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56309 Nov 20 14:32 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51316 Nov 20 14:32 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56643 Nov 20 14:37 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51591 Nov 20 14:37 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56433 Nov 20 14:42 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 14:42 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56191 Nov 20 14:47 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51287 Nov 20 14:47 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56246 Nov 20 14:52 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51460 Nov 20 14:52 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56539 Nov 20 14:57 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51640 Nov 20 14:57 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56866 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51325 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56192 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51264 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56402 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51251 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56332 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51359 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56427 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51407 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56199 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51444 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56389 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56334 Nov 20 14:12 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51608 Nov 20 14:12 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56332 Nov 20 14:17 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 14:17 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:24 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46702 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:31 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42322 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    241 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    241 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    998 Nov 20 13:25 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    784 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308941 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:25 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309244 Nov 20 13:25 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    817 Nov 20 13:25 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 310421 Nov 20 13:25 o_P_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   3092 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   6034 Nov 20 13:26 o_table_out.txt
-rwxr-xr-x 1 ubuntu ubuntu   1550 Nov 20 13:25 o_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5521 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    630 Nov 20 15:05 stamps.txt
```

# REPORT seat 040

Arm 10, id K3, source seat none. SWITCH HindsightDepth. The arm has no patch: exe P is exe B. Model line in SEAT.txt: Grok 4.7.

## Patch

No patch file. sha256 not applicable. `git apply` was not run. `patch=none`.

Both work trees were added at 6b98f2170a3210e71beed04bbd2553972c253ed7. Only `../base` was compiled. The one binary was used for exe B and exe P, which is what this arm specifies.

Build: g++ 13.3.0, CMake Release, GCC's libstdc++. This machine has AVX-512 and BMI2, so FORGE_PORTABLE was left off and FORGE_MARCH stayed the default x86-64-v4. `/usr/bin/c++` is clang 18 and failed to link libstdc++, so the build set `CMAKE_CXX_COMPILER=g++`. Exe path `/agent/repos/base/forge-combo29/build/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, id name `Chess Engine Forge 6.4.24 candidate`. Nothing of the build was committed.

## Honesty

`honesty.sh` ran a fresh process per line, with no setoption. Nodes:

```
honesty_B_bench11.txt: info string bench depth 11 nodes 312866
honesty_B_bench13.txt: info string bench depth 13 nodes 862329
honesty_B_bench16.txt: info string bench depth 16 nodes 3024920
honesty_B_perft5.txt: nodes 4865609
honesty_P_bench11.txt: info string bench depth 11 nodes 312866
honesty_P_bench13.txt: info string bench depth 13 nodes 862329
honesty_P_bench16.txt: info string bench depth 16 nodes 3024920
honesty_P_perft5.txt: nodes 4865609
```

Those are the known numbers (312866, 862329, 3024920, 4865609) on both exes. `honesty=ok`.

## Three O runs

`o_table.py` read `o_B.txt`, `o_P_off.txt`, and `o_P_on.txt`. Its first lines:

```
B n=200 sum=9500069 first3=41311 24872 28574
P_off n=200 sum=9500069 first3=41311 24872 28574
P_on n=200 sum=9845650 first3=23395 31504 35958
P_off_equal_to_B 200 of 200
P_on_differ_from_B 200 of 200
```

Against the table: run (1) 9,500,069 and 41,311 / 24,872 / 28,574; run (2) equal on all 200; run (3) for K3 9,845,650 and 23,395 / 31,504 / 35,958 with 200 differing. All three match. `off_identical=yes`, `on_sum=9845650`, `on_ok=yes`.

S14, Threads 1, and Hash 16 were sent in that order. Run (1) did not send the switch. Run (2) sent `HindsightDepth false`. Run (3) sent `HindsightDepth true`. The .meta files name the same exe path and sha256.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  uho.zip
2632036 lines
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  uho.epd
```

Both hashes match the brief. `book=ok`. This seat took line 40 and every 90th line after it: 29245 lines in mine.epd. The last 300 are the controls and were not played. A check of played FEN values against those 300 found 0 overlaps. ON was white in 5250 games and black in 5250.

## C-ARRIVE

`arrive_check.txt` records the two counts from the trace log:

```
grep -c setoption name HindsightDepth value true:
20
grep -c unknown option|invalid value|No such option:
0
```

The same file has the 20 log lines around the first `setoption name HindsightDepth value true`, sent to the engine named ON. `arrive=ok`.

## C-HALF

`games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 240-22-138 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 4, 41, 88, 67] Elo +212.37 95% [+186.61, +240.39]
```

FULL (20000 nodes) against HALF (10000 nodes), switch false on both. Elo is above +20. `half_elo=+212.37`.

## Pool

21 chunks, each 500 games. Every `chunk_*.out` contains `Finished match`. A search of those 21 logs for adjudicat, resign, maxmoves, and syzygy returned 0 hits in each file. Match commands did not pass `-draw`, `-resign`, `-maxmoves`, or `-tb`.

`POOL.txt`, from `games_tsv.py pool ON` on the 21 tsv files:

```
side ON: games 10500 W-L-D 2937-2677-4886 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [232, 1206, 2149, 1396, 267] Elo +8.60 95% [+4.21, +13.00]
```

## Suspicions, not proven

The tsv Termination column is `normal` on every game. The fastchess logs for the controls and the chunks describe mates, fifty-move draws, threefold repetition, and insufficient material. I did not find an adjudication word in the chunk logs. I am not treating "normal" as proof of the end reason; the Result field is what the pool uses.

Chunk 21 started when elapsed minutes were still 94 (14:57:03 is 94 minutes after 13:22:04) and finished at 15:01:09. That is inside the rule that the last chunk may end by minute 103.

## What I did not do

I did not build a second binary. I did not apply a patch. I did not open a pull request. I did not play a new chunk after minute 95. I did not rerun this morning's seat 030 PGN through `games_tsv.py`, so I did not reproduce that script's published sample line myself. I did not send any option other than S14, Threads, Hash, OwnBook false, and HindsightDepth.

After chunks 1-4, fastchess had written an untracked `config.json` in the repository because `play.sh` had been started with the repository as its current directory. I stopped play after chunk 4 (the running chunk was allowed to finish), deleted that untracked file, and started `play.sh` again from `/home/ubuntu`. It continued at chunk 5. No opening was repeated to add games.

## What I am not sure about

`id=K3` in RESULT.txt is the arm-table name for arm 10. The engine's `id name` is `Chess Engine Forge 6.4.24 candidate`.

The first O harness buffered the engine pipe and timed out before `uciok`. The transcripts in this folder are from the replacement harness, which reads the pipe itself, and `o_table.py` matches the table. I am sure of those committed numbers. I am not sure a different UCI timing would change them; the table match is the check I have.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/040/stamps.txt
?? forge-combo29/grok2/040/POOL.txt
?? forge-combo29/grok2/040/REPORT.md
?? forge-combo29/grok2/040/RESULT.txt
?? forge-combo29/grok2/040/chunk_21.out
?? forge-combo29/grok2/040/chunk_21.tsv
```

## ls -la

```
total 3424
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2170 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56204 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51312 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51389 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56257 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51493 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56058 Nov 20 14:27 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 14:27 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56250 Nov 20 14:31 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51357 Nov 20 14:31 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56239 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51530 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56365 Nov 20 14:40 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51361 Nov 20 14:40 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56165 Nov 20 14:44 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51369 Nov 20 14:44 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56609 Nov 20 14:48 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51590 Nov 20 14:48 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  55913 Nov 20 14:52 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51583 Nov 20 14:52 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55887 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51179 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56584 Nov 20 14:57 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 14:57 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56260 Nov 20 15:01 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51563 Nov 20 15:01 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56326 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51276 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56750 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51592 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56569 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51725 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56487 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51516 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51377 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56188 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51282 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56081 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51519 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56079 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51546 Nov 20 14:11 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46834 Nov 20 13:32 half.out
-rwxr-xr-x 1 ubuntu ubuntu    989 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42221 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:28 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:28 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:28 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:28 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:28 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:28 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:28 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:28 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:28 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:28 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:28 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:28 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    832 Nov 20 13:28 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu    973 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308920 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu   5381 Nov 20 13:27 o_harness.py
-rw-r--r-- 1 ubuntu ubuntu    838 Nov 20 13:27 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 308976 Nov 20 13:27 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    837 Nov 20 13:27 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 309131 Nov 20 13:27 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   1683 Nov 20 13:25 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   5916 Nov 20 13:28 o_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5755 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    230 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     78 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1060 Nov 20 15:03 stamps.txt
```

The listing was taken before this status-and-ls section was written into REPORT.md, so the byte count shown for REPORT.md is the size before that insertion. Every other name in the listing is the file that was committed with it.

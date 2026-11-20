# grok2 seat 019

## Arm and source seat

Arm 9, id S13. Source seat 016. Branch `for-fable-and-opus/grok-016`. Commit `cdde64371237fe7778c713655c0c4b5c957a5fe2`. Switch `IdeaS13`.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed:

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

That is the arm 9 sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree exited 0. `git -C /agent/repos/work diff --stat` printed:

```
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

The patch was not committed. Exe P is `/tmp/forge-work/forge`. Exe B is `/tmp/forge-base/forge`.

## Honesty numbers

Both exes were release builds with CMake and `/usr/bin/g++` (GCC 13.3.0). The machine has AVX-512 and BMI2, so the build used the default `-march=x86-64-v4` and did not set `FORGE_PORTABLE`. A fresh process per line, no `setoption`. Last line of each raw file:

```
== honesty_B_bench11.txt
info string bench depth 11 nodes 312866 time 167 nps 1873449
== honesty_B_bench13.txt
info string bench depth 13 nodes 862329 time 434 nps 1986933
== honesty_B_bench16.txt
info string bench depth 16 nodes 3024920 time 1502 nps 2013928
== honesty_B_perft5.txt
nodes 4865609
== honesty_P_bench11.txt
info string bench depth 11 nodes 312866 time 175 nps 1787805
== honesty_P_bench13.txt
info string bench depth 13 nodes 862329 time 462 nps 1866512
== honesty_P_bench16.txt
info string bench depth 16 nodes 3024920 time 1452 nps 2083278
== honesty_P_perft5.txt
nodes 4865609
```

Known targets: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. All eight matched. Meta files record the exes used for the O runs: B sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, P sha256 `018e977106c57cebbf6cb0339c95c93d9a8117232849895dc94833fbf19adbfc`, id name `Chess Engine Forge 6.4.24 candidate`.

## Three O runs

`python3 forge-combo29/grok2/019/o_table.py` read the raw transcripts (nodes from the last info line before bestmove) and printed:

```
B   sum 9500069 first 41311 24872 28574
OFF sum 9500069 first 41311 24872 28574 differ 0
ON  sum 9722445 first 19900 22525 42778 differ 200
expected B sum 9500069 first 41311 24872 28574
expected ON sum 9722445 first 19900 22525 42778 differ 200
```

Against the arm table: run (1) sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Run (2) equal on all 200 positions. Run (3) sum 9,722,445, first three 19,900 / 22,525 / 42,778, 200 differ. S14 was sent once per process, in the listed order, then Threads 1 and Hash 16. Run (3) also sent `setoption name IdeaS13 value true`. `IdeaS13_Lookback` and `IdeaS13_ReduceDivisor` were left at their defaults.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. Seat 019 took every 90th line starting at line 19 (`wc -l ~/mine.epd` was 29245). The last 300 lines were held back for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE: `grep -c "setoption name IdeaS13 value true"` was 20. `grep -c -E "unknown option|invalid value|No such option"` was 0. The two counts and the 20 log lines are in `arrive_check.txt`.

C-HALF: `python3 ~/games_tsv.py pool FULL` printed, and `half_pool.txt` holds:

```
side FULL: games 400 W-L-D 260-24-116 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 3, 35, 85, 77] Elo +235.45 95% [+208.38, +265.26]
```

FULL's Elo is +235.45, above +20.

## POOL.txt and chunks

20 chunks, 10000 games. `wc -l` of `chunk_*.tsv` summed to 10000. No `FAILED` line in `~/play.log`. `~/play.out` ended with `minute 95: no new chunk`. `POOL.txt` is the pasted output of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/019/chunk_*.tsv`:

```
side ON: games 10000 W-L-D 2602-2730-4668 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [227, 1298, 2068, 1190, 217] Elo -4.45 95% [-8.89, -0.00]
```

## Suspicions, not proven

The upper end of the pool interval prints as -0.00. That is two-decimal rounding of a tiny negative number. I did not recompute it with more digits, so I do not know how far below zero the unrounded bound sits.

## What I did NOT do

I did not open a pull request. I did not commit an engine source file or a binary. I did not send the patch's extra spin options. I did not pass draw, resign, maxmoves, or tablebase adjudication. I did not switch to arm 10. I did not repeat an opening. I did not build with `FORGE_PORTABLE`. The channel fetch found no `FABLE_TO_grok2_<N>.md`. I did not kill fastchess; chunk 20 finished and play.sh stopped itself.

## What I am NOT sure about

S14 was sent once at the start of each O-run process, then each position got `ucinewgame`, `position`, and `go depth 12`. I did not resend S14 before every position. The known node counts matched. The default `c++` on this machine is Clang 18 and failed to link `libstdc++`; the exes that matched the honesty numbers were built with GCC 13.3.0. I did not also build with Clang.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/019/stamps.txt
?? forge-combo29/grok2/019/POOL.txt
?? forge-combo29/grok2/019/REPORT.md
?? forge-combo29/grok2/019/RESULT.txt
```

## ls -la

```
total 3200
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2250 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56421 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51385 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56912 Nov 20 14:20 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 14:20 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56372 Nov 20 14:24 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51524 Nov 20 14:24 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56371 Nov 20 14:29 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51696 Nov 20 14:29 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56109 Nov 20 14:33 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51379 Nov 20 14:33 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56398 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51525 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56218 Nov 20 14:42 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51466 Nov 20 14:42 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56260 Nov 20 14:46 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51576 Nov 20 14:46 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56094 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51485 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56510 Nov 20 14:55 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 14:55 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51183 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56208 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51724 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56589 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51522 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56116 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51257 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56324 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51401 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56047 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51280 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56009 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51281 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56363 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56390 Nov 20 14:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51463 Nov 20 14:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56698 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51367 Nov 20 14:11 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46398 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1036 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42377 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1020 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    850 Nov 20 13:25 o1_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281882 Nov 20 13:25 o1_B.raw
-rw-r--r-- 1 ubuntu ubuntu   1908 Nov 20 13:25 o1_B.rows
-rw-r--r-- 1 ubuntu ubuntu    885 Nov 20 13:25 o2_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282040 Nov 20 13:25 o2_off.raw
-rw-r--r-- 1 ubuntu ubuntu   1908 Nov 20 13:25 o2_off.rows
-rw-r--r-- 1 ubuntu ubuntu    884 Nov 20 13:25 o3_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282252 Nov 20 13:25 o3_on.raw
-rw-r--r-- 1 ubuntu ubuntu   1906 Nov 20 13:25 o3_on.rows
-rw-r--r-- 1 ubuntu ubuntu   4060 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1675 Nov 20 13:26 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5582 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    695 Nov 20 15:02 stamps.txt
```

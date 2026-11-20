# Seat 037 arm 7

Arm 7, K4a. Source seat 093. Commit ddc850cbf04b8c7a8592624037844077b33c8ab0. Switch IdeaK4.

## Patch

sha256 of ~/arm.patch: e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9
Expected sha256: e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9
git apply --check and git apply on the work tree both exited 0. Work tree diff stat:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
```

## Honesty

Fresh process, no setoption. Expected: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.

```
honesty_B_bench11: info string bench depth 11 nodes 312866 time 166 nps 1884734
honesty_B_bench13: info string bench depth 13 nodes 862329 time 439 nps 1964302
honesty_B_bench16: info string bench depth 16 nodes 3024920 time 1439 nps 2102098
honesty_B_perft5: nodes 4865609
honesty_P_bench11: info string bench depth 11 nodes 312866 time 164 nps 1907719
honesty_P_bench13: info string bench depth 13 nodes 862329 time 433 nps 1991521
honesty_P_bench16: info string bench depth 16 nodes 3024920 time 1437 nps 2105024
honesty_P_perft5: nodes 4865609
```

Both exe B (/agent/repos/base/forge-combo29/build/forge) and exe P (/agent/repos/work/forge-combo29/build/forge) matched every line. Built with CMake, g++ 13.3, Release, default FORGE_MARCH x86-64-v4. The machine has AVX-512 and BMI2, so FORGE_PORTABLE was left off. The default /usr/bin/c++ is Clang 18 and cannot link libstdc++; the build uses g++.

## Three O runs

S14, Threads 1, Hash 16, depth 12, 200 positions. Table is the output of o_table.py on the raw transcripts.

Expected (1) exe B: sum 9500069; first three 41311 / 24872 / 28574.
Expected (2) exe P, IdeaK4 false: equal on all 200.
Expected (3) exe P, IdeaK4 true: sum 8921190; first three 24693 / 26341 / 35070; 200 differ.

```
/agent/repos/dwqww/forge-combo29/grok2/037/o_B.txt n=200 sum=9500069 first3=41311 24872 28574
/agent/repos/dwqww/forge-combo29/grok2/037/o_P_off.txt n=200 sum=9500069 first3=41311 24872 28574
differ_from_/agent/repos/dwqww/forge-combo29/grok2/037/o_B.txt 0
/agent/repos/dwqww/forge-combo29/grok2/037/o_P_on.txt n=200 sum=8921190 first3=24693 26341 35070
differ_from_/agent/repos/dwqww/forge-combo29/grok2/037/o_B.txt 200
```

(1) matches. (2) differs on 0 positions. (3) matches the sum, the first three, and 200 positions differ.

## Book

~/uho.zip sha256 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
Expected zip: 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
~/uho.epd lines 2632036 sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
Expected epd: 2632036 lines, 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
Seat 037 takes every 90th line of the book starting at line 37. The last 300 of that list are the controls and are not used by the chunks.

## C-ARRIVE

match.sh on ctl_arrive.epd, 10 rounds, trace log. Count of "setoption name IdeaK4 value true" is 20. Count of unknown option / invalid value / No such option is 0. The engine accepted engine=true. arrive_check.txt:

```
count setoption name IdeaK4 value true: 20
count unknown option|invalid value|No such option: 0
first switch setoption at log line 522; 20 lines around it:
[Engine] [13:27:13.604760] <     140023680726720>  OFF ---> option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
[Engine] [13:27:13.604762] <     140023680726720>  OFF ---> option name CaptureFutilityDepth type spin default 6 min 0 max 15
[Engine] [13:27:13.604764] <     140023680726720>  OFF ---> option name FailLowContinuationBonus type spin default 0 min 0 max 300
[Engine] [13:27:13.604765] <     140023680726720>  OFF ---> option name IdeaK4_Shrink type spin default 24 min 0 max 200
[Engine] [13:27:13.604767] <     140023680726720>  OFF ---> option name Clear Hash type button
[Engine] [13:27:13.604769] <     140023680726720>  OFF ---> uciok
[TRACE ] [13:27:13.604875] <     140023680726720> fastchess --- Refreshing engine ON
[TRACE ] [13:27:13.604886] <     140023680726720> fastchess --- Sending setoption to engine ON Threads 1
[Engine] [13:27:13.604889] <     140023680726720>  ON <--- setoption name Threads value 1
[TRACE ] [13:27:13.604898] <     140023680726720> fastchess --- Sending setoption to engine ON IdeaK4 true
[Engine] [13:27:13.604900] <     140023680726720>  ON <--- setoption name IdeaK4 value true
[TRACE ] [13:27:13.604903] <     140023680726720> fastchess --- Sending setoption to engine ON Hash 16
[Engine] [13:27:13.604904] <     140023680726720>  ON <--- setoption name Hash value 16
[TRACE ] [13:27:13.604907] <     140023680726720> fastchess --- Sending setoption to engine ON OwnBook false
[Engine] [13:27:13.604909] <     140023680726720>  ON <--- setoption name OwnBook value false
[TRACE ] [13:27:13.604912] <     140023680726720> fastchess --- Sending setoption to engine ON LmrQuietBase 93
[Engine] [13:27:13.604914] <     140023680726720>  ON <--- setoption name LmrQuietBase value 93
[TRACE ] [13:27:13.604917] <     140023680726720> fastchess --- Sending setoption to engine ON LmrQuietDivisor 205
[Engine] [13:27:13.604919] <     140023680726720>  ON <--- setoption name LmrQuietDivisor value 205
[TRACE ] [13:27:13.604922] <     140023680726720> fastchess --- Sending setoption to engine ON LmrNoisyBase 13
```

## C-HALF

FULL 20000 nodes versus HALF 10000 nodes, IdeaK4 false on both. pool of half.tsv:

```
side FULL: games 400 W-L-D 234-25-141 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 9, 43, 78, 70] Elo +201.43 95% [+174.01, +231.33]
```

FULL Elo is above +20. Passed.

## Pool

Chunks: 21. Each committed chunk tsv line count (500 expected except the total line):

```
  10500 total
```

POOL.txt:

```
side ON: games 10500 W-L-D 2767-2828-4905 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [245, 1330, 2167, 1257, 251] Elo -2.02 95% [-6.40, +2.37]
```

## Suspicions, not proven

The running pool sat near 0 Elo for the whole match, with the 95% interval covering both a small loss and a small gain at every check I made. Nothing in the games looked like adjudication: chunk logs end on mate, repetition, or the fifty-move rule. No claim that IdeaK4 gains or loses Elo beyond POOL.txt.

## What I did not do

I did not open a pull request. I did not change engine source. I did not send IdeaK4_Shrink. I did not pass -draw, -resign, -maxmoves, or tablebases. I did not replay an opening. I did not play the last 300 lines of mine.epd. I did not re-parse this morning's seat 030 PGN to recheck the known games_tsv.py answer. I did not build with Clang.

## What I am not sure about

I am not sure the games_tsv.py 95% interval is the same estimator fastchess prints for a lopsided result other than C-HALF, where both printed Elo +201.43. I am not sure a FABLE_TO_grok2 file appeared after the last channel fetch below. Channel files found at step 5:

```
none
```

## Times

times: see stamps.txt

git status --short
 M forge-combo29/grok2/037/stamps.txt
?? forge-combo29/grok2/037/POOL.txt
?? forge-combo29/grok2/037/REPORT.md
?? forge-combo29/grok2/037/RESULT.txt

ls -la forge-combo29/grok2/037
total 3336
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2236 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56273 Nov 20 14:13 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 14:13 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56181 Nov 20 14:17 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51445 Nov 20 14:17 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56261 Nov 20 14:22 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:22 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56479 Nov 20 14:26 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 14:26 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56495 Nov 20 14:30 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51449 Nov 20 14:30 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56425 Nov 20 14:34 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51478 Nov 20 14:34 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56154 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51552 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56067 Nov 20 14:43 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51461 Nov 20 14:43 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55851 Nov 20 14:47 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51545 Nov 20 14:47 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56039 Nov 20 14:51 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51528 Nov 20 14:51 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56429 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51153 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56845 Nov 20 14:55 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:55 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56399 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51542 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56351 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51369 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56648 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51534 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56659 Nov 20 13:48 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 13:48 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56329 Nov 20 13:52 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51220 Nov 20 13:52 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56426 Nov 20 13:56 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51201 Nov 20 13:56 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56637 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51365 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 14:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51336 Nov 20 14:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56131 Nov 20 14:09 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51504 Nov 20 14:09 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46890 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1043 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42287 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    236 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 13:24 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 13:24 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    236 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1396 Nov 20 13:24 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281784 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    850 Nov 20 13:25 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281813 Nov 20 13:25 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    849 Nov 20 13:25 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 280854 Nov 20 13:25 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   3649 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    421 Nov 20 13:25 o_table.out
-rw-r--r-- 1 ubuntu ubuntu   1068 Nov 20 13:25 o_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   7308 Nov 20 15:00 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    805 Nov 20 15:00 stamps.txt

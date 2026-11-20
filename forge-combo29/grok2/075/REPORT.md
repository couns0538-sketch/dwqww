# Seat 075 arm 5

Arm 5, id S10, source seat 081, commit b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa, switch IdeaS10. Model Grok 4.7. See SEAT.txt.

## Patch

sha256 of ~/arm.patch, from step2_build.txt:

```
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368
```

That is the arm table sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree exited 0. Diff stat from step2_build.txt: 5 files, 208 insertions, 7 deletions. The patch was not committed. Extra IdeaS10 spin options were left at their defaults and were never sent.

## Honesty

Both exes, one fresh process per line, no setoption. Grep of the raw files:

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

Known pins are 312866, 862329, 3024920, 4865609. Both builds match.

Build: GCC 13.3.0, `CXX=g++ cmake -S forge-combo29 -B /tmp/build-{B,P} -DCMAKE_BUILD_TYPE=Release`. The machine has avx512f and bmi2, so FORGE_PORTABLE stayed off and FORGE_MARCH stayed at the CMake default x86-64-v4.

## Three O runs

`python3 o_table.py o_B.rows o_P_off.rows o_P_on.rows` (re-run at STEP 5, same numbers as o_table.txt):

```
B n=200 sum=9500069 first=41311 / 24872 / 28574
OFF n=200 sum=9500069 first=41311 / 24872 / 28574
ON n=200 sum=9542904 first=41311 / 24872 / 28574
OFF positions differing from B: 0
ON positions differing from B: 10
```

Table for exe B: sum 9500069, first three 41311 / 24872 / 28574. Matched.
Table for switch false: equal to exe B on all 200. Matched.
Table for IdeaS10 true: sum 9542904, first three 41311 / 24872 / 28574, 10 positions differ. Matched.

FEN file sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines.

## Book

```
book_zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
book_epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
book_lines 2632036
```

Both sha256 values match the brief. Seat 075 took every 90th line starting at line 75: 29245 lines in mine.epd. The last 300 are the controls. Chunks used lines 1 through 4750 (19 times 250).

## C-ARRIVE

`grep -c "setoption name IdeaS10 value true"` on the trace log: 20.
`grep -c -E "unknown option|invalid value|No such option"`: 0.
Twenty log lines around the first setoption are in arrive_check.txt. The engine accepted IdeaS10 true and false.

## C-HALF

half_pool.txt, from `python3 games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 236-35-129 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 9, 44, 84, 63] Elo +192.01 95% [+165.76, +220.42]
```

FULL at 20000 nodes against HALF at 10000 nodes. Elo +192.01 is above +20. Pass.

## Pool

19 chunks, 9500 games. Each chunk_*.tsv is 500 lines. play.log has no FAILED line. Pasted POOL.txt:

```
side ON: games 9500 W-L-D 2484-2548-4468 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [155, 924, 2638, 896, 137] Elo -2.34 95% [-6.26, +1.58]
```

## suspicions, not proven

None. The match interval includes 0.

## what I did NOT do

No pull request. No engine source committed. No adjudication flags. The patch's extra spin options were not sent. Openings were not repeated. The reserved last 300 lines of mine.epd were not played. No FABLE_TO_grok2 file was on the handoff branch at any fetch, so nothing there changed this run. Arm 10 was not played.

## what I am NOT sure about

The arrive trace shows fastchess sending IdeaS10 before Hash. match.sh lists nodes and the S14 options on -each, and the switch on -engine. I did not prove that fastchess sends every -each option in source order. C-ARRIVE showed the switch value and no unknown-option line. The O runs, which set options in the written order, matched the known node counts.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/075/stamps.txt
?? forge-combo29/grok2/075/POOL.txt
?? forge-combo29/grok2/075/REPORT.md
?? forge-combo29/grok2/075/RESULT.txt
?? forge-combo29/grok2/075/chunk_19.out
?? forge-combo29/grok2/075/chunk_19.tsv
```

## ls -la

```
total 3144
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2177 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    379 Nov 20 13:33 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56229 Nov 20 14:19 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51512 Nov 20 14:19 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55996 Nov 20 14:24 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51538 Nov 20 14:24 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56490 Nov 20 14:28 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51386 Nov 20 14:28 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56982 Nov 20 14:33 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51510 Nov 20 14:33 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56212 Nov 20 14:37 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 14:37 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56562 Nov 20 14:42 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51588 Nov 20 14:42 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56287 Nov 20 14:47 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51369 Nov 20 14:47 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56484 Nov 20 14:51 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51529 Nov 20 14:51 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56206 Nov 20 14:56 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51423 Nov 20 14:56 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56153 Nov 20 15:01 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51312 Nov 20 15:01 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55964 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51089 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56420 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51252 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56695 Nov 20 13:48 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51456 Nov 20 13:48 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56140 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56093 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51301 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56423 Nov 20 14:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 14:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56404 Nov 20 14:06 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51468 Nov 20 14:06 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56370 Nov 20 14:10 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51460 Nov 20 14:10 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56288 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46643 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1033 Nov 20 13:33 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42242 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    249 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    249 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1211 Nov 20 13:26 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1017 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    771 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281958 Nov 20 13:27 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:27 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu    806 Nov 20 13:27 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282272 Nov 20 13:27 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:27 o_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu    805 Nov 20 13:27 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282327 Nov 20 13:27 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:27 o_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu   5650 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1276 Nov 20 13:27 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    215 Nov 20 13:28 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4399 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    664 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1097 Nov 20 13:28 step2_build.txt
```

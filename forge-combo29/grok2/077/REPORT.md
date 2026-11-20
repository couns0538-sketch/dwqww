# grok2 seat 077

Arm 7, K4a. Source seat 093. Switch IdeaK4. Source commit ddc850cbf04b8c7a8592624037844077b33c8ab0.

## Patch

sha256 of ~/arm.patch, and the work tree after git apply:

```
$ sha256sum ~/arm.patch
e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9  /home/ubuntu/arm.patch
$ git -C /agent/repos/work rev-parse HEAD
6b98f2170a3210e71beed04bbd2553972c253ed7
$ git -C /agent/repos/work diff --stat
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
$ git cat-file -t ddc850cbf04b8c7a8592624037844077b33c8ab0
commit
```

That sha256 is the arm 7 sha256. git apply --check and git apply both exited 0 before the build. The diff stat is the applied patch on the base commit.

I built with g++ 13.3.0 (`-DCMAKE_CXX_COMPILER=g++`) because `/usr/bin/c++` is Clang 18 and its link failed with `cannot find -lstdc++`. The CPU has AVX-512 and BMI2, so I did not set FORGE_PORTABLE. Exe B is `/home/ubuntu/build-b/forge`. Exe P is `/home/ubuntu/build-p/forge`.

## Honesty

Raw lines from the honesty files (one fresh process each, no setoption):

```
honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 176 nps 1777647
honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 518 nps 1664727
honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1500 nps 2016613
honesty_B_perft5.txt:nodes 4865609
honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 213 nps 1468854
honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 480 nps 1796518
honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1484 nps 2038355
honesty_P_perft5.txt:nodes 4865609
```

Known numbers: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match.

## Three O runs

`rows.py` reading `o_B.txt`, `o_Poff.txt`, `o_Pon.txt`:

```
B n=200 sum=9500069 first=41311 / 24872 / 28574
Poff n=200 sum=9500069 first=41311 / 24872 / 28574
Pon n=200 sum=8921190 first=24693 / 26341 / 35070
Poff_differ_from_B=0
Pon_differ_from_B=200
```

Known run (1): sum 9500069, first three 41311 / 24872 / 28574. Run (2) matches run (1) on all 200 positions. Known run (3) for IdeaK4: sum 8921190, first three 24693 / 26341 / 35070, 200 differ. All three match. Threads 1 and Hash 16 were sent before the fourteen S14 options, then IdeaK4 false or true. IdeaK4_Shrink was not sent. The engine advertises it at its default 24.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both sha256 values match the brief. Seat 077 takes line 77 and every 90th line after it. `mine.epd` has 29244 lines. The last 300 are the controls and were not used as chunk openings.

## C-ARRIVE and C-HALF

arrive_check.txt counts:

```
$ grep -c "setoption name IdeaK4 value true" ~/arrive.log
20
$ grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

The engine log shows `ON <--- setoption name IdeaK4 value true`.

`games_tsv.py pool FULL` on half.tsv:

```
side FULL: games 400 W-L-D 242-28-130 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 3, 46, 81, 69] Elo +207.46 95% [+180.83, +236.48]
```

FULL's Elo is above +20.

## POOL

18 chunks, 9000 games. `games_tsv.py pool ON` on `chunk_*.tsv`, written to POOL.txt:

```
side ON: games 9000 W-L-D 2463-2350-4187 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [215, 1072, 1815, 1181, 217] Elo +4.36 95% [-0.41, +9.14]
```

## suspicions, not proven

The point estimate is +4.36 Elo. The 95% interval includes 0, from -0.41 to +9.14. That is not a demonstrated gain.

Every tsv row has Termination `normal`. fastchess stdout for the same games names mates, 3-fold repetition, stalemate, and insufficient material. I did not treat `normal` as a second measurement.

## what I did NOT do

I did not open a pull request. I did not edit engine source. I did not play arm 10. I did not send IdeaK4_Shrink. I did not adjudicate, resign, or cap the move count. I did not repeat an opening. I did not commit a PGN, an executable, or the net.

## what I am NOT sure about

I am not sure the PGN Termination header is more specific than `normal`; the chunk out files are the place that names mate and draw causes.

The handoff branch had no `FABLE_TO_grok2_*.md` at the fetches in this run, including the fetch just before this report. I am not sure a file landed after that fetch.

## times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/077/stamps.txt
?? forge-combo29/grok2/077/POOL.txt
?? forge-combo29/grok2/077/REPORT.md
?? forge-combo29/grok2/077/RESULT.txt
$ ls -la forge-combo29/grok2/077
total 3040
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2237 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:31 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56293 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56443 Nov 20 14:27 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 14:27 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56155 Nov 20 14:31 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51475 Nov 20 14:31 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55991 Nov 20 14:36 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:36 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56099 Nov 20 14:41 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51552 Nov 20 14:41 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56178 Nov 20 14:45 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51375 Nov 20 14:45 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56240 Nov 20 14:50 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:50 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56283 Nov 20 14:55 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51573 Nov 20 14:55 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56289 Nov 20 14:59 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51580 Nov 20 14:59 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56336 Nov 20 13:40 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51269 Nov 20 13:40 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56124 Nov 20 13:45 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51184 Nov 20 13:45 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56319 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51397 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56405 Nov 20 13:54 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51337 Nov 20 13:54 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56335 Nov 20 13:59 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51344 Nov 20 13:59 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56175 Nov 20 14:04 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51225 Nov 20 14:04 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56351 Nov 20 14:09 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51585 Nov 20 14:09 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56700 Nov 20 14:13 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51354 Nov 20 14:13 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56223 Nov 20 14:17 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:17 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:27 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:34 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46712 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu   1040 Nov 20 13:34 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42270 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:26 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:26 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    249 Nov 20 13:26 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    251 Nov 20 13:26 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    249 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    251 Nov 20 13:26 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3042 Nov 20 13:26 honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1024 Nov 20 13:34 match.sh
-rw-r--r-- 1 ubuntu ubuntu    776 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 282055 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    810 Nov 20 13:27 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 282088 Nov 20 13:27 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    809 Nov 20 13:27 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 281046 Nov 20 13:27 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   4494 Nov 20 13:28 o_rows.txt
-rw-r--r-- 1 ubuntu ubuntu   5585 Nov 20 13:27 orun.py
-rw-r--r-- 1 ubuntu ubuntu    513 Nov 20 13:28 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:34 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4929 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   1696 Nov 20 13:27 rows.py
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    706 Nov 20 15:05 stamps.txt
```

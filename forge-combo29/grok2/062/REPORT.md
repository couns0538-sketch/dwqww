# Seat 062, arm 2 (B1b)

Arm 2, source seat 080, branch for-fable-and-opus/grok-080, commit e778c1358711c0571e8f5cc4df87083cce98e03a, switch IdeaB1. exe P is the patched engine. exe B is the plain engine at 6b98f2170a3210e71beed04bbd2553972c253ed7.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed the arm table's sha256. `git apply --check` and `git apply` both exited 0 on the work tree before the build. `patch_check.txt` records the hash and `git diff --stat` after apply:

```
sha256sum ~/arm.patch
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
expected d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196
FETCH_HEAD of for-fable-and-opus/grok-080 was e778c1358711c0571e8f5cc4df87083cce98e03a
git diff --stat in the work tree after git apply --check and git apply
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

The release build used g++ 13.3 (`CMAKE_CXX_COMPILER=g++`). `/usr/bin/c++` is Clang 18 and could not link libstdc++. The CPU has AVX-512 and BMI2, so the build left `FORGE_PORTABLE` off and used the default `-march=x86-64-v4`. IdeaB1_Lanes, IdeaB1_Fade, IdeaB1_Scale and IdeaB1_Cap were left at their defaults.

## Honesty numbers

`honesty.sh`, a fresh process per line, no setoption. Known targets: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes hit them:

```
forge-combo29/grok2/062/B_bench11.txt:info string bench depth 11 nodes 312866 time 174 nps 1798080
forge-combo29/grok2/062/B_bench13.txt:info string bench depth 13 nodes 862329 time 500 nps 1724658
forge-combo29/grok2/062/B_bench16.txt:info string bench depth 16 nodes 3024920 time 1494 nps 2024712
forge-combo29/grok2/062/P_bench11.txt:info string bench depth 11 nodes 312866 time 166 nps 1884734
forge-combo29/grok2/062/P_bench13.txt:info string bench depth 13 nodes 862329 time 456 nps 1891072
forge-combo29/grok2/062/P_bench16.txt:info string bench depth 16 nodes 3024920 time 1458 nps 2074705
nodes 4865609
nodes 4865609
```

The two `nodes 4865609` lines are the last lines of `B_perft5.txt` and `P_perft5.txt`.

## Three O runs

`summarize_o.py` reading the raw transcripts. Known targets: exe B sum 9500069, first 41311 / 24872 / 28574; switch false identical on all 200; switch true sum 9748678, first 17841 / 25977 / 43905, 200 differ. The script printed:

```
file forge-combo29/grok2/062/O_B.txt
positions 200
sum 9500069
first 41311 24872 28574
---
file forge-combo29/grok2/062/O_off.txt
positions 200
sum 9500069
first 41311 24872 28574
differ_from_first 0
---
file forge-combo29/grok2/062/O_on.txt
positions 200
sum 9748678
first 17841 25977 43905
differ_from_first 200
```

The 200 rows are the committed output of the same script in `compare_off.txt` and `compare_on.txt`. Raw transcripts are `O_B.txt`, `O_off.txt`, `O_on.txt`, with `.meta` beside each.

## Book sha256

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
wc -l ~/mine.epd ~/ctl.epd ~/ctl_arrive.epd ~/ctl_half.epd
  29245 /home/ubuntu/mine.epd
    300 /home/ubuntu/ctl.epd
     10 /home/ubuntu/ctl_arrive.epd
    200 /home/ubuntu/ctl_half.epd
  29755 total
```

Zip and epd match the brief. Seat 062 takes every 90th line starting at line 62.

## C-ARRIVE and C-HALF

C-ARRIVE counts from `arrive_check.txt` (the 20 log lines around the first switch setoption are in that file):

```
setoption name IdeaB1 value true: 20
unknown option|invalid value|No such option: 0
```

C-HALF, `games_tsv.py pool FULL` on `half.tsv` (400 games, 200 pairs). Pass was Elo above +20:

```
side FULL: games 400 W-L-D 226-40-134 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 50, 92, 51] Elo +174.99 95% [+150.72, +200.96]
```

## POOL.txt and chunks

15 chunks, each 500 games, 7500 games. `play.log` has no FAILED line. `games_tsv.py pool ON` wrote `POOL.txt`:

```
side ON: games 7500 W-L-D 2018-2049-3433 pairs 3750 (openings not in exactly 2 games: 0)
ptnml [179, 958, 1516, 909, 188] Elo -1.44 95% [-6.68, +3.81]
```

## Suspicions, not proven

The 20-game C-ARRIVE printout in `arrive.out` shows ON behind OFF. That is the trace match of 20 games, and it is not the measured result. The measured pool is the 7500-game `POOL.txt` above. I did not see a harness fault: switch-off matched exe B on all 200 positions, switch-on matched the morning node counts, and the pool had 0 openings that were not in exactly 2 games.

## What I did NOT do

I did not open a pull request. I did not add adjudication, a move limit, or tablebases. I did not send the extra IdeaB1 spin options. I did not fall back to arm 10. I did not commit a PGN, an executable, a net, or an engine source file. I did not push any branch except for-fable-and-opus/grok2-062. No `FABLE_TO_grok2_<N>.md` was on the handoff branch at the fetches in STEP 1 and at the chunk pushes. I did not repeat an opening.

## What I am NOT sure about

I am not sure this x86-64-v4 binary is byte-identical to the PC binary. The honesty numbers and the three O runs matched the published counts. fastchess writes a running results block many times inside `half.out` and the chunk `.out` files. The Elo figures in this report are the `games_tsv.py` lines, not those blocks. I did not read every PGN by hand. `games_tsv.py` accepted all 15 chunks.

## times: see stamps.txt

The last part below is the pasted output of `git status --short` and `ls -la` of this folder.

```
$ git status --short
 M forge-combo29/grok2/062/stamps.txt
?? config.json
?? forge-combo29/grok2/062/POOL.txt
?? forge-combo29/grok2/062/REPORT.md
?? forge-combo29/grok2/062/RESULT.txt
?? forge-combo29/grok2/062/chunk_15.out
?? forge-combo29/grok2/062/chunk_15.tsv

$ ls -la forge-combo29/grok2/062
total 2788
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2129 Nov 20 13:33 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:29 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    461 Nov 20 13:38 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:29 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:29 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  55702 Nov 20 14:33 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51418 Nov 20 14:33 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56410 Nov 20 14:38 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51240 Nov 20 14:38 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56134 Nov 20 14:44 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51465 Nov 20 14:44 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56357 Nov 20 14:49 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51483 Nov 20 14:49 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56369 Nov 20 14:54 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51445 Nov 20 14:54 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56407 Nov 20 15:00 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 15:00 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56254 Nov 20 13:43 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51161 Nov 20 13:43 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56138 Nov 20 13:49 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51168 Nov 20 13:49 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56274 Nov 20 13:54 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51341 Nov 20 13:54 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56680 Nov 20 13:59 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51321 Nov 20 13:59 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56685 Nov 20 14:05 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51370 Nov 20 14:05 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55960 Nov 20 14:11 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51081 Nov 20 14:11 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56048 Nov 20 14:16 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51546 Nov 20 14:16 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  55870 Nov 20 14:22 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51275 Nov 20 14:22 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56728 Nov 20 14:27 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51343 Nov 20 14:27 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   3944 Nov 20 13:30 compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu   3946 Nov 20 13:30 compare_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:32 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46787 Nov 20 13:37 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:38 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1035 Nov 20 13:32 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42287 Nov 20 13:37 half.tsv
-rwxr-xr-x 1 ubuntu ubuntu    729 Nov 20 13:28 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1019 Nov 20 13:32 match.sh
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 13:30 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu 307945 Nov 20 13:30 O_B.txt
-rw-r--r-- 1 ubuntu ubuntu    850 Nov 20 13:30 O_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309928 Nov 20 13:30 O_off.txt
-rw-r--r-- 1 ubuntu ubuntu    849 Nov 20 13:30 O_on.meta
-rw-r--r-- 1 ubuntu ubuntu 310430 Nov 20 13:30 O_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   4365 Nov 20 13:29 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    692 Nov 20 13:31 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:29 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:32 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:29 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:29 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   6218 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     74 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 15:02 stamps.txt
-rwxr-xr-x 1 ubuntu ubuntu   2108 Nov 20 13:28 summarize_o.py
```

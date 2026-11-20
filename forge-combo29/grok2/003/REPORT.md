# grok2 seat 003

## Arm and source seat

Seat 003, arm 3, id B8a, source seat 078, switch IdeaB8.
Source commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0 on for-fable-and-opus/grok-078.
`git rev-parse FETCH_HEAD` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-078` printed that commit.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` (the file written by `git show FETCH_HEAD:forge-combo29/grok/078/idea.patch.txt`):

```
b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. `git -C /agent/repos/work diff --stat` after apply:

```
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

The patch is not committed. Engine sources in this branch are the base tree.

Build decision: `/usr/bin/c++` is Clang 18.1.3 and its link failed with `cannot find -lstdc++`. The brief requires g++ (GCC 13 or newer) and GCC's own C++ library. Both exes were configured with `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (g++ 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` has avx512f and bmi2, so FORGE_PORTABLE was left off and FORGE_MARCH stayed the CMake default x86-64-v4.

## Honesty numbers

A fresh process for each line, no setoption. Expected: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

exe B:

```
forge-combo29/grok2/003/honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 211 nps 1482777
forge-combo29/grok2/003/honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 532 nps 1620919
forge-combo29/grok2/003/honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1791 nps 1688955
nodes 4865609
```

exe P:

```
forge-combo29/grok2/003/honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 328 nps 953859
forge-combo29/grok2/003/honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 570 nps 1512857
forge-combo29/grok2/003/honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1788 nps 1691789
nodes 4865609
```

All eight matched. honesty=ok.

## Three O runs

Arm table for B8a, SWITCH IdeaB8 true: sum 9295189; first three 24947 / 29945 / 39302; 200 differ.
Exe B expected: sum 9500069; first three 41311 / 24872 / 28574.
Exe P with the switch false must match exe B on all 200.

`python3 forge-combo29/grok2/003/o_table.py` reading the raw transcripts:

```
file forge-combo29/grok2/003/o_b.txt
positions 200
sum 9500069
first 41311 24872 28574
file forge-combo29/grok2/003/o_off.txt
positions 200
sum 9500069
first 41311 24872 28574
differ 0
file forge-combo29/grok2/003/o_on.txt
positions 200
sum 9295189
first 24947 29945 39302
differ 200
```

(1) matches the base sum and the first three. (2) differs in 0 positions. (3) matches the arm sum, the first three, and 200 positions differ. on_ok=yes. off_identical=yes. IdeaB8_Weight and IdeaB8_Swing were not sent.

## Book sha256

`book_check.txt`:

```
uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine.epd
29245 /home/ubuntu/mine.epd
```

Zip and epd match the brief. Seat 003 took every 90th line of the epd starting at line 3 (29245 lines). book=ok.

## C-ARRIVE and C-HALF

C-ARRIVE: `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`. `arrive_check.txt`:

```
count setoption name IdeaB8 value true
20
count unknown option|invalid value|No such option
0
first match line
398:[Engine] [13:26:29.379451] <     139772982978240>  ON <--- setoption name IdeaB8 value true
20 log lines around that line
[Engine] [13:26:29.379305] <     139772982978240>  OFF ---> option name CaptureFutilityDepth type spin default 6 min 0 max 15
[Engine] [13:26:29.379306] <     139772982978240>  OFF ---> option name FailLowContinuationBonus type spin default 0 min 0 max 300
[Engine] [13:26:29.379308] <     139772982978240>  OFF ---> option name IdeaB8_Weight type spin default 1024 min 0 max 4096
[Engine] [13:26:29.379309] <     139772982978240>  OFF ---> option name IdeaB8_Swing type spin default 48 min 0 max 500
[Engine] [13:26:29.379315] <     139772982978240>  OFF ---> option name Clear Hash type button
[Engine] [13:26:29.379318] <     139772982978240>  OFF ---> uciok
[TRACE ] [13:26:29.379422] <     139772982978240> fastchess --- Refreshing engine ON
[TRACE ] [13:26:29.379437] <     139772982978240> fastchess --- Sending setoption to engine ON Threads 1
[Engine] [13:26:29.379440] <     139772982978240>  ON <--- setoption name Threads value 1
[TRACE ] [13:26:29.379449] <     139772982978240> fastchess --- Sending setoption to engine ON IdeaB8 true
[Engine] [13:26:29.379451] <     139772982978240>  ON <--- setoption name IdeaB8 value true
[TRACE ] [13:26:29.379454] <     139772982978240> fastchess --- Sending setoption to engine ON Hash 16
[Engine] [13:26:29.379455] <     139772982978240>  ON <--- setoption name Hash value 16
[TRACE ] [13:26:29.379458] <     139772982978240> fastchess --- Sending setoption to engine ON OwnBook false
[Engine] [13:26:29.379459] <     139772982978240>  ON <--- setoption name OwnBook value false
[TRACE ] [13:26:29.379462] <     139772982978240> fastchess --- Sending setoption to engine ON LmrQuietBase 93
[Engine] [13:26:29.379464] <     139772982978240>  ON <--- setoption name LmrQuietBase value 93
[TRACE ] [13:26:29.379467] <     139772982978240> fastchess --- Sending setoption to engine ON LmrQuietDivisor 205
[Engine] [13:26:29.379469] <     139772982978240>  ON <--- setoption name LmrQuietDivisor value 205
[TRACE ] [13:26:29.379471] <     139772982978240> fastchess --- Sending setoption to engine ON LmrNoisyBase 13
```

true-count is 20 (at least 1). refusal-count is 0. arrive=ok.

C-HALF: `~/half.sh` is `~/match.sh` with the two engine lines set to FULL nodes=20000 and HALF nodes=10000, both IdeaB8 false, and `nodes=20000` removed from `-each`. `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/003/half.tsv`:

```
side FULL: games 400 W-L-D 242-21-137 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 30, 101, 63] Elo +216.10 95% [+190.85, +243.55]
```

FULL's Elo is +216.10, above +20. half_elo=+216.10. Pass.

## POOL.txt and chunks

18 chunks, each 500 games, 9000 games. `wc -l forge-combo29/grok2/003/chunk_*.tsv` summed to 9000. `play.log` has no FAILED line. `play.out` ends with `minute 95: no new chunk`. No adjudication flags were passed.

`python3 ~/games_tsv.py pool ON forge-combo29/grok2/003/chunk_*.tsv` wrote POOL.txt:

```
side ON: games 9000 W-L-D 2482-2262-4256 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [177, 1052, 1876, 1164, 231] Elo +8.49 95% [+3.81, +13.19]
```

## suspicions, not proven

None. The node counts matched the arm table on all 200 positions, and every chunk pair count in POOL.txt is an opening in exactly 2 games.

## what I did NOT do

- Did not open a pull request.
- Did not commit an engine source file or a binary.
- Did not send IdeaB8_Weight or IdeaB8_Swing.
- Did not turn on FORGE_PORTABLE.
- Did not replay this morning's seat 030 PGN through games_tsv.py.
- Did not start a chunk after play.sh printed `minute 95: no new chunk`.
- Did not kill fastchess. The last chunk had already finished, and play.sh had exited, before minute 103.
- The handoff branch had no `FABLE_TO_grok2_*.md` at the fetches in STEP 1 and at each chunk push, so no channel order was applied.

## what I am NOT sure about

- The arrive log shows fastchess tracing `Sending setoption to engine ON IdeaB8 true` and the engine-direction line the grep counted. I did not attach a tracer to the engine process beyond that log. The same match.sh drove the chunks.
- I did not count nodes inside each match game. The node-limit evidence is C-HALF.
- `git config user.name` was already set to `Cursor Agent`, so I did not set a local `grok agent` identity. Commits use the existing name.

## times: see stamps.txt

```
2026-11-20T13:21:15Z STEP 1
2026-11-20T13:25:07Z STEP 2
2026-11-20T13:30:22Z STEP 3
2026-11-20T13:39:18Z chunks 1
2026-11-20T13:43:33Z chunks 1 2
2026-11-20T13:47:52Z chunks 1 2 3
2026-11-20T13:52:04Z chunks 1 2 3 4
2026-11-20T13:56:27Z chunks 1 2 3 4 5
2026-11-20T14:00:35Z chunks 1 2 3 4 5 6
2026-11-20T14:04:42Z chunks 1 2 3 4 5 6 7
2026-11-20T14:13:11Z chunks 1 2 3 4 5 6 7 8
2026-11-20T14:17:18Z chunks 1 2 3 4 5 6 7 8 9
2026-11-20T14:21:26Z chunks 1 2 3 4 5 6 7 8 9 10
2026-11-20T14:25:34Z chunks 1 2 3 4 5 6 7 8 9 10 11
2026-11-20T14:29:41Z chunks 1 2 3 4 5 6 7 8 9 10 11 12
2026-11-20T14:33:58Z chunks 1 2 3 4 5 6 7 8 9 10 11 12 13
2026-11-20T14:38:04Z chunks 1 2 3 4 5 6 7 8 9 10 11 12 13 14
2026-11-20T14:42:13Z chunks 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
2026-11-20T14:47:03Z chunks 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
2026-11-20T14:51:47Z chunks 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
2026-11-20T14:57:43Z chunks 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18
2026-11-20T14:58:28Z STEP 5
```

## git status --short and ls -la

Captured after `git add` of the step 5 files and before the final add of this appendix.
```
A  forge-combo29/grok2/003/POOL.txt
AM forge-combo29/grok2/003/REPORT.md
A  forge-combo29/grok2/003/RESULT.txt
A  forge-combo29/grok2/003/play_log.txt
M  forge-combo29/grok2/003/stamps.txt
?? config.json
```

```
total 3004
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 14:59 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:20 ..
-rw-r--r-- 1 ubuntu ubuntu   2305 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    256 Nov 20 13:30 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56492 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51542 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56312 Nov 20 14:22 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51560 Nov 20 14:22 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56018 Nov 20 14:27 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51374 Nov 20 14:27 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56000 Nov 20 14:32 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51338 Nov 20 14:32 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56377 Nov 20 14:37 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51573 Nov 20 14:37 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56561 Nov 20 14:41 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 14:41 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56864 Nov 20 14:46 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51493 Nov 20 14:46 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56331 Nov 20 14:51 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51635 Nov 20 14:51 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56290 Nov 20 14:56 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51592 Nov 20 14:56 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56547 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51272 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56173 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56371 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51446 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56140 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56554 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51261 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56136 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51358 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56382 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56510 Nov 20 14:09 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 14:09 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56642 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51593 Nov 20 14:13 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46788 Nov 20 13:29 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:29 half_pool.out
-rw-r--r-- 1 ubuntu ubuntu   1057 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42260 Nov 20 13:29 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:29 half_tsv.log
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:22 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:22 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 13:22 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:22 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:22 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    784 Nov 20 13:24 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu     88 Nov 20 13:24 o_b.runlog
-rw-r--r-- 1 ubuntu ubuntu 281747 Nov 20 13:24 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:24 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu     90 Nov 20 13:24 o_off.runlog
-rw-r--r-- 1 ubuntu ubuntu 281863 Nov 20 13:24 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    817 Nov 20 13:24 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:24 o_on.runlog
-rw-r--r-- 1 ubuntu ubuntu 281953 Nov 20 13:24 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4036 Nov 20 13:24 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    284 Nov 20 13:25 o_table.out
-rw-r--r-- 1 ubuntu ubuntu   1723 Nov 20 13:24 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    621 Nov 20 14:58 play_log.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 14:57 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   9649 Nov 20 14:59 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 14:58 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:20 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1003 Nov 20 14:58 stamps.txt
```

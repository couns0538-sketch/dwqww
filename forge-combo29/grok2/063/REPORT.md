# Seat 063, arm 3 (B8a)

Arm 3, id B8a, source seat 078, branch for-fable-and-opus/grok-078, commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0. SWITCH IdeaB8. Seat file: model Grok 4.7.

## Patch

`sha256sum ~/arm.patch` printed:

```
b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-078` printed `7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0`. In the work tree, `git apply --check ~/arm.patch` then `git apply ~/arm.patch` both succeeded. `git diff --stat` after apply:

```
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

The patch was applied only in the outside work tree. No engine source was committed. IdeaB8_Weight and IdeaB8_Swing were left at their defaults and were never sent.

## Build

`/usr/bin/c++` is clang++ on this machine, and that link failed with `cannot find -lstdc++`. Both engines were built with `g++` (GCC 13.3.0) and `CMAKE_CXX_COMPILER=g++`, `CMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` has AVX-512 and BMI2, so the defaults were kept: `FORGE_PORTABLE` off, `FORGE_MARCH` x86-64-v4. Exe B is `/agent/repos/base/build-rel/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`. Exe P is `/agent/repos/work/build-rel/forge` sha256 `4109ff6c22cb70f4566803f0f42dba3ff6653c6ab173acefe865ce5945fdadee`. id name of both, from `uci`: Chess Engine Forge 6.4.24 candidate.

## Honesty

A fresh process per line, no setoption. The id name in each `.meta` is from a separate `uci` handshake of that same exe. Measured stdin was only the one command, then quit.

```
honesty_B_bench11.txt info string bench depth 11 nodes 312866 time 255 nps 1226925
honesty_B_bench13.txt info string bench depth 13 nodes 862329 time 586 nps 1471551
honesty_B_bench16.txt info string bench depth 16 nodes 3024920 time 2123 nps 1424832
honesty_B_perft5.txt nodes 4865609
honesty_P_bench11.txt info string bench depth 11 nodes 312866 time 390 nps 802220
honesty_P_bench13.txt info string bench depth 13 nodes 862329 time 1083 nps 796240
honesty_P_bench16.txt info string bench depth 16 nodes 3024920 time 2475 nps 1222189
honesty_P_perft5.txt nodes 4865609
```

Required: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match.

## Three O runs

`o_table.py` read `o_B.raw`, `o_off.raw`, `o_on.raw`. Its committed output `o_table.txt`:

```
B n=200 sum=9500069 first=41311 24872 28574
OFF n=200 sum=9500069 first=41311 24872 28574
ON n=200 sum=9295189 first=24947 29945 39302
OFF_identical=True mismatches=0
ON_differ=200
ON_first3_vs_B 24947/41311 29945/24872 39302/28574
```

Against the arm table: exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574; OFF equal on all 200; ON sum 9,295,189, first three 24,947 / 29,945 / 39,302, 200 differ. All three held. No unknown option, invalid value, invalid FEN, or illegal move in the three raw files (grep count 0).

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both sha256 values match the brief. Seat 063 took every 90th line starting at line 63: `wc -l ~/mine.epd` was 29245. Controls are the last 300 of that file. Chunks used the top, 250 openings each, and stopped at chunk 18 (lines 4251-4500), short of those 300.

## C-ARRIVE

`grep -c "setoption name IdeaB8 value true" ~/arrive.log` = 20. `grep -c -E "unknown option|invalid value|No such option" ~/arrive.log` = 0. The 20 log lines around the first switch setoption are in `arrive_check.txt`. The engine line there is `ON <--- setoption name IdeaB8 value true`.

## C-HALF

`games_tsv.py pool FULL` on `half.tsv` (`half_pool.txt`):

```
side FULL: games 400 W-L-D 240-34-126 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 9, 41, 81, 68] Elo +197.87 95% [+170.25, +227.96]
```

FULL's Elo is +197.87, above +20. Pass. fastchess's own summary printed the same Elo +197.87.

## POOL

18 chunks, each `chunk_N.tsv` is 500 lines, 9000 games. `cut -f5` of every chunk tsv: `9000 normal`. `games_tsv.py pool ON` wrote `POOL.txt`:

```
side ON: games 9000 W-L-D 2549-2317-4134 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [196, 1049, 1834, 1169, 252] Elo +8.96 95% [+4.17, +13.75]
```

## suspicions, not proven

The running pair Elo moved around in the early chunks (about +5 to +17) and then stayed near +9. I do not have a cause for that other than the width of the interval at a few thousand games. I am not claiming a time trend.

## what I did NOT do

No pull request. No engine source committed and no second patch. Arm 10 was not played. Match commands did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. IdeaB8_Weight and IdeaB8_Swing were not sent. No counted opening was repeated. No PGN, exe, or net file was committed. The handoff branch had no `FABLE_TO_grok2_*.md` at the STEP 1 fetch or at any chunk push, so `~/STOP_PLAY` was not created.

fastchess, started with the repo as its working directory, wrote an untracked `config.json` in the repo root. In that file `resign`, `draw`, `maxmoves`, and `tb_adjudication` are all `enabled: false`. That file was not committed.

## what I am NOT sure about

The honesty id name is from a second process, not from the process that printed the bench and perft lines. The node lines themselves are from the measured processes.

I fetched the handoff branch at STEP 1 and at each chunk push, not between them. A channel file could have appeared and disappeared between fetches. None was present at a fetch I did.

## times: see stamps.txt

The first line is `2026-11-20T13:23:08Z STEP 1`. `play.sh` printed `minute 95: no new chunk` after chunk 18 finished. Chunk 18's fastchess run ended with `Finished match` before that, so it counts.

## git status --short and ls -la

Captured after the files in this folder, including this report, were written, and appended below. `config.json` in the repo root is the untracked fastchess file and is outside this folder.

```
===== git status --short =====
 M forge-combo29/grok2/063/stamps.txt
?? config.json
?? forge-combo29/grok2/063/POOL.txt
?? forge-combo29/grok2/063/REPORT.md
?? forge-combo29/grok2/063/RESULT.txt
?? forge-combo29/grok2/063/chunk_18.out
?? forge-combo29/grok2/063/chunk_18.tsv
===== ls -la =====
total 3008
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2239 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56257 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55844 Nov 20 14:27 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51308 Nov 20 14:27 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56395 Nov 20 14:32 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:32 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56100 Nov 20 14:37 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51583 Nov 20 14:37 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56015 Nov 20 14:42 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51669 Nov 20 14:42 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56322 Nov 20 14:46 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51491 Nov 20 14:46 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56188 Nov 20 14:51 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51479 Nov 20 14:51 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56286 Nov 20 14:57 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:57 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55888 Nov 20 15:02 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51339 Nov 20 15:02 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56213 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56667 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51216 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56022 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56334 Nov 20 13:54 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 13:54 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56257 Nov 20 13:58 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51540 Nov 20 13:58 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56506 Nov 20 14:03 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51299 Nov 20 14:03 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56201 Nov 20 14:08 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 14:08 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56282 Nov 20 14:13 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 14:13 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56658 Nov 20 14:18 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51485 Nov 20 14:18 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2802 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46613 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42361 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    319 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    319 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    319 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    321 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    319 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    319 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    319 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    321 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    923 Nov 20 13:27 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1031 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    791 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281809 Nov 20 13:27 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    825 Nov 20 13:27 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282100 Nov 20 13:27 o_off.raw
-rw-r--r-- 1 ubuntu ubuntu    824 Nov 20 13:27 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282166 Nov 20 13:27 o_on.raw
-rw-r--r-- 1 ubuntu ubuntu   3853 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1724 Nov 20 13:27 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    232 Nov 20 13:28 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6349 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    661 Nov 20 15:03 stamps.txt
```

The `ls` size of `REPORT.md` (6349) is from before this status block was appended.

# grok2 seat 033 arm 3

## Arm and source seat

Arm 3, B8a. Source seat 078. Commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0. Switch IdeaB8. seat 033, arm 3, model Grok 4.7, 2026-11-20T13:21:49Z, token 746726855427

The release binaries were built with CMake and g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, default FORGE_MARCH x86-64-v4, FORGE_PORTABLE off. /usr/bin/c++ is Clang 18 and could not link libstdc++, so both builds set CMAKE_CXX_COMPILER=g++. The machine has avx512f and bmi2 (4 cores). exe B is /agent/repos/base/forge-combo29/build/forge. exe P is /agent/repos/work/forge-combo29/build/forge.

## Patch sha256 and git apply

```
sha256sum ~/arm.patch
b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649  /home/ubuntu/arm.patch
expected b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649
match yes
git -C /agent/repos/work diff --stat
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

git apply --check and git apply of ~/arm.patch on the work tree both exited 0 before the patched build. The diff stat above is that applied patch.

## Honesty numbers

Expected: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609, on exe B and exe P, one fresh process per command, no setoption.

```
honesty_B_bench11.txt: nodes 312866 expected 312866 ok
honesty_B_bench13.txt: nodes 862329 expected 862329 ok
honesty_B_bench16.txt: nodes 3024920 expected 3024920 ok
honesty_B_perft5.txt: nodes 4865609 expected 4865609 ok
honesty_P_bench11.txt: nodes 312866 expected 312866 ok
honesty_P_bench13.txt: nodes 862329 expected 862329 ok
honesty_P_bench16.txt: nodes 3024920 expected 3024920 ok
honesty_P_perft5.txt: nodes 4865609 expected 4865609 ok
```

## Three O runs

Expected from the arm table. Run (1) exe B: sum 9500069, first three 41311 / 24872 / 28574. Run (2) exe P, IdeaB8 false: equal on all 200. Run (3) exe P, IdeaB8 true: sum 9295189, first three 24947 / 29945 / 39302, 200 differ.

The lines below are the header rows of `python3 o_table.py` reading o_B.raw, o_P_off.raw, and o_P_on.raw. The 200 rows per run are in o_table.txt.

```
B file /agent/repos/dwqww/forge-combo29/grok2/033/o_B.raw positions 200 sum 9500069
B first 41311 24872 28574
OFF file /agent/repos/dwqww/forge-combo29/grok2/033/o_P_off.raw positions 200 sum 9500069
OFF first 41311 24872 28574
OFF differ 0
ON file /agent/repos/dwqww/forge-combo29/grok2/033/o_P_on.raw positions 200 sum 9295189
ON first 24947 29945 39302
ON differ 200
```

## Book sha256

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
expected 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
wc -l ~/uho.epd
2632036
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
expected lines 2632036 sha 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
book ok
```

Seat openings are every 90th line of that book starting at line 33. wc -l ~/mine.epd was 29245. The last 300 lines were held out for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE: `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`. The two counts and the 20 log lines around the first `setoption name IdeaB8 value true` are in arrive_check.txt. Count of that setoption was 20. Count of unknown option, invalid value, or No such option was 0.

C-HALF used ~/half.sh (match.sh with FULL at 20000 nodes, HALF at 10000 nodes, and no nodes limit on -each). `python3 games_tsv.py pool FULL` printed:

```
side FULL: games 400 W-L-D 232-24-144 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 38, 98, 58] Elo +200.24 95% [+175.61, +226.83]
```

FULL's Elo is above +20, so C-HALF passed.

## POOL.txt and chunks

Finished chunks: 20. Games are counted only from chunk tsv files whose play.log line says done.

```
side ON: games 10000 W-L-D 2813-2499-4688 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [204, 1134, 2069, 1330, 263] Elo +10.91 95% [+6.44, +15.39]
```

## Suspicions, not proven

The chunk tsv Termination column is the word normal. During C-ARRIVE, fastchess's own console named mates, fifty-move draws, threefold repetition, and insufficient material, and the trace log showed IdeaB8 set to true with no unknown-option line. A fastchess config.json written into the repository during that arrive run had resign, draw, maxmoves, and tablebase adjudication set enabled false. I deleted that untracked file and started play.sh with cwd /home/ubuntu. I did not re-check the final position of every chunk game.

The stamps line at 2026-11-20T13:40:37Z lists chunk 1 and chunk 2 on two lines. Chunk 1 was already committed. That line is a formatting mistake. The openings were not played again.

## What I did NOT do

I did not open a pull request. I did not send IdeaB8_Weight or IdeaB8_Swing. I did not pass -draw, -resign, -maxmoves, or a tablebase option to fastchess. I did not play the last 300 lines of mine.epd. I did not commit an engine binary, a PGN, or any engine source. The patch lives only in the work tree. I did not fetch this morning's seat 030 PGN to re-run the known games_tsv.py example. I did not switch to arm 10.

## What I am NOT sure about

Each push fetched handoff/fable-opus-combo29-all-20261114 and searched for FABLE_TO_grok2_. No such file was there. I am not sure a note could have been written under another name.

games_tsv.py scores the named side. C-HALF gives FULL, the side with twice the nodes, about +200 Elo, which is the direction the control asked for. I did not derive a second Elo formula.

## times: see stamps.txt

```
2026-11-20T13:22:05Z STEP 1
2026-11-20T13:26:39Z STEP 2
2026-11-20T13:30:43Z STEP 3
2026-11-20T13:36:07Z chunks chunk_1
2026-11-20T13:40:37Z chunks 1
2
2026-11-20T13:44:58Z chunks 3
2026-11-20T13:49:12Z chunks 4
2026-11-20T13:53:21Z chunks 5
2026-11-20T13:58:09Z chunks 6
2026-11-20T14:02:10Z chunks 7
2026-11-20T14:07:12Z chunks 8
2026-11-20T14:11:14Z chunks 9
2026-11-20T14:15:16Z chunks 10
2026-11-20T14:19:18Z chunks 11
2026-11-20T14:24:20Z chunks 12
2026-11-20T14:28:27Z chunks 13
2026-11-20T14:32:29Z chunks 14
2026-11-20T14:37:01Z chunks 15
2026-11-20T14:41:34Z chunks 16
2026-11-20T14:46:06Z chunks 17
2026-11-20T14:50:39Z chunks 18
2026-11-20T14:55:11Z chunks 19
2026-11-20T14:59:13Z chunks 20
2026-11-20T14:59:17Z STEP 5
```

## git status --short

```
 M forge-combo29/grok2/033/stamps.txt
?? forge-combo29/grok2/033/POOL.txt
?? forge-combo29/grok2/033/REPORT.md
?? forge-combo29/grok2/033/RESULT.txt
?? forge-combo29/grok2/033/book_sha.txt
?? forge-combo29/grok2/033/half.sh
?? forge-combo29/grok2/033/honesty_check.txt
?? forge-combo29/grok2/033/o_summary.txt
?? forge-combo29/grok2/033/patch_check.txt
```

## ls -la

```
total 3344
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 14:59 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2285 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    412 Nov 20 14:59 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56648 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51518 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  57098 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51452 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56005 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51456 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56304 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51440 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56144 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51224 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56173 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51440 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56010 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55751 Nov 20 14:45 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51271 Nov 20 14:45 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56085 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56406 Nov 20 14:54 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51460 Nov 20 14:54 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56270 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51223 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56671 Nov 20 14:58 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51475 Nov 20 14:58 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56455 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56458 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56410 Nov 20 13:48 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51543 Nov 20 13:48 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56379 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51186 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56508 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56290 Nov 20 14:01 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 14:01 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56098 Nov 20 14:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51331 Nov 20 14:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55945 Nov 20 14:10 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51378 Nov 20 14:10 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47361 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1050 Nov 20 14:59 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42436 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 13:24 honesty_B_id.txt
-rw-r--r-- 1 ubuntu ubuntu    231 Nov 20 13:24 honesty_B.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    110 Nov 20 13:24 honesty_B.sha256
-rw-r--r-- 1 ubuntu ubuntu    446 Nov 20 14:59 honesty_check.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   5101 Nov 20 13:24 honesty_P_id.txt
-rw-r--r-- 1 ubuntu ubuntu    231 Nov 20 13:24 honesty_P.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    110 Nov 20 13:24 honesty_P.sha256
-rwxr-xr-x 1 ubuntu ubuntu    722 Nov 20 13:24 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu    552 Nov 20 13:26 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu    580 Nov 20 13:26 honesty_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    865 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 307418 Nov 20 13:25 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    899 Nov 20 13:25 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309231 Nov 20 13:25 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    898 Nov 20 13:26 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 309174 Nov 20 13:26 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   4751 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    370 Nov 20 14:59 o_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   1455 Nov 20 13:25 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   7798 Nov 20 13:26 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    463 Nov 20 14:59 patch_check.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    156 Nov 20 14:59 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6979 Nov 20 14:59 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    228 Nov 20 14:59 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     74 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    731 Nov 20 14:59 stamps.txt
```

# grok2 seat 004

Arm 4, id B8b, source seat 028, commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75, switch IdeaB8. Model Grok 4.7. Branch for-fable-and-opus/grok2-004.

## Patch

sha256 of ~/arm.patch, also copied to idea.patch.txt:

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

`git fetch --depth 1 origin for-fable-and-opus/grok-028` left FETCH_HEAD at 4bf95fd80adf523e97fa250bb8572c946cf0fc75. In /agent/repos/work, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both succeeded. The applied diff is 3 files, 173 insertions, 4 deletions: forge-combo29/include/forge/search.hpp, forge-combo29/src/search.cpp, forge-combo29/src/uci.cpp. IdeaB8_Weight and IdeaB8_Swing were left at their defaults and were never sent.

The machine has AVX-512 and BMI2, so the release build used the CMake default -march=x86-64-v4 and FORGE_PORTABLE off. /usr/bin/c++ is clang 18 and failed to link libstdc++. Both trees were configured with -DCMAKE_CXX_COMPILER=g++ (g++ 13.3.0) and built Release. Exe B is /agent/repos/base/forge-combo29/build/forge sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83. Exe P is /agent/repos/work/forge-combo29/build/forge sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422. id name of both: Chess Engine Forge 6.4.24 candidate.

## Honesty

Each line is a fresh process, `uci` then the command, no setoption. Both exes:

```
bench 11 nodes 312866
bench 13 nodes 862329
bench 16 nodes 3024920
go perft 5 nodes 4865609
```

Those are the known numbers. Raw lines are in honesty_B_*.txt and honesty_P_*.txt, with a .meta beside each.

## O runs

`python3 o_table.py o_b.rows o_off.rows o_on.rows` wrote o_table.txt:

```
B n=200 sum=9500069 first=41311 / 24872 / 28574
OFF n=200 sum=9500069 first=41311 / 24872 / 28574 differ=0
ON n=200 sum=9718009 first=17283 / 17878 / 31115 differ=200
```

Against the arm table: run (1) expected sum 9500069 and first three 41311 / 24872 / 28574. Run (2) IdeaB8 false equals run (1) on all 200 positions (`cmp o_b.rows o_off.rows` was identical). Run (3) IdeaB8 true expected sum 9718009, first three 17283 / 17878 / 31115, 200 positions differ. The rows match. S14, Threads 1 and Hash 16 were sent in that order; the switch line was `setoption name IdeaB8 value true` or `false`. Positions file first200.fens sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief's copy. Seat 004 openings are every 90th line of uho.epd starting at line 4: 29245 lines in ~/mine.epd. The last 300 are ~/ctl.epd (10 in ctl_arrive.epd, 200 in ctl_half.epd). Chunks take 250 lines from the top and stop at chunk 18, line 4500, short of those 300.

## C-ARRIVE and C-HALF

arrive_check.txt counts:

```
grep -c setoption name IdeaB8 value true
20
grep -c -E unknown option|invalid value|No such option
0
```

The log lines around the first `setoption name IdeaB8 value true` are in that file. fastchess accepted `engine=true`.

half_pool.txt, from `python3 games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 226-34-140 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 53, 84, 57] Elo +181.70 95% [+156.96, +208.27]
```

FULL at 20000 nodes versus HALF at 10000 nodes is +181.70, above +20. fastchess printed the same 226-34-140 and Elo 181.70. No -draw, -resign, -maxmoves, or tablebase flag was passed. config.json, written by fastchess into this folder during C-HALF, has resign, draw, maxmoves, and tb_adjudication enabled false.

## POOL

18 chunks, 9000 games, 4500 pairs. `python3 games_tsv.py pool ON chunk_*.tsv` wrote POOL.txt:

```
side ON: games 9000 W-L-D 2543-2298-4159 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [181, 1061, 1845, 1158, 255] Elo +9.46 95% [+4.70, +14.22]
```

play.sh stopped itself with `minute 95: no new chunk` after chunk 18. No chunk line in play.log says FAILED. Each chunk tsv is 500 lines.

## suspicions, not proven

The running pool sat near +12 Elo at 2500 games and near +10 Elo at 7500 games. I have no evidence that the match changed between chunks. It looks like the interval getting narrower.

## what I did NOT do

I did not open a pull request. I did not edit engine source, and I did not commit an engine source file, an executable, a net, or a PGN. I did not send any patch option except IdeaB8. I did not play arm 10. I did not repeat an opening. I did not adjudicate a game. I did not force-push, and I did not write any branch except for-fable-and-opus/grok2-004. The handoff branch never contained a FABLE_TO_grok2 file, so there was no extra channel instruction and I did not create ~/STOP_PLAY.

## what I am NOT sure about

`uci` was sent before each honesty command so the .meta file could record id name. The node counts still match the known numbers. I am sure about the counts and unsure whether a future harness that skips `uci` is what was used this morning. The counts say the result is the same.

git user.name was already set globally to "Cursor Agent", so I left it. Commits are authored as that name.

config.json is fastchess's saved configuration from C-HALF, not a file the brief named. It is in this folder because the shell's current directory was the seat folder when C-HALF ran. Later matches were started from /home/ubuntu.

A helper, ~/push_chunks.sh, committed each finished chunk within a minute of play.sh writing it. The 4-to-5-minute checks still ran, and each push fetched the handoff branch.

## times: see stamps.txt

git status --short
 M forge-combo29/grok2/004/stamps.txt
?? forge-combo29/grok2/004/POOL.txt
?? forge-combo29/grok2/004/REPORT.md
?? forge-combo29/grok2/004/RESULT.txt

ls -la forge-combo29/grok2/004
total 3124
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2220 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56391 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51162 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56280 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51456 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56049 Nov 20 14:29 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51300 Nov 20 14:29 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56197 Nov 20 14:34 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:34 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56270 Nov 20 14:39 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51505 Nov 20 14:39 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56583 Nov 20 14:44 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51486 Nov 20 14:44 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56550 Nov 20 14:49 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51573 Nov 20 14:49 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56252 Nov 20 14:54 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51615 Nov 20 14:54 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56312 Nov 20 14:59 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51488 Nov 20 14:59 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56339 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51035 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56084 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51103 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55849 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51312 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56690 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51548 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55974 Nov 20 13:56 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 13:56 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55893 Nov 20 14:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56244 Nov 20 14:06 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51494 Nov 20 14:06 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56317 Nov 20 14:10 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51523 Nov 20 14:10 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56418 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51556 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   7046 Nov 20 13:31 config.json
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2802 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46857 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:32 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1047 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42315 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_B.log
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5164 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_P.log
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5375 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3935 Nov 20 13:24 honesty.py
-rw-r--r-- 1 ubuntu ubuntu  20136 Nov 20 13:26 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    106 Nov 20 13:26 o_b.log
-rw-r--r-- 1 ubuntu ubuntu    910 Nov 20 13:26 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 281829 Nov 20 13:26 o_b.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_b.rows
-rw-r--r-- 1 ubuntu ubuntu    124 Nov 20 13:26 o_off.log
-rw-r--r-- 1 ubuntu ubuntu    951 Nov 20 13:26 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281976 Nov 20 13:26 o_off.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_off.rows
-rw-r--r-- 1 ubuntu ubuntu    115 Nov 20 13:26 o_on.log
-rw-r--r-- 1 ubuntu ubuntu    950 Nov 20 13:26 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282474 Nov 20 13:26 o_on.raw
-rw-r--r-- 1 ubuntu ubuntu   1899 Nov 20 13:26 o_on.rows
-rw-r--r-- 1 ubuntu ubuntu   6034 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1225 Nov 20 13:25 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:26 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5958 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    720 Nov 20 15:03 stamps.txt

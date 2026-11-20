# grok2 seat 069

Arm 9, id S13, source seat 016, switch IdeaS13.
Source branch for-fable-and-opus/grok-016, commit cdde64371237fe7778c713655c0c4b5c957a5fe2.
Model line in SEAT.txt: Grok 4.7.

## Patch

sha256 of ~/arm.patch (the file taken from forge-combo29/grok/016/idea.patch.txt):

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

That is the table sha256. `git apply --check ~/arm.patch && git apply ~/arm.patch` in the work tree printed APPLY_OK. The work tree diff after that, re-checked at the end, is:

```
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

The patch was applied only in the work tree outside this branch. No engine source is in this commit.

Build decision: `/usr/bin/c++` is clang++ and the first CMake configure failed with `cannot find -lstdc++`. Both exes were then configured with `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (g++ 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` has avx512f and bmi2, so FORGE_PORTABLE was left off and FORGE_MARCH stayed the CMake default x86-64-v4. Exe B is /agent/repos/base/forge-combo29/build/forge. Exe P is /agent/repos/work/forge-combo29/build/forge.

## Honesty

A fresh process for each line, no setoption. Parsed from the raw files by the one-off reader (the lines below are that reader's output):

```
honesty_B bench11 info string bench depth 11 nodes 312866 time 242 nps 1292834
honesty_B bench13 info string bench depth 13 nodes 862329 time 451 nps 1912037
honesty_B bench16 info string bench depth 16 nodes 3024920 time 1514 nps 1997965
honesty_B perft5 nodes 4865609
honesty_P bench11 info string bench depth 11 nodes 312866 time 162 nps 1931271
honesty_P bench13 info string bench depth 13 nodes 862329 time 444 nps 1942182
honesty_P bench16 info string bench depth 16 nodes 3024920 time 1535 nps 1970631
honesty_P perft5 nodes 4865609
```

Table: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match. honesty=ok.

## The three O runs

`python3 forge-combo29/grok2/069/otable.py forge-combo29/grok2/069` reads the transcripts, not the .rows files, then checks the .rows files:

```
B: n 200 sum 9500069 first 41311 / 24872 / 28574
OFF: n 200 sum 9500069 first 41311 / 24872 / 28574
ON: n 200 sum 9722445 first 19900 / 22525 / 42778
OFF identical to B: True
ON positions that differ from B: 200
B sum expected 9500069 match True
B first expected (41311, 24872, 28574) match True
ON sum expected 9722445 match True
ON first expected (19900, 22525, 42778) match True
ON differ expected 200 match True
rows match transcript B: True
rows match transcript OFF: True
rows match transcript ON: True
```

Table for arm 9: ON 9,722,445; 19,900 / 22,525 / 42,778; 200 differ. OFF equal to B on all 200. on_ok=yes. Exe B was the base binary. Exe P with IdeaS13 false and with IdeaS13 true used the patched binary. Threads 1, Hash 16, then the S14 list, then the switch on P only. IdeaS13_Lookback and IdeaS13_ReduceDivisor were not sent.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both sha256 values match the brief. book=ok. Seat 069 takes line 69 and every 90th line after it. ~/mine.epd has 29245 lines. The last 300 were held back as ctl.epd. Chunks used the top of mine.epd and stopped at chunk 21 (5250 openings), short of that reserve.

## C-ARRIVE and C-HALF

arrive_check.txt (counts from grep of ~/arrive.log):

```
setoption name IdeaS13 value true count: 20
unknown option|invalid value|No such option count: 0
```

The 20 log lines around the first setoption are in arrive_check.txt. The engine line is `setoption name IdeaS13 value true`. arrive=ok.

C-HALF, `python3 ~/games_tsv.py pool FULL` on half.tsv (half_pool.txt):

```
side FULL: games 400 W-L-D 242-37-121 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 8, 41, 81, 68] Elo +196.69 95% [+168.72, +227.17]
```

FULL's Elo is +196.69, above +20. half_elo=+196.69.

## POOL

21 chunks, 500 games each, 10500 games. `python3 ~/games_tsv.py pool ON` on chunk_1.tsv through chunk_21.tsv, written to POOL.txt:

```
side ON: games 10500 W-L-D 2724-2861-4915 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [242, 1398, 2107, 1261, 242] Elo -4.53 95% [-8.93, -0.14]
```

Termination field in the 21 tsv files: 10500 rows say `normal`. Result field: 3192 `1-0`, 2393 `0-1`, 4915 `1/2-1/2`. `grep -c -i adjud` on ~/chunk_1.pgn through ~/chunk_21.pgn is 0 for every file. play.sh stopped itself with `minute 95: no new chunk` after chunk 21 had already finished (chunk 21 done 2026-11-20T14:59:07Z). fastchess was not killed.

## suspicions, not proven

The measured Elo is negative and the 95% interval printed by games_tsv.py is entirely below zero. I am not treating that as a proved loss of a specific cause. I did not separate opening luck from the switch by any test beyond the paired openings the script already uses.

I did not re-read every PGN comment. The tsv termination is `normal` and the comments I sampled in chunk 21 are mate scores and mate notes. Absence of the string `adjud` is what I checked, not a hand classification of every ending.

## what I did NOT do

No pull request. No engine source committed. No binary, net, or PGN committed. No adjudication flags (`-draw`, `-resign`, `-maxmoves`, tablebases) in match.sh or half.sh. No second patch and no arm-10 fallback: the ON numbers matched. The reserved 300 openings were not played. IdeaS13_Lookback and IdeaS13_ReduceDivisor were not sent. No FABLE_TO_grok2 file existed on handoff/fable-opus-combo29-all-20261114 at the fetches I made, so nothing on the channel changed the rules.

## what I am NOT sure about

`id` in RESULT.txt is S13, the label on arm 9 in the brief. The switch name is IdeaS13.

fastchess writes config.json into the current directory. C-HALF was started while the shell was in the repository, so a config.json appeared at the repo root. I deleted it and did not commit it. Later matches were started from /home/ubuntu. The man page loads a config only with `-config`. match.sh does not pass `-config`. I did not read every fastchess startup path past that option.

The `ls -la` below was captured after POOL.txt, RESULT.txt and this report body existed, and before this status section was appended, so the byte size of REPORT.md in that listing is the size before these last blocks.

## times: see stamps.txt

First stamp 2026-11-20T13:23:10Z. Chunk 21 done 2026-11-20T14:59:07Z. play.sh then printed `minute 95: no new chunk`.

## git status --short

```
 M forge-combo29/grok2/069/stamps.txt
?? forge-combo29/grok2/069/POOL.txt
?? forge-combo29/grok2/069/REPORT.md
?? forge-combo29/grok2/069/RESULT.txt
?? forge-combo29/grok2/069/chunk_21.out
?? forge-combo29/grok2/069/chunk_21.tsv
```

## ls -la

```
total 3428
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2244 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  55785 Nov 20 14:14 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51583 Nov 20 14:14 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56206 Nov 20 14:18 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51269 Nov 20 14:18 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56032 Nov 20 14:22 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51258 Nov 20 14:22 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56258 Nov 20 14:26 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51450 Nov 20 14:26 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55998 Nov 20 14:30 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51367 Nov 20 14:30 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56422 Nov 20 14:34 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:34 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56184 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51379 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56494 Nov 20 14:42 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51382 Nov 20 14:42 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56455 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56675 Nov 20 14:51 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51688 Nov 20 14:51 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56155 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51221 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56069 Nov 20 14:55 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51590 Nov 20 14:55 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56355 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51563 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56487 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56269 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51202 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56301 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51485 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56502 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51266 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56661 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56485 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56282 Nov 20 14:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56190 Nov 20 14:10 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51512 Nov 20 14:10 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46629 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1045 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42133 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:33 half_tsv_count.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    200 Nov 20 13:27 honesty_B.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 13:27 honesty_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    200 Nov 20 13:27 honesty_P.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   5115 Nov 20 13:27 honesty_P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   2850 Nov 20 13:26 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 13:28 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu 308874 Nov 20 13:28 o_B.transcript
-rw-r--r-- 1 ubuntu ubuntu    831 Nov 20 13:28 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 o_off.rows
-rw-r--r-- 1 ubuntu ubuntu 309065 Nov 20 13:28 o_off.transcript
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 13:28 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 13:28 o_on.rows
-rw-r--r-- 1 ubuntu ubuntu 309250 Nov 20 13:28 o_on.transcript
-rw-r--r-- 1 ubuntu ubuntu   6061 Nov 20 13:27 orun.py
-rw-r--r-- 1 ubuntu ubuntu   2374 Nov 20 13:27 otable.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   7110 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1216 Nov 20 15:02 stamps.txt
```

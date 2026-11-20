# Seat 011, arm 1 (B1a)

Arm 1, source seat 030, branch `for-fable-and-opus/grok-030`, commit `416700fe0ace1656a1285fc536c347718c1a4af7`. Switch `IdeaB1`. `IdeaB1_Scale` and `IdeaB1_Fade` were left at the patch defaults and were never sent.

## Patch

`sha256sum ~/arm.patch` printed:

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check ~/arm.patch && git apply ~/arm.patch` in the work tree exited 0. `git -C /agent/repos/work diff --stat` after that:

```
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

The machine has AVX-512 and BMI2, so both engines are the default Release build (`-march=x86-64-v4`, `FORGE_PORTABLE` off, `g++` 13.3.0). Portable flags were not added.

## Honesty

`grep -H 'nodes ' honesty_*.txt`:

```
honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 171 nps 1829625
honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 568 nps 1518184
honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1497 nps 2020654
honesty_B_perft5.txt:nodes 4865609
honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 165 nps 1896157
honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 452 nps 1907807
honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1440 nps 2100638
honesty_P_perft5.txt:nodes 4865609
```

Bench 11 / 13 / 16 and perft 5 match 312866, 862329, 3024920, and 4865609 on exe B and on exe P. Each line was a fresh process with no setoption.

## Three O runs

`python3 orun_table.py orun_B.txt orun_Poff.txt orun_Pon.txt`:

```
forge-combo29/grok2/011/orun_B.txt: n 200 sum 9500069 first 41311 / 24872 / 28574
forge-combo29/grok2/011/orun_Poff.txt: n 200 sum 9500069 first 41311 / 24872 / 28574 differ 0
forge-combo29/grok2/011/orun_Pon.txt: n 200 sum 10081213 first 12481 / 31753 / 31668 differ 200
```

Against the table: exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Switch false matches exe B on all 200 positions. Switch true sum 10,081,213, first three 12,481 / 31,753 / 31,668, and 200 positions differ.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 011 takes lines 11, 101, 191, ... (`wc -l ~/mine.epd` was 29245). The last 300 of those lines were held back for the controls.

## C-ARRIVE

`arrive_check.txt` (the two counts, then 20 log lines around the first `IdeaB1` setoption):

```
grep -c setoption name IdeaB1 value true: 20
grep -c unknown option|invalid value|No such option: 0
---- 20 lines around the first setoption of IdeaB1 ----
[Engine] [13:27:20.887699] <     139645696337600>  OFF ---> option name IdeaB1_Fade type spin default 4 min 0 max 64
[Engine] [13:27:20.887701] <     139645696337600>  OFF ---> option name Clear Hash type button
[Engine] [13:27:20.887706] <     139645696337600>  OFF ---> uciok
[TRACE ] [13:27:20.887825] <     139645696337600> fastchess --- Refreshing engine ON
[TRACE ] [13:27:20.887839] <     139645696337600> fastchess --- Sending setoption to engine ON Threads 1
[Engine] [13:27:20.887840] <     139645687944896>  ON ---> id name Chess Engine Forge 6.4.24 candidate
[Engine] [13:27:20.887842] <     139645696337600>  ON <--- setoption name Threads value 1
[Engine] [13:27:20.887862] <     139645687944896>  ON ---> id author OpenAI
[TRACE ] [13:27:20.887874] <     139645696337600> fastchess --- Sending setoption to engine ON IdeaB1 true
[Engine] [13:27:20.887875] <     139645687944896>  ON ---> option name Hash type spin default 32 min 1 max 2048
[Engine] [13:27:20.887877] <     139645696337600>  ON <--- setoption name IdeaB1 value true
[Engine] [13:27:20.887878] <     139645687944896>  ON ---> option name Threads type spin default 1 min 1 max 256
[TRACE ] [13:27:20.887880] <     139645696337600> fastchess --- Sending setoption to engine ON Hash 16
[Engine] [13:27:20.887883] <     139645696337600>  ON <--- setoption name Hash value 16
[Engine] [13:27:20.887880] <     139645687944896>  ON ---> option name MultiPV type spin default 1 min 1 max 8
[TRACE ] [13:27:20.887886] <     139645696337600> fastchess --- Sending setoption to engine ON OwnBook false
[Engine] [13:27:20.887887] <     139645687944896>  ON ---> option name Move Overhead type spin default 10 min 0 max 1000
[Engine] [13:27:20.887888] <     139645696337600>  ON <--- setoption name OwnBook value false
[Engine] [13:27:20.887889] <     139645687944896>  ON ---> option name Ponder type check default false
[Engine] [13:27:20.887891] <     139645687944896>  ON ---> option name OwnBook type check default true
```

True-count 20, refusal-count 0.

## C-HALF

`python3 games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 226-30-144 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 12, 40, 84, 63] Elo +186.25 95% [+158.95, +215.83]
```

FULL's Elo is +186.25, above +20. Pass.

## POOL

21 chunks, 10500 games. `POOL.txt` is the output of `python3 games_tsv.py pool ON chunk_*.tsv`:

```
side ON: games 10500 W-L-D 2804-2786-4910 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [267, 1298, 2084, 1352, 249] Elo +0.60 95% [-3.86, +5.05]
```

## suspicions, not proven

None. Every chunk tsv has 500 lines, every opening is in exactly two games, and `grep -c -i adjudicat` on every `chunk_*.out` printed 0. Match.sh passes no `-draw`, `-resign`, or `-maxmoves`.

## what I did NOT do

I did not open a pull request. I did not change engine source beyond applying the given patch in the work tree, and I did not commit any engine file, executable, net, or PGN. I did not send `IdeaB1_Scale` or `IdeaB1_Fade`. I did not fall back to arm 10. I did not start another chunk after play.sh printed `minute 95: no new chunk` (14:59:13Z, chunk 21). I did not kill fastchess: the last chunk had already finished, before minute 103. No `FABLE_TO_grok2_<N>.md` existed on `handoff/fable-opus-combo29-all-20261114` at step 1 or at any step 4 push (the fetch's file list contained zero of those names).

## what I am NOT sure about

The result field `id` is `B1a`, the name on arm row 1. If that field was supposed to be the UCI name, the engines printed `Chess Engine Forge 6.4.24 candidate`.

From chunk 7 on, commits were made by `~/keep.sh` (outside the repo, not committed): every 240 seconds it added finished chunk files with 500 games, committed, pushed, and fetched the channel. I started it after a run of identical interactive polls was interrupted. The committed files are the chunk tsv and out files.

The PGN header `Termination` is `normal` on all 10500 games, including mates. I am not sure that header would change if fastchess had adjudicated a game. The outs do not contain the word adjudicat, and this fastchess leaves draw, resign, and tablebase adjudication off unless those options are passed.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/011/stamps.txt
?? forge-combo29/grok2/011/POOL.txt
?? forge-combo29/grok2/011/REPORT.md
?? forge-combo29/grok2/011/RESULT.txt
```

## ls -la

```
total 3424
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2149 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56324 Nov 20 14:12 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:12 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56131 Nov 20 14:16 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51697 Nov 20 14:16 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56305 Nov 20 14:21 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51249 Nov 20 14:21 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56137 Nov 20 14:25 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51401 Nov 20 14:25 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56364 Nov 20 14:29 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51468 Nov 20 14:29 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56286 Nov 20 14:33 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51501 Nov 20 14:33 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 14:37 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51545 Nov 20 14:37 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56453 Nov 20 14:41 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:41 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56070 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51537 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56367 Nov 20 14:50 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51400 Nov 20 14:50 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56370 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51285 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56151 Nov 20 14:54 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51504 Nov 20 14:54 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  55922 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56121 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51241 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56332 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51341 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56519 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51304 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56392 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51458 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56358 Nov 20 13:56 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51569 Nov 20 13:56 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56352 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51553 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56278 Nov 20 14:04 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51467 Nov 20 14:04 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56265 Nov 20 14:08 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51430 Nov 20 14:08 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46978 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu  42363 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 13:23 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 13:23 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 13:23 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    186 Nov 20 13:23 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 13:23 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 13:23 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 13:23 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    186 Nov 20 13:23 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1092 Nov 20 13:23 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1024 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    779 Nov 20 13:25 orun_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308863 Nov 20 13:25 orun_B.txt
-rw-r--r-- 1 ubuntu ubuntu    813 Nov 20 13:25 orun_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 309043 Nov 20 13:25 orun_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    812 Nov 20 13:25 orun_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 310043 Nov 20 13:25 orun_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   4052 Nov 20 13:25 orun.py
-rw-r--r-- 1 ubuntu ubuntu   1424 Nov 20 13:25 orun_table.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   7402 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    804 Nov 20 15:03 stamps.txt
```

# grok2 seat 029

Arm 9, S13. Source seat 016. Switch IdeaS13. Branch for-fable-and-opus/grok2-029. Model Grok 4.7.

## Patch

Source branch for-fable-and-opus/grok-016. `git rev-parse FETCH_HEAD` printed `cdde64371237fe7778c713655c0c4b5c957a5fe2`, the commit in the arm table.

`sha256sum ~/arm.patch` printed:

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

That is the arm table sha256. In the work tree, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both exited 0. `git diff --stat` printed:

```
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

The patch is not committed. IdeaS13_Lookback and IdeaS13_ReduceDivisor were left at the patch defaults and were never sent.

Build decision: `/usr/bin/c++` is clang 18 and the link failed with `cannot find -lstdc++`. The brief asks for GCC 13 or newer and GCC's own C++ library. Both engines were configured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0) and the default march `x86-64-v4`. The CPU has AVX-512 and BMI2, so FORGE_PORTABLE was left off. flags.make contains `-march=x86-64-v4`.

## Honesty

`python3 harness.py` then `python3 tables.py` on the raw files. Pasted output of `tables.py`:

```
honesty
  B bench11 nodes 312866 expected 312866 ok
  B bench13 nodes 862329 expected 862329 ok
  B bench16 nodes 3024920 expected 3024920 ok
  B perft5 nodes 4865609 expected 4865609 ok
  P bench11 nodes 312866 expected 312866 ok
  P bench13 nodes 862329 expected 862329 ok
  P bench16 nodes 3024920 expected 3024920 ok
  P perft5 nodes 4865609 expected 4865609 ok
O B    positions 200 sum 9500069 first 41311 24872 28574
O off positions 200 sum 9500069 first 41311 24872 28574
O on  positions 200 sum 9722445 first 19900 22525 42778
off_vs_B differ 0 of 200
on_vs_B differ 200 of 200
```

Each honesty line was a fresh process. `uci` was sent so the meta file could record `id name`; no setoption was sent. Both exes match bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.

Meta files: exe B `/agent/repos/base/forge-combo29/build/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, exe P `/agent/repos/work/forge-combo29/build/forge` sha256 `018e977106c57cebbf6cb0339c95c93d9a8117232849895dc94833fbf19adbfc`, id name `Chess Engine Forge 6.4.24 candidate`.

## O runs

Same `tables.py` paste as above. Against the arm table:

- Run (1) exe B: sum 9500069 and first three 41311 / 24872 / 28574. The table's 9,500,069 and 41,311 / 24,872 / 28,574 are those numbers.
- Run (2) exe P, IdeaS13 false: same 200 positions, differ 0.
- Run (3) exe P, IdeaS13 true: sum 9722445, first three 19900 / 22525 / 42778, 200 differ. The table's 9,722,445 and 19,900 / 22,525 / 42,778 and 200 differ are those numbers.

FEN file sha256 from `sha256sum ~/first200.fens`: `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines. S14 was sent in the listed order, plus Hash 16 and Threads 1, once at the start of the process. ucinewgame and isready ran before every position. The harness stops on unknown option, invalid value, invalid FEN, and illegal move. It finished all 200 positions on each run.

## Book

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
  2632036 /home/ubuntu/uho.epd
```

Both sha256 values and the line count match the brief. Seat 029 took every 90th line starting at line 29: 29245 lines in mine.epd. The last 300 are the controls (10 arrive, 200 half). Chunks used the top of mine.epd, lines 1 through 4750.

## C-ARRIVE and C-HALF

C-ARRIVE: `grep -c` of `setoption name IdeaS13 value true` in the trace log was 20. `grep -c` of `unknown option|invalid value|No such option` was 0. The 20 log lines around the first switch setoption are in arrive_check.txt. fastchess accepted `engine=true`.

C-HALF: `python3 games_tsv.py pool FULL` on half.tsv printed:

```
side FULL: games 400 W-L-D 227-37-136 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 11, 48, 81, 60] Elo +179.45 95% [+153.31, +207.61]
```

FULL's Elo is above +20. Passed.

## Pool

19 chunks, 9500 games. Pasted POOL.txt (`python3 games_tsv.py pool ON` on chunk_1.tsv through chunk_19.tsv):

```
side ON: games 9500 W-L-D 2519-2623-4358 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [234, 1212, 1957, 1118, 229] Elo -3.80 95% [-8.44, +0.83]
```

## suspicions, not proven

ON scores -3.80 Elo against OFF. The 95% interval is [-8.44, +0.83] and includes 0, so a loss is not shown.

Finished-game reasons counted from the committed chunk_*.out files (9500 lines):

```
   2994 Draw by 3-fold repetition
   2959 White mates
   2183 Black mates
    720 Draw by fifty moves rule
    625 Draw by insufficient mating material
     19 Draw by stalemate
```

No adjudication phrase appears in that count. The tsv Termination field is the word `normal` on all 9500 rows, which is the PGN header python-chess read.

## what I did NOT do

- No pull request.
- No commit of an engine source file, an exe, a net, a PGN, or the book.
- No second build of the patch and no switch to arm 10.
- No -draw, -resign, -maxmoves, or tablebase flag on fastchess.
- No repeated opening. The reserved last 300 lines of mine.epd were not used in the chunks.
- IdeaS13_Lookback and IdeaS13_ReduceDivisor were never sent.
- No FABLE_TO_grok2 file was on the handoff branch at any fetch, so no channel order was applied.

## what I am NOT sure about

- The result field `id` is S13, the name on arm row 9. If that field was meant to be something else, this is the value I chose.
- The `ls -la` pasted below was taken before this status block was appended, so the listed byte size of REPORT.md is the size before the paste.
- `uci` was sent before each honesty command. The node counts still matched the known numbers.

## times: see stamps.txt

First stamp 2026-11-20T13:21:58Z STEP 1. STEP 5 stamp is the last line of stamps.txt. play.sh printed `minute 95: no new chunk` after chunk 19. No chunk was killed.

## git status --short and ls -la

These two pastes are appended by the next command, from that command's output.

```
$ git status --short
 M forge-combo29/grok2/029/stamps.txt
?? forge-combo29/grok2/029/POOL.txt
?? forge-combo29/grok2/029/REPORT.md
?? forge-combo29/grok2/029/RESULT.txt
?? forge-combo29/grok2/029/endings.txt

$ ls -la forge-combo29/grok2/029
total 3164
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2181 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    366 Nov 20 13:32 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56547 Nov 20 14:17 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 14:17 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56206 Nov 20 14:21 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51581 Nov 20 14:21 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55891 Nov 20 14:26 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51408 Nov 20 14:26 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56331 Nov 20 14:30 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51456 Nov 20 14:30 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55783 Nov 20 14:35 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51385 Nov 20 14:35 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56344 Nov 20 14:39 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51609 Nov 20 14:39 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56162 Nov 20 14:43 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51316 Nov 20 14:43 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56005 Nov 20 14:48 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51575 Nov 20 14:48 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56232 Nov 20 14:52 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51368 Nov 20 14:52 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56471 Nov 20 14:57 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51363 Nov 20 14:57 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56361 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51325 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56309 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56112 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51315 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56059 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51167 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56297 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51526 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56137 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51368 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56145 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51429 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56329 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51542 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56129 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51476 Nov 20 14:12 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu    178 Nov 20 15:00 endings.txt
-rw-r--r-- 1 ubuntu ubuntu     93 Nov 20 13:28 fens_sha.txt
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:32 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46836 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:32 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42177 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   6920 Nov 20 13:25 harness.py
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:25 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:25 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:25 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:25 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5176 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:25 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5176 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:25 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5178 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:25 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5389 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:25 honesty_P_perft5.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:32 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281766 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    847 Nov 20 13:27 o_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 281905 Nov 20 13:27 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    898 Nov 20 13:27 o_P_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282078 Nov 20 13:27 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    896 Nov 20 13:27 o_P_on.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    586 Nov 20 13:28 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    317 Nov 20 13:28 patch_check.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:32 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6661 Nov 20 15:00 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    697 Nov 20 15:00 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2458 Nov 20 13:25 tables.py
```

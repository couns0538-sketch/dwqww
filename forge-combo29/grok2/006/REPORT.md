# Seat 006 arm 6

Arm 6, idea S32. Source seat 074. Switch IdeaS32. Commit 0fd01685b0465c11e29816b5a759e6496d2a69ae on for-fable-and-opus/grok-074.

## Patch

sha256sum of the patch file fetched from that commit:

```
18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch
```

That is the table sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree both exited 0. `git diff --stat` in that work tree:

```
 forge-combo29/include/forge/search.hpp |  6 ++++++
 forge-combo29/src/search.cpp           | 30 +++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  5 +++++
 3 files changed, 40 insertions(+), 1 deletion(-)
```

The patch was not committed. IdeaS32_OwedSlack was left at its default and was never sent.

Release builds used CMake and g++ 13.3.0 (GCC's libstdc++). `/usr/bin/c++` is Clang 18 and failed to link `-lstdc++`, so the generator was `-DCMAKE_CXX_COMPILER=g++`. The CPU has AVX-512 and BMI2, so the build used the CMake default `-march=x86-64-v4` and did not set FORGE_PORTABLE. Exe B is `/agent/repos/base/forge-combo29/build/forge`. Exe P is `/agent/repos/work/forge-combo29/build/forge`.

## Honesty

`numbers.py` read the raw honesty files. Both exes:

```
honesty B
  bench 11 depth 11 nodes 312866 ok
  bench 13 depth 13 nodes 862329 ok
  bench 16 depth 16 nodes 3024920 ok
  perft 5 nodes 4865609 ok
  honesty_B ok
honesty P
  bench 11 depth 11 nodes 312866 ok
  bench 13 depth 13 nodes 862329 ok
  bench 16 depth 16 nodes 3024920 ok
  perft 5 nodes 4865609 ok
  honesty_P ok
```

Known values: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Each line was a fresh process. The process was sent `uci` and then the one command. It was not sent `setoption`.

## Three O runs

Same script, same raw files, against the arm table (O depth 12, S14, 200 positions):

```
o_B sum 9500069 first 41311 24872 28574 rows o_B.rows
o_P_off sum 9500069 first 41311 24872 28574 rows o_P_off.rows
o_P_on sum 9547450 first 41442 24989 28711 rows o_P_on.rows
o_P_off positions differing from o_B: 0
o_P_on positions differing from o_B: 200
o_B expected sum 9500069 first 41311 24872 28574
o_P_on expected sum 9547450 first 41442 24989 28711 differ 200
```

Run (1) matches the plain-engine sum and the first three. Run (2) matches run (1) on all 200 positions. Run (3) matches the arm-6 sum, the first three, and 200 positions different. `first200.fens` sha256 is ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. Seat 006 took every 90th line starting at line 6 (`wc -l ~/mine.epd` = 29245). The last 300 lines were held back for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`: `setoption name IdeaS32 value true` occurred 20 times, and `unknown option|invalid value|No such option` occurred 0 times. The first true setoption is the line `ON <--- setoption name IdeaS32 value true`.

C-HALF, `games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 223-21-156 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 37, 102, 54] Elo +193.17 95% [+168.59, +219.65]
```

FULL's Elo is +193.17, above +20.

## POOL

22 chunks, 11000 games. `wc -l chunk_*.tsv` totalled 11000, and each chunk file is 500 lines. Pasted `POOL.txt`:

```
side ON: games 11000 W-L-D 2800-2999-5201 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [238, 1436, 2341, 1257, 228] Elo -6.29 95% [-10.46, -2.11]
```

Finish lines in the 22 `chunk_*.out` files, 11000 of them, and each file contains one `Finished match`: White mates 3332, Black mates 2467, 3-fold repetition 3577, fifty-move rule 857, insufficient mating material 733, stalemate 34. None of those lines says adjudication. `config.json` left in the repo root by fastchess has resign, draw, maxmoves, and tablebase adjudication all `enabled: false`. It was not committed.

## Suspicions, not proven

The pooled Elo is negative and the 95% interval is entirely below zero. That is the pair-score output of `games_tsv.py`. I do not have a separate cause for the loss beyond the reproduced node counts.

## What I did NOT do

I did not open a pull request. I did not write a new search idea, change engine source on the branch, or fall back to arm 10. I did not pass draw, resign, maxmoves, or tablebase flags. I did not repeat an opening. I did not commit an executable, a net, a PGN, the book, or `config.json`. I did not send IdeaS32_OwedSlack. I did not force-push or write any branch except for-fable-and-opus/grok2-006.

## What I am NOT sure about

Every PGN `Termination` tag is the word `normal` (11000 of them in the tsv files). The chess reasons above come from fastchess's `Finished game` lines in `chunk_*.out`, not from that tag. I do not know why this fastchess writes `Termination normal`.

The handoff branch `handoff/fable-opus-combo29-all-20261114` had no `forge-combo29/soak_all/FABLE_TO_grok2_<N>.md` at STEP 1 or at any chunk push. I treated that as no extra instruction.

`games_tsv.py` and fastchess printed the same +193.17 on C-HALF. I did not ask fastchess for an Elo on the 11000 games. The pool figure is `games_tsv.py`.

## Times

times: see stamps.txt


## git status --short

```
 M forge-combo29/grok2/006/stamps.txt
?? config.json
?? forge-combo29/grok2/006/POOL.txt
?? forge-combo29/grok2/006/REPORT.md
?? forge-combo29/grok2/006/RESULT.txt
```

## ls -la

```
total 3492
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2230 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56493 Nov 20 14:10 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 14:10 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56277 Nov 20 14:14 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51453 Nov 20 14:14 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56392 Nov 20 14:18 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51614 Nov 20 14:18 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56219 Nov 20 14:21 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51511 Nov 20 14:21 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56107 Nov 20 14:25 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51593 Nov 20 14:25 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56815 Nov 20 14:29 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51589 Nov 20 14:29 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56233 Nov 20 14:33 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51592 Nov 20 14:33 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56378 Nov 20 14:37 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51375 Nov 20 14:37 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56674 Nov 20 14:41 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51533 Nov 20 14:41 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56524 Nov 20 14:45 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51635 Nov 20 14:45 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56177 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51151 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56284 Nov 20 14:49 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 14:49 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56840 Nov 20 14:53 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51526 Nov 20 14:53 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  55777 Nov 20 14:56 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:56 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56381 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56022 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51260 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56444 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56468 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51433 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56101 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51305 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56529 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51479 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56595 Nov 20 14:02 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51371 Nov 20 14:02 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56248 Nov 20 14:06 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 14:06 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47156 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1031 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42398 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:26 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:26 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:26 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_B_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:26 honesty_B_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5102 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5102 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5104 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_P_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5315 Nov 20 13:26 honesty_P_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3591 Nov 20 13:25 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    691 Nov 20 13:26 numbers_out.txt
-rw-r--r-- 1 ubuntu ubuntu   3417 Nov 20 13:26 numbers.py
-rw-r--r-- 1 ubuntu ubuntu    907 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu 281840 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    942 Nov 20 13:26 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu 282039 Nov 20 13:26 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    941 Nov 20 13:26 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu 281968 Nov 20 13:26 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   5056 Nov 20 13:26 o_run.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 14:59 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5685 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    757 Nov 20 15:01 stamps.txt
```

# grok2 seat 047 arm 7

Arm 7, K4a. Source seat 093, branch for-fable-and-opus/grok-093, commit ddc850cbf04b8c7a8592624037844077b33c8ab0. SWITCH IdeaK4. Model Grok 4.7. Seat file: seat 047, arm 7, model Grok 4.7, 2026-11-20T13:22:18Z.

## Patch

`sha256sum ~/arm.patch` printed:

```
e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git rev-parse FETCH_HEAD` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-093` printed `ddc850cbf04b8c7a8592624037844077b33c8ab0`. In the work tree, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both succeeded. `git diff --stat` printed:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
```

IdeaK4_Shrink was left at its default. It was never sent.

## Builds

Release CMake build with g++ 13.3.0. The first configure used `/usr/bin/c++`, which is Clang 18, and the link failed with `cannot find -lstdc++`. I deleted those build directories and configured again with `-DCMAKE_CXX_COMPILER=g++`. The CPU flags include AVX-512F and BMI2, so I did not pass `-DFORGE_PORTABLE=ON` or `-DFORGE_MARCH`. Exe B is `/agent/repos/base/forge-combo29/build/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`. Exe P is `/agent/repos/work/forge-combo29/build/forge`, sha256 `9e860c57ba37e64fef39e9980ab4ed4c494474805b7019ad4fc00cc9810b8282`. The same two hashes were printed again at 2026-11-20T15:03:54Z, after the matches. Nothing from either build was committed.

## Honesty

`python3 forge-combo29/grok2/047/otable.py forge-combo29/grok2/047` reads the raw files. Its honesty section:

```
honesty
B bench11 nodes 312866 expected 312866 ok
P bench11 nodes 312866 expected 312866 ok
B bench13 nodes 862329 expected 862329 ok
P bench13 nodes 862329 expected 862329 ok
B bench16 nodes 3024920 expected 3024920 ok
P bench16 nodes 3024920 expected 3024920 ok
B perft5 nodes 4865609 expected 4865609 ok
P perft5 nodes 4865609 expected 4865609 ok
```

Each line was a fresh process, `uci` then `isready` then the command, no `setoption`.

## Three O runs

Same script, same run, against the arm table (sum 9,500,069 and first three 41,311 / 24,872 / 28,574 for exe B; switch off identical; switch on 8,921,190 and 24,693 / 26,341 / 35,070 and 200 differ):

```
orun
B n 200 sum 9500069 first 41311 24872 28574
P_off n 200 sum 9500069 first 41311 24872 28574
P_on n 200 sum 8921190 first 24693 26341 35070
P_off differ_from_B 0
P_on differ_from_B 200
B_expected sum 9500069 first 41311 24872 28574
ON_expected sum 8921190 first 24693 26341 35070 differ 200
B_and_off ok
ON ok
```

Options went out in the S14 order, then Threads 1, then Hash 16, then IdeaK4 true or false on exe P only. `isready` followed every `setoption` and every `position`. FENs sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Those are the brief's zip sha256, line count, and epd sha256. Seat 047 took every 90th line starting at line 47: 29245 lines in mine.epd. The last 300 became the controls. Chunks used the top, 250 openings each, and stopped at chunk 20.

## C-ARRIVE and C-HALF

arrive_check.txt, from the trace log:

```
grep -c "setoption name IdeaK4 value true" arrive.log
20
grep -c -E "unknown option|invalid value|No such option" arrive.log
0
```

The 20 log lines around the first `setoption name IdeaK4 value true` are in that file. fastchess accepted `engine=true`.

C-HALF, `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/047/half.tsv` at 2026-11-20T15:03:54Z:

```
side FULL: games 400 W-L-D 221-29-150 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 9, 43, 91, 56] Elo +181.70 95% [+156.08, +209.29]
```

FULL's Elo is above +20.

## Pool

20 chunks, 10000 games. `python3 ~/games_tsv.py pool ON` on the twenty `chunk_*.tsv` files wrote POOL.txt:

```
side ON: games 10000 W-L-D 2712-2572-4716 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [219, 1194, 2064, 1274, 249] Elo +4.86 95% [+0.38, +9.35]
```

Each chunk tsv has 500 lines. The termination field is `normal` on all 10000 lines. A search of the committed `chunk_*.out` files found no line containing "adjudicat".

## suspicions, not proven

This seat's script prints Elo +4.86 with a 95% interval above 0. That is 5000 pairs from seat 047 only. It is not the arm's combined answer.

## what I did NOT do

I did not open a pull request. I did not commit an engine source file, an exe, an object file, a net, a PGN, or the book. I did not send IdeaK4_Shrink. I did not fall back to arm 10. I did not pass portable or march flags. I did not turn on adjudication, resignation, max-move cutoffs, or tablebases. I did not replay an opening. No `FABLE_TO_grok2_*.md` was on the handoff branch at the fetches I made (last fetched commit `bcfdf4b5ecd5a0e2844a9160514c2b05cf5872c0`, message count 0), so no channel instruction was applied.

## what I am NOT sure about

fastchess wrote an untracked `config.json` in the repository root because `play.sh` was started with that directory as cwd. I did not commit it. The copy I opened had resign, draw, maxmoves, and tb adjudication `enabled` false. I am not sure I read every key. The match that ran is the command line in `match.sh`.

The word `normal` is fastchess's termination header. The chunk logs name mates and rule draws. I did not replay the moves to prove each final position.

## times: see stamps.txt

The first stamp is `2026-11-20T13:22:37Z STEP 1 seat`. Chunk 20 is `2026-11-20T14:59:24Z chunks 20`. Play printed `minute 95: no new chunk` after that chunk.

## git status --short and ls -la

The listing below was captured after POOL.txt, REPORT.md, and RESULT.txt existed. Appending it changes the size of REPORT.md from the size on its own line.

```
$ git status --short
 M forge-combo29/grok2/047/stamps.txt
?? config.json
?? forge-combo29/grok2/047/POOL.txt
?? forge-combo29/grok2/047/REPORT.md
?? forge-combo29/grok2/047/RESULT.txt

$ ls -la forge-combo29/grok2/047
total 3260
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2544 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56554 Nov 20 14:16 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51448 Nov 20 14:16 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56023 Nov 20 14:20 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 14:20 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56255 Nov 20 14:24 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51442 Nov 20 14:24 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56390 Nov 20 14:29 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51651 Nov 20 14:29 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56057 Nov 20 14:33 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51327 Nov 20 14:33 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56545 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51553 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56151 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51570 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56409 Nov 20 14:46 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51612 Nov 20 14:46 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56413 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56327 Nov 20 14:54 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51575 Nov 20 14:54 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56005 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51262 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56503 Nov 20 14:58 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:58 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56083 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56512 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51576 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56018 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51357 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55999 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56646 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56384 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51383 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56554 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51655 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:12 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47065 Nov 20 13:33 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1128 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42384 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:28 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:28 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:28 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:28 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:28 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:28 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:28 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5215 Nov 20 13:28 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:28 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5107 Nov 20 13:28 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:28 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5107 Nov 20 13:28 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:28 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5109 Nov 20 13:28 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:28 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5320 Nov 20 13:28 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   2703 Nov 20 13:26 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu    907 Nov 20 13:28 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281957 Nov 20 13:28 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    941 Nov 20 13:29 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282036 Nov 20 13:29 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    940 Nov 20 13:29 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 281027 Nov 20 13:29 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   4443 Nov 20 13:26 orun.py
-rw-r--r-- 1 ubuntu ubuntu   2820 Nov 20 13:27 otable.py
-rw-r--r-- 1 ubuntu ubuntu    664 Nov 20 13:29 otable.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6381 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    804 Nov 20 15:04 stamps.txt
```

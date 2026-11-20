# REPORT seat 057 arm 7

## Arm and source seat

Seat 057, arm 7, id K4a, source seat 093, commit ddc850cbf04b8c7a8592624037844077b33c8ab0, SWITCH IdeaK4.

SEAT.txt:

```
seat 057, arm 7, model Grok 4.7, 2026-11-20T13:22:18Z, token 229481690118917
```

## Patch sha256 and git apply

`sha256sum ~/arm.patch` (file taken from `for-fable-and-opus/grok-093` at ddc850cbf04b8c7a8592624037844077b33c8ab0, path forge-combo29/grok/093/idea.patch.txt):

```
e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. The applied diff is forge-combo29/include/forge/search.hpp, forge-combo29/src/search.cpp, and forge-combo29/src/uci.cpp (3 files, +23/-1). IdeaK4_Shrink was left at its default and was never sent.

## Honesty numbers

Both exes, a fresh process per line, no setoption. Expected nodes: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.

`grep nodes` of the eight honesty files:

```
honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 166 nps 1884734
honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 434 nps 1986933
honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1508 nps 2005915
honesty_B_perft5.txt:nodes 4865609
honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 183 nps 1709650
honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 483 nps 1785360
honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1489 nps 2031511
honesty_P_perft5.txt:nodes 4865609
```

All eight match. honesty=ok.

Build: GCC g++ 13.3.0, `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++`. `/usr/bin/c++` is Clang 18.1.3 and its test link failed with `cannot find -lstdc++`, so the release builds use g++ and libstdc++. `/proc/cpuinfo` has avx512f and bmi2, so the portable march flags were not added. CMake default is `-march=x86-64-v4` with PEXT and ZMM on. exe B is `/tmp/build-base/forge` sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83. exe P is `/tmp/build-work/forge` sha256 9e860c57ba37e64fef39e9980ab4ed4c494474805b7019ad4fc00cc9810b8282. id name on both: Chess Engine Forge 6.4.24 candidate.

## Three O runs

Arm table for K4a, O depth 12, S14, IdeaK4 true: sum 8921190; first three 24693 / 26341 / 35070; 200 differ. Plain run (1): sum 9500069; first three 41311 / 24872 / 28574. Run (2) must match run (1) on all 200.

`python3 o_table.py o_b_rows.txt o_off_rows.txt o_on_rows.txt` (same text as o_table.txt):

```
B: positions 200 sum 9500069 first 41311 / 24872 / 28574
OFF: positions 200 sum 9500069 first 41311 / 24872 / 28574
ON: positions 200 sum 8921190 first 24693 / 26341 / 35070
OFF positions differing from B: 0
ON positions differing from B: 200
```

off_identical=yes. on_sum=8921190. on_ok=yes.

o_b.meta starts exe `/tmp/build-base/forge` and does not send IdeaK4. o_off.meta and o_on.meta start exe `/tmp/build-work/forge`. o_off.meta ends with `setoption name IdeaK4 value false`. o_on.meta ends with `setoption name IdeaK4 value true`.

## Book sha256

book_check.txt:

```
uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Zip sha256, line count 2632036, and epd sha256 match the brief. book=ok. Seat 057 openings are every 90th line of uho.epd starting at line 57 (`wc -l ~/mine.epd` = 29245). Controls used the last 300 of that file. Chunks took 21 times 250 lines from the top (5250 openings) and did not reach those 300.

## C-ARRIVE and C-HALF

arrive_check.txt counts:

```
grep -c setoption name IdeaK4 value true
20
grep -c -E unknown option|invalid value|No such option
0
```

The first IdeaK4 setoption in arrive.log is engine ON, `setoption name IdeaK4 value true`. arrive=ok.

C-HALF, `python3 games_tsv.py pool FULL half.tsv` (half_pool.txt):

```
side FULL: games 400 W-L-D 227-35-138 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 4, 49, 94, 52] Elo +181.70 95% [+157.69, +207.43]
```

half_elo=+181.70, above +20. fastchess's own half.out line was `Elo: 181.70 +/- 24.87` with Wins 227, Losses 35, Draws 138. PASS.

## POOL.txt and chunks

21 chunks, each `wc -l` 500, total 10500 games. play.log has 21 lines "chunk N done" and no FAILED line. ~/play.out ends with `minute 95: no new chunk`. Chunk 21 finished 2026-11-20T14:59:00Z. It started when chunk 20 finished at 2026-11-20T14:54:56Z, which is before minute 95 (first stamp 2026-11-20T13:22:33Z plus 95 minutes = 2026-11-20T14:57:33Z). No fastchess process was killed.

`python3 ~/games_tsv.py pool ON chunk_*.tsv` written to POOL.txt:

```
side ON: games 10500 W-L-D 2703-2868-4929 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [247, 1374, 2158, 1239, 232] Elo -5.46 95% [-9.82, -1.10]
```

## suspicions, not proven

None. The honesty nodes and the three O runs match the arm table, so this is the K4a patch. The match score is the POOL.txt line above.

## What I did NOT do

- No pull request.
- No engine source, exe, net, or PGN committed.
- IdeaK4_Shrink was not sent.
- Did not fall back to arm 10.
- No adjudication (-draw, -resign, -maxmoves, tablebases).
- No opening was repeated to add games.
- No FABLE_TO_grok2 file was on the handoff branch. Last fetch at this step: bcfdf4b5ecd5a0e2844a9160514c2b05cf5872c0, listing matched nothing.

## What I am NOT sure about

The games_tsv.py point Elo on C-HALF (+181.70) matches fastchess's printed Elo (181.70). The script's 95% interval and fastchess's `+/- 24.87` are not the same width. The match Elo and interval in RESULT.txt are the script's, as specified.

Stamp lines after chunk 9 list chunk numbers in `ls` order, not numeric order. The folder has chunk_1.tsv through chunk_21.tsv, 21 files.

## times: see stamps.txt

## git status --short and ls -la

```
 M forge-combo29/grok2/057/stamps.txt
?? config.json
?? forge-combo29/grok2/057/POOL.txt
?? forge-combo29/grok2/057/REPORT.md
?? forge-combo29/grok2/057/RESULT.txt
```

```
total 3400
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2214 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    219 Nov 20 13:31 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56230 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51442 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56664 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51704 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56283 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51399 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56038 Nov 20 14:27 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:27 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56773 Nov 20 14:31 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51543 Nov 20 14:31 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56660 Nov 20 14:35 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51513 Nov 20 14:35 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56166 Nov 20 14:39 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51378 Nov 20 14:39 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56115 Nov 20 14:43 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51564 Nov 20 14:43 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56008 Nov 20 14:47 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51594 Nov 20 14:47 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56051 Nov 20 14:50 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51642 Nov 20 14:50 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56178 Nov 20 13:39 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  50962 Nov 20 13:39 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56336 Nov 20 14:54 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 14:54 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56561 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56377 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51407 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56373 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56276 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51421 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56651 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51418 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56491 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51423 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56518 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51530 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56308 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51524 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55908 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51339 Nov 20 14:11 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46811 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:34 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42382 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1011 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    774 Nov 20 13:29 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 308960 Nov 20 13:29 o_b_raw.txt
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:29 o_b_rows.txt
-rw-r--r-- 1 ubuntu ubuntu   4845 Nov 20 13:29 o_harness.py
-rw-r--r-- 1 ubuntu ubuntu    808 Nov 20 13:29 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 308989 Nov 20 13:29 o_off_raw.txt
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:29 o_off_rows.txt
-rw-r--r-- 1 ubuntu ubuntu    807 Nov 20 13:29 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 308038 Nov 20 13:29 o_on_raw.txt
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 13:29 o_on_rows.txt
-rw-r--r-- 1 ubuntu ubuntu   1082 Nov 20 13:25 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    243 Nov 20 13:30 o_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6196 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1303 Nov 20 15:02 stamps.txt
```

# Seat 070, arm 10

Arm 10, row K3. Source seat none. The switch is HindsightDepth, an option of the base engine. There is no morning patch and no source commit.

## Patch

No patch. sha256 not applicable. `git apply` was not run. Both work trees are commit 6b98f2170a3210e71beed04bbd2553972c253ed7. The two release binaries are the same bytes:

```
e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /agent/repos/base/forge-combo29/build/forge
e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /agent/repos/work/forge-combo29/build/forge
binaries_identical yes
```

That block is from `build_notes.txt`. The CPU has AVX-512 and BMI2, so the build left `FORGE_PORTABLE` off and kept the CMake default `-march=x86-64-v4`. Compiler: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0. `id name` from the engine: Chess Engine Forge 6.4.24 candidate.

## Honesty

A fresh process for each line, no setoption. Both exe B and exe P:

```
bench 11 nodes 312866
bench 13 nodes 862329
bench 16 nodes 3024920
go perft 5 nodes 4865609
```

Raw lines:

```
honesty_B_bench_11.txt:info string bench depth 11 nodes 312866 time 160 nps 1955412
honesty_B_bench_13.txt:info string bench depth 13 nodes 862329 time 430 nps 2005416
honesty_B_bench_16.txt:info string bench depth 16 nodes 3024920 time 1414 nps 2139264
honesty_B_go_perft_5.txt:nodes 4865609
honesty_P_bench_11.txt:info string bench depth 11 nodes 312866 time 159 nps 1967710
honesty_P_bench_13.txt:info string bench depth 13 nodes 862329 time 428 nps 2014787
honesty_P_bench_16.txt:info string bench depth 16 nodes 3024920 time 1412 nps 2142294
honesty_P_go_perft_5.txt:nodes 4865609
```

## Three O runs

`o_table.py` read the raw transcripts. Known targets: run (1) sum 9500069, first three 41311 / 24872 / 28574; run (2) identical to (1); run (3) sum 9845650, first three 23395 / 31504 / 35958, 200 differ. Output:

```
o1_B positions 200 sum 9500069 first 41311 24872 28574
o1_B expect_sum 9500069 sum_ok True first_ok True
o2_P_off positions 200 sum 9500069 first 41311 24872 28574
o2_P_off expect_sum 9500069 sum_ok True first_ok True
o2_P_off differ_from_o1 0
o2_P_off identical_to_o1 True
o3_P_on positions 200 sum 9845650 first 23395 31504 35958
o3_P_on expect_sum 9845650 sum_ok True first_ok True
o3_P_on differ_from_o1 200
```

S14, Threads 1 and Hash 16 were sent in that order. Run (1) did not send HindsightDepth. Run (2) sent `false`. Run (3) sent `true`. The option lists are in the `.meta` files.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the known copy. `first200.fens` sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines. Seat 070's book slice is 29245 lines (`mine.epd`).

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`:

```
grep -c setoption name HindsightDepth value true: 20
grep -c -E unknown option|invalid value|No such option: 0
```

The 20-line window contains `setoption name HindsightDepth value true`. fastchess accepted `engine=true`.

C-HALF, pasted from `half_pool.txt` (`games_tsv.py pool FULL`):

```
side FULL: games 400 W-L-D 216-34-150 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 12, 43, 88, 55] Elo +170.59 95% [+144.12, +199.02]
```

FULL's Elo is +170.59, above +20.

## POOL

22 chunks, each 500 games, 11000 games. `games_tsv.py pool ON` wrote `POOL.txt`:

```
side ON: games 11000 W-L-D 3060-2809-5131 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [239, 1281, 2273, 1404, 303] Elo +7.93 95% [+3.62, +12.24]
```

Play stopped with `minute 95: no new chunk` after chunk 22. That chunk had started before minute 95 and finished at 15:00:26Z. Nothing was killed.

## suspicions, not proven

fastchess wrote an untracked `config.json` in the repository root because the match process inherited that working directory. The copy I opened has resign, draw, maxmoves and tablebase adjudication all `enabled: false`. The match command line has no `-draw`, `-resign`, `-maxmoves` or tablebase flag. I did not prove there is no other adjudication path inside fastchess. Sampled game ends in the logs were mates, fifty-move draws, repetitions and insufficient material.

The channel branch never contained a `FABLE_TO_grok2_*.md` file on the fetches I made.

## what I did NOT do

I did not apply a patch, change engine source, open a pull request, or commit a binary, a net, a PGN or the book. I did not send any engine option besides the S14 list, Threads, Hash, OwnBook and HindsightDepth. I did not play the last 300 lines of `mine.epd` (22 chunks use the first 5500 lines; the file has 29245). I did not turn on `FORGE_PORTABLE`.

## what I am NOT sure about

The result field `id` is `K3`, the row label in the arm table. The switch name is HindsightDepth. I am not sure which of those two strings the field was meant to hold.

A background script committed chunks 7 through 22 and read the channel. Chunks 1 through 6 were committed from the foreground checks. I checked that each chunk file is 500 lines and that the pool script accepted every game. I did not re-read all 22 fastchess summaries by hand at the end.

## times: see stamps.txt

First stamp 2026-11-20T13:23:32Z STEP 1. Last stamp is STEP 5.

## git status --short

 M forge-combo29/grok2/070/stamps.txt
?? config.json
?? forge-combo29/grok2/070/POOL.txt
?? forge-combo29/grok2/070/REPORT.md
?? forge-combo29/grok2/070/RESULT.txt

## ls -la forge-combo29/grok2/070

total 3440
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2295 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1360 Nov 20 13:29 build_notes.txt
-rw-r--r-- 1 ubuntu ubuntu  56269 Nov 20 14:13 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51320 Nov 20 14:13 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56285 Nov 20 14:17 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51352 Nov 20 14:17 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56158 Nov 20 14:21 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51343 Nov 20 14:21 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56079 Nov 20 14:25 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51623 Nov 20 14:25 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56347 Nov 20 14:29 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51437 Nov 20 14:29 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56050 Nov 20 14:33 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 14:33 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56347 Nov 20 14:37 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51429 Nov 20 14:37 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56539 Nov 20 14:40 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 14:40 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56228 Nov 20 14:44 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51516 Nov 20 14:44 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56735 Nov 20 14:48 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51644 Nov 20 14:48 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56133 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51198 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56187 Nov 20 14:52 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51534 Nov 20 14:52 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56239 Nov 20 14:56 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51430 Nov 20 14:56 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56271 Nov 20 15:00 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51593 Nov 20 15:00 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56254 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51265 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56417 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51438 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56801 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51541 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56038 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51433 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56070 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51462 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56440 Nov 20 14:01 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51370 Nov 20 14:01 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56797 Nov 20 14:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56024 Nov 20 14:09 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51298 Nov 20 14:09 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47091 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:33 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu    981 Nov 20 13:33 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42432 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_B_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_B_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_B_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_B_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_B_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:28 honesty_B_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_B_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:28 honesty_B_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_P_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_P_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_P_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 honesty_P_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_P_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:28 honesty_P_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu    173 Nov 20 13:28 honesty_P_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:28 honesty_P_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    965 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:29 o1_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281593 Nov 20 13:29 o1_B.txt
-rw-r--r-- 1 ubuntu ubuntu    835 Nov 20 13:29 o2_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281611 Nov 20 13:29 o2_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    834 Nov 20 13:29 o3_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 281767 Nov 20 13:29 o3_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    412 Nov 20 13:29 o_table.out
-rw-r--r-- 1 ubuntu ubuntu   1685 Nov 20 13:29 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5603 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    230 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    785 Nov 20 15:04 stamps.txt

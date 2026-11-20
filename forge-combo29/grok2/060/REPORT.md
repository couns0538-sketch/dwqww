# grok2 seat 060

Arm 10, K3. Source seat none. SWITCH HindsightDepth, the base engine's own option. No patch.

## Patch

Arm 10 has no patch, so there is no sha256 and no `git apply`. exe P is a second build of the same commit as exe B (`6b98f2170a3210e71beed04bbd2553972c253ed7`). Both binaries sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` (from `O_B.meta` and `O_P_on.meta`). id name: Chess Engine Forge 6.4.24 candidate.

Decision: `/usr/bin/c++` is Clang 18 and the first CMake configure failed with `cannot find -lstdc++`. I reconfigured both trees with `-DCMAKE_CXX_COMPILER=g++` (GCC 13.3). `/proc/cpuinfo` has `avx512f` and `bmi2`, so I did not pass `-DFORGE_PORTABLE=ON` or `-DFORGE_MARCH=x86-64-v3`. The match binary is exe B, as the brief says for arm 10 (`~/match.sh`).

## Honesty

`summarize_o.py` read the raw honesty files:

```
honesty B 312866 862329 3024920 4865609
honesty P 312866 862329 3024920 4865609
```

Those are bench 11, bench 13, bench 16, and `go perft 5`. They match 312866, 862329, 3024920, 4865609. A fresh process per line, no setoption.

## Three O runs

Same script, depth 12, S14, Threads 1, Hash 16, 200 positions from `first200.fens` (sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`):

```
O_B n 200 sum 9500069 first 41311 24872 28574
O_P_off n 200 sum 9500069 first 41311 24872 28574
O_P_on n 200 sum 9845650 first 23395 31504 35958
off_differ 0 on_differ 200
off_equal True
```

Against the arm table: run (1) sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Run (2) equal on all 200. Run (3) sum 9,845,650, first three 23,395 / 31,504 / 35,958, 200 differ. `O_P_on.meta` sends `setoption name HindsightDepth value true`. `O_P_off.meta` sends false. `O_B.meta` does not send the switch. No unknown option, invalid value, invalid FEN, or illegal move in the three transcripts.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 060 takes every 90th line of `uho.epd` starting at line 60. The last 300 lines of `mine.epd` were held back for the controls. Chunks used lines 1 to 4250 of `mine.epd`.

## C-ARRIVE

`arrive_check.txt`: `setoption name HindsightDepth value true` count 20. `unknown option|invalid value|No such option` count 0. The 20 log lines around the first switch setoption are in that file. fastchess accepted `engine=true`.

## C-HALF

`games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 236-30-134 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 43, 86, 64] Elo +197.87 95% [+171.49, +226.49]
```

FULL (20000 nodes) against HALF (10000 nodes), switch false. Elo is above +20.

## Pool

17 chunks, 8500 games. `POOL.txt` is the pasted output of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/060/chunk_*.tsv`:

```
side ON: games 8500 W-L-D 2283-2300-3917 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [205, 1072, 1733, 1015, 225] Elo -0.69 95% [-5.64, +4.25]
```

Every chunk tsv has 500 lines. All 8500 termination fields are `normal`. Ply length: min 10, median 137, max 704, 9 games under 20 plies. No chunk FAILED. Play stopped itself with `minute 95: no new chunk` after chunk 17. No chunk was killed.

## Suspicions, not proven

The nine games under 20 plies are short, and the termination field is still `normal`. I did not open those games. `match.sh` sets no `-draw`, `-resign`, or `-maxmoves`.

## What I did NOT do

No pull request. No engine source edit, no binary, no PGN, and no net file in the commit. No patch. No second C-HALF (the first passed). No repeated opening. The handoff branch had no `FABLE_TO_grok2_*.md` at the step 1 fetch or at any chunk push, so nothing on the channel changed the rules. `config.json` at the repository root is not mine and is not added.

## What I am NOT sure about

`id=K3` in RESULT.txt is the short name on arm row 10. The brief does not define that field in another sentence.

Chunk files after chunk 7 were committed by `~/watch_chunks.sh` (outside the repo): it waits until `play.log` says the chunk is done and the tsv has 500 lines, then commits, pushes, and reads the channel. I started it so a finished chunk is still pushed if this chat is cut. The pushes are on `for-fable-and-opus/grok2-060`.

The `ls -la` below was captured after these files existed and before the step 5 commit. Appending it changed the size of this file, so the listed size of `REPORT.md` is the size before this section was appended.

## times: see stamps.txt

First stamp `2026-11-20T13:23:09Z`. Chunk 17 stamp `2026-11-20T15:00:26Z`. This step's stamp is the last line of `stamps.txt`.

```
$ git status --short
 M forge-combo29/grok2/060/stamps.txt
?? config.json
?? forge-combo29/grok2/060/POOL.txt
?? forge-combo29/grok2/060/REPORT.md
?? forge-combo29/grok2/060/RESULT.txt

$ ls -la forge-combo29/grok2/060
total 2952
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2244 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56195 Nov 20 14:23 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51416 Nov 20 14:23 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56355 Nov 20 14:28 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51501 Nov 20 14:28 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56532 Nov 20 14:33 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51649 Nov 20 14:33 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55909 Nov 20 14:39 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:39 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56471 Nov 20 14:43 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51626 Nov 20 14:43 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  55903 Nov 20 14:49 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51277 Nov 20 14:49 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56242 Nov 20 14:54 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51493 Nov 20 14:54 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56591 Nov 20 14:58 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51567 Nov 20 14:58 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55702 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51101 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56128 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51155 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55838 Nov 20 13:48 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51229 Nov 20 13:48 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56346 Nov 20 13:53 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51355 Nov 20 13:53 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56525 Nov 20 13:58 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51397 Nov 20 13:58 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56714 Nov 20 14:03 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51497 Nov 20 14:03 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56152 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51557 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56183 Nov 20 14:12 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:12 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56504 Nov 20 14:18 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51478 Nov 20 14:18 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:27 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47154 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1070 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42127 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:26 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:26 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:26 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:26 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    746 Nov 20 13:26 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1049 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    799 Nov 20 13:27 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281831 Nov 20 13:27 O_B.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 13:27 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281826 Nov 20 13:27 O_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 13:27 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 281896 Nov 20 13:27 O_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4358 Nov 20 13:27 orun.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5022 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    228 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    981 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2396 Nov 20 13:27 summarize_o.py
```

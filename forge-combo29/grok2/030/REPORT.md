# REPORT seat 030

## Arm and source seat

Seat 030, arm 10, label K3. Source seat: none. SWITCH HindsightDepth, the base engine's own option. Model line in SEAT.txt: Grok 4.7.

## Patch sha256 and git apply

No patch. sha256: none. `git apply` was not run. The brief says arm 10 has no patch and exe P is exe B itself.

Work tree `../work` was created at 6b98f2170a3210e71beed04bbd2553972c253ed7 and left unpatched. One release binary was built and used for both exe B and exe P:

`/agent/repos/base/forge-combo29/build/forge`

The machine's `/proc/cpuinfo` has `avx512f` and `bmi2`, so the build left `FORGE_PORTABLE` off and used the CMake default `-march=x86-64-v4`. The first configure used `/usr/bin/c++`, which is Clang, and the link failed with `cannot find -lstdc++`. The build that was measured was reconfigured with `CMAKE_CXX_COMPILER=g++` (g++ 13.3.0) and GCC's libstdc++. See BUILD.txt.

## Honesty numbers

Raw lines are `honesty_*.txt`. The table is the output of `python3 run_step2.py table` saved as `o_table.txt`:

```
honesty
B_bench11 312866 expect 312866 ok
B_bench13 862329 expect 862329 ok
B_bench16 3024920 expect 3024920 ok
B_perft5 4865609 expect 4865609 ok
P_bench11 312866 expect 312866 ok
P_bench13 862329 expect 862329 ok
P_bench16 3024920 expect 3024920 ok
P_perft5 4865609 expect 4865609 ok
```

Each honesty line was a fresh process. The only commands before the bench or perft line were `uci` (to record `id name`) and then the measured command. No `setoption`.

## The three O runs

Same script output, from `o1_B.rows`, `o2_P_off.rows`, and `o3_P_on.rows`:

```
o1_B n 200 sum 9500069 expect_sum 9500069 first 41311 24872 28574 expect_first 41311 24872 28574
o1_B identical 200 of 200
o1_B match True
o2_P_off n 200 sum 9500069 expect_sum 9500069 first 41311 24872 28574 expect_first 41311 24872 28574
o2_P_off identical 200 of 200
o2_P_off match True
o3_P_on n 200 sum 9845650 expect_sum 9845650 first 23395 31504 35958 expect_first 23395 31504 35958
o3_P_on differ 200 expect_differ 200
o3_P_on match True
```

Against the brief's table: run (1) plain sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Run (2) switch false equal to (1) on all 200. Run (3) arm 10 switch true: sum 9,845,650; first three 23,395 / 31,504 / 35,958; 200 differ. All three matched.

S14, Threads 1, and Hash 16 were sent once at the start of each O process, each followed by `isready`. Runs 2 and 3 also sent `setoption name HindsightDepth value false` and `value true`. Every position was `ucinewgame`, `isready`, `position fen`, `isready`, `go depth 12`. Nodes are from the last `info` line that carried a `nodes` field before `bestmove`.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`, the same as the brief. `wc -l ~/uho.epd` printed 2632036. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, the same as the brief. book=ok.

Seat 030 openings are every 90th line of that file starting at line 30 (`~/mine.epd`, 29245 lines). The last 300 lines are `~/ctl.epd`. Chunks took lines from the top: 19 chunks times 250 openings is lines 1 through 4750, which does not reach those 300.

## C-ARRIVE and C-HALF

`arrive_check.txt` (counts, then 20 log lines around the first switch setoption):

```
true_count 20
bad_count 0
```

`grep -c "setoption name HindsightDepth value true"` was 20. `grep -c -E "unknown option|invalid value|No such option"` was 0. fastchess accepted `engine=true`.

C-HALF, output of `python3 ~/games_tsv.py pool FULL` saved as `half_pool.txt`:

```
side FULL: games 400 W-L-D 236-43-121 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 11, 47, 76, 65] Elo +182.83 95% [+155.38, +212.56]
```

FULL's Elo is +182.83, above +20. PASS. `grep -c -i adjudicat` on `~/half.out` was 0. The same search on `chunk_*.out` printed no files.

## POOL.txt and chunks

19 chunks, each 500 games, 9500 games. `wc -l chunk_*.tsv` totalled 9500. `play.log` has no FAILED line. play.sh then printed `minute 95: no new chunk` and exited. Chunk 19 had been started before minute 95 and finished at 2026-11-20T15:00:30Z, before minute 103. No fastchess process was killed.

Pasted `POOL.txt`, the output of `python3 ~/games_tsv.py pool ON` on the 19 chunk tsv files:

```
side ON: games 9500 W-L-D 2653-2446-4401 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [209, 1075, 1994, 1244, 228] Elo +7.57 95% [+3.00, +12.14]
```

## suspicions, not proven

fastchess left an untracked `config.json` in the repository root. Its resign, draw, maxmoves, and tablebase switches are `enabled: false`. I did not prove that fastchess never read that file. The match command line did not pass `-draw`, `-resign`, `-maxmoves`, or a tablebase path, and the committed game logs contain no line matching `adjudicat`.

## what I did NOT do

I did not apply a patch, build a second binary, open a pull request, force-push, or write any branch except `for-fable-and-opus/grok2-030`. I did not commit an executable, a net, a PGN, or the book. I did not repeat an opening. I did not send any engine option other than Threads, Hash, OwnBook, the S14 list, and HindsightDepth. I did not start a chunk at or after minute 95.

## what I am NOT sure about

The RESULT `id` field is `K3`, the label of arm 10 in the brief. I am not sure that field was meant to be that label rather than the engine's `id name` (`Chess Engine Forge 6.4.24 candidate`, recorded in the `.meta` files).

Each channel read was `git fetch --depth 1` of `handoff/fable-opus-combo29-all-20261114` and a listing of that tip. The tips I saw were `2b55a2216d319c923d16363f5c434eedcb78a95b`, then `010e2575f5e86abaae85552cd5168f56bb2c4f2d`, then `bcfdf4b5ecd5a0e2844a9160514c2b05cf5872c0`. None of those trees contained a `FABLE_TO_grok2_` file. A note that exists only off the tip would not have been visible.

## times: see stamps.txt

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/030/stamps.txt
?? config.json
?? forge-combo29/grok2/030/POOL.txt
?? forge-combo29/grok2/030/REPORT.md
?? forge-combo29/grok2/030/RESULT.txt
?? forge-combo29/grok2/030/chunk_19.out
?? forge-combo29/grok2/030/chunk_19.tsv
?? forge-combo29/grok2/030/play.log
```

## ls -la

```
total 3272
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2219 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    903 Nov 20 13:27 BUILD.txt
-rw-r--r-- 1 ubuntu ubuntu  56454 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51499 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56490 Nov 20 14:22 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51378 Nov 20 14:22 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56670 Nov 20 14:27 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51556 Nov 20 14:27 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56283 Nov 20 14:31 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51334 Nov 20 14:31 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56292 Nov 20 14:36 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51493 Nov 20 14:36 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56121 Nov 20 14:41 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51349 Nov 20 14:41 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56104 Nov 20 14:46 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51575 Nov 20 14:46 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55892 Nov 20 14:50 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:50 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56061 Nov 20 14:55 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51450 Nov 20 14:55 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56361 Nov 20 15:00 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 15:00 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56336 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51316 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55956 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51204 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56444 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51485 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56089 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51341 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56505 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51368 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56331 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51510 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56330 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51453 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56166 Nov 20 14:09 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51448 Nov 20 14:09 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56117 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51556 Nov 20 14:13 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:23 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2802 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46549 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:31 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42156 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:31 half_tsv_log.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5021 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5021 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5023 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5236 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5021 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5021 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5023 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5236 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1049 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    792 Nov 20 13:26 o1_B.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o1_B.rows
-rw-r--r-- 1 ubuntu ubuntu 309243 Nov 20 13:26 o1_B.txt
-rw-r--r-- 1 ubuntu ubuntu    834 Nov 20 13:26 o2_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o2_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu 309097 Nov 20 13:26 o2_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    833 Nov 20 13:26 o3_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o3_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu 309235 Nov 20 13:26 o3_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    732 Nov 20 13:27 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    656 Nov 20 15:02 play.log
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6278 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    229 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu  10467 Nov 20 13:25 run_step2.py
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    767 Nov 20 15:02 stamps.txt
```

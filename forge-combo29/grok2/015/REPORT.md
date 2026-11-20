# Seat 015, arm 5 (S10)

Arm 5, source seat 081, switch IdeaS10. Branch for-fable-and-opus/grok2-015. Model Grok 4.7. Exe P is the base commit 6b98f2170a3210e71beed04bbd2553972c253ed7 plus the seat 081 patch. Exe B is that base commit with no patch. Both are Release builds with g++ 13.3.0 and the CMake default march x86-64-v4. The machine has AVX-512F and BMI2, so FORGE_PORTABLE was left off.

The handoff branch had no forge-combo29/soak_all/FABLE_TO_grok2_*.md file at step 1 or at any later fetch (count 0).

## Patch

Source commit b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa, which is what `git rev-parse FETCH_HEAD` printed after `git fetch --depth 1 origin for-fable-and-opus/grok-081`.

`sha256sum ~/arm.patch` printed:

```
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  /home/ubuntu/arm.patch
```

That is the arm 5 sha256. `git apply --check` and `git apply` in the work tree both exited 0. patch_apply.txt records the diff stat: 5 files, 208 insertions, 7 deletions. No engine source was committed.

## Honesty

A fresh process for each line, no setoption. Output of `python3 forge-combo29/grok2/015/o_table.py` (same text as o_table.out):

```
honesty
B bench11 312866 expect 312866 ok
B bench13 862329 expect 862329 ok
B bench16 3024920 expect 3024920 ok
B perft5 4865609 expect 4865609 ok
P bench11 312866 expect 312866 ok
P bench13 862329 expect 862329 ok
P bench16 3024920 expect 3024920 ok
P perft5 4865609 expect 4865609 ok
honesty_all ok
```

## Three O runs

Same script, depth 12, S14 in the brief's order, then Threads 1, then Hash 16. Switch only on exe P. Table values: B sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Arm 5 on: sum 9,542,904, first three 41,311 / 24,872 / 28,574, 10 positions differ.

```
o_runs
B sum 9500069 first 41311 24872 28574
B expect_sum 9500069 expect_first 41311 24872 28574 match True
P_off sum 9500069 first 41311 24872 28574 differ_from_B 0 identical True
P_on sum 9542904 first 41311 24872 28574 differ_from_B 10
P_on expect_sum 9542904 expect_first 41311 24872 28574 expect_differ 10
P_on_match True
```

Raw transcripts: o_B.txt, o_P_off.txt, o_P_on.txt, each with a .meta file. id name on those runs: Chess Engine Forge 6.4.24 candidate.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both sha256 values match the brief. Seat 015 takes every 90th line of the epd starting at line 15. mine.epd has 29245 lines. The last 300 are ctl.epd. Chunks used the top 5250 lines (21 times 250) and did not reach that tail.

## C-ARRIVE

`grep -c` of `setoption name IdeaS10 value true` in the trace log was 20. `grep -c` of `unknown option|invalid value|No such option` was 0. The two counts and 20 log lines around the first switch setoption are in arrive_check.txt. The engine line in that window is `ON <--- setoption name IdeaS10 value true`.

## C-HALF

Output of `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/015/half.tsv` (same text as half_pool.txt):

```
side FULL: games 400 W-L-D 235-30-135 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 3, 46, 94, 57] Elo +196.69 95% [+172.78, +222.42]
```

FULL's Elo is above +20. fastchess printed Elo 196.69 on the same 400 games.

## Games

21 chunks, each 500 games, each chunk_*.out contains "Finished match". play.log has no FAILED line. play.sh printed `minute 95: no new chunk` and exited. No fastchess process was killed.

Pasted POOL.txt (`python3 ~/games_tsv.py pool ON` on the 21 chunk tsv files):

```
side ON: games 10500 W-L-D 2780-2861-4859 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [148, 1069, 2893, 996, 144] Elo -2.68 95% [-6.37, +1.01]
```

## Suspicions, not proven

The arrive trace shows fastchess sending Threads and IdeaS10 before Hash and the LMR options. match.sh names those values; this report does not show that a different send order would change a node count. The O runs, which sent S14 in the brief's order, matched the known counts.

The commit whose stamp line says `chunks 1` also contains chunk_2.out and chunk_2.tsv. Chunk 2 finished as those files were added. Later stamp lines name the chunks added in that commit. Chunk 21 is in the final commit.

## What I did not do

No pull request. No engine source, executable, net, PGN, or opening book in the commit. The patch's other spins (IdeaS10_Margin, IdeaS10_Flat, IdeaS10_Look, IdeaS10_Shrink, IdeaS10_Depth) were left at their defaults. The fastchess command line has no draw, resign, maxmoves, or tablebase adjudication. The last 300 openings were not used as match games. Arm 10 was not played. Openings were not repeated to add games. fastchess wrote config.json in the repo root during C-HALF because the shell was in the repo; that file had adjudication enabled false, and it was deleted without being committed.

## What I am not sure about

I am not sure fastchess applies -each options in the order written in match.sh. The trace quoted above is the order I saw for the first engine start.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/015/stamps.txt
?? forge-combo29/grok2/015/POOL.txt
?? forge-combo29/grok2/015/REPORT.md
?? forge-combo29/grok2/015/RESULT.txt
?? forge-combo29/grok2/015/chunk_21.out
?? forge-combo29/grok2/015/chunk_21.tsv
```

## ls -la forge-combo29/grok2/015

```
total 3356
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2203 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56152 Nov 20 14:12 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51483 Nov 20 14:12 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56472 Nov 20 14:16 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51577 Nov 20 14:16 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55878 Nov 20 14:20 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51463 Nov 20 14:20 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56268 Nov 20 14:24 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 14:24 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56349 Nov 20 14:29 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51538 Nov 20 14:29 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56008 Nov 20 14:33 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51314 Nov 20 14:33 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56687 Nov 20 14:37 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51717 Nov 20 14:37 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56390 Nov 20 14:42 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51557 Nov 20 14:42 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55992 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51388 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56199 Nov 20 14:50 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:50 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56169 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51288 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56158 Nov 20 14:54 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51345 Nov 20 14:54 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  55896 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51475 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56280 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51348 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55824 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51272 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56136 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56250 Nov 20 13:52 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 13:52 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 13:56 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51490 Nov 20 13:56 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56274 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56559 Nov 20 14:04 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51477 Nov 20 14:04 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56643 Nov 20 14:08 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 14:08 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:24 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47300 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42326 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    368 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    368 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    368 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    370 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    368 Nov 20 13:24 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    368 Nov 20 13:24 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    368 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    370 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1145 Nov 20 13:24 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1026 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281741 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    820 Nov 20 13:25 o_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282092 Nov 20 13:25 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    855 Nov 20 13:25 o_P_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282178 Nov 20 13:25 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    854 Nov 20 13:25 o_P_on.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu   3827 Nov 20 13:24 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    628 Nov 20 13:25 o_table.out
-rwxr-xr-x 1 ubuntu ubuntu   3094 Nov 20 13:24 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    574 Nov 20 13:25 patch_apply.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5454 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    696 Nov 20 15:01 stamps.txt
```

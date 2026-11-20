# Seat 025, arm 5 (S10)

Arm 5, source seat 081, branch `for-fable-and-opus/grok-081`, commit `b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa`. Switch `IdeaS10`. This seat's branch is `for-fable-and-opus/grok2-025`. Model name passed to the seat script: Grok 4.7.

## Patch

`sha256sum ~/arm.patch` printed `196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368`, the arm table value. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both succeeded (`APPLY_OK`, 5 files, 208 insertions, 7 deletions). The patch is not committed. Engine sources in this branch are untouched.

## Honesty

Both exes, one fresh process per command, no setoption. Nodes from the committed raw files:

- exe B bench 11: 312866; bench 13: 862329; bench 16: 3024920; perft 5: 4865609
- exe P bench 11: 312866; bench 13: 862329; bench 16: 3024920; perft 5: 4865609

Those are the known pins. `id name` in the `.meta` files is `Chess Engine Forge 6.4.24 candidate`. The machine has AVX-512 and BMI2, so the release build used CMake's default `FORGE_MARCH=x86-64-v4` and `FORGE_PORTABLE` off, with `CMAKE_CXX_COMPILER=g++` (GCC 13.3). The first `c++` link failed to find libstdc++.

## Three O runs

`otable.py` read the raw transcripts and printed `o_table.txt`:

```
B: n 200 sum 9500069 first 41311 / 24872 / 28574
Poff: n 200 sum 9500069 first 41311 / 24872 / 28574
Pon: n 200 sum 9542904 first 41311 / 24872 / 28574
off_identical 200 of 200
on_differ 10 of 200
```

Arm table for S10, switch true: sum 9,542,904; first three 41,311 / 24,872 / 28,574; 10 differ. Exe B sum 9,500,069 and the same first three. Switch false matched exe B on all 200 positions.

## Book

`~/uho.zip` sha256 `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `~/uho.epd` 2632036 lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both match the brief. Seat 025 took every 90th line starting at line 25 (`29245` lines in `~/mine.epd`). The last 300 lines were held out. Chunks used the top of the file and did not reach them.

## C-ARRIVE and C-HALF

C-ARRIVE: `arrive_check.txt` records `count setoption name IdeaS10 value true: 20` and `count unknown option|invalid value|No such option: 0`, plus 20 log lines around the first `setoption name IdeaS10 value true`. fastchess accepted `engine=true`.

C-HALF: `half_pool.txt` is the `games_tsv.py pool FULL` output:

```
side FULL: games 400 W-L-D 227-36-137 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 12, 43, 83, 61] Elo +180.58 95% [+153.61, +209.71]
```

FULL's Elo is above +20. Pass.

## POOL

22 chunks, each 500 games, 11000 games. `POOL.txt`:

```
side ON: games 11000 W-L-D 2827-3001-5172 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [170, 1156, 2997, 1032, 145] Elo -5.50 95% [-9.13, -1.86]
```

No chunk logged FAILED. No adjudication flags were passed to fastchess.

## Suspicions, not proven

The depth-12 sample changes only 10 of 200 positions, so many 20000-node games may never exercise the rule. I did not prove how often it fired inside the match, or that the Elo loss comes only from those positions.

## What I did NOT do

I did not open a pull request. I did not commit an engine binary, a net, a PGN, or any engine source. I did not send `IdeaS10_Look`, `IdeaS10_Shrink`, or `IdeaS10_Depth`. I did not repeat an opening. I did not play the held-out 300 lines. No `FABLE_TO_grok2_*.md` file was on the handoff branch at any fetch, so nothing on the channel was applied and `~/STOP_PLAY` was not created. The first honesty script sent `bench` and the depth as two lines; those outputs were wrong, the script was corrected, and only the corrected files are in the commit.

## What I am NOT sure about

I am not sure the RESULT field `id` was meant to be the arm label `S10` rather than the engine's `id name`. I used `S10`. Options for the O runs were sent once at process start, not again before every position. The node counts still matched the table. A watcher process committed each finished chunk and fetched the channel, on a 240 second cycle, instead of a hand-typed command each time. The push lines are in `~/commit_chunks.log` on this machine, and the final `git ls-remote` check is the one that says the remote has the last commit.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/025/stamps.txt
?? config.json
?? forge-combo29/grok2/025/POOL.txt
?? forge-combo29/grok2/025/REPORT.md
?? forge-combo29/grok2/025/RESULT.txt
```

## ls -la

```
total 3508
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2195 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56040 Nov 20 14:10 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:10 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56728 Nov 20 14:14 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51588 Nov 20 14:14 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56226 Nov 20 14:18 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51544 Nov 20 14:18 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56464 Nov 20 14:22 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51645 Nov 20 14:22 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56448 Nov 20 14:26 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51586 Nov 20 14:26 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  55894 Nov 20 14:30 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51464 Nov 20 14:30 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56205 Nov 20 14:34 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51414 Nov 20 14:34 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56744 Nov 20 14:39 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51645 Nov 20 14:39 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56560 Nov 20 14:43 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51607 Nov 20 14:43 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56284 Nov 20 14:47 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 14:47 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56427 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51314 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56420 Nov 20 14:51 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51637 Nov 20 14:51 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56520 Nov 20 14:55 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51477 Nov 20 14:55 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56007 Nov 20 14:58 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51505 Nov 20 14:58 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56113 Nov 20 13:38 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51186 Nov 20 13:38 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56605 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51688 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56426 Nov 20 13:46 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51332 Nov 20 13:46 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56105 Nov 20 13:50 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51468 Nov 20 13:50 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 13:54 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51344 Nov 20 13:54 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56183 Nov 20 13:58 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51386 Nov 20 13:58 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56844 Nov 20 14:02 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 14:02 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56635 Nov 20 14:06 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51433 Nov 20 14:06 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46853 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1034 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42350 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    220 Nov 20 13:25 honesty_B.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    220 Nov 20 13:25 honesty_P.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    727 Nov 20 13:25 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1030 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    832 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308841 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    867 Nov 20 13:25 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 309178 Nov 20 13:25 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    866 Nov 20 13:25 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 309243 Nov 20 13:25 o_Pon.txt
-rwxr-xr-x 1 ubuntu ubuntu   4100 Nov 20 13:24 orun.py
-rwxr-xr-x 1 ubuntu ubuntu   1573 Nov 20 13:24 otable.py
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:25 o_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4509 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    785 Nov 20 15:01 stamps.txt
```

# grok2 seat 026

Arm 6, id S32. Source seat 074. Commit 0fd01685b0465c11e29816b5a759e6496d2a69ae. Switch IdeaS32.

## Patch

`git fetch --depth 1 origin for-fable-and-opus/grok-074` then `git rev-parse FETCH_HEAD` printed `0fd01685b0465c11e29816b5a759e6496d2a69ae`.

`sha256sum ~/arm.patch` (re-run at report time):

```
18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. The diff stat was 3 files, 40 insertions, 1 deletion (`search.hpp`, `search.cpp`, `uci.cpp`).

## Honesty

`summarize_step2.py` reading the raw honesty files:

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
```

Each line is a fresh process of that exe, with no setoption. Expected values are the brief's pins: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.

## Three O runs

Same script, same raw files. Table values for arm 6: off sum 9,500,069 and first three 41,311 / 24,872 / 28,574; on sum 9,547,450, first three 41,442 / 24,989 / 28,711, 200 differ.

```
o_B positions 200 missing 0 sum 9500069 first [41311, 24872, 28574]
o_P_off positions 200 missing 0 sum 9500069 first [41311, 24872, 28574]
o_P_on positions 200 missing 0 sum 9547450 first [41442, 24989, 28711]
o_P_off differ_from_B 0
o_P_on differ_from_B 200
```

(1) matches the plain-engine sum and first three. (2) matches (1) on all 200 positions. (3) matches the arm table sum, first three, and 200 differing positions.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both sha256 values and the line count match the brief.

## C-ARRIVE

`grep -c "setoption name IdeaS32 value true" ~/arrive.log` printed 20. `grep -c -E "unknown option|invalid value|No such option" ~/arrive.log` printed 0. The 20 log lines around the first switch setoption are in `arrive_check.txt`. fastchess accepted `engine=true`.

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok2/026/half.tsv`:

```
side FULL: games 400 W-L-D 248-30-122 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 36, 89, 68] Elo +212.37 95% [+185.81, +241.34]
```

FULL's Elo is above +20. Pass.

## Pool

18 chunks, 9000 games. `wc -l chunk_*.tsv` totalled 9000. `~/play.log` has no FAILED line. `play.out` ends with `minute 95: no new chunk`.

Pasted `POOL.txt`:

```
side ON: games 9000 W-L-D 2402-2410-4188 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [201, 1123, 1846, 1143, 187] Elo -0.31 95% [-4.98, +4.37]
```

## suspicions, not proven

Chunk wall time grew from 00:04:42 on chunk 1 to about 00:05:06 later. I did not show that this changed any game. The matches are node-limited.

## what I did NOT do

I did not open a pull request. I did not edit engine source and I did not commit a binary. I did not send IdeaS32_OwedSlack. I did not pass adjudication flags. I did not switch to arm 10. I did not repeat an opening. No `FABLE_TO_grok2_*.md` file was on `handoff/fable-opus-combo29-all-20261114` at the STEP 1 fetch or at any STEP 4 push.

## what I am NOT sure about

The `git apply` transcript was not saved as its own file. The patch sha256 was re-measured and the on-sum matched the table, which is the check that exe P is that build.

fastchess sends the switch and the S14 options; the arrive log shows that for the 20-game sample, including `setoption name IdeaS32 value true` and zero refusal lines. I did not read the engine log of all 9000 games.

The id name in each honesty `.meta` comes from a separate `uci` process of the same binary. The bench and perft processes themselves were started with only that one command.

## times: see stamps.txt

times: see stamps.txt

## git status --short and ls -la

The next two blocks are the command output taken after REPORT.md, RESULT.txt, POOL.txt, and the STEP 5 stamp line were written, and before the STEP 5 commit.

```
 M forge-combo29/grok2/026/stamps.txt
?? config.json
?? forge-combo29/grok2/026/POOL.txt
?? forge-combo29/grok2/026/REPORT.md
?? forge-combo29/grok2/026/RESULT.txt
?? forge-combo29/grok2/026/chunk_18.out
?? forge-combo29/grok2/026/chunk_18.tsv
```

```
total 3088
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 14:59 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2298 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  55966 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56210 Nov 20 14:23 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51477 Nov 20 14:23 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56351 Nov 20 14:28 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 14:28 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55869 Nov 20 14:33 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51422 Nov 20 14:33 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56517 Nov 20 14:38 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51440 Nov 20 14:38 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56482 Nov 20 14:43 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51360 Nov 20 14:43 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56377 Nov 20 14:47 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51408 Nov 20 14:47 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56047 Nov 20 14:52 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51483 Nov 20 14:52 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56581 Nov 20 14:57 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 14:57 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  55863 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51111 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56386 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51408 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56298 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51311 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56510 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51599 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56534 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51387 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55994 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51354 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56005 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56385 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51545 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56281 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51540 Nov 20 14:13 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:26 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46571 Nov 20 13:29 half.out
-rw-r--r-- 1 ubuntu ubuntu   1030 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42274 Nov 20 13:29 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    822 Nov 20 13:24 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1028 Nov 20 13:26 match.sh
-rw-r--r-- 1 ubuntu ubuntu    844 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 306240 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    879 Nov 20 13:25 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 307953 Nov 20 13:25 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    878 Nov 20 13:25 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 308012 Nov 20 13:25 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4652 Nov 20 13:24 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:26 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 14:58 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4648 Nov 20 14:59 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 14:59 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    630 Nov 20 14:59 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2476 Nov 20 13:24 summarize_step2.py
```

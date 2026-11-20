# Seat 036 report

Arm 6, id S32. Source seat 074, branch for-fable-and-opus/grok-074, commit 0fd01685b0465c11e29816b5a759e6496d2a69ae. Switch IdeaS32. exe P is the base commit 6b98f2170a3210e71beed04bbd2553972c253ed7 plus that patch. exe B is the base commit with no patch. Both were release builds with g++ 13.3.0 and the CMake default -march=x86-64-v4 (this machine has AVX-512 and BMI2, so FORGE_PORTABLE was not turned on).

## Patch sha256 and git apply

18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch

Expected 18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5. It matches. git apply --check and git apply were run in /agent/repos/work. The patch applied. A later --check in the same command failed because the patch was already in the tree. The work-tree diff after apply:

 forge-combo29/include/forge/search.hpp |  6 ++++++
 forge-combo29/src/search.cpp           | 30 +++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  5 +++++
 3 files changed, 40 insertions(+), 1 deletion(-)

## Honesty

Fresh processes, no setoption. Output of read_honesty.py:

tag B
bench11 nodes 312866 expected 312866 ok
bench13 nodes 862329 expected 862329 ok
bench16 nodes 3024920 expected 3024920 ok
perft5 nodes 4865609 expected 4865609 ok
honesty ok

tag P
bench11 nodes 312866 expected 312866 ok
bench13 nodes 862329 expected 862329 ok
bench16 nodes 3024920 expected 3024920 ok
perft5 nodes 4865609 expected 4865609 ok
honesty ok

## Three O runs

Expected (1) exe B: sum 9500069; first three 41311 / 24872 / 28574.
Expected (2) exe P, IdeaS32 false: equal to (1) on all 200.
Expected (3) exe P, IdeaS32 true: sum 9547450; first three 41442 / 24989 / 28711; 200 differ.

Output of read_orun.py on the raw transcripts:

===== B =====
positions 200
sum 9500069
first 41311 24872 28574
===== OFF vs B =====
positions 200
sum 9500069
first 41311 24872 28574
differ 0
identical
===== ON vs B =====
positions 200
sum 9547450
first 41442 24989 28711
differ 200
not_identical

(1) and (3) match the arm table. (2) is identical to (1).

## Book

4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd

Both hashes match the brief's copy (zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07, epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a, 2632036 lines). Seat 036 took every 90th line of the epd starting at line 36 (29245 lines). The last 300 were kept for the controls. Chunks used the top of that file.

## C-ARRIVE and C-HALF

arrive_check.txt:

count setoption name IdeaS32 value true
20
count unknown option|invalid value|No such option
0
---- 20 log lines around the first setoption of the switch ----
first line number 394
[Engine] [13:32:51.774774] <     139830403000000>  OFF ---> option name CaptureFutilityDepth type spin default 6 min 0 max 15
[Engine] [13:32:51.774777] <     139830403000000>  OFF ---> option name FailLowContinuationBonus type spin default 0 min 0 max 300
[Engine] [13:32:51.774780] <     139830403000000>  OFF ---> option name IdeaS32_OwedSlack type spin default 0 min 0 max 64
[Engine] [13:32:51.774783] <     139830403000000>  OFF ---> option name Clear Hash type button
[Engine] [13:32:51.774787] <     139830403000000>  OFF ---> uciok
[TRACE ] [13:32:51.774982] <     139830403000000> fastchess --- Refreshing engine ON
[TRACE ] [13:32:51.775001] <     139830403000000> fastchess --- Sending setoption to engine ON Threads 1
[Engine] [13:32:51.775006] <     139830403000000>  ON <--- setoption name Threads value 1
[TRACE ] [13:32:51.775030] <     139830403000000> fastchess --- Sending setoption to engine ON IdeaS32 true
[Engine] [13:32:51.775047] <     139830403000000>  ON <--- setoption name IdeaS32 value true
[TRACE ] [13:32:51.775055] <     139830403000000> fastchess --- Sending setoption to engine ON Hash 16
[Engine] [13:32:51.775058] <     139830403000000>  ON <--- setoption name Hash value 16
[TRACE ] [13:32:51.775063] <     139830403000000> fastchess --- Sending setoption to engine ON OwnBook false
[Engine] [13:32:51.775066] <     139830403000000>  ON <--- setoption name OwnBook value false
[TRACE ] [13:32:51.775072] <     139830403000000> fastchess --- Sending setoption to engine ON LmrQuietBase 93
[Engine] [13:32:51.775075] <     139830403000000>  ON <--- setoption name LmrQuietBase value 93
[TRACE ] [13:32:51.775080] <     139830403000000> fastchess --- Sending setoption to engine ON LmrQuietDivisor 205
[Engine] [13:32:51.775083] <     139830403000000>  ON <--- setoption name LmrQuietDivisor value 205
[TRACE ] [13:32:51.775089] <     139830403000000> fastchess --- Sending setoption to engine ON LmrNoisyBase 13
[Engine] [13:32:51.775092] <     139830403000000>  ON <--- setoption name LmrNoisyBase value 13

The switch setoption count is 20 and the refusal count is 0. The engine named ON received `setoption name IdeaS32 value true`.

half pool, output of games_tsv.py pool FULL:

side FULL: games 400 W-L-D 218-40-142 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 11, 52, 85, 52] Elo +166.23 95% [+141.39, +192.76]

FULL's Elo is +166.23, above +20. C-HALF passed. fastchess's own summary in half.out printed the same Elo and the same pentanomial.

## POOL

19 chunks, 500 games each, 9500 games. No chunk was marked FAILED. Output of games_tsv.py pool ON on chunk_*.tsv:

side ON: games 9500 W-L-D 2539-2485-4476 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [210, 1111, 2078, 1117, 234] Elo +1.97 95% [-2.56, +6.51]

## suspicions, not proven

The 95% interval includes 0. This seat's 9500 games do not separate a gain of a few Elo from noise. That is the measurement. I do not have a suspicion that the harness played the wrong binary: honesty, switch-off identical to the base, and switch-on node counts all matched the known numbers, and C-HALF showed the node limit reaching the named side.

## what I did NOT do

I did not open a pull request. I did not commit an engine binary, a net, a PGN, or any engine source file. The patch lives only in the work tree that built exe P. I did not send IdeaS32_OwedSlack; it stayed at the default 0. I did not pass -draw, -resign, -maxmoves, or tablebases. I did not repeat an opening. I did not fall back to arm 10. No file FABLE_TO_grok2_N.md was on the handoff branch at any fetch, so nothing from the channel changed the run.

## what I am NOT sure about

fastchess wrote config.json in the repository root because the match's working directory was the repository. Its adjudication switches were off. I deleted that untracked file, and the __pycache__ directory under this seat folder, before the listing below. They are not results. I am not sure whether a later reader will mind that the status pasted here was taken before the step 5 commit, so it still shows these new files as untracked.

## times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/036/stamps.txt
?? forge-combo29/grok2/036/POOL.txt
?? forge-combo29/grok2/036/REPORT.md
?? forge-combo29/grok2/036/RESULT.txt
```

## ls -la

```
total 3236
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2226 Nov 20 13:33 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:26 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:26 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:26 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    171 Nov 20 13:26 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56351 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51302 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56533 Nov 20 14:24 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51598 Nov 20 14:24 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56240 Nov 20 14:28 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51478 Nov 20 14:28 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56233 Nov 20 14:32 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51439 Nov 20 14:32 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56421 Nov 20 14:37 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:37 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56300 Nov 20 14:41 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51512 Nov 20 14:41 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56350 Nov 20 14:45 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51525 Nov 20 14:45 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56100 Nov 20 14:50 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51307 Nov 20 14:50 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56309 Nov 20 14:54 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:54 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56514 Nov 20 14:59 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51398 Nov 20 14:59 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56022 Nov 20 13:41 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51209 Nov 20 13:41 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56503 Nov 20 13:45 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51482 Nov 20 13:45 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56333 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56355 Nov 20 13:54 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51394 Nov 20 13:54 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56539 Nov 20 13:58 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51304 Nov 20 13:58 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56672 Nov 20 14:03 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51556 Nov 20 14:03 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56213 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51452 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56361 Nov 20 14:11 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51500 Nov 20 14:11 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56562 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51523 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:26 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:33 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46891 Nov 20 13:36 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:36 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1033 Nov 20 13:33 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42179 Nov 20 13:36 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:31 honesty_B.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:31 honesty_P.txt
-rwxr-xr-x 1 ubuntu ubuntu    760 Nov 20 13:25 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1017 Nov 20 13:33 match.sh
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:31 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 307488 Nov 20 13:31 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 13:31 o_b.txt.err
-rw-r--r-- 1 ubuntu ubuntu    854 Nov 20 13:31 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309207 Nov 20 13:31 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 13:31 o_off.txt.err
-rw-r--r-- 1 ubuntu ubuntu    852 Nov 20 13:31 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 309139 Nov 20 13:31 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 13:31 o_on.txt.err
-rw-r--r-- 1 ubuntu ubuntu   5950 Nov 20 13:30 orun.py
-rw-r--r-- 1 ubuntu ubuntu    249 Nov 20 13:31 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:26 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:26 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    169 Nov 20 13:26 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:33 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    171 Nov 20 13:26 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1091 Nov 20 13:25 read_honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1317 Nov 20 13:26 read_orun.py
-rw-r--r-- 1 ubuntu ubuntu   7211 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    636 Nov 20 15:01 stamps.txt
```

# grok2 seat 076

Arm 6, id S32, source seat 074, commit 0fd01685b0465c11e29816b5a759e6496d2a69ae, SWITCH IdeaS32. Model Grok 4.7.

## Patch

sha256 of `~/arm.patch` (from `for-fable-and-opus/grok-074`, file `forge-combo29/grok/074/idea.patch.txt`):

```
18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git rev-parse FETCH_HEAD` printed `0fd01685b0465c11e29816b5a759e6496d2a69ae`. In `/agent/repos/work`, `git apply --check ~/arm.patch` then `git apply ~/arm.patch` both exited 0. `git diff --stat` there after that, and again at report time:

```
 forge-combo29/include/forge/search.hpp |  6 ++++++
 forge-combo29/src/search.cpp           | 30 +++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  5 +++++
 3 files changed, 40 insertions(+), 1 deletion(-)
```

IdeaS32_OwedSlack was left at its default. It was never sent.

## Honesty

`honesty_table.py` on the raw bench and perft files, exe B and exe P, each line a fresh process, no setoption:

```
honesty_b_bench11.txt: info string bench depth 11 nodes 312866 time 170 nps 1840388
honesty_b_bench13.txt: info string bench depth 13 nodes 862329 time 468 nps 1842583
honesty_b_bench16.txt: info string bench depth 16 nodes 3024920 time 1621 nps 1866082
honesty_b_perft5.txt: nodes 4865609
honesty_p_bench11.txt: info string bench depth 11 nodes 312866 time 180 nps 1738144
honesty_p_bench13.txt: info string bench depth 13 nodes 862329 time 458 nps 1882814
honesty_p_bench16.txt: info string bench depth 16 nodes 3024920 time 1527 nps 1980956
honesty_p_perft5.txt: nodes 4865609
```

Known nodes: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match.

The first cmake used `/usr/bin/c++` (Clang 18) and failed to link `-lstdc++`. The rebuild used `g++` 13.3.0 (GCC's own library), Release, default `FORGE_MARCH=x86-64-v4`. `/proc/cpuinfo` has avx512f and bmi2, so portable mode was not used.

## O runs

`o_table.py` reading `o_b.raw`, `o_off.raw`, `o_on.raw`:

```
B n=200 sum=9500069 first=41311 24872 28574
OFF n=200 sum=9500069 first=41311 24872 28574
ON n=200 sum=9547450 first=41442 24989 28711
OFF positions differing from B: 0
ON positions differing from B: 200
```

Against the arm table: B sum 9500069 and first three 41311 / 24872 / 28574; OFF equal on all 200; ON sum 9547450, first three 41442 / 24989 / 28711, 200 differ. All three hold. Options in each `.meta`: S14 in the listed order, then Threads 1, then Hash 16, then IdeaS32 true or false on exe P. Exe B was not sent IdeaS32. The three runs ran at the same time; the node counts still match the table.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both sha256 values and the line count match the brief. Seat 076 takes every 90th line from line 76. `mine.epd` has 29245 lines. Chunks used the top 23*250 = 5750 lines. The control tail starts at line 28946.

## C-ARRIVE and C-HALF

Arrive, re-counted from `~/arrive.log` at report time:

```
20
0
```

`setoption name IdeaS32 value true` appears 20 times. `unknown option|invalid value|No such option` appears 0 times. The 20 log lines around the first switch setoption are in `arrive_check.txt`. fastchess accepted `engine=true`.

C-HALF, `games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 248-26-126 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 5, 39, 81, 74] Elo +217.35 95% [+189.51, +247.91]
```

FULL's Elo is +217.35, above +20. fastchess printed the same Elo, 217.35.

## Pool

23 chunks, 11500 games. `POOL.txt`:

```
side ON: games 11500 W-L-D 3082-3037-5381 pairs 5750 (openings not in exactly 2 games: 0)
ptnml [269, 1389, 2402, 1408, 282] Elo +1.36 95% [-2.83, +5.55]
```

Finish reasons in the committed `chunk_*.out` files (`grep Finished game`):

```
   2655 Black mates
   3606 Draw by 3-fold repetition
    936 Draw by fifty moves rule
    813 Draw by insufficient mating material
     26 Draw by stalemate
   3464 White mates
```

Those six counts add to 11500. The draw lines add to 5381, the same draw count as the pool.

## suspicions, not proven

The ON point estimate was about +8 Elo after 4000 games and +1.36 after 11500. The 95% interval at the end includes 0. I have no evidence this path is anything other than the sample moving inside a widening then tightening interval.

fastchess wrote `/agent/repos/dwqww/config.json` while the match ran (timestamp 15:01, during chunk 23). I opened it. `resign.enabled`, `draw.enabled`, `maxmoves.enabled`, and `tb_adjudication.enabled` are all false. `match.sh` passes no `-draw`, `-resign`, `-maxmoves`, or tablebase flag. I did not commit `config.json`.

## what I did NOT do

- No pull request.
- No engine source, binary, net, or PGN committed. The patch was applied only in the work tree.
- IdeaS32_OwedSlack was not sent.
- Arm 10 was not played. The ON sum matched.
- The reserved last 300 openings of `mine.epd` were not played.
- No `FABLE_TO_grok2_*.md` existed on `handoff/fable-opus-combo29-all-20261114` at STEP 1, at the chunk pushes, or at 2026-11-20T15:05:01Z. Nothing from the channel changed the run.
- `config.json` was not added.

## what I am NOT sure about

- Whether fastchess's own Elo over the 23 separate PGNs would match `games_tsv.py` to the hundredth. On C-HALF the two agreed at +217.35. The match result above is the pool script, which is the one the brief asks for.
- The three O runs shared the machine. They matched the known node counts, so I am treating the counts as unaffected. I did not also run them one at a time.

## times: see stamps.txt

The first stamp is 2026-11-20T13:23:28Z. Play printed `minute 95: no new chunk` after chunk 23. Chunk 23 was started before minute 95 and finished at 2026-11-20T15:01:37Z.

## git status --short


```
 M forge-combo29/grok2/076/stamps.txt
?? config.json
?? forge-combo29/grok2/076/POOL.txt
?? forge-combo29/grok2/076/REPORT.md
?? forge-combo29/grok2/076/RESULT.txt
```

## ls -la

```
total 3516
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2324 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56374 Nov 20 14:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51386 Nov 20 14:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56633 Nov 20 14:15 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51586 Nov 20 14:15 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56234 Nov 20 14:19 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 14:19 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56927 Nov 20 14:23 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51453 Nov 20 14:23 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56156 Nov 20 14:26 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:26 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56521 Nov 20 14:30 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51585 Nov 20 14:30 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56120 Nov 20 14:34 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51382 Nov 20 14:34 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56658 Nov 20 14:38 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51487 Nov 20 14:38 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56032 Nov 20 14:42 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 14:42 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56348 Nov 20 14:46 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:46 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56535 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51237 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56167 Nov 20 14:49 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 14:49 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56228 Nov 20 14:53 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51489 Nov 20 14:53 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56448 Nov 20 14:57 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51551 Nov 20 14:57 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56129 Nov 20 15:01 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu  51424 Nov 20 15:01 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu  56375 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51412 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56520 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51493 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56222 Nov 20 13:48 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 13:48 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56387 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56242 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51356 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56599 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51615 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56575 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51609 Nov 20 14:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:32 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46578 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu   1005 Nov 20 13:32 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42226 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    350 Nov 20 13:27 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu    400 Nov 20 13:27 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu   1017 Nov 20 13:32 match.sh
-rw-r--r-- 1 ubuntu ubuntu    759 Nov 20 13:27 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 281698 Nov 20 13:27 o_b.raw
-rw-r--r-- 1 ubuntu ubuntu    794 Nov 20 13:27 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281766 Nov 20 13:27 o_off.raw
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:27 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 281718 Nov 20 13:27 o_on.raw
-rw-r--r-- 1 ubuntu ubuntu   3738 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1412 Nov 20 13:27 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:32 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5980 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1413 Nov 20 15:05 stamps.txt
```

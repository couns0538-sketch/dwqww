# Seat 079, arm 9

Arm 9, id S13, source seat 016, commit cdde64371237fe7778c713655c0c4b5c957a5fe2 on branch for-fable-and-opus/grok-016. Switch IdeaS13. Model Grok 4.7.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed the arm's sha256. `git apply --check` then `git apply` on the work tree succeeded.

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

```
git apply --check ~/arm.patch && git apply ~/arm.patch
APPLY_OK
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

The CPU has avx512f and bmi2, and g++ is 13.3.0, so both engines were Release builds with the lock flags (`-march=x86-64-v4`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`). That choice is recorded in build_note.txt. The book download and the fastchess build ran while those compiles ran. They do not change either engine.

## Honesty numbers

`honesty_table.py` read the raw bench and perft transcripts. Exe B and exe P both match.

```
b bench11 nodes 312866 expected 312866 ok
b bench13 nodes 862329 expected 862329 ok
b bench16 nodes 3024920 expected 3024920 ok
b perft5 nodes 4865609 expected 4865609 ok
honesty ok
```

```
p bench11 nodes 312866 expected 312866 ok
p bench13 nodes 862329 expected 862329 ok
p bench16 nodes 3024920 expected 3024920 ok
p perft5 nodes 4865609 expected 4865609 ok
honesty ok
```

Each measured command was the first line of a fresh process. No setoption was sent before it. `uci` was sent after the measurement so the transcript contains `id name`.

## Three O runs

`o_table.py` read o_b.txt, o_off.txt and o_on.txt. Threads 1 and Hash 16 were sent first, then the S14 options in the brief's order, then IdeaS13 on exe P only.

Known row for arm 9: sum 9,722,445; first three 19,900 / 22,525 / 42,778; 200 differ. Base row: sum 9,500,069; first three 41,311 / 24,872 / 28,574.

```
B sum 9500069 first 41311 24872 28574
OFF sum 9500069 first 41311 24872 28574
ON sum 9722445 first 19900 22525 42778
OFF equal to B on 200 of 200
ON differ from B on 200 of 200
B vs known ok sum 9500069 want 9500069 first 41311 24872 28574 want 41311 24872 28574
OFF vs B yes
ON vs known ok sum 9722445 want 9722445 first 19900 22525 42778 want 19900 22525 42778 differ 200 want 200
```

## Book sha256

Both digests match the brief. Seat 079 took every 90th line starting at line 79.

```
uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
mine.epd ctl
  29244 /home/ubuntu/mine.epd
    300 /home/ubuntu/ctl.epd
     10 /home/ubuntu/ctl_arrive.epd
    200 /home/ubuntu/ctl_half.epd
  29754 total
```

## C-ARRIVE and C-HALF

Arrive: `grep -c` of `setoption name IdeaS13 value true` printed 20. `grep -c` of `unknown option|invalid value|No such option` printed 0. The 20 log lines around the first switch setoption are in arrive_check.txt. The first engine line of that setoption is `ON <--- setoption name IdeaS13 value true`.

Half, from `games_tsv.py pool FULL` on half.tsv (400 games, FULL at 20000 nodes against HALF at 10000, switch false on both):

```
side FULL: games 400 W-L-D 235-32-133 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 48, 83, 63] Elo +194.34 95% [+168.65, +222.12]
```

FULL's Elo is above +20.

## POOL.txt and the number of chunks

20 chunks, each 500 games, 10000 games. `games_tsv.py pool ON` on chunk_1.tsv through chunk_20.tsv:

```
side ON: games 10000 W-L-D 2598-2775-4627 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [277, 1297, 2002, 1174, 250] Elo -6.15 95% [-10.76, -1.54]
```

Chunk 20 started when chunk 19 finished at 14:54:51Z (minute 91) and fastchess printed `Finished match` at 14:59:13Z. play.sh then printed `minute 95: no new chunk` and exited. No chunk was killed.

## suspicions, not proven

The patch stores `ss->pawn_key` on every node even when IdeaS13 is off. Exe P with the switch false matched exe B on all 200 positions, so that store did not change these node counts. Nothing else looked wrong in the games: every chunk tsv has 500 lines, the pool has 0 openings that are not in exactly two games, and play.log has no FAILED line.

## what I did NOT do

I did not open a pull request. I did not commit an engine source file, an executable, a net, or a PGN. I did not pass any adjudication option to fastchess. I did not set IdeaS13_Lookback or IdeaS13_ReduceDivisor; they stayed at the patch defaults. I did not fall back to arm 10. I did not replay an opening. I did not add the untracked config.json at the repository root.

## what I am NOT sure about

The arrive log contains 20 copies of `setoption name IdeaS13 value true` for a 20-game control. The check requires one or more, and the refusal count is 0, so the control passed. I am not sure whether fastchess sends that option once per game or once per engine process.

fastchess prints its own Elo after each chunk. Those figures are not the pair Elo from games_tsv.py. The result line uses only games_tsv.py.

## times: see stamps.txt

## git status --short

## ls -la
```
 M forge-combo29/grok2/079/stamps.txt
?? config.json
?? forge-combo29/grok2/079/POOL.txt
?? forge-combo29/grok2/079/REPORT.md
?? forge-combo29/grok2/079/RESULT.txt
?? forge-combo29/grok2/079/chunk_20.out
?? forge-combo29/grok2/079/chunk_20.tsv
```

```
total 3300
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2218 Nov 20 13:35 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    204 Nov 20 13:28 b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    204 Nov 20 13:28 b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    204 Nov 20 13:28 b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:28 b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    375 Nov 20 13:35 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    206 Nov 20 13:28 b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:28 b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1271 Nov 20 13:29 build_note.txt
-rw-r--r-- 1 ubuntu ubuntu  56250 Nov 20 14:16 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 14:16 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56445 Nov 20 14:21 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51492 Nov 20 14:21 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56337 Nov 20 14:25 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51535 Nov 20 14:25 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55866 Nov 20 14:29 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51416 Nov 20 14:29 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56318 Nov 20 14:33 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51699 Nov 20 14:33 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56001 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51534 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56042 Nov 20 14:42 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51361 Nov 20 14:42 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56591 Nov 20 14:46 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 14:46 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56260 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51467 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56236 Nov 20 14:54 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51429 Nov 20 14:54 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56489 Nov 20 13:39 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51241 Nov 20 13:39 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56297 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51458 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56035 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51381 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56719 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51482 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56257 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56102 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51248 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56153 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51320 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  55729 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51368 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56497 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56430 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51452 Nov 20 14:12 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu     93 Nov 20 13:29 fen_sha.txt
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46709 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1033 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42166 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:33 half_tsv_log.txt
-rw-r--r-- 1 ubuntu ubuntu    182 Nov 20 13:29 honesty_b.txt
-rw-r--r-- 1 ubuntu ubuntu    182 Nov 20 13:29 honesty_p.txt
-rw-r--r-- 1 ubuntu ubuntu   2402 Nov 20 13:27 honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1425 Nov 20 13:27 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu   1017 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    771 Nov 20 13:29 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 281838 Nov 20 13:29 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    806 Nov 20 13:29 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282096 Nov 20 13:29 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    805 Nov 20 13:29 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282192 Nov 20 13:29 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   5543 Nov 20 13:28 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   2304 Nov 20 13:28 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    383 Nov 20 13:29 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 13:29 patch_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:29 patch_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    204 Nov 20 13:28 p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5176 Nov 20 13:28 p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    204 Nov 20 13:28 p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5176 Nov 20 13:28 p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    204 Nov 20 13:28 p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5178 Nov 20 13:28 p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    206 Nov 20 13:28 p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5389 Nov 20 13:28 p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   5583 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    723 Nov 20 15:02 stamps.txt
```

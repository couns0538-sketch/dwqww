# grok2 seat 034

Arm 4, id B8b. Source seat 028, branch for-fable-and-opus/grok-028, commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75. Switch IdeaB8. exe P is /tmp/forge-work/forge. exe B is /tmp/forge-base/forge. Both are Release CMake builds with g++ 13.3.0. The CPU has AVX-512 and BMI2, so the build used the default march x86-64-v4 and left FORGE_PORTABLE off.

## Patch

sha256 of ~/arm.patch, from `git show FETCH_HEAD:forge-combo29/grok/028/idea.patch.txt` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-028`:

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

`git rev-parse FETCH_HEAD` printed 4bf95fd80adf523e97fa250bb8572c946cf0fc75. In the work tree, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both exited 0. The apply stat was 3 files, 173 insertions, 4 deletions (search.hpp, search.cpp, uci.cpp).

## Honesty

`show_measures.py` read the raw logs. Both engines:

```
honesty b
  bench11 312866 expect 312866 ok
  bench13 862329 expect 862329 ok
  bench16 3024920 expect 3024920 ok
  perft5 4865609 expect 4865609 ok
honesty p
  bench11 312866 expect 312866 ok
  bench13 862329 expect 862329 ok
  bench16 3024920 expect 3024920 ok
  perft5 4865609 expect 4865609 ok
```

Each line was a fresh process. The .meta files record the exe path, sha256, and id name `Chess Engine Forge 6.4.24 candidate`. No setoption was sent before those commands.

## Three O runs

Same script, against the arm table (sum 9,500,069 and first three 41,311 / 24,872 / 28,574 for exe B; IdeaB8 on: 9,718,009; 17,283 / 17,878 / 31,115; 200 differ):

```
positions b 200 off 200 on 200
sum b 9500069 off 9500069 on 9718009
first3 b 41311 24872 28574
first3 off 41311 24872 28574
first3 on 17283 17878 31115
off positions differ from b 0
on positions differ from b 200
b sum vs 9500069 ok
b first3 vs 41311 24872 28574 ok
off identical yes
on sum vs 9718009 ok
on first3 vs 17283 17878 31115 ok
on differ vs 200 ok
```

first200.fens sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines. S14 and Threads 1, Hash 16 were sent in the brief's order. Run (3) also sent `setoption name IdeaB8 value true`. IdeaB8_Weight and IdeaB8_Swing were left at their defaults.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 034 took every 90th line from line 34: 29245 lines in ~/mine.epd. The last 300 are the controls and were not used as chunk openings.

## C-ARRIVE and C-HALF

C-ARRIVE, from arrive_check.txt: `setoption name IdeaB8 value true` count 20, and `unknown option|invalid value|No such option` count 0. The trace shows the engine ON receiving `setoption name IdeaB8 value true`.

C-HALF, fastchess on 400 games (FULL 20000 nodes vs HALF 10000, switch false on both), from half.out:

```
Results of FULL vs HALF (20000 nodes - 10000 nodes, 1t, 16MB, ctl_half.epd):
Elo: 207.46 +/- 26.98, nElo: 329.85 +/- 34.05
LOS: 100.00 %, DrawRatio: 19.50 %, PairsRatio: 25.83
Games: 400, Wins: 244, Losses: 30, Draws: 126, Points: 307.0 (76.75 %)
Ptnml(0-2): [0, 6, 39, 90, 65], WL/DD Ratio: 1.60
Finished match
```

`games_tsv.py pool FULL` on half.tsv printed:

```
side FULL: games 400 W-L-D 244-30-126 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 39, 90, 65] Elo +207.46 95% [+181.60, +235.57]
```

FULL's Elo is +207.46, above +20. Pass.

## Pool

20 chunks, 10000 games. No chunk failed. play.sh then printed `minute 95: no new chunk`. POOL.txt, from `python3 ~/games_tsv.py pool ON` on the chunk tsv files:

```
side ON: games 10000 W-L-D 2777-2531-4692 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [213, 1166, 2040, 1324, 257] Elo +8.55 95% [+4.05, +13.05]
```

## suspicions, not proven

fastchess wrote an untracked config.json at the repository root while matches ran from that directory. The resign, draw, maxmoves, and tablebase blocks in it have `"enabled": false`. match.sh does not pass -draw, -resign, -maxmoves, or tablebases. Sampled chunk outs end on mate, 3-fold repetition, or insufficient mating material. I did not prove that no game was cut short by some other fastchess default.

The tsv Termination field is the word normal. Scoring uses the Result header. On the half control the script's W-L-D and pentanomial matched the fastchess console.

## what I did NOT do

I did not open a pull request. I did not edit engine source. I did not build a new idea. I did not send IdeaB8_Weight or IdeaB8_Swing. I did not fall back to arm 10. I did not repeat an opening. I did not commit PGNs, binaries, or config.json. No FABLE_TO_grok2 file was on the handoff branch at any fetch, so I never touched ~/STOP_PLAY. I did not kill a chunk: the last one finished at 14:57:13Z, and play.sh started no further chunk.

## what I am NOT sure about

I am not sure the interval in POOL.txt is the same estimator fastchess prints as `Elo +/-`. The half control's point Elo matched fastchess to the printed 207.46. The match chunks were not rescored with fastchess's own formula.

I am not sure a later handoff note appeared in the seconds after the last channel fetch at 14:58:37Z. That fetch still had no FABLE_TO_grok2 file.

## times: see stamps.txt

The first stamp is 2026-11-20T13:22:12Z. Chunk 20's stamp is 2026-11-20T14:58:35Z. STEP 5 is the stamp added with this report.

## git status --short and ls -la

The next two blocks are the command output captured after POOL.txt, REPORT.md, RESULT.txt, and the STEP 5 stamp existed.

```
$ git status --short
 M forge-combo29/grok2/034/stamps.txt
?? config.json
?? forge-combo29/grok2/034/POOL.txt
?? forge-combo29/grok2/034/REPORT.md
?? forge-combo29/grok2/034/RESULT.txt
```

```
$ ls -la forge-combo29/grok2/034
total 3288
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2236 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    229 Nov 20 13:31 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56481 Nov 20 14:14 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51423 Nov 20 14:14 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56655 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51493 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56328 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51363 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56557 Nov 20 14:27 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51328 Nov 20 14:27 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 14:31 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51534 Nov 20 14:31 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56362 Nov 20 14:35 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51306 Nov 20 14:35 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56292 Nov 20 14:40 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51335 Nov 20 14:40 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55866 Nov 20 14:44 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51331 Nov 20 14:44 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56588 Nov 20 14:48 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:48 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56125 Nov 20 14:52 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51604 Nov 20 14:52 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55870 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  50959 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56445 Nov 20 14:57 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51538 Nov 20 14:57 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56295 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51337 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56523 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51255 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56196 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51421 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56359 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56823 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51522 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56063 Nov 20 14:01 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51443 Nov 20 14:01 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56466 Nov 20 14:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51587 Nov 20 14:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55949 Nov 20 14:10 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51551 Nov 20 14:10 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46591 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu   1035 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42300 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:26 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5215 Nov 20 13:26 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5170 Nov 20 13:26 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5170 Nov 20 13:26 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5172 Nov 20 13:26 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    142 Nov 20 13:26 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5383 Nov 20 13:26 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1019 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    657 Nov 20 13:26 measures.txt
-rw-r--r-- 1 ubuntu ubuntu    874 Nov 20 13:26 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_b.rows
-rw-r--r-- 1 ubuntu ubuntu 281683 Nov 20 13:26 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    915 Nov 20 13:26 o_p_off.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_p_off.rows
-rw-r--r-- 1 ubuntu ubuntu 281807 Nov 20 13:26 o_p_off.txt
-rw-r--r-- 1 ubuntu ubuntu    914 Nov 20 13:26 o_p_on.meta
-rw-r--r-- 1 ubuntu ubuntu   1899 Nov 20 13:26 o_p_on.rows
-rw-r--r-- 1 ubuntu ubuntu 282419 Nov 20 13:26 o_p_on.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 14:58 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5894 Nov 20 15:00 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 14:59 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   6551 Nov 20 13:25 run_measures.py
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   3690 Nov 20 13:26 show_measures.py
-rw-r--r-- 1 ubuntu ubuntu    743 Nov 20 15:00 stamps.txt
```

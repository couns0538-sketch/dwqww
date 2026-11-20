# Seat 059, arm 9

Arm 9, S13. Source seat 016. Branch `for-fable-and-opus/grok-016`, commit `cdde64371237fe7778c713655c0c4b5c957a5fe2`. Switch `IdeaS13`. The other patch options (`IdeaS13_Lookback`, `IdeaS13_ReduceDivisor`) were left at their defaults and were never sent.

## Patch

`sha256sum ~/arm.patch` printed:

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree both exited 0. After apply, `git -C /agent/repos/work diff --stat` printed:

```
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

Exe B is `/tmp/build-base/forge` (plain tree). Exe P is `/tmp/build-work/forge` (patched tree). Both are Release builds with g++ 13.3.0 and the CMake default `-march=x86-64-v4`. The machine's flags include `avx512f` and `bmi2`, so `FORGE_PORTABLE` was left off. No build product was committed.

## Honesty

`python3 sum_runs.py` reads the raw bench and perft files. Both exes match the known nodes. Pasted output is in the O section below (the honesty half of the same run).

## Three O runs

Known table for this arm: exe B sum 9,500,069, first three 41,311 / 24,872 / 28,574. Switch false equals exe B on all 200. Switch true: sum 9,722,445; first three 19,900 / 22,525 / 42,778; 200 differ.

Pasted output of `python3 sum_runs.py` (it reads `honesty_*` and `o1_raw.txt`, `o2_raw.txt`, `o3_raw.txt`):

```
== honesty_B honesty ==
bench 11 depth 11 nodes 312866 expect 312866 ok
bench 13 depth 13 nodes 862329 expect 862329 ok
bench 16 depth 16 nodes 3024920 expect 3024920 ok
go perft 5 nodes 4865609 expect 4865609 ok
== honesty_P honesty ==
bench 11 depth 11 nodes 312866 expect 312866 ok
bench 13 depth 13 nodes 862329 expect 862329 ok
bench 16 depth 16 nodes 3024920 expect 3024920 ok
go perft 5 nodes 4865609 expect 4865609 ok
== O runs ==
o1 B n 200 sum 9500069 first 41311 24872 28574 differ_from_o1 0
o2 P false n 200 sum 9500069 first 41311 24872 28574 differ_from_o1 0
o3 P true n 200 sum 9722445 first 19900 22525 42778 differ_from_o1 200
o2_equal_o1 True
o1_sum_expect 9500069 match True
o1_first_expect 41311 24872 28574 match True
o3_sum_expect 9722445 match True
o3_first_expect 19900 22525 42778 match True
o3_differ_expect 200 match True
```

## Book

`sha256sum` of the zip and of the unzipped epd, and `wc -l` of the epd, saved in `book_check.txt`:

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd_lines 2632036
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine_lines 29245
```

Both hashes match the brief. Seat 059 takes every 90th line of `uho.epd` starting at line 59 (`mine.epd`, 29245 lines). The last 300 of those lines were held out for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE: `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` finished the match (20 games). Counts from `arrive_check.txt`:

```
true_count 20
bad_count 0
```

`true_count` is the count of `setoption name IdeaS13 value true`. `bad_count` is the count of `unknown option|invalid value|No such option`. The 20 log lines around the first switch setoption are in `arrive_check.txt`.

C-HALF passed on the first run. Pasted output of `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/059/half.tsv`:

```
side FULL: games 400 W-L-D 225-35-140 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 10, 48, 80, 61] Elo +179.45 95% [+152.81, +208.19]
```

FULL's Elo is above +20.

## Pool

21 chunks, each 500 games (`wc -l` total 10500). `play.sh` then printed `minute 95: no new chunk` and exited. No chunk was killed. No chunk logged FAILED.

Pasted `POOL.txt` (`python3 ~/games_tsv.py pool ON forge-combo29/grok2/059/chunk_*.tsv`):

```
side ON: games 10500 W-L-D 2690-2873-4937 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [266, 1344, 2172, 1243, 225] Elo -6.06 95% [-10.43, -1.68]
```

## Suspicions, not proven

The node cap is 20000, so a short-game effect could move the Elo without saying what the same switch does on a time control. The interval above is only the 20000-node match. I did not run a second control that would separate those.

The arrive trace is interleaved across engines. The setoption line is in the 20-line excerpt, and the count of that line in the whole log is 20. I did not hand-check all 20 occurrences.

## What I did not do

I did not open a pull request. I did not edit engine source on this branch. I did not add adjudication (`-draw`, `-resign`, `-maxmoves`, tablebases). I did not replay an opening. I did not send `IdeaS13_Lookback` or `IdeaS13_ReduceDivisor`. I did not fall back to arm 10. I did not commit an executable, a net, a PGN, or the book. The handoff branch had no `FABLE_TO_grok2_*.md` file at the fetches I made, so no channel instruction was applied.

## What I am not sure about

`id` in `RESULT.txt` is `S13`, the label on arm 9 in the arm table. The brief does not define that field in another sentence.

`games_tsv.py` records the PGN `Termination` header. fastchess wrote `normal` there. Results are still `1-0`, `0-1`, or `1/2-1/2`, and every opening paired into exactly two games.

The `ls` pasted below was taken after this file and `RESULT.txt` existed, and before this `ls` text was appended, so the listed byte size of `REPORT.md` is the size before the appendix.

## Times

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/059/stamps.txt
?? config.json
?? forge-combo29/grok2/059/POOL.txt
?? forge-combo29/grok2/059/REPORT.md
?? forge-combo29/grok2/059/RESULT.txt

$ ls -la forge-combo29/grok2/059
total 3376
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2314 Nov 20 13:32 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    217 Nov 20 13:34 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56659 Nov 20 14:14 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51381 Nov 20 14:14 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56038 Nov 20 14:18 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 14:18 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56481 Nov 20 14:22 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 14:22 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56131 Nov 20 14:26 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 14:26 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55781 Nov 20 14:30 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 14:30 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56743 Nov 20 14:34 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51317 Nov 20 14:34 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  55947 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51318 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56090 Nov 20 14:42 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51511 Nov 20 14:42 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56474 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51608 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56395 Nov 20 14:50 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51486 Nov 20 14:50 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56447 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51152 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56467 Nov 20 14:54 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51720 Nov 20 14:54 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56529 Nov 20 14:57 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51634 Nov 20 14:57 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56326 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56906 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51257 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56864 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51466 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56472 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51217 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55861 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51295 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56895 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51580 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56299 Nov 20 14:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51471 Nov 20 14:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56655 Nov 20 14:10 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51429 Nov 20 14:10 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:27 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46875 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:34 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1031 Nov 20 13:34 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42353 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   7020 Nov 20 13:29 harness.py
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    290 Nov 20 13:27 honesty_B.runlog
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 13:27 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    290 Nov 20 13:27 honesty_P.runlog
-rw-r--r-- 1 ubuntu ubuntu   1020 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281589 Nov 20 13:29 o1_raw.txt
-rw-r--r-- 1 ubuntu ubuntu    774 Nov 20 13:29 o1_raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    185 Nov 20 13:29 o1.runlog
-rw-r--r-- 1 ubuntu ubuntu 281795 Nov 20 13:29 o2_raw.txt
-rw-r--r-- 1 ubuntu ubuntu    809 Nov 20 13:29 o2_raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    185 Nov 20 13:29 o2.runlog
-rw-r--r-- 1 ubuntu ubuntu 281987 Nov 20 13:29 o3_raw.txt
-rw-r--r-- 1 ubuntu ubuntu    808 Nov 20 13:29 o3_raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    185 Nov 20 13:29 o3.runlog
-rw-r--r-- 1 ubuntu ubuntu    849 Nov 20 15:00 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5929 Nov 20 15:00 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1257 Nov 20 15:00 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3129 Nov 20 13:27 sum_runs.py
```

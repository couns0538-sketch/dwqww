# grok2 seat 009

Arm 9, id S13, source seat 016, branch for-fable-and-opus/grok-016, commit cdde64371237fe7778c713655c0c4b5c957a5fe2. SWITCH IdeaS13. exe P is /tmp/forge-builds/work/forge. exe B is /tmp/forge-builds/base/forge. Both are Release builds with g++ 13.3.0, the default march x86-64-v4 (this machine has AVX-512 and BMI2, so FORGE_PORTABLE was left off).

## Patch

sha256 of ~/arm.patch:

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

That is the arm 9 sha256. git rev-parse FETCH_HEAD printed cdde64371237fe7778c713655c0c4b5c957a5fe2. In the work tree, `git apply --check ~/arm.patch` then `git apply ~/arm.patch` printed APPLY OK and this stat:

```
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

The patch is not committed. The other patch options, IdeaS13_Lookback and IdeaS13_ReduceDivisor, were left at their defaults and were never sent.

## Honesty

Fresh process per line, uci and isready only, no setoption. table.py read the raw files:

```
HONESTY
B bench11 [('11', '312866')]
B bench13 [('13', '862329')]
B bench16 [('16', '3024920')]
B perft5 ['nodes 4865609']
P bench11 [('11', '312866')]
P bench13 [('13', '862329')]
P bench16 [('16', '3024920')]
P perft5 ['nodes 4865609']
```

Known targets are bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Both exes match. honesty_B_bench11.meta records exe /tmp/forge-builds/base/forge, sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83, id name Chess Engine Forge 6.4.24 candidate, options (none). The patched exe sha256 in orun_3_Pon.meta is 018e977106c57cebbf6cb0339c95c93d9a8117232849895dc94833fbf19adbfc, same id name.

## Three O runs

Same table.py output, from orun_1_B.out, orun_2_Poff.out, orun_3_Pon.out:

```
O RUNS
B count 200 sum 9500069 first 41311 24872 28574
Poff count 200 sum 9500069 first 41311 24872 28574
Pon count 200 sum 9722445 first 19900 22525 42778
Poff positions differing from B: 0
Pon positions differing from B: 200
```

Known run (1): sum 9500069, first three 41311 / 24872 / 28574. Run (2) equals run (1) on all 200 positions. Arm 9 run (3): sum 9722445, first three 19900 / 22525 / 42778, 200 differ. All three match. orun_2_Poff.meta sends IdeaS13 value false. orun_3_Pon.meta sends IdeaS13 value true. Both send Threads 1, Hash 16, and the S14 options in the listed order.

## Book

book_sha.txt:

```
sha256sum ~/uho.zip ~/uho.epd
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
```

Those are the published zip and epd hashes. Seat 009 took every 90th line of uho.epd starting at line 9. The last 300 of that file were held out as ctl.epd and were not used for chunks.

## C-ARRIVE

arrive_check.txt counts:

```
grep -c setoption name IdeaS13 value true: 20
grep -c unknown option|invalid value|No such option: 0
```

The first `setoption name IdeaS13 value true` is log line 398. The 20 lines around it are in arrive_check.txt. fastchess accepted `engine=true`.

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok2/009/half.tsv` printed:

```
side FULL: games 400 W-L-D 229-42-129 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 8, 51, 87, 54] Elo +176.10 95% [+151.48, +202.48]
```

FULL's Elo is above +20. Pass. half.sh gives FULL 20000 nodes and HALF 10000 nodes, both with IdeaS13 false, and nodes=20000 is not in -each.

## Games

20 chunks, each chunk_N.tsv has 500 lines (10000 games). No chunk FAILED. play.sh printed `minute 95: no new chunk` after chunk 20. No fastchess process was killed. POOL.txt, from `python3 ~/games_tsv.py pool ON` on every chunk_*.tsv:

```
side ON: games 10000 W-L-D 2607-2782-4611 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [283, 1228, 2099, 1161, 229] Elo -6.08 95% [-10.62, -1.55]
```

## suspicions, not proven

ON scored 2607 wins, 2782 losses, 4611 draws. The pair Elo is -6.08 with a 95% interval from -10.62 to -1.55. That interval is below zero in this sample. I am not asserting a cause.

The arrive log shows fastchess sending Threads, then IdeaS13, then Hash, then OwnBook, then the S14 spins. The O-run harness sent Threads, Hash, the S14 list, then the switch. C-ARRIVE had zero refusal lines and C-HALF passed, so the options were accepted. I do not know whether that order difference changes a game.

## what I did NOT do

I did not open a pull request. I did not edit engine source; the only source change is the given patch applied in the uncommitted work tree. I did not send IdeaS13_Lookback or IdeaS13_ReduceDivisor. I did not adjudicate (no draw, resign, maxmoves, or tablebases). I did not replay an opening. I did not run games_tsv.py on this morning's seat 030 PGN, so I did not reproduce that script's known answer of W-L-D 351-325-430. No FABLE_TO_grok2 file was on the handoff branch at the fetches I made (the newest name search printed none).

## what I am NOT sure about

I am not sure the games_tsv.py pentanomial matches fastchess's own pentanomial on the chunks. I used games_tsv.py, as specified, and every opening was in exactly two games. I am not sure a cut-off during chunk 20 would have been scored; it finished with "Finished match" at 2026-11-20T14:59:45Z, before minute 103. The repository already had user.name "Cursor Agent", so I left it.

## times: see stamps.txt

The first stamp is 2026-11-20T13:21:19Z STEP 1. Chunk 20's play.log line is 2026-11-20T14:59:45Z chunk 20 done. play.out then says `minute 95: no new chunk`.

## git status --short and ls -la

The next two blocks are the command output captured after POOL.txt, this report, RESULT.txt, and the STEP 5 stamp line were on disk.

```
$ git status --short
 M forge-combo29/grok2/009/stamps.txt
?? config.json
?? forge-combo29/grok2/009/POOL.txt
?? forge-combo29/grok2/009/REPORT.md
?? forge-combo29/grok2/009/RESULT.txt
?? forge-combo29/grok2/009/chunk_19.out
?? forge-combo29/grok2/009/chunk_19.tsv
?? forge-combo29/grok2/009/chunk_20.out
?? forge-combo29/grok2/009/chunk_20.tsv
```

```
$ ls -la forge-combo29/grok2/009
total 3260
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2274 Nov 20 13:26 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    249 Nov 20 13:30 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56179 Nov 20 14:14 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51548 Nov 20 14:14 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56126 Nov 20 14:18 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51546 Nov 20 14:18 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56725 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51460 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56502 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51250 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55920 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51428 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56207 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56404 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55995 Nov 20 14:46 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51366 Nov 20 14:46 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55966 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51593 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56401 Nov 20 14:55 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51630 Nov 20 14:55 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56249 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51305 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56434 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51641 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56553 Nov 20 13:38 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51310 Nov 20 13:38 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56463 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56130 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51321 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56122 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55905 Nov 20 13:56 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 13:56 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  55819 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51355 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56298 Nov 20 14:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56367 Nov 20 14:09 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 14:09 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:26 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46632 Nov 20 13:29 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1043 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42242 Nov 20 13:29 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:24 honesty_B_bench11.out
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:24 honesty_B_bench13.out
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:24 honesty_B_bench16.out
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5215 Nov 20 13:24 honesty_B_perft5.out
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:24 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5184 Nov 20 13:24 honesty_P_bench11.out
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:24 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5184 Nov 20 13:24 honesty_P_bench13.out
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5186 Nov 20 13:24 honesty_P_bench16.out
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5397 Nov 20 13:24 honesty_P_perft5.out
-rw-r--r-- 1 ubuntu ubuntu   3112 Nov 20 13:24 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1027 Nov 20 13:26 match.sh
-rw-r--r-- 1 ubuntu ubuntu    837 Nov 20 13:24 orun_1_B.meta
-rw-r--r-- 1 ubuntu ubuntu 282005 Nov 20 13:24 orun_1_B.out
-rw-r--r-- 1 ubuntu ubuntu    872 Nov 20 13:24 orun_2_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 282270 Nov 20 13:24 orun_2_Poff.out
-rw-r--r-- 1 ubuntu ubuntu    871 Nov 20 13:24 orun_3_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 282621 Nov 20 13:24 orun_3_Pon.out
-rw-r--r-- 1 ubuntu ubuntu   4564 Nov 20 13:24 orun.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:26 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6396 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1061 Nov 20 15:02 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2349 Nov 20 13:24 table.py
```

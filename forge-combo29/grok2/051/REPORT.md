# grok2 seat 051

Arm 1, id B1a, source seat 030, switch IdeaB1. Model Grok 4.7. Branch for-fable-and-opus/grok2-051.

## Patch

Source commit 416700fe0ace1656a1285fc536c347718c1a4af7 on for-fable-and-opus/grok-030. `sha256sum ~/arm.patch` printed the arm's sha256:

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

`git apply --check ~/arm.patch && git apply ~/arm.patch` in the work tree exited 0. The work tree diff stat after apply:

```
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

IdeaB1_Scale and IdeaB1_Fade were left at their defaults. Only IdeaB1 was sent.

## Honesty

A fresh process for each line, no setoption. Both exe B and exe P:

- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609

Those are the nodes fields of the saved files honesty_B_*.txt and honesty_P_*.txt.

## O runs

`python3 forge-combo29/grok2/051/o_table.py` on o1_B.raw, o2_P_off.raw, o3_P_on.raw printed:

```
B sum 9500069 first 41311 24872 28574
OFF sum 9500069 first 41311 24872 28574
ON sum 10081213 first 12481 31753 31668
off_differ 0
on_differ 200
```

The arm table asks for exe B sum 9500069 and first three 41311 / 24872 / 28574; switch false equal on all 200; switch true sum 10081213, first three 12481 / 31753 / 31668, 200 positions differ. The printed rows match that table.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Those match the brief's copy. Seat 051 took every 90th line from line 51: 29245 lines in mine.epd. The last 300 are ctl.epd and were not used by the chunks.

## C-ARRIVE and C-HALF

C-ARRIVE: `grep -c "setoption name IdeaB1 value true"` on arrive.log printed 20. `grep -c -E "unknown option|invalid value|No such option"` printed 0. The 20 log lines around the first `setoption name IdeaB1` are in arrive_check.txt.

C-HALF: `python3 ~/games_tsv.py pool FULL` on half.tsv printed:

```
side FULL: games 400 W-L-D 234-23-143 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 8, 34, 97, 61] Elo +203.83 95% [+178.29, +231.52]
```

FULL's Elo is above +20, so the control passed.

## Pool

19 chunks, 9500 games. `python3 ~/games_tsv.py pool ON` wrote POOL.txt:

```
side ON: games 9500 W-L-D 2507-2550-4443 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [236, 1133, 2026, 1148, 207] Elo -1.57 95% [-6.14, +2.99]
```

## Suspicions, not proven

The point estimate is a small loss for IdeaB1 on. The 95% interval includes both a few Elo down and a few Elo up. I do not treat -1.57 as a measured gain or a measured loss beyond that interval.

fastchess wrote config.json in the repository root during C-HALF (its opening file is ctl_half.epd and its pgn is half.pgn). In that file resign, draw, maxmoves, and tb_adjudication are all enabled false. I did not pass -draw, -resign, or -maxmoves. Chunk processes were started from $HOME with match.sh's command line.

## What I did not do

I did not open a pull request. I did not commit an engine binary, a net, a PGN, or the book. I did not commit config.json. I did not change engine source on this branch; the patch is only in the outside work tree. I did not play the reserved last 300 openings. I did not repeat an opening. I did not switch to arm 10. No FABLE_TO_grok2 file was on the handoff branch at any fetch.

## What I am not sure about

The honesty .meta id name comes from a separate `uci` of the same binary. The honesty process itself was sent only the bench or perft line and quit.

I did not read fastchess's source to prove it never adjudicates unless a flag is set. The saved match outputs end games by mate, the fifty-move rule, threefold repetition, or insufficient material.

## Times

times: see stamps.txt

## git status --short and ls -la

The next two blocks are the command output taken after this report and RESULT.txt were written, and before the STEP 5 commit.

```
$ git status --short
 M forge-combo29/grok2/051/stamps.txt
?? config.json
?? forge-combo29/grok2/051/POOL.txt
?? forge-combo29/grok2/051/REPORT.md
?? forge-combo29/grok2/051/RESULT.txt

$ ls -la forge-combo29/grok2/051
total 3228
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2107 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    243 Nov 20 13:29 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  55942 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51435 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55997 Nov 20 14:22 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51506 Nov 20 14:22 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56339 Nov 20 14:27 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:27 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56423 Nov 20 14:32 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51581 Nov 20 14:32 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56336 Nov 20 14:36 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51588 Nov 20 14:36 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56429 Nov 20 14:41 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51529 Nov 20 14:41 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56333 Nov 20 14:45 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51500 Nov 20 14:45 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56173 Nov 20 14:50 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51614 Nov 20 14:50 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56713 Nov 20 14:54 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51525 Nov 20 14:54 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56273 Nov 20 14:59 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51461 Nov 20 14:59 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56450 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51182 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56361 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51281 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56503 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51420 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56169 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51405 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56459 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51388 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56208 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51254 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56432 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51358 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56409 Nov 20 14:09 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51515 Nov 20 14:09 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56423 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:13 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46918 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1057 Nov 20 13:33 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42223 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:33 half_tsv_count.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    314 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    314 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    792 Nov 20 13:26 o1_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308992 Nov 20 13:26 o1_B.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o1_B.txt
-rw-r--r-- 1 ubuntu ubuntu    826 Nov 20 13:26 o2_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309240 Nov 20 13:26 o2_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o2_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    825 Nov 20 13:26 o3_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 310216 Nov 20 13:26 o3_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   1898 Nov 20 13:26 o3_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4799 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1443 Nov 20 13:26 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:27 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    540 Nov 20 13:27 patch_check.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4452 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1079 Nov 20 15:01 stamps.txt
```

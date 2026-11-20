# grok2 seat 067

Arm 7, K4a. Source seat 093. Switch IdeaK4. Commit ddc850cbf04b8c7a8592624037844077b33c8ab0.

## Patch sha256 and git apply

```
e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check` and `git apply` both succeeded on the work tree. `git diff --stat` in that tree:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
```

The patch was not committed. IdeaK4_Shrink was left at its default and was never sent.

## Honesty

Known: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Grep of the saved files:

```
forge-combo29/grok2/067/honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 322 nps 971633
forge-combo29/grok2/067/honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 478 nps 1804035
forge-combo29/grok2/067/honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1636 nps 1848973
forge-combo29/grok2/067/honesty_B_perft5.txt:nodes 4865609
forge-combo29/grok2/067/honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 385 nps 812638
forge-combo29/grok2/067/honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 507 nps 1700846
forge-combo29/grok2/067/honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1619 nps 1868387
forge-combo29/grok2/067/honesty_P_perft5.txt:nodes 4865609
```

Both exes match. honesty=ok.

## Three O runs

Table: (1) sum 9500069, first three 41311 / 24872 / 28574. (2) equal to (1) on all 200. (3) sum 8921190, first three 24693 / 26341 / 35070, 200 differ.

`o_rows.py` on the raw transcripts:

```
FILE forge-combo29/grok2/067/o_B.raw
SUM 9500069
COUNT 200
FIRST3 41311 24872 28574
FILE forge-combo29/grok2/067/o_P_off.raw
SUM 9500069
COUNT 200
FIRST3 41311 24872 28574
DIFFER 0 of 200
EQUAL True
FILE forge-combo29/grok2/067/o_B.raw
SUM 9500069
COUNT 200
FIRST3 41311 24872 28574
FILE forge-combo29/grok2/067/o_P_on.raw
SUM 8921190
COUNT 200
FIRST3 24693 26341 35070
DIFFER 200 of 200
EQUAL False
```

Full rows are the committed output in o_table_off.txt and o_table_on.txt. off_identical=yes. on_sum=8921190. on_ok=yes.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

book=ok. Seat 067 took every 90th line starting at line 67 (29245 lines). The last 300 were the controls. Chunks used the top of mine.epd, 250 openings each, and did not reach those 300.

## C-ARRIVE and C-HALF

arrive_check.txt:

```
setoption name IdeaK4 value true count: 20
unknown option|invalid value|No such option count: 0
```

arrive=ok.

half_pool.txt, from `games_tsv.py pool FULL` on half.tsv:

```
side FULL: games 400 W-L-D 235-35-130 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 8, 45, 82, 64] Elo +190.85 95% [+164.06, +219.88]
```

half_elo=+190.85, above +20.

## POOL.txt and chunks

21 chunks, 500 games each, 10500 games. POOL.txt:

```
side ON: games 10500 W-L-D 2811-2843-4846 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [265, 1315, 2119, 1289, 262] Elo -1.06 95% [-5.51, +3.39]
```

## suspicions, not proven

An untracked config.json appeared in the repository root at 14:59 UTC, outside this seat folder. I did not write it and did not commit it. The match command did not pass draw, resign, maxmoves, or tablebase options. Logged game endings in the controls were mates, threefold repetition, the fifty-move rule, and insufficient material.

## what I did NOT do

No pull request. No engine source committed. No portable build: this machine has AVX-512 and BMI2, so the Release build used the CMake default march x86-64-v4. IdeaK4_Shrink was not sent. The on-sum matched, so arm 10 was not played. Openings were not repeated. No adjudication flags were passed to fastchess.

## what I am NOT sure about

The RESULT id field is K4a, the label of arm 7 in the arm table. Fastchess sends engine options in its own order; the arrive log shows IdeaK4 value true was delivered and the refusal count was 0. I do not know which process created config.json.

## times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/067/stamps.txt
?? config.json
?? forge-combo29/grok2/067/POOL.txt
?? forge-combo29/grok2/067/REPORT.md
?? forge-combo29/grok2/067/RESULT.txt
?? forge-combo29/grok2/067/chunk_21.out
?? forge-combo29/grok2/067/chunk_21.tsv

$ ls -la forge-combo29/grok2/067
total 3388
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2257 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56328 Nov 20 14:13 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51218 Nov 20 14:13 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56193 Nov 20 14:17 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 14:17 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56297 Nov 20 14:21 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51351 Nov 20 14:21 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56465 Nov 20 14:25 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:25 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56053 Nov 20 14:29 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51449 Nov 20 14:29 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  55870 Nov 20 14:33 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51287 Nov 20 14:33 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56583 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51498 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56145 Nov 20 14:42 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51370 Nov 20 14:42 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56337 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51464 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56420 Nov 20 14:50 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51433 Nov 20 14:50 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56246 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51127 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56168 Nov 20 14:54 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51507 Nov 20 14:54 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56109 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51738 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56160 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51455 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56476 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51358 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  55886 Nov 20 13:48 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51315 Nov 20 13:48 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56226 Nov 20 13:52 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51431 Nov 20 13:52 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56172 Nov 20 13:56 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51235 Nov 20 13:56 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56324 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51249 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56176 Nov 20 14:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51402 Nov 20 14:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56641 Nov 20 14:09 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51580 Nov 20 14:09 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46670 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1007 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42259 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1025 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    789 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308986 Nov 20 13:26 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    825 Nov 20 13:26 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309152 Nov 20 13:26 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    823 Nov 20 13:26 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 308157 Nov 20 13:26 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   1860 Nov 20 13:26 o_rows.py
-rw-r--r-- 1 ubuntu ubuntu   3936 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   4029 Nov 20 13:26 o_table_off.txt
-rw-r--r-- 1 ubuntu ubuntu   4029 Nov 20 13:26 o_table_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4744 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    742 Nov 20 15:01 stamps.txt
```

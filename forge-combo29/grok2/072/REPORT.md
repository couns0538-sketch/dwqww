# Seat 072 arm 2 (B1b)

Arm 2, id B1b, source seat 080, commit e778c1358711c0571e8f5cc4df87083cce98e03a, switch IdeaB1. Model Grok 4.7. exe P is /agent/repos/work/build/forge (base 6b98f2170a3210e71beed04bbd2553972c253ed7 plus the patch). exe B is /agent/repos/base/build/forge. Both are GCC 13.3.0 Release builds, default FORGE_MARCH x86-64-v4, FORGE_PORTABLE off: this CPU advertises avx512f and bmi2.

## Patch sha256 and git apply

sha256 of ~/arm.patch, from `sha256sum`:

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm 2 sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. After that, `git apply --reverse --check ~/arm.patch` also exited 0 and the patch was not reversed. Recorded output:

```
git apply --reverse --check: OK (patch matches the work tree; not reversed)
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

## Honesty

`python3 summarize_honesty.py honesty_*.txt` (reads the raw files):

```
honesty_B_bench11.txt 312866
honesty_B_bench13.txt 862329
honesty_B_bench16.txt 3024920
honesty_B_perft5.txt 4865609
honesty_P_bench11.txt 312866
honesty_P_bench13.txt 862329
honesty_P_bench16.txt 3024920
honesty_P_perft5.txt 4865609
```

Known numbers: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match. Each line was a fresh process with no setoption.

## Three O runs

`python3 summarize_o.py o_B.txt o_P_off.txt o_P_on.txt`:

```
forge-combo29/grok2/072/o_B.txt sum 9500069 first 41311 24872 28574 differ_from_first_file 0
forge-combo29/grok2/072/o_P_off.txt sum 9500069 first 41311 24872 28574 differ_from_first_file 0
forge-combo29/grok2/072/o_P_on.txt sum 9748678 first 17841 25977 43905 differ_from_first_file 200
```

Against the arm 2 table: (1) exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574. (2) switch false, differ_from_first_file 0, so all 200 positions equal (1). (3) switch true, sum 9,748,678, first three 17,841 / 25,977 / 43,905, 200 positions differ. All three match.

## Book

```
uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
  2632036 /home/ubuntu/uho.epd
    29245 /home/ubuntu/mine.epd
```

Zip sha256, epd sha256, and line count match the known copy.

## C-ARRIVE and C-HALF

C-ARRIVE, from arrive_check.txt (grep counts):

```
grep -c setoption name IdeaB1 value true:
20
grep -c unknown option|invalid value|No such option:
0
```

The 20-line window around the first `setoption name IdeaB1 value true` is in arrive_check.txt. The engine log shows that line sent to ON. Zero refusal lines. fastchess accepted `engine=true`.

C-HALF, `python3 games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 228-30-142 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 40, 101, 52] Elo +188.54 95% [+164.64, +214.19]
```

FULL's Elo is +188.54, above +20. Pass.

## POOL and chunks

14 chunks, each 500 games, 7000 games. `python3 games_tsv.py pool ON chunk_*.tsv` wrote POOL.txt:

```
side ON: games 7000 W-L-D 1822-1880-3298 pairs 3500 (openings not in exactly 2 games: 0)
ptnml [196, 847, 1442, 849, 166] Elo -2.88 95% [-8.33, +2.58]
```

Chunk 14 started because chunk 13 finished at 2026-11-20T14:58:10Z and the minute-95 cutoff is 2026-11-20T14:58:13Z (95 minutes after the first stamp 2026-11-20T13:23:13Z). play.sh checks that cutoff only before starting a chunk, so it started chunk 14. Chunk 14 finished at 2026-11-20T15:03:32Z. Minute 103 is 2026-11-20T15:06:13Z. It was not killed. It is counted.

## suspicions, not proven

None. The match interval includes 0. That is the measured interval.

## what I did NOT do

No pull request. No `-draw`, `-resign`, `-maxmoves`, or tablebase flags. No engine source committed and no edit beyond applying the given patch in the work tree. IdeaB1_Lanes, IdeaB1_Fade, IdeaB1_Scale, and IdeaB1_Cap were not sent. No opening was repeated to add games. No FABLE_TO_grok2 file was on the handoff branch at any fetch. fastchess wrote config.json in the repository root because the match cwd was the repo; resign, draw, maxmoves, and tablebase adjudication were all disabled in it. I deleted that file and did not commit it.

## what I am NOT sure about

I am not sure a later reader will want chunk 14 dropped for starting three seconds before the cutoff. I counted it because play.sh started it while the clock was still under 95 minutes and it finished before minute 103. The timestamps above are the play.log lines and the first stamp.

## times: see stamps.txt

times: see stamps.txt

## git status --short and ls -la

The blocks below were appended from the commands.

```
$ git status --short
 M forge-combo29/grok2/072/stamps.txt
?? forge-combo29/grok2/072/POOL.txt
?? forge-combo29/grok2/072/REPORT.md
?? forge-combo29/grok2/072/RESULT.txt
?? forge-combo29/grok2/072/chunk_14.out
?? forge-combo29/grok2/072/chunk_14.tsv
?? forge-combo29/grok2/072/summarize_honesty.py
```

```
$ ls -la forge-combo29/grok2/072
total 2620
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:06 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2186 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    269 Nov 20 13:31 book_sha256.txt
-rw-r--r-- 1 ubuntu ubuntu  56446 Nov 20 14:39 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51530 Nov 20 14:39 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56416 Nov 20 14:45 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 14:45 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56193 Nov 20 14:51 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51622 Nov 20 14:51 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56286 Nov 20 14:58 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:58 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56147 Nov 20 15:03 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51560 Nov 20 15:03 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56392 Nov 20 13:42 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51290 Nov 20 13:42 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56428 Nov 20 13:49 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51358 Nov 20 13:49 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56187 Nov 20 13:55 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51471 Nov 20 13:55 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56402 Nov 20 14:01 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51320 Nov 20 14:01 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56777 Nov 20 14:07 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 14:07 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56427 Nov 20 14:14 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 14:14 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 14:20 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51389 Nov 20 14:20 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56426 Nov 20 14:26 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51365 Nov 20 14:26 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56262 Nov 20 14:33 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51552 Nov 20 14:33 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:27 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46935 Nov 20 13:36 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:36 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu    958 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42282 Nov 20 13:36 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    297 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    297 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    297 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    297 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    297 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    297 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3108 Nov 20 13:27 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1027 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    779 Nov 20 13:29 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 282385 Nov 20 13:29 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    813 Nov 20 13:29 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282858 Nov 20 13:29 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    812 Nov 20 13:29 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 283023 Nov 20 13:29 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4905 Nov 20 13:29 orun.py
-rw-r--r-- 1 ubuntu ubuntu    425 Nov 20 13:30 patch_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:30 patch_sha256.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:05 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5432 Nov 20 15:06 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:06 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    792 Nov 20 15:06 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    582 Nov 20 15:06 summarize_honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1294 Nov 20 13:27 summarize_o.py
```

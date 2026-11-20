# grok2 seat 028

Arm 8, K4b, source seat 043, switch IdeaK4. The source commit is 2f38a63656ec17062b581c933fcc77d961b946f1 on for-fable-and-opus/grok-043. `git rev-parse FETCH_HEAD` printed that commit. `sha256sum ~/arm.patch` printed `b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81`. `git apply --check` and `git apply` both succeeded in the work tree. The diff stat was 3 files, 20 insertions, 2 deletions.

The machine's `/usr/bin/c++` is Clang 18 and the link failed with `cannot find -lstdc++`. The builds used `g++` 13.3.0, which links GCC's own libstdc++. `lscpu` shows avx512f, avx512bw, avx512cd, avx512dq, avx512vl and bmi2, so the Release build kept the default march x86-64-v4 and did not set FORGE_PORTABLE. Local `user.name` was unset in this repository, so it was set here only, to `grok agent` / `grok@invalid`.

## Honesty

`sum_step2.py` reads the raw honesty files. Its output:

```
honesty
  B bench11 312866
  B bench13 862329
  B bench16 3024920
  B perft5 4865609
  P bench11 312866
  P bench13 862329
  P bench16 3024920
  P perft5 4865609
```

Those are the known bench 11 / 13 / 16 and perft 5 counts, on exe B and on exe P.

## The three O runs

The same script, against the arm table (sum 9,500,069 and first three 41,311 / 24,872 / 28,574 for the plain engine; IdeaK4 on: 8,983,632; 23,741 / 21,846 / 35,911; 200 differ):

```
o runs
  B positions 200 sum 9500069 first [41311, 24872, 28574]
  P_off positions 200 sum 9500069 first [41311, 24872, 28574] differ_from_B 0
  P_on positions 200 sum 8983632 first [23741, 21846, 35911] differ_from_B 200
```

Run (1) matches the plain engine. Run (2) matches run (1) on all 200 positions. Run (3) matches the arm table.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `wc -l ~/uho.epd` printed 2632036 and `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Seat 028 took every 90th line starting at line 28: 29245 lines in mine.epd. The last 300 were the controls and were not used as chunk openings.

## C-ARRIVE

`grep -c "setoption name IdeaK4 value true"` on the trace log printed 20. `grep -c -E "unknown option|invalid value|No such option"` printed 0. The 20 lines around the first switch setoption are in arrive_check.txt. The engine received `setoption name IdeaK4 value true`.

## C-HALF

`games_tsv.py pool FULL` on half.tsv:

```
side FULL: games 400 W-L-D 220-30-150 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 7, 41, 99, 51] Elo +179.45 95% [+154.51, +206.23]
```

FULL's Elo is above +20.

## Pool

20 chunks, 10000 games. `games_tsv.py pool ON` wrote POOL.txt:

```
side ON: games 10000 W-L-D 2626-2770-4604 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [261, 1252, 2099, 1146, 242] Elo -5.00 95% [-9.53, -0.48]
```

`endings.py` reads the chunk logs and the tsv files:

```
out files 20 brace phrases 10000
3132	White mates
3066	Draw by 3-fold repetition
2264	Black mates
767	Draw by fifty moves rule
745	Draw by insufficient mating material
26	Draw by stalemate
tsv files 20 games 10000
10000	normal
```

## Suspicions, not proven

The interval from the given pool script is entirely below zero for this match. That is the script's number for these 10000 games at 20000 nodes, one thread, switch on against switch off. I am not claiming anything past that sample.

Every tsv Termination field is the word normal, while the fastchess log names mates and rule draws. The brace phrases add to 10000, one per game. A search of the chunk logs for adjudicat, resign and maxmove printed 0 hits.

## What I did not do

No pull request. No engine source file is in this branch. The patch sits only in the work tree outside the clone that was pushed. IdeaK4_Shrink was left at the patch default and was never sent. No adjudication, draw, resign, maxmoves or tablebase option was passed to fastchess. The last 300 openings of mine.epd were not played as chunks. Arm 10 was not used. No branch was force-pushed. PGNs, the book, the executables and the net were not committed.

The handoff branch had no forge-combo29/soak_all/FABLE_TO_grok2 file at step 1 or at any chunk push.

From chunk 12 on, ~/keep_commit.sh committed each finished chunk and fetched the channel. Chunks were taking about four minutes, and that script pushed each one within a minute.

## What I am not sure about

I did not open all 10000 games one by one. The pool script accepted every row, and every opening was in exactly two games. I am not sure a fastchess header other than Termination could still record a clock loss that the brace text does not show. The brace census has no such phrase.

fastchess wrote a config.json in the repository root because the shell's current directory was the clone. I did not commit it. I am not sure whether later chunks rewrote it.

## times: see stamps.txt

The first stamp is 2026-11-20T13:22:27Z. The last chunk finished at 14:59:51Z and was pushed at 15:00:32Z. play.sh then printed `minute 95: no new chunk`.

## git status --short and ls -la

The next two blocks are the command output captured after this report, RESULT.txt, POOL.txt and endings.py were written.

```
$ git status --short
 M forge-combo29/grok2/028/stamps.txt
?? config.json
?? forge-combo29/grok2/028/POOL.txt
?? forge-combo29/grok2/028/REPORT.md
?? forge-combo29/grok2/028/RESULT.txt
?? forge-combo29/grok2/028/endings.out
?? forge-combo29/grok2/028/endings.py

$ ls -la forge-combo29/grok2/028
total 3268
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2206 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  55807 Nov 20 14:17 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51137 Nov 20 14:17 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56218 Nov 20 14:21 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51390 Nov 20 14:21 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56580 Nov 20 14:25 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51487 Nov 20 14:25 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55897 Nov 20 14:30 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51344 Nov 20 14:30 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56591 Nov 20 14:34 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51530 Nov 20 14:34 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56143 Nov 20 14:38 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51392 Nov 20 14:38 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56791 Nov 20 14:42 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51613 Nov 20 14:42 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56270 Nov 20 14:47 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51560 Nov 20 14:47 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56005 Nov 20 14:51 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 14:51 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56191 Nov 20 14:55 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51463 Nov 20 14:55 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56588 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51291 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56173 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51478 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56189 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51321 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56743 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51366 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  55969 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51142 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56257 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56408 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51333 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56475 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56151 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51354 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56227 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:12 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:03 endings.out
-rw-r--r-- 1 ubuntu ubuntu    954 Nov 20 15:03 endings.py
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47109 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:34 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1057 Nov 20 13:34 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42384 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:28 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:28 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:28 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:28 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:28 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:28 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:28 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 13:28 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:28 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 13:28 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:28 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5101 Nov 20 13:28 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:28 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5312 Nov 20 13:28 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    802 Nov 20 13:28 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu    821 Nov 20 13:29 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281792 Nov 20 13:29 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    855 Nov 20 13:29 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281925 Nov 20 13:29 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    854 Nov 20 13:29 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 280863 Nov 20 13:29 o_P_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   4095 Nov 20 13:28 o_run.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5511 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    723 Nov 20 15:04 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    384 Nov 20 13:29 sum_step2.out
-rwxr-xr-x 1 ubuntu ubuntu   2791 Nov 20 13:28 sum_step2.py
```

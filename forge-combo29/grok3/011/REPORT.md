# REPORT

Seat 011, arm 2, 2000 nodes. Chunk size 500 openings (1000 games). Match: main (IdeaB8 and HindsightDepth both on, against both off). take_seat3.sh was run as `bash ~/take_seat3.sh "Grok 4.7"`.

## Patch

sha256 of `~/b8.patch`: `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474` (matches).

`git fetch` of `for-fable-and-opus/grok-028` printed `FETCH_HEAD=4bf95fd80adf523e97fa250bb8572c946cf0fc75`.

`git apply --check ~/b8.patch` and `git apply ~/b8.patch` in the worktree at base `6b98f2170a3210e71beed04bbd2553972c253ed7` both succeeded. `git diff --stat` after apply:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

The first cmake used `/usr/bin/c++`, which is clang++ 18.1.3, and stopped with `/usr/bin/ld: cannot find -lstdc++`. I removed `~/build` and configured again with `-DCMAKE_CXX_COMPILER=g++` (GCC 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` includes `avx512f` and `bmi2`, so I did not add `-DFORGE_PORTABLE=ON`. The binary is `/home/ubuntu/build/forge`. The `.meta` files name that path, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, id name `Chess Engine Forge 6.4.24 candidate`.

## Honesty

Fresh process for each line, no setoption. Raw files in this folder.

- `honesty_bench11.txt`: `info string bench depth 11 nodes 312866 time 170 nps 1840388`
- `honesty_bench13.txt`: `info string bench depth 13 nodes 862329 time 446 nps 1933473`
- `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920 time 1444 nps 2094819`
- `honesty_perft5.txt` last line: `nodes 4865609`

These are the known numbers.

## Four O runs

(1) `o_off.rows.txt`: `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. Matches. `sha256sum` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. Matches.

(2) `o_b8.rows.txt`: `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`. Matches.

(3) `o_k3.rows.txt`: `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`. Matches.

(4) `o_both.rows.txt`: `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. No known answer was given. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed `200`.

Seats 001, 002, 004 and 010 had already published `o_both.rows.txt`. Each file had 200 rows, sum 9758416, first three node counts 18538, 34070, 39093, the same as this seat. I did not read every other seat.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. Matches.

`wc -l ~/uho.epd` printed `2632036`. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Matches.

`wc -l ~/mine.epd` printed `13390`. The last 300 lines were kept for the controls (`ctl.epd` 300, `ctl_arrive.epd` 10, `ctl_half.epd` 200).

## Known answer of games_tsv.py

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. Matches.

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

Matches.

## C-ARRIVE

`arrive_check.txt` counts: `setoption name IdeaB8 value true: 20`, `setoption name HindsightDepth value true: 20`, `unknown option|invalid value|no such option: 0`. The same file holds the 20 log lines around the first IdeaB8 setoption (log line 398). The engine named ON received `setoption name IdeaB8 value true` and `setoption name HindsightDepth value true`.

## C-HALF

```
400 games -> forge-combo29/grok3/011/half.tsv
side FULL: games 400 W-L-D 259-56-85 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 16, 49, 51, 84] Elo +194.34 95% [+163.52, +228.21]
```

PASS. FULL's Elo +194.34 is above +20. `half.out` line 936: `Elo: 194.34 +/- 32.34, nElo: 251.28 +/- 34.05`.

## POOL

26 chunks. `wc -l` of `chunk_*.tsv` printed `26000 total`. `play.log` has no `FAILED` line. `play.out` ends with `openings used up`.

Pasted `POOL.txt`:

```
side ON: games 26000 W-L-D 9617-8501-7882 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1166, 2561, 4801, 2935, 1537] Elo +14.92 95% [+11.58, +18.26]
```

## suspicions, not proven

At 2,000 nodes the measured Elo is +14.92 with 95% interval [+11.58, +18.26]. That interval lies above about +10 and reaches about +17. This seat did not play 20,000 or 60,000 nodes.

The both-on node sum 9,758,416 is near IdeaB8 alone (9,718,009) and below HindsightDepth alone (9,845,650). Node sums are not Elo. I do not treat them as the add-up result.

## what I did NOT do

I did not open a pull request. I did not use `--force`. I did not push any branch other than `for-fable-and-opus/grok3-011`. I did not play the fallback match. `match.sh` and `half.sh` pass no `-draw`, `-resign`, `-maxmoves`, or tablebase switch. During chunk 26 fastchess wrote an untracked `config.json` in the repository root; resign, draw, maxmoves and tablebase adjudication were all `enabled: false` in it. I did not commit that file. I deleted it after reading it. I did not commit an executable, a net, a PGN, or any engine source. I did not repeat an opening. `git ls-tree` of `handoff/fable-opus-combo29-all-20261114` (`13ff5655fe5c04280d7e99169d1ccfb18e6d6d6d`) listed no `forge-combo29/soak_all/FABLE_TO_grok3_*.md`, at step 1 and again in the middle of step 4. I did not sleep another 60 seconds for `setup_bg`: `~/setup_bg.log` already contained `fastchess OK`, `python-chess OK`, `book OK`, and `setup_bg done`.

## what I am NOT sure about

I compared `o_both.rows.txt` with seats 001, 002, 004 and 010 only. I am not sure whether fastchess wrote `config.json` more than once; I saw one file, dated 19:31, and then removed it. The running fastchess command line for chunk 1 had no adjudication switch.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok3/011/stamps.txt
?? forge-combo29/grok3/011/POOL.txt
?? forge-combo29/grok3/011/REPORT.md
?? forge-combo29/grok3/011/RESULT.txt
```

## ls -la

```
total 5756
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:34 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu   2253 Nov 20 18:58 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110630 Nov 20 19:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102479 Nov 20 19:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 110443 Nov 20 19:12 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102588 Nov 20 19:12 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 111027 Nov 20 19:13 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102592 Nov 20 19:13 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 111074 Nov 20 19:15 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102602 Nov 20 19:15 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 110798 Nov 20 19:16 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102603 Nov 20 19:16 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110501 Nov 20 19:17 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102570 Nov 20 19:17 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110814 Nov 20 19:19 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102456 Nov 20 19:19 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 110669 Nov 20 19:20 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102506 Nov 20 19:20 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 111154 Nov 20 19:21 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102730 Nov 20 19:21 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 111006 Nov 20 19:22 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102486 Nov 20 19:22 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110863 Nov 20 19:00 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102427 Nov 20 19:00 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 110400 Nov 20 19:24 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102329 Nov 20 19:24 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 110876 Nov 20 19:25 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102597 Nov 20 19:25 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110581 Nov 20 19:26 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102697 Nov 20 19:26 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 111178 Nov 20 19:27 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102836 Nov 20 19:27 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110560 Nov 20 19:29 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102352 Nov 20 19:29 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110376 Nov 20 19:30 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102586 Nov 20 19:30 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110428 Nov 20 19:31 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102422 Nov 20 19:31 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110686 Nov 20 19:01 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102632 Nov 20 19:01 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 111583 Nov 20 19:02 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102451 Nov 20 19:02 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110744 Nov 20 19:03 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102490 Nov 20 19:03 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 110392 Nov 20 19:05 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102423 Nov 20 19:05 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110612 Nov 20 19:06 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102607 Nov 20 19:06 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 110844 Nov 20 19:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102724 Nov 20 19:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110166 Nov 20 19:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102375 Nov 20 19:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110348 Nov 20 19:10 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102370 Nov 20 19:10 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 18:58 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45748 Nov 20 18:58 half.out
-rwxr-xr-x 1 ubuntu ubuntu    986 Nov 20 18:58 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42187 Nov 20 18:58 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:54 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:54 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:54 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:54 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1022 Nov 20 18:58 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:55 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:55 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:55 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:55 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:55 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:55 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:54 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:54 o_off.rows.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu   3582 Nov 20 18:54 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu   1755 Nov 20 18:58 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:33 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6174 Nov 20 19:34 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:34 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1065 Nov 20 19:34 stamps.txt
```

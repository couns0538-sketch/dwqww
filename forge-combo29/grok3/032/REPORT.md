# grok3 seat 032

Seat 032, arm 2, 2,000 nodes. Chunks are 500 openings (1,000 games). The match is the main match: IdeaB8 and HindsightDepth both on, against both off.

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

That file is `git show 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`. `git rev-parse FETCH_HEAD` after fetching `for-fable-and-opus/grok-028` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`.

`git apply --check ~/b8.patch` then `git apply ~/b8.patch` in the work tree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`. Apply succeeded. The diff stat was `search.hpp`, `search.cpp`, and `uci.cpp` (173 insertions, 4 deletions).

The machine's `/usr/bin/c++` is Clang 18.1.3 and CMake's compiler test failed with `cannot find -lstdc++`. The brief says to build with g++. CMake was re-run with `-DCMAKE_CXX_COMPILER=g++`. `~/cmake_build.log` says `The CXX compiler identification is GNU 13.3.0`. `/proc/cpuinfo` has AVX-512 and BMI2, so `-DFORGE_PORTABLE` was not added. The engine is `/home/ubuntu/build/forge`. Each O-run `.meta` file names that path, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, and `id name Chess Engine Forge 6.4.24 candidate`.

## Honesty

- `honesty_bench11.txt`: `info string bench depth 11 nodes 312866`
- `honesty_bench13.txt`: `info string bench depth 13 nodes 862329`
- `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920`
- `honesty_perft5.txt`: `nodes 4865609`

These are the known numbers.

## Four O runs

(1) `o_off.rows.txt`: rows 200, sum 9,500,069, first three 41,311 / 24,872 / 28,574. sha256 `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. Matches the known answer.

(2) `o_b8.rows.txt`: rows 200, sum 9,718,009, first three 17,283 / 17,878 / 31,115. Matches.

(3) `o_k3.rows.txt`: rows 200, sum 9,845,650, first three 23,395 / 31,504 / 35,958. Matches.

(4) `o_both.rows.txt`: rows 200, sum 9,758,416, first three 18,538 / 34,070 / 39,093. `paste` of (1) and (4) with `awk '$2 != $5'` counted 200 positions. A second run of (4) by itself wrote identical rows (`cmp` equal).

## Book

`~/uho.zip` sha256 `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07` (matches the given copy).

`~/uho.epd` 2632036 lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (matches the given copy).

`~/mine.epd` is 13390 lines. The last 300 lines were kept for the controls and were not used as chunk openings.

## games_tsv.py known answer

`~/ka.tsv` sha256 `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`.

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

Matches.

## C-ARRIVE

Counts on `~/arrive.log`: `setoption name IdeaB8 value true` = 20, `setoption name HindsightDepth value true` = 20, `unknown option|invalid value|no such option` = 0. Those three counts and the 20 log lines around the first IdeaB8 setoption are in `arrive_check.txt`. That window shows `ON <--- setoption name IdeaB8 value true`.

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok3/032/half.tsv` printed:

```
side FULL: games 400 W-L-D 264-49-87 pairs 200 (openings not in exactly 2 games: 0)
ptnml [4, 9, 43, 56, 88] Elo +208.68 95% [+176.27, +244.72]
```

PASS: FULL's Elo is above +20. The last Elo line in `half.out` is `Elo: 208.68 +/- 34.22`.

## Pool

26 chunks. `POOL.txt`:

```
side ON: games 26000 W-L-D 9649-8422-7929 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1177, 2546, 4742, 2943, 1592] Elo +16.41 95% [+13.04, +19.78]
```

Each of the 26 `chunk_*.out` files contains one `Finished match`. A search of those files for adjudication, resign, and maxmoves found none. `play.sh` ended with `openings used up` after chunk 26. No chunk failed and no commit or push failed.

## suspicions, not proven

None.

## what I did NOT do

- No pull request.
- No engine source committed. The patch is applied only in the work tree outside the repository.
- No binary, object file, net, PGN, or book committed.
- No fallback match. `ON_B8` stayed `true`.
- No adjudication, draw rule, resign, maxmoves, or tablebases.
- No `--force`. The only branch pushed is `for-fable-and-opus/grok3-032`.
- `config.json` at the repository root is untracked and was not added. It is outside this seat's folder.
- The channel (`handoff/fable-opus-combo29-all-20261114`, `forge-combo29/soak_all/`) had no `FABLE_TO_grok3_<N>.md` at STEP 1 or in the middle of STEP 4.
- No other seat's `o_both.rows.txt` was read.

## what I am NOT sure about

Run (4) has no published known answer. This seat's committed rows and a second solo run of the same command agree on sum 9,758,416 and the same 200 rows. I do not know whether every other seat printed that same sum.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok3/032/stamps.txt
?? config.json
?? forge-combo29/grok3/032/POOL.txt
?? forge-combo29/grok3/032/REPORT.md
?? forge-combo29/grok3/032/RESULT.txt
```

## ls -la

```
total 5764
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:29 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu   2326 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110634 Nov 20 19:06 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102694 Nov 20 19:06 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 111311 Nov 20 19:07 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102512 Nov 20 19:07 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 110991 Nov 20 19:08 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102748 Nov 20 19:08 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 110516 Nov 20 19:09 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102638 Nov 20 19:09 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 110630 Nov 20 19:11 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102403 Nov 20 19:11 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110661 Nov 20 19:12 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102431 Nov 20 19:12 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110769 Nov 20 19:13 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102609 Nov 20 19:13 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 110461 Nov 20 19:15 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102389 Nov 20 19:15 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 110988 Nov 20 19:16 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102789 Nov 20 19:16 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 110532 Nov 20 19:17 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102474 Nov 20 19:17 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110593 Nov 20 18:55 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102492 Nov 20 18:55 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 110386 Nov 20 19:19 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102381 Nov 20 19:19 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 110680 Nov 20 19:20 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102512 Nov 20 19:20 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110972 Nov 20 19:21 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102514 Nov 20 19:21 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 110601 Nov 20 19:22 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102557 Nov 20 19:22 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110691 Nov 20 19:24 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102643 Nov 20 19:24 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 111281 Nov 20 19:25 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102678 Nov 20 19:25 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110538 Nov 20 19:26 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102312 Nov 20 19:26 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110569 Nov 20 18:56 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102508 Nov 20 18:56 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110900 Nov 20 18:57 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102676 Nov 20 18:57 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 111024 Nov 20 18:58 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102550 Nov 20 18:58 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 111037 Nov 20 18:59 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102535 Nov 20 18:59 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110115 Nov 20 19:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102566 Nov 20 19:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 110719 Nov 20 19:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102629 Nov 20 19:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110538 Nov 20 19:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102438 Nov 20 19:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110164 Nov 20 19:04 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102357 Nov 20 19:04 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:53 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45796 Nov 20 18:53 half.out
-rwxr-xr-x 1 ubuntu ubuntu    986 Nov 20 18:53 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42086 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1022 Nov 20 18:53 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:53 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu   1755 Nov 20 18:53 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:27 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   9941 Nov 20 19:29 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:29 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     88 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 19:29 stamps.txt
```

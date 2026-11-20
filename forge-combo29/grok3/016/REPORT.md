# grok3 seat 016

Seat 016, arm 1, 20,000 nodes, chunks of 250 openings (500 games). Match is the main match: IdeaB8 and HindsightDepth both on, against both off. Model name passed to take_seat3.sh: Grok 4.7.

## Patch

`git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-028` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`.

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`.

`git apply --check ~/b8.patch` and `git apply ~/b8.patch` in the worktree `../work` (base `6b98f2170a3210e71beed04bbd2553972c253ed7`) both succeeded. `git diff --stat` there printed:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

The patch is not committed. The engine source in this branch is unchanged.

The first cmake used `/usr/bin/c++`, which is clang, and stopped with `cannot find -lstdc++`. I configured again with `-DCMAKE_CXX_COMPILER=g++` (GCC 13.3.0). `/proc/cpuinfo` has `avx512f` and `bmi2`, so I did not pass `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. The binary is `/home/ubuntu/build/forge`. Its sha256, from `o_off.rows.txt.meta`, is `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`.

## Honesty

Each line is one fresh process, no setoption before the command. Raw files: `honesty_bench11.txt`, `honesty_bench13.txt`, `honesty_bench16.txt`, `honesty_perft5.txt`.

- bench 11: nodes 312866
- bench 13: nodes 862329
- bench 16: nodes 3024920
- go perft 5: nodes 4865609

These are the known numbers.

## Four O runs

The four runs were four processes at the same time. The three known answers matched, so I did not repeat them one at a time. Prints are in `o_off.print.txt`, `o_b8.print.txt`, `o_k3.print.txt`, `o_both.print.txt`. Rows are the `.rows.txt` files.

Against the known text:

1. Both off. Printed `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. `sha256sum o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. This is the known answer. off_ok=yes.
2. IdeaB8 only. Printed `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`. This is the known answer. b8_ok=yes.
3. HindsightDepth only. Printed `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`. This is the known answer. k3_ok=yes.
4. Both on. No known answer was given. Printed `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. An awk sum of `o_both.rows.txt` is 9758416, and the first three node counts in that file are 18538, 34070, 39093. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200. All 200 positions have a different node count from the both-off run.

## Book

`book_check.txt`:

```
sha256sum uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
wc -l and sha256sum uho.epd
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
wc -l mine.epd
13390 /home/ubuntu/mine.epd
```

Zip and epd sha256 match the given copies. book=ok. This seat's openings are 13,390 lines. The controls are the last 300 of those lines and were not used in the chunks.

## games_tsv.py known answer

`tsv_ka.txt`:

```
sha256sum ka.tsv
6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd  /home/ubuntu/ka.tsv
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

sha256 and the pool lines match the known answer. tsv_ka=ok.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): IdeaB8 value true appears 20 times, HindsightDepth value true appears 20 times, and the refusal pattern count is 0. The same file has 20 log lines around the first `setoption name IdeaB8 value true` (log line 617). arrive=ok.

C-HALF (`half_pool.txt`), side FULL:

```
side FULL: games 400 W-L-D 269-43-88 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 8, 39, 64, 87] Elo +222.41 95% [+191.14, +257.24]
```

FULL's Elo is +222.41, above +20. half_elo=+222.41. `half.tsv` has 400 games.

## POOL.txt

9 chunks, each 500 games (`wc -l chunk_*.tsv` is 500 nine times). `play.out` ends with `minute 46: no new chunk`. No line in `~/play.log` contains FAILED.

Pasted `POOL.txt`:

```
side ON: games 4500 W-L-D 1323-1121-2056 pairs 2250 (openings not in exactly 2 games: 0)
ptnml [88, 503, 906, 625, 128] Elo +15.61 95% [+8.87, +22.35]
```

The 95% interval is [+8.87, +22.35]. It contains both of the round figures named in the brief (about +17 and about +10), so this seat's games do not by themselves decide add versus overlap.

## suspicions, not proven

None. The interval above is the measurement, not a guess about which round figure is right. I am not claiming the two ideas add or that they overlap.

## what I did NOT do

I did not open a pull request. I did not change engine source on this branch, and I did not commit an executable, a net, a PGN, or the patch. I did not pass adjudication flags (`-draw`, `-resign`, `-maxmoves`) and I did not use tablebases. fastchess wrote `config.json` in the repository root because that was the working directory; resign, draw, maxmoves and tablebase adjudication are all `"enabled": false` in it. I moved that file to `/home/ubuntu/fastchess_config.json` and did not commit it. I did not start a chunk after minute 46. I did not play the fallback match. I did not force-push. The channel file `FABLE_TO_grok3_<N>.md` was not on `handoff/fable-opus-combo29-all-20261114` at step 1 or at the step 4 fetch.

## what I am NOT sure about

I have not seen the other seats' both-on O run, so I cannot check that their both_sum matches 9758416. I ran the four O runs at the same time; the three known answers matched, which is why I kept the both-on rows. The 20 lines in `arrive_check.txt` are the first IdeaB8 setoption plus the lines immediately around it.

## times: see stamps.txt

The first line of `stamps.txt` is `2026-11-20T18:49:20Z STEP 1 seat`. Chunk 9's line is `2026-11-20T19:36:04Z chunk 9 done`.

## git status --short and ls -la

Taken after `POOL.txt`, `REPORT.md` and `RESULT.txt` were written, then this listing was appended, so the size of `REPORT.md` in the listing is the size before this section was appended.
```
$ git status --short
 M forge-combo29/grok3/016/stamps.txt
?? forge-combo29/grok3/016/POOL.txt
?? forge-combo29/grok3/016/REPORT.md
?? forge-combo29/grok3/016/RESULT.txt

$ ls -la forge-combo29/grok3/016
total 1200
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:39 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2284 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu   292 Nov 20 18:55 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu 55670 Nov 20 18:59 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51587 Nov 20 18:59 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56206 Nov 20 19:04 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51429 Nov 20 19:04 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56179 Nov 20 19:09 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51572 Nov 20 19:09 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56504 Nov 20 19:13 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51727 Nov 20 19:13 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56433 Nov 20 19:17 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51494 Nov 20 19:17 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56181 Nov 20 19:22 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51699 Nov 20 19:22 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56328 Nov 20 19:26 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51637 Nov 20 19:26 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56457 Nov 20 19:31 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51615 Nov 20 19:31 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56021 Nov 20 19:36 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51542 Nov 20 19:36 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:53 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 46228 Nov 20 18:54 half.out
-rw-r--r-- 1 ubuntu ubuntu   144 Nov 20 18:54 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:53 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41965 Nov 20 18:54 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    46 Nov 20 18:54 half_tsv.print.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:53 match.sh
-rw-r--r-- 1 ubuntu ubuntu    60 Nov 20 18:52 o_b8.print.txt
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    60 Nov 20 18:52 o_both.print.txt
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    60 Nov 20 18:52 o_k3.print.txt
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    60 Nov 20 18:52 o_off.print.txt
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:53 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:53 play.sh
-rw-r--r-- 1 ubuntu ubuntu   151 Nov 20 19:38 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6639 Nov 20 19:39 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   291 Nov 20 19:39 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    90 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   472 Nov 20 19:39 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   245 Nov 20 18:55 tsv_ka.txt
```

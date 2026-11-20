# grok3 seat 027

Seat 027, arm 3, 60000 nodes. Chunks are 100 openings (200 games). Match is the main match: ON (IdeaB8 true, HindsightDepth true) against OFF (both false).

## Patch sha256 and git apply

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`. That is the required hash. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-028` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. In the worktree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`, `git apply --check ~/b8.patch && git apply ~/b8.patch` printed `APPLY_OK`. The worktree, not this branch, now has local modifications in `forge-combo29/include/forge/search.hpp`, `forge-combo29/src/search.cpp`, and `forge-combo29/src/uci.cpp`. None of those files were committed.

The first cmake used `/usr/bin/c++`, which is Clang 18.1.3, and stopped with `cannot find -lstdc++` (`BUILD_FAILED` in `~/cmake_build.log`). The brief requires g++. I configured again with `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (g++ 13.3.0). `/proc/cpuinfo` has `avx512f` and `bmi2`, so I did not add `-DFORGE_PORTABLE=ON` or `-DFORGE_MARCH`. The second build printed `BUILD_OK`. The exe is `/home/ubuntu/build/forge`. Its sha256 in the O-run `.meta` files is `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`.

## Honesty numbers

Fresh processes, no setoption. Required nodes, and the lines in the saved files:

- bench 11: 312866. `honesty_bench11.txt`: `info string bench depth 11 nodes 312866 time 160 nps 1955412`
- bench 13: 862329. `honesty_bench13.txt`: `info string bench depth 13 nodes 862329 time 423 nps 2038602`
- bench 16: 3024920. `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920 time 1402 nps 2157574`
- go perft 5: 4865609. `honesty_perft5.txt` ends with `nodes 4865609`

## Four O runs

`~/first200.fens` sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines.

Against the known text:

1. IdeaB8=false HindsightDepth=false. Required sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Printed `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. `sha256sum o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`.
2. IdeaB8=true HindsightDepth=false. Required sum 9,718,009 and first three 17,283 / 17,878 / 31,115. Printed `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`.
3. IdeaB8=false HindsightDepth=true. Required sum 9,845,650 and first three 23,395 / 31,504 / 35,958. Printed `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`.
4. IdeaB8=true HindsightDepth=true. No known answer. Printed `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200. A recount of node counts that differ is also 200.

The `.meta` files send Threads 1, Hash 16, the 14 S14 settings, then the two idea options for that run.

## Book sha256

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `wc -l ~/uho.epd` printed 2632036. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both hashes match the given copy. `~/mine.epd` has 13390 lines (seat 027, lines at and after 2150027, every 36th).

## Known answer of games_tsv.py

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text. The same two lines are in `ka_check.txt`.

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`: `setoption name IdeaB8 value true` count 20, `setoption name HindsightDepth value true` count 20, refusal count 0. The same file has 20 log lines (arrive.log lines 519-538) around the first IdeaB8 setoption, which is line 529. fastchess accepted `engine=true`. `~/arrive.out` contains `Finished match`.

C-HALF: `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/027/half.tsv` printed:

```
side FULL: games 400 W-L-D 274-43-83 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 10, 39, 61, 90] Elo +228.86 95% [+197.73, +263.59]
```

FULL's Elo is above +20. Pass. `half.out` from fastchess also shows Elo 228.86 on 400 games.

## POOL.txt and chunks

9 chunks, each 200 games, 1800 games. `~/play.log` has no FAILED line. play.sh printed `minute 46: no new chunk` and exited. Chunk 9 had already printed `Finished match` at 19:39:08Z. Nothing was killed.

Pasted `POOL.txt`:

```
side ON: games 1800 W-L-D 479-424-897 pairs 900 (openings not in exactly 2 games: 0)
ptnml [29, 211, 374, 248, 38] Elo +10.62 95% [+0.44, +20.82]
```

## suspicions, not proven

None. Chunk 9's own fastchess summary was Elo -6.95 on 200 games. That line is one chunk. The result above is the games_tsv pool of all nine chunks. I did not treat the single-chunk line as a fault.

## what I did NOT do

I did not open a pull request. I did not commit engine source, the exe, a net, a PGN, or the book. I did not pass adjudication options. I did not play the fallback match. I did not rerun C-HALF. I did not add portable build flags. I did not force-push or write any branch except `for-fable-and-opus/grok3-027`. I did not start a chunk after minute 46. There was no `FABLE_TO_grok3_<N>.md` on `handoff/fable-opus-combo29-all-20261114` at STEP 1 or at the STEP 4 channel read (`git ls-tree` of `forge-combo29/soak_all/` had no file of that name), so there was no STOP.

## what I am NOT sure about

I am not sure other seats print the same run-4 sum 9758416. This machine printed it. No known answer was given for run 4. I am not sure the 20-line arrive window had to be lines 519-538 rather than another 20 lines around line 529. The counts themselves are 20, 20, and 0.

## times: see stamps.txt

fastchess wrote `config.json` in the repository root at the end of the matches (the shell was in the repo when play.sh started). I did not add it. In that file resign, draw, maxmoves, and tb_adjudication all have `enabled` false. Every chunk row has a scored result (no `*`). The Termination header on all 1800 games is `normal`. Ply counts run from 17 to 515.

## git status --short

```
 M forge-combo29/grok3/027/stamps.txt
?? config.json
?? forge-combo29/grok3/027/POOL.txt
?? forge-combo29/grok3/027/REPORT.md
?? forge-combo29/grok3/027/RESULT.txt
?? forge-combo29/grok3/027/ka_check.txt
```

## ls -la forge-combo29/grok3/027

```
total 636
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:42 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2272 Nov 20 18:56 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22400 Nov 20 19:01 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20727 Nov 20 19:01 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22574 Nov 20 19:06 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20753 Nov 20 19:06 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22202 Nov 20 19:11 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20599 Nov 20 19:11 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22727 Nov 20 19:15 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20755 Nov 20 19:15 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22587 Nov 20 19:20 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20593 Nov 20 19:20 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22668 Nov 20 19:25 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20700 Nov 20 19:25 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22548 Nov 20 19:29 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20654 Nov 20 19:29 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22535 Nov 20 19:34 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20687 Nov 20 19:34 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 22320 Nov 20 19:39 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 20595 Nov 20 19:39 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:53 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45663 Nov 20 18:56 half.out
-rw-r--r-- 1 ubuntu ubuntu   145 Nov 20 18:56 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:53 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42086 Nov 20 18:56 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:52 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   228 Nov 20 19:41 ka_check.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:53 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:53 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:40 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  5986 Nov 20 19:42 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:42 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    90 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   418 Nov 20 19:42 stamps.txt
```

The listing above is from before this status section was appended, so `REPORT.md` is longer in the commit than 5986 bytes.

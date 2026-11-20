# grok3 seat 034

Seat 034, arm 1, 20,000 nodes, chunks of 250 openings (500 games). Model Grok 4.7. Match: main (IdeaB8=true and HindsightDepth=true against both false). Branch `for-fable-and-opus/grok3-034`.

## Patch

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`. That is the required hash. The patch was `git show 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`. `git rev-parse FETCH_HEAD` after fetching `for-fable-and-opus/grok-028` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. In the work tree, `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both succeeded.

The first cmake used `/usr/bin/c++` (Clang 18.1.3) and stopped with `cannot find -lstdc++`. The brief requires g++ and GCC's C++ library, so I removed `~/build` and configured again with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0). `lscpu` showed AVX-512 and BMI2, so I did not add `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. The binary is `~/build/forge`. Nothing from the build was committed.

## Honesty

Fresh processes, no setoption. Raw files: `honesty_bench11.txt`, `honesty_bench13.txt`, `honesty_bench16.txt`, `honesty_perft5.txt`.

- bench 11: `info string bench depth 11 nodes 312866 time 164 nps 1907719` (required 312866)
- bench 13: `info string bench depth 13 nodes 862329 time 439 nps 1964302` (required 862329)
- bench 16: `info string bench depth 16 nodes 3024920 time 1419 nps 2131726` (required 3024920)
- go perft 5: last line `nodes 4865609` (required 4865609)

## Four O runs

`o_runs.py` on `~/build/forge` and `~/first200.fens` (`sha256` `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines). Sums below were added from the row files.

Required text, and what the files hold:

1. Both off. Required sum 9,500,069 and first three 41,311 / 24,872 / 28,574. File: sum 9500069, first three 41311 / 24872 / 28574. `sha256sum o_off.rows.txt` is `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`.
2. IdeaB8 only. Required sum 9,718,009 and first three 17,283 / 17,878 / 31,115. File: sum 9718009, first three 17283 / 17878 / 31115.
3. HindsightDepth only. Required sum 9,845,650 and first three 23,395 / 31,504 / 35,958. File: sum 9845650, first three 23395 / 31504 / 35958.
4. Both on. No required answer. File: sum 9758416, first three 18538 / 34070 / 39093, 200 rows. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200.

`.meta` for the both-on run names exe `/home/ubuntu/build/forge`, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, id name `Chess Engine Forge 6.4.24 candidate`.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `wc -l ~/uho.epd` printed 2632036. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both match the brief. `~/mine.epd` has 13389 lines. Controls used the last 300 of those lines (`ctl_arrive.epd` 10, `ctl_half.epd` 200). Chunks took lines from the top and stopped at chunk 11 (lines 2501–2750), short of those 300.

## games_tsv.py known answer

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): IdeaB8 value true counted 20, HindsightDepth value true counted 20, `unknown option|invalid value|no such option` counted 0. The same file has 20 log lines around the first `setoption name IdeaB8 value true` (arrive.log line 398). fastchess accepted `engine=true`.

C-HALF, `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/034/half.tsv`:

```
side FULL: games 400 W-L-D 274-46-80 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 48, 55, 90] Elo +224.97 95% [+194.40, +258.97]
```

FULL's Elo is above +20. Pass. `half.out` agrees (Elo 224.97, 400 games, Finished match).

## POOL.txt and chunks

11 chunks, each 500 games, 5500 games. No chunk line in `~/play.log` says FAILED. Chunk 11 was started after chunk 10's stamp `2026-11-20T19:34:53Z`, which is before minute 46 (`2026-11-20T18:49:44Z` plus 46 minutes is `2026-11-20T19:35:44Z`). Chunk 11's stamp is `2026-11-20T19:39:01Z`, before minute 51 (`2026-11-20T19:40:44Z`). `~/play.out` then printed `minute 46: no new chunk`.

Pasted `POOL.txt`:

```
side ON: games 5500 W-L-D 1583-1368-2549 pairs 2750 (openings not in exactly 2 games: 0)
ptnml [118, 599, 1133, 750, 150] Elo +13.59 95% [+7.51, +19.67]
```

## suspicions, not proven

The both-on node sum is 9758416 against 9500069 off, 9718009 for IdeaB8 alone and 9845650 for HindsightDepth alone. The node increase with both on is larger than IdeaB8 alone and smaller than HindsightDepth alone, so the two node increases are not added together. Node counts are not Elo.

The match interval [+7.51, +19.67] contains both a gain near +10 and a gain near +17. This one seat does not decide whether the two ideas add or overlap.

## what I did NOT do

No pull request. No `--force`. No commit of engine source, the binary, a net, a PGN, the book, or `config.json`. No adjudication options (`-draw`, `-resign`, `-maxmoves`, tablebases). No fallback match. No chunk started at or after minute 46. No second seat's branch was written.

## what I am NOT sure about

I have not seen another seat's both-on O run. The brief says every seat must print the same sum and that a seat which differs is not pooled. Mine is 9758416, first three 18538 / 34070 / 39093, and 200 positions differ from the off run.

fastchess wrote `config.json` in the repository root because `match.sh` was started with that directory as the working directory. It is untracked. I did not add it.

## times: see stamps.txt

## git status --short and ls -la

The pasted output follows, captured after `POOL.txt`, `RESULT.txt`, `REPORT.md` and the STEP 5 stamp line existed.

```
$ git status --short
 M forge-combo29/grok3/034/stamps.txt
?? config.json
?? forge-combo29/grok3/034/POOL.txt
?? forge-combo29/grok3/034/REPORT.md
?? forge-combo29/grok3/034/RESULT.txt

$ ls -la forge-combo29/grok3/034
total 1384
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:41 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2313 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 55915 Nov 20 19:34 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51395 Nov 20 19:34 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 56159 Nov 20 19:39 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 51571 Nov 20 19:39 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 56452 Nov 20 18:57 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51709 Nov 20 18:57 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56441 Nov 20 19:01 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51600 Nov 20 19:01 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56224 Nov 20 19:05 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51466 Nov 20 19:05 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56367 Nov 20 19:10 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51707 Nov 20 19:10 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56073 Nov 20 19:14 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51532 Nov 20 19:14 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56341 Nov 20 19:18 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51658 Nov 20 19:18 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56370 Nov 20 19:22 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51463 Nov 20 19:22 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56267 Nov 20 19:26 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51736 Nov 20 19:26 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56467 Nov 20 19:30 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51677 Nov 20 19:30 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45650 Nov 20 18:53 half.out
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41979 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu   153 Nov 20 19:40 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6330 Nov 20 19:41 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   294 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    87 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   488 Nov 20 19:41 stamps.txt
```

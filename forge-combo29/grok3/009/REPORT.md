# grok3 seat 009

Seat 009, arm 3, 60,000 nodes, chunks of 100 openings (200 games). Model Grok 4.7. Branch for-fable-and-opus/grok3-009. Match is the main match: IdeaB8 and HindsightDepth both on, against both off.

Channel: `git ls-tree` of handoff/fable-opus-combo29-all-20261114 `forge-combo29/soak_all/` showed no `FABLE_TO_grok3_*.md` at STEP 1 and again at 2026-11-20T19:13:07Z. Nothing extra applied.

## Patch sha256 and git apply

`sha256sum ~/b8.patch` (bytes from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`, and `git rev-parse FETCH_HEAD` after fetching `for-fable-and-opus/grok-028` was that same commit):

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/b8.patch
```

`git apply --check ~/b8.patch` then `git apply ~/b8.patch` in the work tree at `6b98f2170a3210e71beed04bbd2553972c253ed7` printed `APPLY_OK`.

Build: `/usr/bin/c++` is clang++ 18.1.3 and its link test failed with `cannot find -lstdc++`. CMake was rerun with `-DCMAKE_CXX_COMPILER=g++` (GCC 13.3.0). The CPU has AVX-512 and BMI2, so `FORGE_PORTABLE` was left off and `-march` stayed the project's `x86-64-v4`. The exe is `/home/ubuntu/build/forge`. Its sha256, from each O-run `.meta`, is `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`. id name: `Chess Engine Forge 6.4.24 candidate`.

## Honesty numbers

Fresh process, no setoption, raw files in this folder:

```
info string bench depth 11 nodes 312866 time 170 nps 1840388
info string bench depth 13 nodes 862329 time 446 nps 1933473
info string bench depth 16 nodes 3024920 time 1476 nps 2049403
nodes 4865609
```

These are the known nodes: 312866, 862329, 3024920, 4865609.

## Four O runs

`~/first200.fens` sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines.

(1) IdeaB8=false HindsightDepth=false printed `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. `sha256sum` of `o_off.rows.txt` is `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`.

(2) IdeaB8=true HindsightDepth=false printed `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`.

(3) IdeaB8=false HindsightDepth=true printed `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`.

(4) IdeaB8=true HindsightDepth=true printed `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. First rows of `o_both.rows.txt`: `18538`, `34070`, `39093`. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed `200` (every position's node count differs from the off run).

The four runs were four processes at once. (1) (2) and (3) matched the known numbers, including the off-run sha256, so the parallel run did not change the counts.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both match the given copies. `~/mine.epd` has 13390 lines (seat 009, lines after 2,150,000, every 36th).

## Known answer of games_tsv.py

`sha256sum ~/ka.tsv` is `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`.

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

## C-ARRIVE and C-HALF

C-ARRIVE (`match.sh` on 10 openings, 10 rounds, trace log). Counts in `arrive_check.txt`: IdeaB8 value true = 20, HindsightDepth value true = 20, refusal lines = 0. The 20 log lines around the first IdeaB8 setoption are in that file. fastchess accepted `engine=true`.

C-HALF (`half.sh`, 200 openings, 200 rounds, 400 games). `games_tsv.py pool FULL` printed:

```
side FULL: games 400 W-L-D 265-40-95 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 10, 37, 67, 85] Elo +221.14 95% [+190.39, +255.29]
```

FULL's Elo is above +20. Passed.

## POOL.txt and chunks

8 chunks, 200 games each, 1600 games. No chunk failed. Chunk 8 finished at 2026-11-20T19:35:35Z; play.sh then printed `minute 46: no new chunk` and exited. No game was killed.

Pasted `POOL.txt`:

```
side ON: games 1600 W-L-D 413-354-833 pairs 800 (openings not in exactly 2 games: 0)
ptnml [26, 173, 341, 236, 24] Elo +12.82 95% [+2.35, +23.31]
```

## suspicions, not proven

The point estimate +12.82 at 60,000 nodes sits between a full add of the two known 20,000-node gains and a complete overlap. The 95% interval [+2.35, +23.31] covers both. This seat does not decide which story is true. fastchess also prints an Elo in each `chunk_N.out`; the number above is only from `games_tsv.py`.

## what I did NOT do

No pull request. No engine source committed or edited by me (only the given patch in a work tree outside the branch). No `--force`. No adjudication flags (`-draw`, `-resign`, `-maxmoves`, tablebases). fastchess wrote an untracked `config.json` in the repository root during the match; resign, draw, maxmoves and tablebase adjudication are `enabled: false` in it. I did not `git add` that file. No PGN, exe, net, or patch file committed. No second seat's branch. The fallback match was not played.

## what I am NOT sure about

I have not seen the other seats' run (4). I cannot check that their both-on sum equals 9,758,416. I am sure of the numbers printed above, because I opened the files after the commands.

## times: see stamps.txt

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok3/009/stamps.txt
?? config.json
?? forge-combo29/grok3/009/POOL.txt
?? forge-combo29/grok3/009/REPORT.md
?? forge-combo29/grok3/009/RESULT.txt
```

## ls -la forge-combo29/grok3/009

```
total 588
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:38 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2243 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22995 Nov 20 19:00 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20593 Nov 20 19:00 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22585 Nov 20 19:06 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20655 Nov 20 19:06 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22397 Nov 20 19:11 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20764 Nov 20 19:11 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22742 Nov 20 19:16 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20836 Nov 20 19:16 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22666 Nov 20 19:21 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20698 Nov 20 19:21 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22623 Nov 20 19:26 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20768 Nov 20 19:26 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22652 Nov 20 19:31 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20699 Nov 20 19:31 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22620 Nov 20 19:35 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20729 Nov 20 19:35 chunk_8.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:53 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 46351 Nov 20 18:55 half.out
-rw-r--r-- 1 ubuntu ubuntu   145 Nov 20 18:55 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:53 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42153 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    46 Nov 20 18:55 half_tsv_run.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:53 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:53 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:53 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:37 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  5699 Nov 20 19:38 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:38 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   429 Nov 20 19:38 stamps.txt
```

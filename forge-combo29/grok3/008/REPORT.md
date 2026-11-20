# grok3 seat 008

Seat 008, arm 2, 2,000 nodes. Chunk size 500 openings (1,000 games). Match is the main match: IdeaB8=true and HindsightDepth=true (ON) against IdeaB8=false and HindsightDepth=false (OFF). Same exe on both sides.

## Patch

`sha256sum ~/b8.patch` (rechecked 2026-11-20T19:33:23Z):

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/b8.patch
```

That is the required hash. Source commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75` (`git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-028`). In the worktree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`: `git apply --check ~/b8.patch` then `git apply ~/b8.patch` printed `APPLY OK`. `git diff --stat`:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

The worktree is outside the repository. No engine source, object file, or exe was committed.

Decision: the first cmake used `/usr/bin/c++`, which is clang++ 18, and the link failed with `cannot find -lstdc++`. The brief requires g++ (GCC 13 or newer) and GCC's libstdc++. I deleted `~/build` and configured again with `-DCMAKE_CXX_COMPILER=g++`. `~/cmake_build.log` line 1: `-- The CXX compiler identification is GNU 13.3.0`. `/proc/cpuinfo` has AVX-512 and BMI2, so I did not pass `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. Exe is `/home/ubuntu/build/forge`, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, `id name Chess Engine Forge 6.4.24 candidate`. All four O-run `.meta` files name that exe and that sha256.

## Honesty

Fresh processes, no setoption before the command. Raw files: `honesty_bench11.txt`, `honesty_bench13.txt`, `honesty_bench16.txt`, `honesty_perft5.txt`.

```
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 427 nps 2019505
info string bench depth 16 nodes 3024920 time 1416 nps 2136242
nodes 4865609
```

These are the required nodes: 312866, 862329, 3024920, 4865609.

## Four O runs

`python3 ~/o_runs.py` on `/home/ubuntu/build/forge` and `~/first200.fens` (sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines).

| run | options | printed sum and first three | against the brief |
| --- | --- | --- | --- |
| o_off | IdeaB8=false HindsightDepth=false | rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574 | matches |
| o_b8 | IdeaB8=true HindsightDepth=false | rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115 | matches |
| o_k3 | IdeaB8=false HindsightDepth=true | rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958 | matches |
| o_both | IdeaB8=true HindsightDepth=true | rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093 | no known answer |

`sha256sum forge-combo29/grok3/008/o_off.rows.txt`:

```
dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7
```

That is the required hash. Rechecked `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` at 2026-11-20T19:33:23Z: `200`. First three both-on rows are `18538`, `34070`, `39093`. Every one of the 200 positions has a different node count from both-off.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Zip and epd match the brief. `~/mine.epd` has 13390 lines. Seat 008 takes every 36th line from line 2150008.

## games_tsv.py known answer

`sha256sum ~/ka.tsv` from `for-fable-and-opus/grok2-004` `forge-combo29/grok2/004/chunk_1.tsv`:

```
6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd  /home/ubuntu/ka.tsv
```

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That matches the brief.

## C-ARRIVE

`bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` exited 0 and printed `Finished match`. Counts in `arrive_check.txt` (also the 20 log lines around the first IdeaB8 setoption):

```
setoption name IdeaB8 value true: 20
setoption name HindsightDepth value true: 20
unknown option|invalid value|no such option: 0
```

Required: IdeaB8 true at least 1, HindsightDepth true at least 1, refusals 0. The whole arrive log was not committed.

## C-HALF

`bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn` exited 0, `Finished match`, 400 games. `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/008/half.tsv` (run again at step 5):

```
side FULL: games 400 W-L-D 287-40-73 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 5, 40, 54, 100] Elo +250.49 95% [+217.81, +287.47]
```

PASS: FULL Elo +250.49 is above +20. fastchess printed `Elo: 250.49 +/- 34.83` and the same W-L-D and pentanomial. `half.out` and `half.tsv` are in this folder.

## Pool

26 chunks, each `chunk_N.tsv` is 1000 lines, 26000 games. `~/play.log` has no `FAILED` line. `play.out` ends with `openings used up`. Chunk 26 stamp `2026-11-20T19:29:40Z` is 40 minutes 22 seconds after the STEP 1 stamp `2026-11-20T18:49:18Z`, before minute 46. No chunk was killed. `python3 ~/games_tsv.py pool ON forge-combo29/grok3/008/chunk_*.tsv` wrote `POOL.txt`:

```
side ON: games 26000 W-L-D 9499-8353-8148 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1143, 2539, 4849, 2967, 1502] Elo +15.32 95% [+12.01, +18.64]
```

Pentanomial counts sum to 13000 pairs. W+L+D = 26000. Openings not in exactly 2 games: 0.

## suspicions, not proven

Run 4's node sum 9,758,416 sits near IdeaB8 alone (9,718,009) and below HindsightDepth alone (9,845,650), and all 200 positions changed node count versus both-off. That is a depth-12 node-count fact. It does not by itself say whether the Elo gains add.

The game result at 2,000 nodes is Elo +15.32 with 95% interval [+12.01, +18.64]. The earlier swarm's alone gains (+10.25 and +6.75) were at 20,000 nodes, so this interval is not a direct add-or-overlap test against those two numbers. I do not claim the gains add or overlap beyond this interval.

`games_tsv.py` half interval [+217.81, +287.47] is not the same width as fastchess `250.49 +/- 34.83`. The point estimate +250.49 matches. I did not decide which variance formula is intended past using `games_tsv.py` as specified. The pass condition (Elo above +20) holds on both prints.

## what I did NOT do

No pull request. No fallback match (`ON_B8` stayed true). No `--force`. No push except `for-fable-and-opus/grok3-008`. No engine source committed. No PGN, exe, or net committed. No adjudication flags (`-draw`, `-resign`, `-maxmoves`, tablebases) were passed. fastchess wrote an untracked `config.json` in the repository root because `play.sh` was started with that cwd; its resign, draw, maxmoves, and tb_adjudication `enabled` fields are false. I did not `git add` it. No second channel file existed to obey. I did not start another chunk after `openings used up`.

## what I am NOT sure about

I have not seen the other seats' run-4 sums. If another seat's both-on rows differ from sum 9,758,416 and first three 18,538 / 34,070 / 39,093, this seat's run 4 is the one that would not be pooled; the rows file is `o_both.rows.txt`.

I am sure the playing binary is the g++ build whose honesty and O-run numbers matched, because each `.meta` records that path and sha256. I am not sure a clang build would have produced the same nodes; I did not keep the failed clang configure.

## times: see stamps.txt

STEP 1 `2026-11-20T18:49:18Z`. Channel at step 1 and again during step 4 (`git ls-tree` of `handoff/fable-opus-combo29-all-20261114`): no `FABLE_TO_grok3_*.md`. `~/setup_bg.log`: `fastchess OK`, `python-chess OK`, `book OK`, `setup_bg done`.

## git status --short and ls -la

The next two blocks are the raw command output, pasted after this file and `RESULT.txt` and the STEP 5 stamp line existed.

```
$ git status --short
 M forge-combo29/grok3/008/stamps.txt
?? config.json
?? forge-combo29/grok3/008/POOL.txt
?? forge-combo29/grok3/008/REPORT.md
?? forge-combo29/grok3/008/RESULT.txt
```

```
$ ls -la forge-combo29/grok3/008
total 5772
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:33 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu   2212 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110676 Nov 20 19:08 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102654 Nov 20 19:08 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 110355 Nov 20 19:10 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102562 Nov 20 19:10 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 111060 Nov 20 19:11 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102503 Nov 20 19:11 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 110870 Nov 20 19:12 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102714 Nov 20 19:12 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 110911 Nov 20 19:14 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102644 Nov 20 19:14 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110923 Nov 20 19:15 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102471 Nov 20 19:15 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110561 Nov 20 19:16 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102542 Nov 20 19:16 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 111092 Nov 20 19:17 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102821 Nov 20 19:17 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 111176 Nov 20 19:19 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102881 Nov 20 19:19 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 111037 Nov 20 19:20 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102352 Nov 20 19:20 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 111200 Nov 20 18:56 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102670 Nov 20 18:56 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 110342 Nov 20 19:21 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102563 Nov 20 19:21 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 110901 Nov 20 19:23 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102597 Nov 20 19:23 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110969 Nov 20 19:24 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102289 Nov 20 19:24 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 111175 Nov 20 19:25 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102700 Nov 20 19:25 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 111157 Nov 20 19:27 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102376 Nov 20 19:27 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110344 Nov 20 19:28 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102687 Nov 20 19:28 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 111007 Nov 20 19:29 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102799 Nov 20 19:29 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 111069 Nov 20 18:58 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102839 Nov 20 18:58 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 111396 Nov 20 18:59 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102735 Nov 20 18:59 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110887 Nov 20 19:00 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102849 Nov 20 19:00 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 111034 Nov 20 19:02 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102731 Nov 20 19:02 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110832 Nov 20 19:03 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102491 Nov 20 19:03 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 110710 Nov 20 19:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102445 Nov 20 19:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110539 Nov 20 19:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102605 Nov 20 19:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110541 Nov 20 19:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102242 Nov 20 19:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:55 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45518 Nov 20 18:55 half.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 18:55 half.sh
-rw-r--r-- 1 ubuntu ubuntu  41921 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:53 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:53 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1022 Nov 20 18:55 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:53 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:53 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:53 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:53 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:53 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:53 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:53 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:53 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:55 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu   1755 Nov 20 18:55 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:31 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   8124 Nov 20 19:33 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:33 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 19:34 stamps.txt
```

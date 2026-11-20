# grok3 seat 015

Seat 015, arm 3, 60,000 nodes. Chunk size 100 openings (200 games). Model Grok 4.7. Match is the main match: IdeaB8=true and HindsightDepth=true (ON) against IdeaB8=false and HindsightDepth=false (OFF). Same exe for both sides.

## Patch

Source commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75` (`for-fable-and-opus/grok-028`, `git rev-parse FETCH_HEAD` printed that hash).

`sha256sum ~/b8.patch` printed:

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/b8.patch
```

That is the required hash. In the worktree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`, `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both exited 0 (the shell printed `APPLY OK`). The patch was not committed. The engine source in this branch is unchanged.

The first cmake used `/usr/bin/c++`, which is Clang 18.1.3, and the link failed (`cannot find -lstdc++`). The brief requires g++. I removed `~/build` and configured again with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` contains avx512 and bmi2, so I did not pass `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. `cmake --build` printed `Built target forge` and `BUILD_OK`. Exe is `/home/ubuntu/build/forge`.

## Honesty

Fresh process, no setoption, raw files in this folder:

- bench 11: `info string bench depth 11 nodes 312866 time 163 nps 1919423`
- bench 13: `info string bench depth 13 nodes 862329 time 438 nps 1968787`
- bench 16: `info string bench depth 16 nodes 3024920 time 1418 nps 2133229`
- go perft 5: `nodes 4865609`

Those node counts are the required ones.

## Four O runs

`o_runs.py` on `/home/ubuntu/build/forge`, 200 fens, depth 12. Each `.meta` names that exe, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, `id name Chess Engine Forge 6.4.24 candidate`.

(1) IdeaB8=false HindsightDepth=false. Printed `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. `sha256sum` of `o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. Both match the known answer.

(2) IdeaB8=true HindsightDepth=false. Printed `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`. Matches the known answer.

(3) IdeaB8=false HindsightDepth=true. Printed `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`. Matches the known answer.

(4) IdeaB8=true HindsightDepth=true. No known answer was given. Printed `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. The first three rows of `o_both.rows.txt` are `18538`, `34070`, `39093`. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed `200`.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07` (matches). `wc -l ~/uho.epd` printed `2632036`. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (matches). Own openings: `wc -l ~/mine.epd` printed `13390`.

## games_tsv.py known answer

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the known answer.

## C-ARRIVE

`bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` exited 0 and `~/arrive.out` contains `Finished match` (20 games). Counts, also in `arrive_check.txt`:

- `setoption name IdeaB8 value true`: 20
- `setoption name HindsightDepth value true`: 20
- `unknown option|invalid value|no such option`: 0

The 20 log lines around the first IdeaB8 setoption are in `arrive_check.txt`.

## C-HALF

`bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn` exited 0 (`Finished match`, 400 games, about 20 seconds). `python3 ~/games_tsv.py pool FULL` on `half.tsv` printed:

```
side FULL: games 400 W-L-D 270-47-83 pairs 200 (openings not in exactly 2 games: 0)
ptnml [3, 12, 36, 57, 92] Elo +218.61 95% [+185.40, +255.79]
```

FULL's Elo is above +20. Pass.

## Pool

9 chunks, 200 games each, 1800 games. Each chunk's fastchess log contains `Finished match`. No chunk line says FAILED. Chunk 9 was started at 19:34:09Z, before minute 46 (19:35:19Z), and finished at 19:38:45Z, before minute 51 (19:40:19Z). `play.out` then printed `minute 46: no new chunk`. No opening was repeated to add games.

Pasted `POOL.txt`:

```
side ON: games 1800 W-L-D 475-400-925 pairs 900 (openings not in exactly 2 games: 0)
ptnml [27, 183, 410, 248, 32] Elo +14.48 95% [+4.75, +24.24]
```

## suspicions, not proven

This seat's Elo is +14.48 with 95% interval [+4.75, +24.24] at 60,000 nodes. The interval covers both "about +10" and "about +17". 1800 games from one seat do not decide whether the two ideas add or overlap. The node sum of run (4), 9,758,416, is not the sum of the two separate node-sum gaps, and a node sum is not Elo. I do not treat it as evidence about adding versus overlapping.

## what I did NOT do

I did not open a pull request. I did not use `--force`. I did not push any branch except `for-fable-and-opus/grok3-015`. I did not commit engine source, the exe, a net, a PGN, or the book. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not play the fallback match. I did not kill a running chunk. No `FABLE_TO_grok3_*.md` file was on `handoff/fable-opus-combo29-all-20261114` at step 1 or in the middle of step 4. I did not commit the untracked `config.json` in the repository root (fastchess wrote it; its resign, draw, maxmoves, and tablebase flags are all `enabled: false`).

## what I am NOT sure about

I am not sure other seats print the same run (4). There was no known answer. This machine printed sum 9,758,416, first three 18,538 / 34,070 / 39,093, and 200 of 200 positions differ from run (1). Runs (1) (2) and (3) matched the known numbers on this same exe.

`play.sh` was started with the repository as its working directory, so fastchess wrote `config.json` there. I left that file untracked on purpose.

## times: see stamps.txt

STEP 1 stamp is `2026-11-20T18:49:19Z`. Minute 46 is 19:35:19Z. Minute 51 is 19:40:19Z.


## git status --short

```
 M forge-combo29/grok3/015/stamps.txt
?? config.json
?? forge-combo29/grok3/015/POOL.txt
?? forge-combo29/grok3/015/REPORT.md
?? forge-combo29/grok3/015/RESULT.txt
```

`config.json` is outside this folder. It is not added.

## ls -la

Taken after POOL.txt, REPORT.md, RESULT.txt and the STEP 5 stamp were written, and before this status block was appended (so `REPORT.md` is longer in the commit than the 6232 bytes below). Every other name is unchanged.

```
total 628
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:41 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2198 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22587 Nov 20 19:00 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20659 Nov 20 19:00 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22609 Nov 20 19:05 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20707 Nov 20 19:05 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22325 Nov 20 19:10 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20633 Nov 20 19:10 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22536 Nov 20 19:14 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20628 Nov 20 19:14 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22768 Nov 20 19:19 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20740 Nov 20 19:19 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22630 Nov 20 19:24 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20619 Nov 20 19:24 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22573 Nov 20 19:29 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20624 Nov 20 19:29 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22506 Nov 20 19:34 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20744 Nov 20 19:34 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 22487 Nov 20 19:38 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 20660 Nov 20 19:38 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:55 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45682 Nov 20 18:55 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:55 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42021 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:55 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:53 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:55 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:40 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6232 Nov 20 19:41 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    90 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   418 Nov 20 19:40 stamps.txt
```

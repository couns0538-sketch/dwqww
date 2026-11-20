# Seat 054, arm 4 (B8b)

Arm 4, source seat 028, branch `for-fable-and-opus/grok-028`, commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. Switch `IdeaB8`. `id` in RESULT.txt is the arm name B8b from the arm table.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` (also `patch_sha256.txt`):

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check` then `git apply` on the work tree exited 0. `git -C /agent/repos/work diff --stat` (`patch_apply.txt`):

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

The patch stays in the work tree only. No engine source is in this commit. `IdeaB8_Weight` and `IdeaB8_Swing` were left at their defaults and were never sent.

Build: `/usr/bin/c++` is Clang 18.1.3 and failed to link `-lstdc++`. Both exes were configured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0, GCC's libstdc++). The CPU has AVX-512 and BMI2, so the build did not pass `FORGE_PORTABLE` or `FORGE_MARCH=x86-64-v3`. Exe B is `/agent/repos/base/forge-combo29/build/forge`. Exe P is `/agent/repos/work/forge-combo29/build/forge`.

## Honesty

`python3 harness.py summarize` wrote `o_table.txt`. Both exes, fresh process per line, no setoption before the command:

```
honesty
  B bench11 312866 want 312866 ok
  B bench13 862329 want 862329 ok
  B bench16 3024920 want 3024920 ok
  B goperft5 4865609 want 4865609 ok
  P bench11 312866 want 312866 ok
  P bench13 862329 want 862329 ok
  P bench16 3024920 want 3024920 ok
  P goperft5 4865609 want 4865609 ok
```

## Three O runs

Same script, same file, against the arm table (base sum 9,500,069 and first three 41,311 / 24,872 / 28,574; arm 4 on 9,718,009, first three 17,283 / 17,878 / 31,115, 200 differ):

```
o_B n 200 sum 9500069 first 41311 24872 28574
o_P_off n 200 sum 9500069 first 41311 24872 28574
off_equal 200 of 200
o_P_on n 200 sum 9718009 first 17283 17878 31115 differ 200
```

Raw transcripts and `.meta` files: `o_B.txt`, `o_P_off.txt`, `o_P_on.txt`. Positions file `first200.fens` sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines.

## Book

`book_sha256.txt`:

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. Seat 054 takes every 90th line of `~/uho.epd` starting at line 54 (`~/mine.epd`, 29245 lines). The last 300 lines were held out for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE: `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`. Counts from `arrive_check.txt`:

```
grep -c setoption name IdeaB8 value true
20
grep -c -E unknown option|invalid value|No such option
0
```

The log accepted `engine=true` and contains the engine lines. The first `setoption name IdeaB8 value true` is in that file with the surrounding lines.

C-HALF: `~/half.sh` is `match.sh` with the two required changes (FULL 20000 nodes, HALF 10000 nodes, no `nodes=` on `-each`). `half_pool.txt` from `python3 ~/games_tsv.py pool FULL`:

```
side FULL: games 400 W-L-D 233-29-138 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 13, 33, 91, 63] Elo +195.51 95% [+168.58, +224.76]
```

FULL's Elo is above +20.

## POOL.txt and chunks

20 chunks, each 500 games, 10000 games. `python3 ~/games_tsv.py pool ON forge-combo29/grok2/054/chunk_*.tsv` wrote `POOL.txt`:

```
side ON: games 10000 W-L-D 2790-2562-4648 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [220, 1129, 2114, 1277, 260] Elo +7.92 95% [+3.45, +12.40]
```

Play stopped itself with `minute 95: no new chunk` after chunk 20. No chunk logged FAILED. No chunk was killed. Openings were the top of `~/mine.epd`, 250 new lines per chunk, not the held-out 300.

## Suspicions, not proven

None. The match command passed no `-draw`, `-resign`, `-maxmoves`, or tablebase flags. A fastchess `config.json` written into the repo root during play had resign, draw, maxmoves, and tablebase adjudication all `enabled: false`. I deleted that untracked file and did not commit it.

## What I did NOT do

No pull request. No commit of an exe, object file, net, PGN, or the opening book. No edit of engine source beyond applying the given patch in the work tree. No `--force`, and no push except `HEAD:refs/heads/for-fable-and-opus/grok2-054`. No `IdeaB8_Weight` or `IdeaB8_Swing`. Arm 10 was not played. No opening was repeated to add games.

## What I am NOT sure about

The RESULT `id` field: I used `B8b` because that is the name on arm row 4. The switch name is `IdeaB8`.

`games_tsv.py` is the only Elo printed here. I did not recompute the interval with another formula.

Node counts matched the table on this machine. I am not claiming the container's nodes-per-second is a speed result.

Local `user.name` was unset. I set `user.name` to `grok agent` and `user.email` to `grok@invalid` in this repository only.

After chunk 9, `~/commit_watch.sh` committed and pushed new `chunk_*` files every 240 seconds and fetched the handoff branch. No `FABLE_TO_grok2_*.md` existed at any of those fetches, including the fetch at STEP 1.

## times: see stamps.txt

The first stamp is `2026-11-20T13:23:31Z STEP 1`. Chunk 20 finished at `2026-11-20T15:01:53Z`. STEP 5 stamp is in `stamps.txt`.

## git status --short

```
 M forge-combo29/grok2/054/stamps.txt
?? forge-combo29/grok2/054/POOL.txt
?? forge-combo29/grok2/054/REPORT.md
?? forge-combo29/grok2/054/RESULT.txt
?? forge-combo29/grok2/054/patch_apply.txt
?? forge-combo29/grok2/054/patch_sha256.txt
```

## ls -la forge-combo29/grok2/054

Listing taken before this section was appended to REPORT.md.

```
total 3288
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:06 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2216 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:29 book_sha256.txt
-rw-r--r-- 1 ubuntu ubuntu  56408 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51504 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56184 Nov 20 14:22 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:22 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 14:26 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 14:26 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55998 Nov 20 14:31 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51410 Nov 20 14:31 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56132 Nov 20 14:35 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51388 Nov 20 14:35 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56693 Nov 20 14:39 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51451 Nov 20 14:39 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56052 Nov 20 14:44 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:44 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56385 Nov 20 14:48 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51496 Nov 20 14:48 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55607 Nov 20 14:52 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51306 Nov 20 14:52 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  55969 Nov 20 14:57 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51414 Nov 20 14:57 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56408 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51162 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56205 Nov 20 15:01 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 15:01 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56335 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51301 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56943 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56312 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51354 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56595 Nov 20 13:56 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 13:56 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55961 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51453 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56441 Nov 20 14:05 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51287 Nov 20 14:05 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56753 Nov 20 14:09 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51490 Nov 20 14:09 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56076 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51327 Nov 20 14:13 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:27 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46820 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:34 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1045 Nov 20 13:34 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42393 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   7598 Nov 20 13:27 harness.py
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_B_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:27 honesty_B_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5164 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:27 honesty_P_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5375 Nov 20 13:27 honesty_P_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    787 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 282034 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    821 Nov 20 13:27 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282052 Nov 20 13:27 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    820 Nov 20 13:28 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282740 Nov 20 13:28 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    467 Nov 20 13:28 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 15:06 patch_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 15:05 patch_sha256.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:05 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5969 Nov 20 15:06 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:06 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    926 Nov 20 15:06 stamps.txt
```

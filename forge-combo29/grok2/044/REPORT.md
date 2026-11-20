# grok2 seat 044

## Arm and source seat

Seat 044, arm 4, id B8b, source seat 028, model Grok 4.7.
Source branch `for-fable-and-opus/grok-028`, commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75` (`git rev-parse FETCH_HEAD` printed that commit).
SWITCH `IdeaB8`. `IdeaB8_Weight` and `IdeaB8_Swing` were left at their defaults and were never sent.

## Patch sha256 and git apply

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree. `git diff --stat` there:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

Build: the first CMake configure used `/usr/bin/c++`, which is clang 18, and the link failed with `cannot find -lstdc++`. I configured again with `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (g++ 13.3.0). `/proc/cpuinfo` has AVX-512 and BMI2, so I did not set `FORGE_PORTABLE` or `FORGE_MARCH`. Exe B is `/tmp/forge-base/forge`. Exe P is `/tmp/forge-work/forge`. Both say `id name Chess Engine Forge 6.4.24 candidate`. Sha256 and the option lines are in the `.meta` files.

## Honesty numbers

`summarize.py` reading the raw honesty files (`numbers.txt`):

```
honesty
  b bench11 312866 expected 312866 ok
  b bench13 862329 expected 862329 ok
  b bench16 3024920 expected 3024920 ok
  b perft5 4865609 expected 4865609 ok
  p bench11 312866 expected 312866 ok
  p bench13 862329 expected 862329 ok
  p bench16 3024920 expected 3024920 ok
  p perft5 4865609 expected 4865609 ok
```

Exe B and exe P both match bench 11, bench 13, bench 16, and `go perft 5`. Each line was a fresh process with no setoption.

## Three O runs

Same script, same file, against the arm table (B sum 9500069 and first three 41311 / 24872 / 28574; ON sum 9718009, first three 17283 / 17878 / 31115, 200 differ; OFF identical to B):

```
O
B positions 200 missing 0 sum 9500069 first 41311 24872 28574
OFF positions 200 missing 0 sum 9500069 first 41311 24872 28574
OFF differ_from_B 0
ON positions 200 missing 0 sum 9718009 first 17283 17878 31115
ON differ_from_B 200
OFF_identical_to_B True
```

Run (1) exe B, run (2) exe P with `IdeaB8 false`, run (3) exe P with `IdeaB8 true`. S14, Threads 1, and Hash 16 were sent before every position. Raw transcripts are `o_b.txt`, `o_off.txt`, `o_on.txt`.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both match the brief. `uho.epd` has 2632036 lines. Seat 044 takes every 90th line from line 44: `mine.epd` has 29245 lines. The last 300 are the controls and were not used by the chunks.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): `setoption name IdeaB8 value true` count 20. `unknown option|invalid value|No such option` count 0.

C-HALF, `games_tsv.py pool FULL` (`half_pool.txt`):

```
side FULL: games 400 W-L-D 220-29-151 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 9, 46, 86, 58] Elo +180.58 95% [+154.60, +208.55]
```

FULL's Elo is above +20.

## POOL.txt and chunks

21 chunks, each 500 games. `wc -l` of `chunk_*.tsv` totals 10500. `play.log` has no FAILED line. `grep -c -i adjudicat` on every `chunk_*.out` is 0. No `-draw`, `-resign`, or `-maxmoves` was passed.

`POOL.txt`, from `python3 ~/games_tsv.py pool ON forge-combo29/grok2/044/chunk_*.tsv`:

```
side ON: games 10500 W-L-D 2888-2631-4981 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [217, 1188, 2219, 1373, 253] Elo +8.51 95% [+4.19, +12.83]
```

## Suspicions, not proven

I suspected fastchess might load `config.json` from the repository directory (the match processes were started with that cwd, and fastchess wrote `config.json` there) and adjudicate games. After the match I grepped that file: the five `"enabled"` fields are false. Every chunk log has zero lines matching `adjudicat`. The suspicion is not supported. `config.json` is untracked and was not committed.

## What I did NOT do

I did not open a pull request. I did not change engine source and I did not commit an executable, a net, a PGN, or the book. I did not push any branch except `for-fable-and-opus/grok2-044`, and I did not force-push. No `FABLE_TO_grok2_*.md` file was on the handoff branch at the fetches I made. No chunk failed, so none was replayed. I did not fall back to arm 10. I did not kill a running chunk: `play.sh` printed `minute 95: no new chunk` after chunk 21 finished.

## What I am NOT sure about

The match tsv files do not record per-move node counts. The node limit is the fastchess `nodes=20000` argument, and C-HALF is the check that a node limit reaches the engine. I did not separately count nodes inside the 10500 games.

## Times

times: see stamps.txt

## git status --short and ls -la

The next two blocks are the command output taken after this report and `RESULT.txt` were written, before the STEP 5 commit.

```
$ git status --short
 M forge-combo29/grok2/044/stamps.txt
?? config.json
?? forge-combo29/grok2/044/POOL.txt
?? forge-combo29/grok2/044/REPORT.md
?? forge-combo29/grok2/044/RESULT.txt
```

```
$ ls -la forge-combo29/grok2/044
total 3436
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2228 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56565 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56584 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51415 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56498 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51514 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56216 Nov 20 14:27 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51445 Nov 20 14:27 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56528 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51589 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56375 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51479 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56353 Nov 20 14:40 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51398 Nov 20 14:40 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56433 Nov 20 14:44 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 14:44 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56326 Nov 20 14:48 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51671 Nov 20 14:48 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56407 Nov 20 14:52 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51273 Nov 20 14:52 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55785 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51061 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56678 Nov 20 14:56 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51568 Nov 20 14:56 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56256 Nov 20 15:00 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51551 Nov 20 15:00 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56582 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56382 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51326 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56201 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51332 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56474 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56386 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51363 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56332 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56365 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56363 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 14:11 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:27 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47405 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42344 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:33 half_tsv_log.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:27 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:27 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:27 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:27 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:27 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:27 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:27 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:27 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    728 Nov 20 13:26 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1019 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    574 Nov 20 13:28 numbers.txt
-rw-r--r-- 1 ubuntu ubuntu    947 Nov 20 13:27 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 307450 Nov 20 13:27 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    981 Nov 20 13:27 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309062 Nov 20 13:27 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    980 Nov 20 13:28 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 309633 Nov 20 13:28 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   3921 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5376 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    754 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2180 Nov 20 13:27 summarize.py
```

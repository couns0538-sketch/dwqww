# grok2 seat 002

Arm 2, B1b. Source seat 080. Commit e778c1358711c0571e8f5cc4df87083cce98e03a. Switch IdeaB1.

## Patch

sha256 of `~/arm.patch` (also `patch.sha256`):

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-080` printed e778c1358711c0571e8f5cc4df87083cce98e03a. In `/agent/repos/work`, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both exited 0. Later `git apply --reverse --check ~/arm.patch` printed REVERSE_CHECK_OK. `patch.stat`:

```
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

The other IdeaB1 spins (Lanes, Fade, Scale, Cap) were left at their defaults and were never sent.

## Builds

GCC 13.3.0, CMake Release, GCC's libstdc++. `/usr/bin/c++` is Clang 18.1.3 and its link failed with `cannot find -lstdc++`, so both configures used `-DCMAKE_CXX_COMPILER=g++`. The CPU has AVX-512 and BMI2, so FORGE_PORTABLE was left off and FORGE_MARCH stayed the default x86-64-v4. Exe B is `/agent/repos/base/forge-combo29/build/forge`. Exe P is `/agent/repos/work/forge-combo29/build/forge`. id name on both: Chess Engine Forge 6.4.24 candidate.

## Honesty

Fresh process per line, no setoption. `summarize.py honesty` printed:

```
tag B
bench11 312866 file forge-combo29/grok2/002/B_bench11.txt
bench13 862329 file forge-combo29/grok2/002/B_bench13.txt
bench16 3024920 file forge-combo29/grok2/002/B_bench16.txt
perft5 4865609 file forge-combo29/grok2/002/B_perft5.txt
tag P
bench11 312866 file forge-combo29/grok2/002/P_bench11.txt
bench13 862329 file forge-combo29/grok2/002/P_bench13.txt
bench16 3024920 file forge-combo29/grok2/002/P_bench16.txt
perft5 4865609 file forge-combo29/grok2/002/P_perft5.txt
```

Those are the four known numbers, on B and on P. `B_bench11.txt` begins `info string bench depth 11 nodes 312866`.

## Three O runs

S14, then Threads 1, Hash 16. Run (3) also sent `setoption name IdeaB1 value true`. Run (2) sent `value false`. `summarize.py orun` and `summarize.py differ` printed:

```
file forge-combo29/grok2/002/o_b.txt
positions 200 missing 0 sum 9500069
first3 41311 24872 28574
file forge-combo29/grok2/002/o_off.txt
positions 200 missing 0 sum 9500069
first3 41311 24872 28574
file forge-combo29/grok2/002/o_on.txt
positions 200 missing 0 sum 9748678
first3 17841 25977 43905
compared 200 differ 0
compared 200 differ 200
```

Table for arm 2: off equals the plain engine (sum 9,500,069; first three 41,311 / 24,872 / 28,574). On: sum 9,748,678; first three 17,841 / 25,977 / 43,905; 200 differ. The runs match that table.

## Book

```
uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd lines 2632036
uho.epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine.epd lines 29245
```

Both hashes match the brief. Seat 002 took every 90th line starting at line 2.

## C-ARRIVE

`arrive_check.txt` records grep counts 20 and 0. The engine accepted `setoption name IdeaB1 value true`. No unknown option, invalid value, or "No such option".

## C-HALF

`games_tsv.py pool FULL` on `half.tsv` printed:

```
side FULL: games 400 W-L-D 229-23-148 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 10, 33, 98, 59] Elo +197.87 95% [+172.23, +225.62]
```

FULL's Elo is above +20. Twice the nodes won.

## Pool

15 chunks, 7500 games. `POOL.txt` is the pasted output of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/002/chunk_*.tsv`:

```
side ON: games 7500 W-L-D 2005-2000-3495 pairs 3750 (openings not in exactly 2 games: 0)
ptnml [183, 898, 1568, 933, 168] Elo +0.23 95% [-4.93, +5.40]
```

## Suspicions, not proven

None. The pool interval covers 0, so this sample does not show a gain. That is the measurement, not a suspicion about a broken match.

## What I did NOT do

- No pull request.
- No engine source edit. The patch was applied only in the work tree, which is not committed.
- No adjudication (`-draw`, `-resign`, `-maxmoves`, tablebases).
- Did not send IdeaB1_Lanes, IdeaB1_Fade, IdeaB1_Scale, or IdeaB1_Cap.
- Did not switch to arm 10. Runs (1), (2), and (3) matched the table.
- No `FABLE_TO_grok2_<N>.md` existed on `handoff/fable-opus-combo29-all-20261114` at step 1 or at the chunk pushes.
- Did not replay this morning's seat 030 PGN through `games_tsv.py`.
- Did not play openings past the reserved tail of `mine.epd`.

## What I am NOT sure about

`play.log` stamps chunk 13 done at 14:38:44Z and chunk 14 done at 14:53:51Z, while `chunk_14.out` says `Total Time: 00:04:59`. I do not know why the log gap is longer than fastchess's own timer. `chunk_14.tsv` has 500 scored games and was committed. The watcher wrote no log line between 14:37:47Z and 14:55:53Z; I committed chunk 13 myself at 14:51:51Z. The watcher then pushed chunks 14 and 15 and exited. I do not know why that log gap happened. `git log` contains all 15 chunk commits.

times: see stamps.txt

## git status --short and ls -la

These two outputs were captured after this file, RESULT.txt, and POOL.txt were written, and then appended. A later append of the outputs themselves changes this file's size from the `ls` line.

```
$ git status --short
 M forge-combo29/grok2/002/stamps.txt
?? config.json
?? forge-combo29/grok2/002/POOL.txt
?? forge-combo29/grok2/002/REPORT.md
?? forge-combo29/grok2/002/RESULT.txt
```

```
$ ls -la forge-combo29/grok2/002
total 2800
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:06 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:20 ..
-rw-r--r-- 1 ubuntu ubuntu   2224 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    333 Nov 20 13:25 B_honesty.meta
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 13:25 B_idname.txt
-rw-r--r-- 1 ubuntu ubuntu    233 Nov 20 13:33 book.sha256
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56327 Nov 20 14:23 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51339 Nov 20 14:23 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56339 Nov 20 14:28 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51584 Nov 20 14:28 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56899 Nov 20 14:33 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51528 Nov 20 14:33 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56246 Nov 20 14:38 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:38 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56320 Nov 20 14:53 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51462 Nov 20 14:53 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56282 Nov 20 14:59 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51507 Nov 20 14:59 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56749 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51152 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55763 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51118 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56234 Nov 20 13:48 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51198 Nov 20 13:48 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56032 Nov 20 13:53 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51357 Nov 20 13:53 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56515 Nov 20 13:58 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51387 Nov 20 13:58 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56345 Nov 20 14:03 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51536 Nov 20 14:03 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56130 Nov 20 14:08 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51494 Nov 20 14:08 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56339 Nov 20 14:13 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51439 Nov 20 14:13 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56111 Nov 20 14:18 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51333 Nov 20 14:18 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47054 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:33 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1103 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42371 Nov 20 13:31 half.tsv
-rwxr-xr-x 1 ubuntu ubuntu    965 Nov 20 13:24 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu    476 Nov 20 13:27 honesty_summary.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    801 Nov 20 13:26 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 314871 Nov 20 13:26 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    835 Nov 20 13:26 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 315261 Nov 20 13:26 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    834 Nov 20 13:26 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 316439 Nov 20 13:26 o_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   4468 Nov 20 13:24 orun.py
-rw-r--r-- 1 ubuntu ubuntu    407 Nov 20 13:27 orun_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:27 patch.sha256
-rw-r--r-- 1 ubuntu ubuntu    349 Nov 20 13:27 patch.stat
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    333 Nov 20 13:25 P_honesty.meta
-rw-r--r-- 1 ubuntu ubuntu   5223 Nov 20 13:25 P_idname.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:05 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   5782 Nov 20 15:06 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:20 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    874 Nov 20 15:06 stamps.txt
-rwxr-xr-x 1 ubuntu ubuntu   2797 Nov 20 13:24 summarize.py
```

# Seat 035, arm 5 (S10)

Arm 5, id S10. Source seat 081, branch `for-fable-and-opus/grok-081`, commit `b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa`. `git rev-parse FETCH_HEAD` printed that commit. Switch name `IdeaS10`.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed:

```
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  /home/ubuntu/arm.patch
```

That is the table sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree succeeded. `git diff --stat` then printed:

```
 forge-combo29/include/forge/eval.hpp   |   3 +
 forge-combo29/include/forge/search.hpp |  10 ++
 forge-combo29/src/eval.cpp             |  26 ++++++
 forge-combo29/src/search.cpp           | 163 +++++++++++++++++++++++++++++++--
 forge-combo29/src/uci.cpp              |  13 ++-
 5 files changed, 208 insertions(+), 7 deletions(-)
```

Build: `/usr/bin/c++` is Clang 18 and failed to link `libstdc++`. Both trees were configured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. The CPU has AVX-512 and BMI2, so `FORGE_PORTABLE` stayed off and `-march` stayed the CMake default `x86-64-v4`. Exe B is `/tmp/forge-b/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` (`honesty_B_bench11.meta`). Exe P is `/tmp/forge-p/forge`, sha256 `8430a8b654d504f7e69d11b1dc3daf73854fa5e2c9a477cc893c7eb1dddf80bc` (`o_P_on.txt.meta`). id name on both: `Chess Engine Forge 6.4.24 candidate`. No engine source and no binary was committed.

## Honesty numbers

`honesty_table.sh` reads the raw files. Its output `honesty_table.out`:

```
== honesty_B_bench11.txt
info string bench depth 11 nodes 312866 time 168 nps 1862297
== honesty_B_bench13.txt
info string bench depth 13 nodes 862329 time 431 nps 2000763
== honesty_B_bench16.txt
info string bench depth 16 nodes 3024920 time 1456 nps 2077554
== honesty_B_perft5.txt
nodes 4865609
== honesty_P_bench11.txt
info string bench depth 11 nodes 312866 time 169 nps 1851278
== honesty_P_bench13.txt
info string bench depth 13 nodes 862329 time 444 nps 1942182
== honesty_P_bench16.txt
info string bench depth 16 nodes 3024920 time 1992 nps 1518534
== honesty_P_perft5.txt
nodes 4865609
```

Table: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match. Each line was a fresh process with no setoption.

## Three O runs

`o_table.py` reads `o_B.txt`, `o_P_off.txt`, `o_P_on.txt`. Output `o_table.out`:

```
forge-combo29/grok2/035/o_B.txt sum 9500069 first 41311 24872 28574 differ_from_first 0
forge-combo29/grok2/035/o_P_off.txt sum 9500069 first 41311 24872 28574 differ_from_first 0
forge-combo29/grok2/035/o_P_on.txt sum 9542904 first 41311 24872 28574 differ_from_first 10
```

Against the table:

- (1) exe B: sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Match.
- (2) exe P, `IdeaS10` false: same 200 positions as (1). Match (`differ_from_first 0`).
- (3) exe P, `IdeaS10` true: sum 9,542,904, first three 41,311 / 24,872 / 28,574, 10 positions differ. Match.

Options sent are listed in the `.meta` files. Run (3) ends with `setoption name IdeaS10 value true`. Run (2) ends with `setoption name IdeaS10 value false`. No other IdeaS10 spin was sent.

## Book sha256

`book_sha.txt`:

```
uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd 2632036 lines 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine.epd 29245 lines
ctl.epd 300 ctl_arrive 10 ctl_half 200
```

Both hashes match the brief. Seat 035 takes every 90th line of the book starting at line 35. The first line of `~/mine.epd` is line 35 of `~/uho.epd`. The 22 chunks are the first 5500 lines of `mine.epd` (checked equal to those slices). They do not reach the last 300 lines used for the controls.

## C-ARRIVE and C-HALF

`arrive_check.txt` counts, from the trace log of `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`:

```
grep -c setoption name IdeaS10 value true: 20
grep -c unknown option|invalid value|No such option: 0
```

The same file has the 20 log lines around the first `setoption name IdeaS10 value true` (log line 542). `engine=true` was accepted.

C-HALF, re-read from `half.tsv` by `games_tsv.py pool FULL`:

```
side FULL: games 400 W-L-D 231-23-146 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 4, 39, 102, 55] Elo +200.24 95% [+176.63, +225.65]
```

FULL (20000 nodes) against HALF (10000 nodes), both with `IdeaS10` false. Elo +200.24 is above +20. Pass.

## POOL.txt and chunks

22 chunks, each `chunk_N.tsv` has 500 lines, 11000 games. Every termination field is `normal`. `POOL.txt` is the output of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/035/chunk_*.tsv`:

```
side ON: games 11000 W-L-D 2874-3002-5124 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [153, 1101, 3122, 969, 155] Elo -4.04 95% [-7.60, -0.49]
```

`play.sh` printed `minute 95: no new chunk` after chunk 22 and exited. No chunk was killed. No `FAILED` line in `~/play.log`.

## Suspicions, not proven

None. The 95% interval is entirely below 0 in this sample. That is the measured interval, not a claim about a cause.

## What I did NOT do

- Did not open a pull request.
- Did not change engine source, and did not commit an exe, a net, a PGN, or an object file.
- Did not fall back to arm 10. Run (3) matched.
- Did not send the extra IdeaS10 spin options. They stayed at the engine defaults.
- Did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. `fastchess` wrote `config.json` in the repository root because `play.sh` was started with that cwd. I did not commit it. In that file `resign`, `draw`, `maxmoves`, and `tb_adjudication` all have `enabled` false. All 11000 games are tagged `normal`.
- Did not repeat an opening. Chunks are disjoint slices of the top of `mine.epd`.
- The handoff branch had no `forge-combo29/soak_all/FABLE_TO_grok2_*.md` at step 1 or at any step 4 push, so there was no extra channel instruction and no `~/STOP_PLAY`.

## What I am NOT sure about

- I did not replay this morning's seat 030 PGN through `games_tsv.py`. The script text is the one in the brief. The known answer for that PGN was not re-checked here.
- One stamp line, `2026-11-20T14:12:44Z chunks 10 1 2 3 4 5 6 7 8 9`, lists numbers in lexical order. Later lines are numeric. The tsv files on disk are chunks 1 through 22.
- The `ls -la` below was captured and then pasted into this file, so the listed byte size of `REPORT.md` is the size before that paste. Every other name in that listing is the folder as committed.

## times: see stamps.txt

First stamp line: `2026-11-20T13:21:58Z STEP 1`. Chunk 22 finished `2026-11-20T14:58:34Z`. `play.sh` then stopped for minute 95.

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/035/stamps.txt
?? config.json
?? forge-combo29/grok2/035/POOL.txt
?? forge-combo29/grok2/035/REPORT.md
?? forge-combo29/grok2/035/RESULT.txt
?? forge-combo29/grok2/035/chunk_21.out
?? forge-combo29/grok2/035/chunk_21.tsv
?? forge-combo29/grok2/035/chunk_22.out
?? forge-combo29/grok2/035/chunk_22.tsv
```

```
$ ls -la forge-combo29/grok2/035
total 3468
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2236 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    264 Nov 20 13:27 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  55771 Nov 20 14:10 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51468 Nov 20 14:10 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56430 Nov 20 14:14 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51526 Nov 20 14:14 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55727 Nov 20 14:18 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51512 Nov 20 14:18 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56125 Nov 20 14:22 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51363 Nov 20 14:22 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56350 Nov 20 14:26 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51541 Nov 20 14:26 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56628 Nov 20 14:30 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51647 Nov 20 14:30 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56437 Nov 20 14:34 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51402 Nov 20 14:34 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56147 Nov 20 14:38 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 14:38 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56139 Nov 20 14:42 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51397 Nov 20 14:42 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56573 Nov 20 14:46 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51495 Nov 20 14:46 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56166 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51154 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55875 Nov 20 14:50 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 14:50 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56412 Nov 20 14:54 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51642 Nov 20 14:54 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56643 Nov 20 14:58 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51394 Nov 20 14:58 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56497 Nov 20 13:38 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51471 Nov 20 13:38 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56833 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56154 Nov 20 13:46 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51476 Nov 20 13:46 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56274 Nov 20 13:50 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51497 Nov 20 13:50 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56420 Nov 20 13:54 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51216 Nov 20 13:54 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56295 Nov 20 13:58 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51357 Nov 20 13:58 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56800 Nov 20 14:02 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:02 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56027 Nov 20 14:06 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51523 Nov 20 14:06 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47044 Nov 20 13:29 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1033 Nov 20 13:27 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42256 Nov 20 13:29 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    245 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    245 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    245 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    245 Nov 20 13:24 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    245 Nov 20 13:24 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    245 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    247 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1158 Nov 20 13:24 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu    596 Nov 20 13:26 honesty_table.out
-rwxr-xr-x 1 ubuntu ubuntu    346 Nov 20 13:26 honesty_table.sh
-rwxr-xr-x 1 ubuntu ubuntu   1017 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu 284513 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    842 Nov 20 13:25 o_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 284892 Nov 20 13:25 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    880 Nov 20 13:25 o_P_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 284924 Nov 20 13:25 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    878 Nov 20 13:25 o_P_on.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu   4331 Nov 20 13:24 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    272 Nov 20 13:26 o_table.out
-rwxr-xr-x 1 ubuntu ubuntu   1589 Nov 20 13:24 o_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 14:59 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6651 Nov 20 15:00 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1192 Nov 20 15:00 stamps.txt
```

# grok2 seat 038

Arm 8, K4b. Source seat 043, branch `for-fable-and-opus/grok-043`, commit `2f38a63656ec17062b581c933fcc77d961b946f1`. Switch `IdeaK4`. `IdeaK4_Shrink` was left at the patch default and was never sent.

## Patch sha256 and git apply

`git rev-parse FETCH_HEAD` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-043` printed `2f38a63656ec17062b581c933fcc77d961b946f1`.

```
sha256sum ~/arm.patch
b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
```

That is the arm 8 sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree exited 0. `git diff --stat` after apply:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 16 ++++++++++++++--
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 20 insertions(+), 2 deletions(-)
```

Release builds used CMake and g++ 13.3.0. The machine's `c++` is Clang 18 and its link test failed with `cannot find -lstdc++`, so both configures passed `-DCMAKE_CXX_COMPILER=g++`. `/proc/cpuinfo` has AVX-512 and BMI2, so `FORGE_PORTABLE` stayed off and `FORGE_MARCH` stayed the CMake default `x86-64-v4`. Exe B is `/tmp/forge-build/base/forge`. Exe P is `/tmp/forge-build/work/forge`. No build product was committed.

## Honesty

A fresh process for each line, `uci` then the command, no `setoption`. Output of `python3 forge-combo29/grok2/038/summarize.py`:

```
honesty B bench11 depth 11 nodes 312866
honesty B bench13 depth 13 nodes 862329
honesty B bench16 depth 16 nodes 3024920
honesty B perft5 nodes 4865609
honesty P bench11 depth 11 nodes 312866
honesty P bench13 depth 13 nodes 862329
honesty P bench16 depth 16 nodes 3024920
honesty P perft5 nodes 4865609
```

The known numbers are bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both executables match.

## Three O runs

Same script, against the arm table. Known exe B: sum 9500069, first three 41311 / 24872 / 28574. Known IdeaK4 on: sum 8983632, first three 23741 / 21846 / 35911, 200 differ.

```
o_B.txt: positions 200 sum 9500069 first 41311 / 24872 / 28574
o_P_off.txt: positions 200 sum 9500069 first 41311 / 24872 / 28574
o_P_on.txt: positions 200 sum 8983632 first 23741 / 21846 / 35911
off vs B differ 0
on vs B differ 200
```

Run (2) matches run (1) on all 200 positions. Run (3) matches the arm 8 row. The FEN file sha256 is `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. Seat 038 took every 90th line of `~/uho.epd` starting at line 38. The last 300 of that slice were held out for the controls. Chunk openings start at line 1 of `~/mine.epd`. The committed chunk opening files do not intersect `~/ctl.epd` (checked for the chunks that had already been sliced when that `comm` was run, chunks 1 to 4; later chunks are the following 250-line slices from the top, and 21 chunks use 5250 lines, while the reserved tail starts at line 28946 of 29245).

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`:

```
grep -c "setoption name IdeaK4 value true" ~/arrive.log
20
grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

The 20 log lines around the first `setoption name IdeaK4 value true` are in `arrive_check.txt`. Fastchess accepted `engine=true`.

C-HALF, output of `python3 ~/games_tsv.py pool FULL`:

```
side FULL: games 400 W-L-D 235-27-138 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 5, 39, 99, 57] Elo +200.24 95% [+176.01, +226.37]
```

FULL's Elo is +200.24, above +20. Passed on the first run.

## POOL.txt

21 chunks, 10500 games. Pasted `POOL.txt` (the stdout of `python3 ~/games_tsv.py pool ON` on `chunk_*.tsv`):

```
side ON: games 10500 W-L-D 2794-2793-4913 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [234, 1356, 2096, 1303, 261] Elo +0.03 95% [-4.38, +4.45]
```

Every chunk tsv has 500 lines. `play.log` has no FAILED line. Sides are 5250 `ON vs OFF` and 5250 `OFF vs ON`. Every result is `1-0`, `0-1`, or `1/2-1/2`. Plies: min 12, max 767, mean 146.156. `grep` of all `chunk_*.out` for adjudication, resign, maxmoves, syzygy, unknown option, invalid value, and "No such option" summed to 0.

## Suspicions, not proven

The PGN `Termination` header is `normal` on all 10500 games. Fastchess's own match log names mates and repetitions. I did not prove what that header would contain if a game had been adjudicated. The node-limit games are long (up to 767 plies) and the match logs do not contain the adjudication words above.

## What I did NOT do

I did not open a pull request. I did not commit an engine source file, an executable, a net, a PGN, or the book. I did not change the patch. I did not send `IdeaK4_Shrink`. I did not fall back to arm 10. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not repeat an opening. I did not force-push. A `config.json` written by fastchess into the repository during C-HALF (adjudication flags present and `enabled: false`) was deleted and not committed. Later matches were started from the home directory.

## What I am NOT sure about

I am not sure fastchess's compiled-in default, with no config file, is incapable of adjudication. The config it wrote had every adjudication switch disabled, and the match logs have none of those words. I did not read the fastchess source to prove the default. The 4-minute check, commit, push, and channel read were done by `~/watch_chunks.sh` (sleep 240, then the chunk list, then push) after chunk 4, because one shell command cannot cover the match. I read `~/watch.log` after it. No `FABLE_TO_grok2_*.md` existed on `handoff/fable-opus-combo29-all-20261114` at any of those fetches.

## times: see stamps.txt

`ls` of this folder was captured after this report and `RESULT.txt` existed and before the status text below was appended, so this file is longer in the commit than that listing's size for `REPORT.md`.


## git status --short

```
 M forge-combo29/grok2/038/stamps.txt
?? forge-combo29/grok2/038/POOL.txt
?? forge-combo29/grok2/038/REPORT.md
?? forge-combo29/grok2/038/RESULT.txt
```

## ls -la

```
total 3376
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2300 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56783 Nov 20 14:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56394 Nov 20 14:15 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51507 Nov 20 14:15 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56413 Nov 20 14:19 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51494 Nov 20 14:19 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56378 Nov 20 14:23 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51626 Nov 20 14:23 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56317 Nov 20 14:27 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51382 Nov 20 14:27 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56758 Nov 20 14:30 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51634 Nov 20 14:30 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56354 Nov 20 14:39 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51382 Nov 20 14:39 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56373 Nov 20 14:43 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51575 Nov 20 14:43 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56173 Nov 20 14:47 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51415 Nov 20 14:47 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56461 Nov 20 14:51 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51468 Nov 20 14:51 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56767 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51272 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56078 Nov 20 14:55 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51592 Nov 20 14:55 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  55761 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56093 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51232 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56241 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51416 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56230 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51311 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56071 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56249 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51417 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56301 Nov 20 13:58 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51379 Nov 20 13:58 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56085 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56684 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51458 Nov 20 14:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46875 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu    951 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42256 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:31 half_tsv_count.txt
-rw-r--r-- 1 ubuntu ubuntu   7661 Nov 20 13:26 harness.py
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5101 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    167 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5312 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1025 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    780 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281691 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    814 Nov 20 13:27 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281807 Nov 20 13:27 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    813 Nov 20 13:27 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 280698 Nov 20 13:27 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    790 Nov 20 13:27 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6187 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    864 Nov 20 15:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3154 Nov 20 13:25 summarize.py
-rw-r--r-- 1 ubuntu ubuntu    537 Nov 20 13:27 summary_step2.txt
```

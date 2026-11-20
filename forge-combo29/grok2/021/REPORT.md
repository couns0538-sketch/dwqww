# grok2 seat 021

## Arm and source

Arm 1, B1a. Source seat 030, branch `for-fable-and-opus/grok-030`, commit `416700fe0ace1656a1285fc536c347718c1a4af7`. `git rev-parse FETCH_HEAD` printed that commit. Switch name `IdeaB1`. `IdeaB1_Scale` and `IdeaB1_Fade` were left at the patch defaults and were never sent.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed:

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

That is the arm table sha256. In the work tree (`git apply --check` then `git apply`), the apply succeeded. `git -C /agent/repos/work diff --stat` printed:

```
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

Work tree HEAD stayed `6b98f2170a3210e71beed04bbd2553972c253ed7`. The patch is not committed.

Build: g++ 13.3.0, CMake Release, default `FORGE_MARCH=x86-64-v4`, `FORGE_PORTABLE` left off. `/proc/cpuinfo` has `avx512` and `bmi2`, so the portable flags were not added. `/usr/bin/c++` is Clang and failed to link `libstdc++`; both builds used `-DCMAKE_CXX_COMPILER=g++`. Exe B is `/agent/repos/base/forge-combo29/build/forge`. Exe P is `/agent/repos/work/forge-combo29/build/forge`. No engine binary or source file is in this commit.

## Honesty

`python3 forge-combo29/grok2/021/tables.py` reads the raw transcripts and printed:

```
honesty
  B bench11 312866 expect 312866 OK
  B bench13 862329 expect 862329 OK
  B bench16 3024920 expect 3024920 OK
  B perft5 4865609 expect 4865609 OK
  P bench11 312866 expect 312866 OK
  P bench13 862329 expect 862329 OK
  P bench16 3024920 expect 3024920 OK
  P perft5 4865609 expect 4865609 OK
```

Each line is one fresh process, command then `quit`, no `setoption`. Raw files: `honesty_B_*.txt` and `honesty_P_*.txt`, with a `.meta` beside each (exe path, sha256, id name `Chess Engine Forge 6.4.24 candidate`, no options).

## Three O runs

Same script, same run, against the arm table (sum 9,500,069 and first three 41,311 / 24,872 / 28,574 for B; switch off identical; switch on sum 10,081,213, first three 12,481 / 31,753 / 31,668, 200 differ):

```
B n 200 sum 9500069 first 41311 / 24872 / 28574
Poff n 200 sum 9500069 first 41311 / 24872 / 28574
Pon n 200 sum 10081213 first 12481 / 31753 / 31668
off_identical True
on_differ 200
```

S14 plus Threads 1 and Hash 16 were sent before every `go depth 12`, each followed by `isready` through `readyok`. Run (3) also sent `setoption name IdeaB1 value true`. Run (2) sent `value false`. No unknown-option stop. Rows are in `o_B.raw`, `o_Poff.raw`, `o_Pon.raw`.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 021 takes every 90th line starting at line 21 (`wc -l ~/mine.epd` = 29245). The last 300 lines were held back for the controls.

## C-ARRIVE and C-HALF

`arrive_check.txt` begins:

```
setoption name IdeaB1 value true count: 20
unknown/invalid/No such option count: 0
```

The trace log accepted `engine=true`. The 20 lines around the first `setoption name IdeaB1 value true` are in that file. Count 20 is at least 1. Refusal count is 0.

C-HALF, `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/021/half.tsv`:

```
side FULL: games 400 W-L-D 223-34-143 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 8, 49, 89, 54] Elo +178.33 95% [+153.73, +204.70]
```

FULL's Elo is above +20. All 400 half games and all 9000 match games have Termination `normal`.

## POOL.txt and chunks

18 chunks, each 500 games, 9000 games. `python3 ~/games_tsv.py pool ON forge-combo29/grok2/021/chunk_*.tsv` wrote `POOL.txt`:

```
side ON: games 9000 W-L-D 2380-2386-4234 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [213, 1100, 1856, 1142, 189] Elo -0.23 95% [-4.93, +4.46]
```

`play.sh` then printed `minute 95: no new chunk` and exited. No chunk was killed. No `FAILED` line in `~/play.log`. Openings came from the top of `~/mine.epd` and did not reach the held-back 300.

## Suspicions, not proven

The pooled interval crosses zero. I do not read -0.23 Elo as a loss or a gain. One seat's 9000 games is a wider interval than the swarm's +/- 2 Elo target. Fastchess printed a chunk-18 Elo near -12; that is one 500-game block, and the pool above is the result that was scored.

## What I did not do

I did not open a pull request. I did not add adjudication (`-draw`, `-resign`, `-maxmoves`, tablebases). I did not send the patch's extra spins. I did not commit an exe, a net, a PGN, or the book. I did not commit `config.json` in the repository root (fastchess wrote it because the match cwd was the repo; its resign, draw, and maxmoves `enabled` fields are false). I did not change any branch except `for-fable-and-opus/grok2-021`. No `FABLE_TO_grok2_<N>.md` file was on the handoff branch at any fetch.

## What I am not sure about

I am not sure fastchess never reads `./config.json` even when the command line is explicit. The file's adjudication switches are off, and every scored game's Termination is `normal`, which is the check I have. I am not sure the 20-line arrive window is the window a reader would have sliced; the two counts are the pass condition, and the setoption line is inside the slice.

## Times

times: see stamps.txt

## git status --short and ls -la

These were pasted from the commands run after this report and `RESULT.txt` existed, before the STEP 5 commit.

```
 M forge-combo29/grok2/021/stamps.txt
?? config.json
?? forge-combo29/grok2/021/POOL.txt
?? forge-combo29/grok2/021/REPORT.md
?? forge-combo29/grok2/021/RESULT.txt
?? forge-combo29/grok2/021/chunk_18.out
?? forge-combo29/grok2/021/chunk_18.tsv
```

```
total 3104
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2235 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56181 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56649 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51593 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56376 Nov 20 14:30 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 14:30 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56252 Nov 20 14:35 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51417 Nov 20 14:35 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55841 Nov 20 14:39 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51380 Nov 20 14:39 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56562 Nov 20 14:44 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51606 Nov 20 14:44 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56339 Nov 20 14:49 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51595 Nov 20 14:49 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56383 Nov 20 14:54 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51551 Nov 20 14:54 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56400 Nov 20 14:59 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51433 Nov 20 14:59 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56282 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51269 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56687 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51447 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55736 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51301 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56682 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51380 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56072 Nov 20 13:56 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51451 Nov 20 13:56 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56398 Nov 20 14:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 14:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56253 Nov 20 14:06 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51353 Nov 20 14:06 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56549 Nov 20 14:11 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51341 Nov 20 14:11 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56091 Nov 20 14:16 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51331 Nov 20 14:16 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46897 Nov 20 13:31 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1040 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42246 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:26 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:26 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:26 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    205 Nov 20 13:26 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    205 Nov 20 13:26 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   2687 Nov 20 13:25 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 307314 Nov 20 13:26 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu    827 Nov 20 13:26 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 309128 Nov 20 13:26 o_Poff.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_Poff.rows
-rw-r--r-- 1 ubuntu ubuntu    826 Nov 20 13:26 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 310095 Nov 20 13:26 o_Pon.raw
-rw-r--r-- 1 ubuntu ubuntu   1898 Nov 20 13:26 o_Pon.rows
-rw-r--r-- 1 ubuntu ubuntu   5256 Nov 20 13:26 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5933 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    745 Nov 20 15:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1870 Nov 20 13:27 tables.py
```

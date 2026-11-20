# Seat 066, arm 6, S32

Arm 6, source seat 074, branch `for-fable-and-opus/grok-074`, commit `0fd01685b0465c11e29816b5a759e6496d2a69ae`. Switch `IdeaS32`. Model Grok 4.7. `git rev-parse FETCH_HEAD` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-074` printed that commit.

## Patch

`sha256sum ~/arm.patch` printed:

```
18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch
```

That is the table value. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree succeeded. The diff stat was `search.hpp` 6 lines, `search.cpp` 30 lines, `uci.cpp` 5 lines: 3 files, 40 insertions, 1 deletion. `IdeaS32_OwedSlack` stayed at its default. It was never sent.

## Builds

`/usr/bin/c++` is Clang 18.1.3 and its link failed with `cannot find -lstdc++`. The brief asks for g++ (GCC 13 or newer) and GCC's own C++ library. Both trees were configured with `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (g++ 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` has `avx512f` and `bmi2`, so `FORGE_PORTABLE` stayed off and `-march` stayed the CMake default `x86-64-v4`.

exe B: `/home/ubuntu/build-B/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, id name `Chess Engine Forge 6.4.24 candidate`.

exe P: `/home/ubuntu/build-P/forge`, sha256 `8d1e0952373d4776ee703ec0fa5d741e25e659efface288aa5bed0169302f428`, same id name. It advertises `option name IdeaS32 type check default false`.

## Honesty

A fresh process for each line, no setoption. Pasted from `python3 forge-combo29/grok2/066/summarize.py forge-combo29/grok2/066`:

```
honesty
B bench11 nodes 312866 expected 312866 ok
B bench13 nodes 862329 expected 862329 ok
B bench16 nodes 3024920 expected 3024920 ok
B perft5 nodes 4865609 expected 4865609 ok
P bench11 nodes 312866 expected 312866 ok
P bench13 nodes 862329 expected 862329 ok
P bench16 nodes 3024920 expected 3024920 ok
P perft5 nodes 4865609 expected 4865609 ok
```

## The three O runs

Positions: `for-fable-and-opus/kimi5-work`, `forge-combo29/tests_kimi5_job3/first200.fens`, 200 lines, sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`. S14, then Threads 1, Hash 16. Run 2 also sent `IdeaS32 false`. Run 3 sent `IdeaS32 true`. Same summarize.py stdout:

```
orun
o1_B positions 200 missing 0 sum 9500069 first 41311 24872 28574
o2_Poff positions 200 missing 0 sum 9500069 first 41311 24872 28574
o3_Pon positions 200 missing 0 sum 9547450 first 41442 24989 28711
o2_vs_o1 differ 0
o3_vs_o1 differ 200
o3 expected sum 9547450 first 41442 24989 28711 differ 200
o3_ok true
```

Against the table: run 1 is 9,500,069 and 41,311 / 24,872 / 28,574. Run 2 matches run 1 on all 200 positions. Run 3 is 9,547,450 and 41,442 / 24,989 / 28,711, and 200 positions differ. `on_ok` is yes.

## Book

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
wc -l ~/mine.epd ~/ctl.epd ~/ctl_arrive.epd ~/ctl_half.epd
  29245 /home/ubuntu/mine.epd
    300 /home/ubuntu/ctl.epd
     10 /home/ubuntu/ctl_arrive.epd
    200 /home/ubuntu/ctl_half.epd
  29755 total
```

Both book hashes match. Seat 066 takes every 90th line of the book starting at line 66. Chunks 1 to 21 use lines 1 to 5250 of `~/mine.epd`. The reserved 300 lines start at line 28946.

## C-ARRIVE

`bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` exited 0 and printed `Finished match`. `engine=true` was accepted. From `arrive_check.txt`:

```
grep -c "setoption name IdeaS32 value true" ~/arrive.log
20
grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

The same file has the 20 log lines around the first `setoption name IdeaS32 value true` (engine ON, value true).

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok2/066/half.tsv` printed:

```
side FULL: games 400 W-L-D 230-29-141 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 5, 49, 86, 60] Elo +192.01 95% [+167.03, +218.93]
```

FULL's Elo is +192.01, above +20. Passed.

## Pool

21 chunks, 500 games each, 10500 games. No chunk output contains `adjudicat`. Every opening in the tsv files is in exactly two games. `python3 ~/games_tsv.py pool ON forge-combo29/grok2/066/chunk_*.tsv` printed `POOL.txt`:

```
side ON: games 10500 W-L-D 2824-2876-4800 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [288, 1253, 2163, 1315, 231] Elo -1.72 95% [-6.14, +2.70]
```

## Suspicions, not proven

At 1000 games the same script printed Elo -18.08 with the interval under zero. At 10500 games it is -1.72 with the interval crossing zero. That is the sample moving. I did not find a second fault that would explain the early number: no adjudication line, no control-book opening, no fen outside a pair, and the node-limit control passed.

## What I did not do

I did not open a pull request. I did not change engine source and I did not commit an engine binary, a net, a pgn, or a bytecode file (one `__pycache__` file was committed by mistake in the step 2 commit and removed in the next commit). I did not send `IdeaS32_OwedSlack`. I did not fall back to arm 10. I did not adjudicate, and I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not replay an opening. I did not play the reserved last 300 lines of `~/mine.epd`. I did not commit `config.json`.

## What I am not sure about

The first harness called `select` on a Python text pipe and waited out with no line. A throwaway script using the same `Popen` flags did receive `id name`. The transcripts in this folder were read by a thread on the byte pipe, and those transcripts match the known node counts. I do not know why that `select` missed the data.

fastchess, started with this repository as its current directory, wrote `config.json` here. In that file `resign`, `draw`, `maxmoves`, and `tb_adjudication` are all `enabled: false`. I did not prove that a later process never reread the file. Every chunk's command line sets the same options, and none of the 21 chunk logs contains `adjudicat`.

## Times

times: see stamps.txt

## Status and listing

Captured after `POOL.txt`, `REPORT.md`, and `RESULT.txt` were written, and after the step 5 stamp line, before the commit of those files.

```
$ git status --short
 M forge-combo29/grok2/066/stamps.txt
?? config.json
?? forge-combo29/grok2/066/POOL.txt
?? forge-combo29/grok2/066/REPORT.md
?? forge-combo29/grok2/066/RESULT.txt

$ ls -la forge-combo29/grok2/066
total 3356
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2256 Nov 20 13:33 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    461 Nov 20 13:36 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56279 Nov 20 14:16 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51492 Nov 20 14:16 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56009 Nov 20 14:20 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51359 Nov 20 14:20 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56329 Nov 20 14:24 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51440 Nov 20 14:24 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56174 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51392 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55968 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51356 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56280 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51652 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56786 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51529 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56048 Nov 20 14:45 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:45 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56561 Nov 20 14:49 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51667 Nov 20 14:49 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56183 Nov 20 14:53 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51506 Nov 20 14:53 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55717 Nov 20 13:40 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51149 Nov 20 13:40 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56315 Nov 20 14:57 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51539 Nov 20 14:57 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56264 Nov 20 15:01 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51447 Nov 20 15:01 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  55975 Nov 20 13:44 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51254 Nov 20 13:44 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 13:48 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51300 Nov 20 13:48 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56158 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51316 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56340 Nov 20 13:56 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51419 Nov 20 13:56 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56335 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56059 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51364 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56332 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51343 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56170 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51431 Nov 20 14:12 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:26 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:33 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46878 Nov 20 13:35 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:35 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:33 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42169 Nov 20 13:35 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   7557 Nov 20 13:30 harness.py
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:30 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:30 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:30 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:30 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:30 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:30 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:30 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:30 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:30 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:30 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:30 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:30 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:30 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:30 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:30 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:30 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1025 Nov 20 13:33 match.sh
-rw-r--r-- 1 ubuntu ubuntu    867 Nov 20 13:30 o1_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281778 Nov 20 13:30 o1_B.txt
-rw-r--r-- 1 ubuntu ubuntu    903 Nov 20 13:31 o2_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 281859 Nov 20 13:31 o2_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    901 Nov 20 13:31 o3_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 281889 Nov 20 13:31 o3_Pon.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:33 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6645 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    869 Nov 20 15:05 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3606 Nov 20 13:26 summarize.py
-rw-r--r-- 1 ubuntu ubuntu    663 Nov 20 13:31 summarize_step2.txt
```

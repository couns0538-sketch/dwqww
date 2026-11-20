# REPORT seat 012 arm 2

## Arm and the source seat

Seat 012, arm 2 (B1b). Source seat 080, branch `for-fable-and-opus/grok-080`, commit `e778c1358711c0571e8f5cc4df87083cce98e03a`. Switch `IdeaB1`. The known on-run is sum 9748678, first three 17841 / 25977 / 43905, 200 positions differ from exe B.

`git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-080` printed that commit.

## Patch sha256 and git apply

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. The work tree diff after apply:

```
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

The patch is not committed. No engine source is in this branch.

## Honesty numbers

Expected on exe B and exe P, each command a fresh process, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Output of `python3 forge-combo29/grok2/012/read_honesty.py` (reads the raw `honesty_*.txt` files):

```
honesty_B_bench11.txt nodes 312866
honesty_B_bench13.txt nodes 862329
honesty_B_bench16.txt nodes 3024920
honesty_B_perft5.txt nodes 4865609
honesty_P_bench11.txt nodes 312866
honesty_P_bench13.txt nodes 862329
honesty_P_bench16.txt nodes 3024920
honesty_P_perft5.txt nodes 4865609
```

All eight match. Builds used CMake Release and `/usr/bin/g++` (GCC 13.3.0). The default `c++` is Clang 18 and failed to link `libstdc++`, so it was not used. `lscpu` showed AVX-512 and BMI2, so the build did not pass `FORGE_PORTABLE` or a lower `-march`.

## The three O runs

S14 in the brief's order, then Threads 1, then Hash 16. Run (1) exe B, switch omitted (the base engine has no IdeaB1). Run (2) exe P, IdeaB1 false. Run (3) exe P, IdeaB1 true. Depth 12, ucinewgame and isready before every position, isready after every setoption.

Output of `python3 forge-combo29/grok2/012/read_o.py` on the raw files:

```
forge-combo29/grok2/012/o_B.txt: positions 200 sum 9500069 first 41311 / 24872 / 28574
forge-combo29/grok2/012/o_Poff.txt: positions 200 sum 9500069 first 41311 / 24872 / 28574
  differ_from_first 0 length_mismatch 0
forge-combo29/grok2/012/o_Pon.txt: positions 200 sum 9748678 first 17841 / 25977 / 43905
  differ_from_first 200 length_mismatch 0
```

Run (1) matches the known base sum and first three. Run (2) matches run (1) on all 200 positions. Run (3) matches the arm table: sum 9748678, first three 17841 / 25977 / 43905, 200 differ.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. Seat 012 took every 90th line starting at line 12: 29245 lines in `~/mine.epd`. The last 300 are the controls and were not used as match openings.

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt` (counts from the trace log):

```
setoption name IdeaB1 value true: 20
unknown option|invalid value|No such option: 0
```

The first switch setoption is in that file, with the surrounding log lines. fastchess accepted `engine=true`.

C-HALF, output of `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/012/half.tsv`:

```
side FULL: games 400 W-L-D 226-35-139 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 55, 77, 61] Elo +180.58 95% [+154.60, +208.55]
```

FULL (20000 nodes) against HALF (10000 nodes) is +180.58, above +20. Pass. 400 games, 200 pairs, no opening outside exactly two games.

## POOL.txt and the number of chunks

17 chunks, each 500 games, 8500 games. Each chunk's fastchess log contains `Finished match`. `play.log` has no `FAILED` line. `play.sh` stopped itself with `minute 95: no new chunk` after chunk 17 (logged 2026-11-20T14:58:43Z).

`POOL.txt`, which is the stdout of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/012/chunk_*.tsv`:

```
side ON: games 8500 W-L-D 2290-2256-3954 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [206, 1002, 1779, 1078, 185] Elo +1.39 95% [-3.45, +6.23]
```

## suspicions, not proven

The point estimate is about +1.4 Elo for IdeaB1 on against off, at 20000 nodes, one thread. The 95% interval from the pair scores runs from -3.45 to +6.23 and includes negative values. That is not a demonstrated gain. I did not look for a subset of openings or a termination type that would move the estimate.

The patched engine also advertises `IdeaB1_Fade`, `IdeaB1_Scale`, and `IdeaB1_Cap`. They were left at default and were never sent. I did not measure what those knobs do.

## what I did NOT do

I did not open a pull request. I did not commit an engine binary, a net, a PGN, or any engine source. I did not change engine code; the given patch was applied only in the work tree. I did not send any option other than S14, Threads, Hash, OwnBook false (in the matches), and IdeaB1. I did not adjudicate games. I did not repeat an opening. I did not fall back to arm 10. I did not build with `FORGE_PORTABLE`. No `FABLE_TO_grok2_<N>.md` file was on the handoff branch at step 1 or at the later fetches, so no channel instruction was applied. An untracked `config.json` sat at the repository root; I did not create it for this seat and I did not add it.

## what I am NOT sure about

I am not sure the morning games left `IdeaB1_Fade`, `IdeaB1_Scale`, and `IdeaB1_Cap` at the defaults this binary advertises. The brief says every other option stays at its default, and the depth-12 node counts matched the table with only IdeaB1 changed, so the on-run is the build that produced those counts.

I am not sure a longer match would keep the sign of the +1.39 Elo. The interval still covers zero.

The option order for the O runs was the S14 list, then Threads 1, then Hash 16, then the switch. The node counts matched. I did not try another order.

## times: see stamps.txt

The clock starts at the first line of `stamps.txt`. The listing of that file, `git status --short`, and `ls -la` of this folder are pasted below from the commands that produced them. Those two listings were captured after this body, `POOL.txt`, and `RESULT.txt` were written, and then concatenated onto this file, so the size of `REPORT.md` in the listing is the size before the paste.

```
$ cat forge-combo29/grok2/012/stamps.txt
2026-11-20T13:21:49Z STEP 1
2026-11-20T13:25:43Z STEP 2
2026-11-20T13:31:03Z STEP 3
2026-11-20T13:40:00Z chunks 1
2026-11-20T13:44:23Z chunks 2
2026-11-20T13:48:40Z chunks 3
2026-11-20T13:52:55Z chunks 4 
2026-11-20T14:01:15Z chunks 5 
2026-11-20T14:05:27Z chunks 6 
2026-11-20T14:09:35Z chunks 7 
2026-11-20T14:12:43Z chunks 8 
2026-11-20T14:18:00Z chunks 9 
2026-11-20T14:23:17Z chunks 10 
2026-11-20T14:28:34Z chunks 11 
2026-11-20T14:33:52Z chunks 12 
2026-11-20T14:39:09Z chunks 13 
2026-11-20T14:43:41Z chunks 14 
2026-11-20T14:48:58Z chunks 15 
2026-11-20T14:54:15Z chunks 16 
2026-11-20T14:58:47Z chunks 17 
2026-11-20T14:59:36Z STEP 5 reader
2026-11-20T15:01:07Z STEP 5
```

```
$ git status --short
 M forge-combo29/grok2/012/stamps.txt
?? config.json
?? forge-combo29/grok2/012/POOL.txt
?? forge-combo29/grok2/012/REPORT.md
?? forge-combo29/grok2/012/RESULT.txt
```

```
$ ls -la forge-combo29/grok2/012
total 2900
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2193 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56220 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56396 Nov 20 14:28 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51519 Nov 20 14:28 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56667 Nov 20 14:33 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 14:33 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56877 Nov 20 14:38 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51653 Nov 20 14:38 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56130 Nov 20 14:43 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51538 Nov 20 14:43 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56122 Nov 20 14:48 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51451 Nov 20 14:48 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56594 Nov 20 14:53 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51489 Nov 20 14:53 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56888 Nov 20 14:58 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51495 Nov 20 14:58 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56588 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51228 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55811 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51200 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56410 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  55914 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51383 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56244 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51424 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55775 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51236 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56700 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51454 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56383 Nov 20 14:12 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51449 Nov 20 14:12 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56356 Nov 20 14:17 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51401 Nov 20 14:17 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46910 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu  42314 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:24 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:24 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:24 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281886 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    837 Nov 20 13:25 o_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282088 Nov 20 13:25 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    871 Nov 20 13:25 o_Poff.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 283270 Nov 20 13:25 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu    870 Nov 20 13:25 o_Pon.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3998 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 14:59 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    374 Nov 20 14:59 read_honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1525 Nov 20 13:25 read_o.py
-rw-r--r-- 1 ubuntu ubuntu   7643 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     74 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    679 Nov 20 15:01 stamps.txt
```

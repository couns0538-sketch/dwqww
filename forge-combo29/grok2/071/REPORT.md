# Seat 071, arm 1 (B1a)

Arm 1, source seat 030, branch `for-fable-and-opus/grok-030`, commit `416700fe0ace1656a1285fc536c347718c1a4af7`, switch `IdeaB1`. exe P is the base commit `6b98f2170a3210e71beed04bbd2553972c253ed7` plus that patch. exe B is the base commit with no patch.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed the arm's sha256. `git apply --check` then `git apply` on the work tree printed nothing and left this stat:

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

The same text is in `patch_apply.txt`. The patch file was not committed.

Build: GCC 13.3.0 (`CMAKE_CXX_COMPILER=g++`). `/usr/bin/c++` is Clang 18 and failed to link `libstdc++`, so it was not used. The CPU has AVX-512 and BMI2, so `FORGE_PORTABLE` stayed off and `FORGE_MARCH` stayed `x86-64-v4`. No engine source and no binary was committed.

## Honesty numbers

`report_tables.py` read the raw transcripts:

```
B_bench11 312866
B_bench13 862329
B_bench16 3024920
B_perft5 nodes 4865609
P_bench11 312866
P_bench13 862329
P_bench16 3024920
P_perft5 nodes 4865609
```

Those are the known pins (bench 11 / 13 / 16 and `go perft 5`) for both exes. Each line was a fresh process with no `setoption`. The `.meta` files name the exe, its sha256, and the `id name` line.

## The three O runs

Same script, from `O1.rows`, `O2.rows`, `O3.rows`:

```
O1 positions 200 sum 9500069 first 41311 24872 28574
O2 positions 200 sum 9500069 first 41311 24872 28574
O3 positions 200 sum 10081213 first 12481 31753 31668
O2 equal to O1 on 200 of 200 positions
O3 differs from O1 on 200 of 200 positions
```

Against the arm table: run (1) sum 9,500,069 and first three 41,311 / 24,872 / 28,574; run (2) equal on all 200; run (3) sum 10,081,213, first three 12,481 / 31,753 / 31,668, 200 differ. All of those held. Options in the `.meta` files are Threads 1, Hash 16, the S14 list in the brief's order, and for O2/O3 `setoption name IdeaB1 value false` or `true`. `IdeaB1_Scale` and `IdeaB1_Fade` were not sent.

## Book

```
uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd lines 2632036 sha 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine.epd lines 29245
```

Both sha256 values match the brief. Seat 071 took every 90th line of `uho.epd` starting at line 71. The last 300 of those lines were the controls and were not used by the chunks.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): `setoption name IdeaB1 value true` count 20, and `unknown option|invalid value|No such option` count 0. The 20 log lines around the first switch setoption are in that file. The engine line is `ON <--- setoption name IdeaB1 value true`. `value false` was also sent 20 times. The 20-game PGN carried FEN headers and finished with mates, repetitions, or insufficient material.

C-HALF, output of `games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 230-26-144 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 39, 97, 57] Elo +195.51 95% [+170.79, +222.18]
```

FULL's Elo is above +20. Pass.

## POOL.txt and chunks

19 chunks, 500 games each, 9500 games. `games_tsv.py pool ON` wrote `POOL.txt`:

```
side ON: games 9500 W-L-D 2551-2543-4406 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [234, 1208, 1872, 1188, 248] Elo +0.29 95% [-4.42, +5.01]
```

Each `chunk_*.out` contains one `Finished match` line. A search for `adjudicat` in those files is 0 on every chunk. No draw, resign, max-move, or tablebase adjudication was passed to fastchess.

## suspicions, not proven

The first copy of `o_run.py` tested `" nodes "` against `line.split()`, which cannot succeed, and it stopped on position 1. The depth-12 info line already in that partial transcript was 41311 nodes, the known first position. The parser was changed to look for the token `nodes`, and the three O runs were re-run. The committed rows are from that second run. I did not keep the partial transcript.

fastchess, run from the repository directory for C-HALF, wrote an untracked `config.json` there. Its adjudication flags were disabled. I deleted that file and did not commit it. Later matches were started from the home directory.

The commit watcher sometimes left a gap of a few minutes between log lines, then resumed and pushed the chunk that had finished. I did not see a rejected push. I do not know why those gaps happened.

## what I did NOT do

I did not open a pull request. I did not change engine source, and I did not invent a new patch. I did not send `IdeaB1_Scale` or `IdeaB1_Fade`. I did not play arm 10. I did not repeat an opening to get more games. I did not commit a PGN, an executable, a net, or an object file. I did not force-push, and I did not write any branch except `for-fable-and-opus/grok2-071`.

## what I am NOT sure about

I am not sure the option order in the matches equals the O-run order. fastchess sends `IdeaB1` from the `-engine` line before Hash and the S14 options. The O runs sent Threads, Hash, S14, then `IdeaB1`. Both orders delivered every option (the arrive log and the O `.meta` files). The known node counts were reproduced with the O-run order.

I am not sure a different compiler would have reproduced the pins. This g++ build did.

The Elo interval from 9500 games is about +/- 5. The point estimate is +0.29. The interval covers zero and also a few Elo either way. That is the script's interval, not a claim that the switch is zero.

## times: see stamps.txt

```
2026-11-20T13:23:21Z STEP 1 seat
2026-11-20T13:29:22Z STEP 2 builds and known numbers
2026-11-20T13:34:04Z STEP 3 controls
2026-11-20T13:39:05Z chunks 1
2026-11-20T13:43:25Z chunks 2
2026-11-20T13:47:50Z chunks 3
2026-11-20T13:52:06Z chunks 4
2026-11-20T13:56:27Z chunks 5
2026-11-20T14:00:46Z chunks 6
2026-11-20T14:05:13Z chunks 7
2026-11-20T14:09:37Z chunks 8
2026-11-20T14:12:36Z chunks 9
2026-11-20T14:17:18Z chunks 10
2026-11-20T14:21:20Z chunks 11
2026-11-20T14:26:02Z chunks 12
2026-11-20T14:30:04Z chunks 13
2026-11-20T14:34:07Z chunks 14
2026-11-20T14:41:45Z chunks 15
2026-11-20T14:45:47Z chunks 16
2026-11-20T14:49:50Z chunks 17
2026-11-20T14:58:44Z chunks 18
2026-11-20T15:02:47Z chunks 19
2026-11-20T15:04:54Z STEP 5 pool report
```

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/071/stamps.txt
?? forge-combo29/grok2/071/POOL.txt
?? forge-combo29/grok2/071/REPORT.md
?? forge-combo29/grok2/071/RESULT.txt
?? forge-combo29/grok2/071/report_tables.py

$ ls -la forge-combo29/grok2/071
total 3148
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2212 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:26 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:26 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:26 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    229 Nov 20 13:34 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:26 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56582 Nov 20 14:16 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51443 Nov 20 14:16 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56250 Nov 20 14:21 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:21 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56291 Nov 20 14:25 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 14:25 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56178 Nov 20 14:29 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51388 Nov 20 14:29 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56345 Nov 20 14:33 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51605 Nov 20 14:33 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56324 Nov 20 14:41 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51383 Nov 20 14:41 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56234 Nov 20 14:45 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51595 Nov 20 14:45 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56495 Nov 20 14:49 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51540 Nov 20 14:49 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55965 Nov 20 14:54 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51452 Nov 20 14:54 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56264 Nov 20 15:02 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 15:02 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55969 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51165 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56195 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51358 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56186 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51390 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56218 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51400 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56068 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51425 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56655 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51588 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56352 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56079 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51309 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56001 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:12 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu    907 Nov 20 13:29 compare_o.py
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47018 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:34 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1014 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42519 Nov 20 13:34 half.tsv
-rwxr-xr-x 1 ubuntu ubuntu    783 Nov 20 13:26 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:28 O1.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 O1.rows
-rw-r--r-- 1 ubuntu ubuntu 282034 Nov 20 13:28 O1.txt
-rw-r--r-- 1 ubuntu ubuntu    827 Nov 20 13:28 O2.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 O2.rows
-rw-r--r-- 1 ubuntu ubuntu 282109 Nov 20 13:28 O2.txt
-rw-r--r-- 1 ubuntu ubuntu    826 Nov 20 13:28 O3.meta
-rw-r--r-- 1 ubuntu ubuntu   1898 Nov 20 13:28 O3.rows
-rw-r--r-- 1 ubuntu ubuntu 283095 Nov 20 13:28 O3.txt
-rwxr-xr-x 1 ubuntu ubuntu   4538 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    727 Nov 20 13:29 patch_apply.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:28 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:28 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:28 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:28 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:28 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:28 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:28 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   6815 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   1560 Nov 20 15:04 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    743 Nov 20 15:04 stamps.txt
```

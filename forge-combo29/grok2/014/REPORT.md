# grok2 seat 014

Arm 4, B8b. Source seat 028. Branch `for-fable-and-opus/grok-028`, commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. Switch `IdeaB8`. The base engine is commit `6b98f2170a3210e71beed04bbd2553972c253ed7`.

## Patch

`sha256sum ~/arm.patch` printed:

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

That is the arm 4 sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree both exited 0. The work tree still shows:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

`IdeaB8_Weight` and `IdeaB8_Swing` were left at their defaults. They were never sent.

The machine has AVX-512 and BMI2 (`avx512f`, `bmi2` in `/proc/cpuinfo`) and `g++` is GCC 13.3.0, so the release build used the CMake defaults (`FORGE_PORTABLE` off, `-march=x86-64-v4`). Exe B is `/agent/repos/base/forge-combo29/build/forge`. Exe P is `/agent/repos/work/forge-combo29/build/forge`.

## Honesty

`tables.py` reads the raw honesty files. Its output:

```
HONESTY
B bench11 nodes 312866 expected 312866 match True
B bench13 nodes 862329 expected 862329 match True
B bench16 nodes 3024920 expected 3024920 match True
B perft5 nodes 4865609 expected 4865609 match True
P bench11 nodes 312866 expected 312866 match True
P bench13 nodes 862329 expected 862329 match True
P bench16 nodes 3024920 expected 3024920 match True
P perft5 nodes 4865609 expected 4865609 match True
```

## The three O runs

Same script, same run, continued:

```
O RUNS
B positions 200 sum 9500069 expected 9500069 match True
B first3 41311 24872 28574 expected 41311 24872 28574 match True
Poff positions 200 sum 9500069 expected 9500069 match True
Poff first3 41311 24872 28574 expected 41311 24872 28574 match True
Poff identical to B True positions 200
Pon positions 200 sum 9718009 expected 9718009 match True
Pon first3 17283 17878 31115 expected 17283 17878 31115 match True
Pon differ 200 expected 200 match True
```

Against the arm table: exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Switch false matches exe B on all 200 positions. Switch true sum 9,718,009, first three 17,283 / 17,878 / 31,115, 200 positions differ.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

`wc -l ~/uho.epd` printed 2632036. Both hashes match the brief. Seat 014 took every 90th line starting at line 14 (`~/mine.epd`, 29245 lines). The last 300 lines were held back for the controls. The 20 chunks used lines 1 to 5000 of `mine.epd`.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`), two counts:

```
setoption name IdeaB8 value true: 20
unknown option|invalid value|No such option: 0
```

The 20 log lines around the first switch setoption are in that file. fastchess accepted `engine=true`.

C-HALF, `games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 240-32-128 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 4, 48, 80, 67] Elo +200.24 95% [+173.71, +229.07]
```

fastchess printed `Elo: 200.24 +/- 27.68` for the same match. FULL is above +20. Pass.

## Pool and chunks

20 chunks, each 500 games (`wc -l` on `chunk_*.tsv` is 500 for every file, 10000 total). `POOL.txt` is the pasted output of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/014/chunk_*.tsv`:

```
side ON: games 10000 W-L-D 2855-2537-4608 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [227, 1099, 2064, 1349, 261] Elo +11.05 95% [+6.54, +15.57]
```

Every opening FEN is in exactly two games. Every termination field in the tsv files is `normal`. A search of the chunk logs for adjudication, resign, maxmoves, syzygy, unknown option, and invalid value found no hits. Chunk 20 finished at 14:57:44Z, after minute 95 and before minute 103. play.sh then printed `minute 95: no new chunk` and exited. No chunk was killed.

## Suspicions, not proven

The running Elo of ON was about +20 after 1500 games and about +11 after 10000. That drop is what a noisy early sample does. I have no other explanation, and I do not have one.

## What I did NOT do

I did not open a pull request. I did not commit engine source, the patch, an executable, a net, or a PGN. I did not send any option except Threads, Hash, the S14 list, and `IdeaB8`. I did not turn on adjudication. I did not replay an opening to get more games. I did not switch to arm 10. No `FABLE_TO_grok2_<N>.md` file was on the handoff branch at any fetch I made (last fetched handoff commit `bcfdf4b5ecd5a0e2844a9160514c2b05cf5872c0`). I did not add `config.json`, which fastchess wrote in the repository root during C-HALF.

## What I am NOT sure about

I am not sure the tsv word `normal` is fastchess's name for every finished game. The match logs do name mates, fifty-move draws, and threefold draws, and the logs have no adjudication words. I am not sure this script's Elo interval matches another pentanomial calculator to the last hundredth. On C-HALF it matched fastchess's own Elo figure of 200.24. A watcher (`~/commit_chunks.sh`) committed and pushed finished chunks about every 200 seconds and fetched the channel on each push. I am sure those pushes contain the chunk files play.sh wrote. I am not sure a channel file that appeared and disappeared inside one 200 second gap would have been seen. None was present at the fetches.

## times: see stamps.txt

The first stamp is `2026-11-20T13:21:24Z STEP 1`. Minute 95 is 95 minutes after that line.

## git status --short

```
 M forge-combo29/grok2/014/stamps.txt
?? config.json
?? forge-combo29/grok2/014/POOL.txt
?? forge-combo29/grok2/014/REPORT.md
?? forge-combo29/grok2/014/RESULT.txt
```

## ls -la

```
total 3316
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2204 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56005 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51502 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56178 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51424 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56469 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51319 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56232 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51475 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56239 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51498 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56513 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51428 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56150 Nov 20 14:40 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51399 Nov 20 14:40 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56221 Nov 20 14:45 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:45 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55968 Nov 20 14:49 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51410 Nov 20 14:49 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  55859 Nov 20 14:53 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:53 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56500 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51311 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56512 Nov 20 14:57 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51563 Nov 20 14:57 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56409 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51290 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56221 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51463 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56292 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51264 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56210 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51422 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55969 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51290 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51500 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56925 Nov 20 14:06 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51574 Nov 20 14:06 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56018 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 14:11 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:32 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46578 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1077 Nov 20 13:32 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42291 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    218 Nov 20 13:26 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    218 Nov 20 13:26 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    218 Nov 20 13:26 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    220 Nov 20 13:26 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    218 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    218 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    218 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    220 Nov 20 13:26 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1999 Nov 20 13:26 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:32 match.sh
-rw-r--r-- 1 ubuntu ubuntu    896 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308825 Nov 20 13:27 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    937 Nov 20 13:27 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 309036 Nov 20 13:27 o_Poff.raw
-rw-r--r-- 1 ubuntu ubuntu    936 Nov 20 13:27 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 309620 Nov 20 13:27 o_Pon.raw
-rw-r--r-- 1 ubuntu ubuntu   6103 Nov 20 13:26 o_run.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:32 play.sh
-rw-r--r-- 1 ubuntu ubuntu    156 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5923 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    228 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1158 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    872 Nov 20 13:28 step2_table.txt
-rw-r--r-- 1 ubuntu ubuntu   3125 Nov 20 13:26 tables.py
```

# grok2 seat 005

Arm 5, S10. Source seat 081. Branch `for-fable-and-opus/grok-081`, commit `b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa` (`git rev-parse FETCH_HEAD` printed that). Switch `IdeaS10`. `id` in RESULT.txt is `S10`, the name on that arm's row.

## Patch

`sha256sum ~/arm.patch` printed:

```
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. The applied diff was 5 files, 208 insertions, 7 deletions. Patch status: ok.

Build decision: `/usr/bin/c++` is Clang 18 and CMake's compiler test failed with `cannot find -lstdc++`. The brief asks for g++ (GCC 13 or newer) and GCC's own C++ library. Both engines were configured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0) and `-DCMAKE_BUILD_TYPE=Release`. `/proc/cpuinfo` contains `avx512f`, `avx512bw`, `avx512cd`, `avx512dq`, `avx512vl`, and `bmi2`, so `FORGE_PORTABLE` was left off and `-march` stayed the CMake default `x86-64-v4`. Exe B is `/home/ubuntu/builds/base/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`. Exe P is `/home/ubuntu/builds/work/forge` sha256 `8430a8b654d504f7e69d11b1dc3daf73854fa5e2c9a477cc893c7eb1dddf80bc`. Both say `id name Chess Engine Forge 6.4.24 candidate`.

## Honesty

`python3 otable.py honesty` on the raw files printed:

```
forge-combo29/grok2/005/honesty_B_bench11.txt 312866
forge-combo29/grok2/005/honesty_B_bench13.txt 862329
forge-combo29/grok2/005/honesty_B_bench16.txt 3024920
forge-combo29/grok2/005/honesty_B_goperft5.txt 4865609
forge-combo29/grok2/005/honesty_P_bench11.txt 312866
forge-combo29/grok2/005/honesty_P_bench13.txt 862329
forge-combo29/grok2/005/honesty_P_bench16.txt 3024920
forge-combo29/grok2/005/honesty_P_goperft5.txt 4865609
```

Those are the known numbers on exe B and exe P: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609. Honesty: ok.

## O runs

`python3 otable.py oruns o_B.txt o_off.txt o_on.txt` printed:

```
positions B 200 off 200 on 200
B sum 9500069 first 41311 24872 28574
off sum 9500069 first 41311 24872 28574 differ 0
on sum 9542904 first 41311 24872 28574 differ 10
```

Against the table: (1) sum 9,500,069 and first three 41,311 / 24,872 / 28,574. (2) equal to (1) on all 200 positions. (3) arm 5's on-sum 9,542,904, the same first three, and 10 positions differ. All three matched. `on_ok=yes`. `off_identical=yes`.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both sha256 values match the brief. Book: ok. Seat 005 took every 90th line starting at line 5 (29,245 lines). The last 300 became `ctl.epd` (10 arrive, 200 half). I then deleted those 300 lines from `mine.epd` (left 28,945). Reason: `play.sh` does not stop before the reserved lines, and this machine finishes a chunk in about four minutes, so an untrimmed file would have reached them. Chunks 1-20 use lines 1-5000 of that file, which are the same lines as the original cut. The reserved openings were not played.

## C-ARRIVE and C-HALF

`arrive_check.txt` counts:

```
grep -c "setoption name IdeaS10 value true" ~/arrive.log
20
grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

Arrive: ok. The 20 log lines around the first switch setoption are in `arrive_check.txt`. The engine line is `ON <--- setoption name IdeaS10 value true`.

`python3 games_tsv.py pool FULL half.tsv` printed:

```
side FULL: games 400 W-L-D 231-27-142 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 44, 87, 62] Elo +195.51 95% [+169.84, +223.28]
```

FULL's Elo is +195.51, above +20. C-HALF passed. `half_elo=+195.51`.

## Pool

20 chunks, each 500 lines, 10,000 games. `python3 games_tsv.py pool ON chunk_*.tsv` wrote POOL.txt:

```
side ON: games 10000 W-L-D 2646-2740-4614 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [165, 1009, 2737, 933, 156] Elo -3.27 95% [-7.13, +0.60]
```

## suspicions, not proven

fastchess sent the match options in a different order from `orun.py`. The arrive trace shows `Threads` and `IdeaS10` going out before `LmrQuietBase`. None of those options was refused. I did not measure whether that order changes node counts relative to the O-run order. The games are the games that were played.

## what I did NOT do

No pull request. No new engine source and no edited engine source in the seat branch. The patch's other options (`IdeaS10_Margin`, `IdeaS10_Flat`, `IdeaS10_Look`, `IdeaS10_Shrink`, `IdeaS10_Depth`) were left at their defaults and were never sent. No adjudication, no draw rule, no resign rule, no max-move cutoff, no tablebases. Arm 10 was not played, because run (3) matched. No force-push and no push to any branch except `for-fable-and-opus/grok2-005`. The handoff branch had no `FABLE_TO_grok2_<N>.md`, so there was no channel instruction. `git config user.name` was already set, so I did not change it.

## what I am NOT sure about

RESULT.txt `id=S10` is the arm-row name. The template does not define `id` beyond that, so that choice is mine.

I am not sure fastchess's `nodes=20000` is the same cutoff the morning games used, beyond what C-HALF shows: the side named FULL, given 20000 nodes, beat the side named HALF, given 10000, by +195.51 Elo.

Commit `e70d7ba00` stored an empty `chunk_8.tsv` because the checker ran while `games_tsv.py` had just created the file. Commit `1651d2ba8` replaced it with the finished file. The file in HEAD has 500 lines (`wc -l`). The pool used that file.

## times: see stamps.txt

The first stamp is `2026-11-20T13:21:15Z STEP 1`. Chunk 20 finished at `2026-11-20T14:58:50Z`. `play.sh` then printed `minute 95: no new chunk`.

## git status --short and ls -la

The listing below was captured after POOL.txt, RESULT.txt, REPORT.md, and the STEP 5 stamp existed, and before this listing was appended. Appending this listing is the only later edit to REPORT.md.

```
$ git status --short
 M forge-combo29/grok2/005/stamps.txt
?? config.json
?? forge-combo29/grok2/005/POOL.txt
?? forge-combo29/grok2/005/REPORT.md
?? forge-combo29/grok2/005/RESULT.txt

$ ls -la
total 3260
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2244 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56195 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51628 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55625 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51287 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55685 Nov 20 14:24 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 14:24 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56514 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51626 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56254 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51593 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56286 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  55858 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56421 Nov 20 14:46 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51445 Nov 20 14:46 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56243 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51566 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56398 Nov 20 14:54 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51531 Nov 20 14:54 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56759 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51327 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56245 Nov 20 14:58 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:58 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56294 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51292 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56578 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51266 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56496 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51330 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56031 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56416 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  55950 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51435 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56079 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51375 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56087 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 14:11 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46919 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    963 Nov 20 13:32 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42289 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:25 honesty_B_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:25 honesty_B_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5342 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5342 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5344 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:25 honesty_P_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5555 Nov 20 13:25 honesty_P_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4111 Nov 20 13:25 honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1029 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu    844 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281609 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    879 Nov 20 13:26 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281981 Nov 20 13:26 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    878 Nov 20 13:26 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282045 Nov 20 13:26 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4922 Nov 20 13:25 orun.py
-rw-r--r-- 1 ubuntu ubuntu   2449 Nov 20 13:25 otable.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:05 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6098 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    757 Nov 20 15:05 stamps.txt
```

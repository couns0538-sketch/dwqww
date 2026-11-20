# Seat 041 arm 1 (B1a)

Arm 1, id B1a, source seat 030, commit 416700fe0ace1656a1285fc536c347718c1a4af7, switch IdeaB1. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-030` printed that commit. Model line in SEAT.txt: Grok 4.7.

## Patch

sha256 of `~/arm.patch` (the file `git show FETCH_HEAD:forge-combo29/grok/030/idea.patch.txt` wrote):

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check` then `git apply` in the work tree both exited 0. The work tree diff is still that patch: `search.hpp` +3, `search.cpp` +67, `uci.cpp` 6 lines changed, 3 files, 74 insertions, 2 deletions. No engine file was committed.

## Builds

Both trees are commit 6b98f2170a3210e71beed04bbd2553972c253ed7. Release CMake with `CMAKE_CXX_COMPILER=g++` (g++ 13.3.0). The machine has AVX-512 and BMI2, so the build used the default march (x86-64-v4) and left FORGE_PORTABLE off. The plain `c++` on this machine is Clang and cannot link libstdc++; that configure was discarded and not used.

exe B: `/agent/repos/base/build/forge`
exe P: `/agent/repos/work/build/forge`

`O_P_on.meta` records exe P, sha256 `5f3d519f607b83522b46ba8c36fed568493633fc81efe405dee930b4707eb30a`, `id name Chess Engine Forge 6.4.24 candidate`, and IdeaB1 true after the S14 list.

## Honesty

Fresh process per line, no setoption. Grep of the raw files:

```
B_bench11.txt: info string bench depth 11 nodes 312866
B_bench13.txt: info string bench depth 13 nodes 862329
B_bench16.txt: info string bench depth 16 nodes 3024920
B_perft5.txt:  nodes 4865609
P_bench11.txt: info string bench depth 11 nodes 312866
P_bench13.txt: info string bench depth 13 nodes 862329
P_bench16.txt: info string bench depth 16 nodes 3024920
P_perft5.txt:  nodes 4865609
```

These are the four required counts on both executables.

## Three O runs

`summarize_o.py` on the raw transcripts (`O_summary.txt`):

```
O_B.raw.txt        positions 200  sum 9500069  first 41311 / 24872 / 28574  differ_from_first 0
O_P_off.raw.txt    positions 200  sum 9500069  first 41311 / 24872 / 28574  differ_from_first 0
O_P_on.raw.txt     positions 200  sum 10081213 first 12481 / 31753 / 31668  differ_from_first 200
```

Against the arm table: exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Switch false matches exe B on all 200 positions. Switch true sum 10,081,213, first three 12,481 / 31,753 / 31,668, 200 positions differ. S14, Threads 1 and Hash 16 were sent before every position. A text-mode Python pipe stalled (both sides blocked in read). The runs that produced these files use unbuffered binary pipes. The counts are the table's counts.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 lines
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both sha256 values are the ones in the brief. Seat 041 takes every 90th line starting at line 41. `~/mine.epd` has 29245 lines. The last 300 are the controls and were not used as chunk openings.

## C-ARRIVE

`arrive_check.txt`: `setoption name IdeaB1 value true` count 20, and `unknown option|invalid value|No such option` count 0. The 20 log lines around the first hit show fastchess sending `setoption name IdeaB1 value true` to the engine named ON, then Hash 16, OwnBook false, and LmrQuietBase 93. No refusal. The trace flag `engine=true` was accepted.

## C-HALF

`games_tsv.py pool FULL` on `half.tsv` (400 games, 200 pairs, 0 openings not in exactly 2 games):

```
side FULL: games 400 W-L-D 242-32-126 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 5, 44, 87, 64] Elo +202.63 95% [+177.07, +230.34]
```

FULL's Elo is +202.63, above +20. Twice the nodes won. Fastchess's own line for the same match was Elo 202.63, Wins 242, Losses 32, Draws 126.

## Pool

17 chunks, each 500 games, 8500 games. `play.out` ends with `minute 95: no new chunk` after chunk 17. Chunk 17 was started after chunk 16 finished at 14:56:02Z (minute 94) and finished at 15:00:19Z (minute 98), before minute 103. No chunk was killed. `play.log` has 17 `done` lines and no `FAILED`.

`POOL.txt`, pasted from `python3 ~/games_tsv.py pool ON` on `chunk_*.tsv`:

```
side ON: games 8500 W-L-D 2307-2277-3916 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [212, 1023, 1750, 1053, 212] Elo +1.23 95% [-3.69, +6.15]
```

## Suspicions, not proven

The +1.23 Elo point is inside an interval that also contains 0. That is the measured interval. I am not calling it a gain.

`games_tsv.py` stores the PGN Termination header. On the half sample the header is `normal` while fastchess's live log names mate, repetition, fifty-move draws and insufficient material. The Result field is what the pool scores, and the half W-L-D matches fastchess's printed 242-32-126. I did not read all 8500 termination headers.

## What I did not do

No pull request. No engine source committed. No adjudication flags (`-draw`, `-resign`, `-maxmoves`) and no tablebases. IdeaB1_Scale and IdeaB1_Fade were left at their defaults and were not sent. Arm 10 was not played. The reserved last 300 openings were not used as chunks. No `FABLE_TO_grok2_*.md` file was on the handoff branch at any fetch, so nothing from the channel changed the run. I did not replay the morning seat 030 PGN through `games_tsv.py`.

## What I am not sure about

From chunk 10 onward, a background script did the 4-minute check, `git add` of `chunk_*`, commit, push, and channel read, because a long series of identical waits was interrupted. The script's log and `git log` show chunks 10 through 17 pushed. I did not watch those pushes as they happened.

I am not sure the fastchess log's word `normal` never hides a cutoff. The command line had no adjudication options, and the arrive games that I looked at ended by the rules of chess.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/041/stamps.txt
?? config.json
?? forge-combo29/grok2/041/POOL.txt
?? forge-combo29/grok2/041/REPORT.md
?? forge-combo29/grok2/041/RESULT.txt
```

## ls -la

```
total 2988
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2242 Nov 20 13:45 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:24 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:24 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:24 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    182 Nov 20 13:24 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56303 Nov 20 14:29 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 14:29 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56789 Nov 20 14:33 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51511 Nov 20 14:33 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56334 Nov 20 14:38 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51489 Nov 20 14:38 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56297 Nov 20 14:42 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51438 Nov 20 14:42 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56087 Nov 20 14:47 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51399 Nov 20 14:47 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56258 Nov 20 14:51 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51469 Nov 20 14:51 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56019 Nov 20 14:56 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51353 Nov 20 14:56 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56245 Nov 20 15:00 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51338 Nov 20 15:00 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56061 Nov 20 13:49 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51294 Nov 20 13:49 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55758 Nov 20 13:54 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51138 Nov 20 13:54 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56105 Nov 20 13:58 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51336 Nov 20 13:58 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56538 Nov 20 14:03 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 14:03 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56611 Nov 20 14:07 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 14:07 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55831 Nov 20 14:11 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 14:11 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56216 Nov 20 14:16 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51479 Nov 20 14:16 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56214 Nov 20 14:20 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51536 Nov 20 14:20 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56247 Nov 20 14:24 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51446 Nov 20 14:24 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:45 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46620 Nov 20 13:45 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1032 Nov 20 13:45 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42052 Nov 20 13:45 half.tsv
-rwxr-xr-x 1 ubuntu ubuntu    713 Nov 20 13:24 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1027 Nov 20 13:45 match.sh
-rw-r--r-- 1 ubuntu ubuntu    878 Nov 20 13:40 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu 307455 Nov 20 13:40 O_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    912 Nov 20 13:40 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309110 Nov 20 13:40 O_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    911 Nov 20 13:40 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 310157 Nov 20 13:40 O_P_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   4882 Nov 20 13:39 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    343 Nov 20 13:40 O_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:24 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:24 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:24 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:45 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    182 Nov 20 13:24 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   6155 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    635 Nov 20 15:02 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1589 Nov 20 13:26 summarize_o.py
```

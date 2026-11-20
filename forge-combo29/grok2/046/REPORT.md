# grok2 seat 046

Arm 6, S32. Source seat 074. Branch `for-fable-and-opus/grok-074`, commit `0fd01685b0465c11e29816b5a759e6496d2a69ae`. SWITCH `IdeaS32`. `IdeaS32_OwedSlack` was left at its default and was never sent.

## Patch

`sha256sum ~/arm.patch` printed `18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5`, the arm table value. In `/agent/repos/work`, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both exited 0. `git diff --stat` after apply: `search.hpp` 6 insertions, `search.cpp` 30 lines changed, `uci.cpp` 5 insertions.

## Honesty

Fresh process, no setoption. Both exe B (`/agent/repos/base/forge-combo29/build/forge`) and exe P (`/agent/repos/work/forge-combo29/build/forge`) printed:

- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609

Built with CMake, `CMAKE_CXX_COMPILER=g++` (GCC 13.3.0). `/usr/bin/c++` is Clang 18 and failed to link libstdc++. The CPU has AVX-512 and BMI2, so `FORGE_PORTABLE` was left off. Nothing of either build was committed.

## O runs

`o_sum.py` on the raw transcripts:

```
forge-combo29/grok2/046/o1_B.raw.txt: n 200 sum 9500069 first 41311 / 24872 / 28574
forge-combo29/grok2/046/o2_Poff.raw.txt: n 200 sum 9500069 first 41311 / 24872 / 28574
forge-combo29/grok2/046/o3_Pon.raw.txt: n 200 sum 9547450 first 41442 / 24989 / 28711
differ forge-combo29/grok2/046/o2_Poff.raw.txt vs forge-combo29/grok2/046/o1_B.raw.txt: 0
differ forge-combo29/grok2/046/o3_Pon.raw.txt vs forge-combo29/grok2/046/o1_B.raw.txt: 200
```

Arm table: exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574; switch off equal on all 200; switch on sum 9,547,450, first three 41,442 / 24,989 / 28,711, 200 differ. The three runs match that table.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both sha256 values match the brief. Seat 046 takes book line 46 and every 90th line after it: 29245 lines in `~/mine.epd`. The last 300 are the controls and were not used by the chunks.

## C-ARRIVE

`arrive_check.txt`: `setoption name IdeaS32 value true` count 20; `unknown option|invalid value|No such option` count 0. The 20 lines around the first switch setoption are in that file. A later count of `setoption name <option> value` in `~/arrive.log` was 40 for each of IdeaS32, Threads, Hash, OwnBook, and every S14 name (both engines, 20 games).

## C-HALF

`games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 243-25-132 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 4, 40, 90, 66] Elo +212.37 95% [+186.81, +240.15]
```

FULL's Elo is +212.37, above +20.

## Pool

14 chunks, 500 games each. `games_tsv.py pool ON` on `chunk_*.tsv`, pasted from `POOL.txt`:

```
side ON: games 7000 W-L-D 1821-1905-3274 pairs 3500 (openings not in exactly 2 games: 0)
ptnml [143, 891, 1525, 789, 152] Elo -4.17 95% [-9.37, +1.03]
```

Termination field of every chunk row (`term_counts.txt`):

```
   7000 normal
   1592 0-1
   2134 1-0
   3274 1/2-1/2
```

## Suspicions, not proven

`play.log` has chunk 11 at 14:13:31Z and chunk 12 at 14:53:03Z. Around 14:52Z, chunk 12 was already on game 483 of 500 and the six `forge` processes had an elapsed time of 3:46. I did not prove whether the machine clock paused in that gap. Chunk 12 still ended with "Finished match" and 500 scored games, so it counts.

fastchess wrote `config.json` in the repository root at 15:01Z. I moved it to `~/fastchess-config.json` and did not commit it. I did not determine whether that file can change a match. The match command did not pass `-resign`, `-draw`, or `-maxmoves`, and all 7000 terminations are `normal`.

## What I did not do

I did not open a pull request. I did not commit an engine source file, an executable, a net, or a PGN. I did not play arm 10. I did not send `IdeaS32_OwedSlack`. I did not repeat an opening. No `FABLE_TO_grok2_<N>.md` was on `handoff/fable-opus-combo29-all-20261114` at any fetch I made (fetched again at each chunk push). `git user.name` was already set, so I did not change it.

From the chunk-8 push onward, the 4-minute commit and channel check ran as `~/commit_watch.sh` in a tmux session, the same add/commit/push and handoff fetch as the earlier checks. That session exited after the chunk-14 push.

## What I am not sure about

I am not sure the wall-clock gap above was a pause rather than a stall inside fastchess. I am not sure fastchess sends the S14 options in the written order; the arrive log shows them sent, and the counts of unknown-option lines are 0.

## Times

times: see stamps.txt

## git status --short and ls -la

The two pastes below were taken after this file and `RESULT.txt` were written, and they are the last lines of this file.


```
$ git status --short
 M forge-combo29/grok2/046/stamps.txt
?? forge-combo29/grok2/046/POOL.txt
?? forge-combo29/grok2/046/REPORT.md
?? forge-combo29/grok2/046/RESULT.txt
?? forge-combo29/grok2/046/term_counts.txt

$ ls -la forge-combo29/grok2/046
total 2612
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2103 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    457 Nov 20 13:30 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56472 Nov 20 14:09 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51528 Nov 20 14:09 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56293 Nov 20 14:13 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51511 Nov 20 14:13 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56216 Nov 20 14:53 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51153 Nov 20 14:53 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56864 Nov 20 14:57 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51463 Nov 20 14:57 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56241 Nov 20 15:01 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 15:01 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56525 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55958 Nov 20 13:38 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51266 Nov 20 13:38 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56268 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51350 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56107 Nov 20 13:46 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 13:46 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56600 Nov 20 13:50 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 13:50 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56529 Nov 20 13:54 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 13:54 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56135 Nov 20 13:58 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51334 Nov 20 13:58 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56270 Nov 20 14:02 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:02 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56889 Nov 20 14:05 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 14:05 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:23 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46797 Nov 20 13:30 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:27 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42254 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4941 Nov 20 13:25 honesty_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:25 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5049 Nov 20 13:25 honesty_P_uci.txt
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281788 Nov 20 13:25 o1_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 13:25 o1_B.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 281867 Nov 20 13:25 o2_Poff.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    831 Nov 20 13:25 o2_Poff.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 281827 Nov 20 13:25 o3_Pon.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 13:25 o3_Pon.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3603 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1519 Nov 20 13:24 o_sum.py
-rw-r--r-- 1 ubuntu ubuntu    438 Nov 20 13:25 o_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5128 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    789 Nov 20 15:04 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    129 Nov 20 15:04 term_counts.txt
```

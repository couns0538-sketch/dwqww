# grok2 seat 064

Arm 4, B8b, source seat 028, branch `for-fable-and-opus/grok-028`, commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. SWITCH `IdeaB8`. Model Grok 4.7.

## Patch

`sha256sum ~/arm.patch` printed:

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

That is the arm 4 sha256. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-028` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree exited 0. The diff stat was `search.hpp`, `search.cpp`, `uci.cpp`, 3 files, 173 insertions, 4 deletions.

## Builds

GCC 13.3.0, and the CPU advertises BMI2 and AVX-512, so the builds did not pass `FORGE_PORTABLE`. CMake's default `c++` is Clang 18.1.3 and its configure failed with `cannot find -lstdc++`. The brief asks for g++ and GCC's own C++ library, so both trees were configured with `-DCMAKE_CXX_COMPILER=g++`. Exe B is `/agent/repos/base/forge-combo29/build/forge`. Exe P is `/agent/repos/work/forge-combo29/build/forge`.

## Honesty

`python3 forge-combo29/grok2/064/summarize.py forge-combo29/grok2/064` printed:

```
honesty
B bench11 312866 expected 312866 ok
B bench13 862329 expected 862329 ok
B bench16 3024920 expected 3024920 ok
B perft5 4865609 expected 4865609 ok
P bench11 312866 expected 312866 ok
P bench13 862329 expected 862329 ok
P bench16 3024920 expected 3024920 ok
P perft5 4865609 expected 4865609 ok
o1 positions 200 sum 9500069 first 41311 24872 28574
o1 expected sum 9500069 first 41311 24872 28574
o2 positions 200 sum 9500069 first 41311 24872 28574 differ_from_o1 0
o3 positions 200 sum 9718009 first 17283 17878 31115 differ_from_o1 200
o3 expected sum 9718009 first 17283 17878 31115 differ 200
o1_match True
o2_match True
o3_match True
```

Raw files: `honesty_B_*.txt`, `honesty_P_*.txt`, and their `.meta` files. No setoption was sent on those processes.

## Three O runs

Same script output, against the arm 4 row (sum 9,718,009; first three 17,283 / 17,878 / 31,115; 200 differ) and the plain row (sum 9,500,069; first three 41,311 / 24,872 / 28,574):

- (1) exe B: sum 9500069, first three 41311 24872 28574. Matches.
- (2) exe P, `IdeaB8 false`: same 200 node counts as (1). `o2_off.txt.meta` contains `setoption name IdeaB8 value false`.
- (3) exe P, `IdeaB8 true`: sum 9718009, first three 17283 17878 31115, 200 differ. Matches. `o3_on.txt.meta` contains `setoption name IdeaB8 value true`. `IdeaB8_Weight` and `IdeaB8_Swing` were not sent.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 064 took every 90th line of `uho.epd` starting at line 64: 29245 lines in `~/mine.epd`. The last 300 are the controls. Chunks used the top. 17 chunks use 4250 openings.

## C-ARRIVE

`arrive_check.txt` records the two counts and 20 log lines around the first switch setoption:

```
grep -c setoption name IdeaB8 value true
20
grep -c -E unknown option|invalid value|No such option
0
```

The trace line is `ON <--- setoption name IdeaB8 value true`. fastchess accepted `engine=true`.

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok2/064/half.tsv` printed:

```
side FULL: games 400 W-L-D 222-31-147 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 8, 51, 83, 58] Elo +180.58 95% [+155.29, +207.75]
```

FULL (20000 nodes) against HALF (10000 nodes), both with `IdeaB8 false`. Elo +180.58 is above +20. The final line in `half.out` is `Elo: 180.58 +/- 26.23`.

## Pool

17 chunks, 8500 games. `POOL.txt` is the pasted output of `python3 ~/games_tsv.py pool ON forge-combo29/grok2/064/chunk_*.tsv`:

```
side ON: games 8500 W-L-D 2451-2084-3965 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [164, 978, 1697, 1149, 262] Elo +15.01 95% [+10.07, +19.96]
```

The Termination column of every chunk tsv is `normal` (8500 of 8500). `match.sh` passes no `-draw`, `-resign`, `-maxmoves`, and no tablebase flag.

## Suspicions, not proven

The first O-run harness treated the first `bestmove` as the answer to every later position, so that transcript was not a 200-position measurement. Position 1 of that bad file was 41311 nodes. The harness was fixed and the three runs were repeated. The files in this folder are the repeat, and they match the table. I am not treating the discarded transcript as a result.

I counted `normal` in the tsv and I read mates, threefold, and the fifty-move rule in `arrive.out` and `half.out`. I did not re-read all 8500 PGN headers. The PGNs were not committed.

## What I did not do

No pull request. No engine source committed and no engine source edited by me; the patch is the given file. No exe, object file, net file, or PGN committed. `IdeaB8_Weight` and `IdeaB8_Swing` were not sent. Arm 10 was not played. No opening was repeated. No chunk was killed: chunk 17 finished at 15:00:28Z, and minute 103 was 15:05:50Z. The channel fetch never found a `FABLE_TO_grok2_*.md`.

## What I am not sure about

fastchess sent `Threads`, `IdeaB8`, `Hash`, and `OwnBook` before the S14 spin options. I am not sure that order is the same as sending the S14 list first. The values are the ones in `match.sh`, and C-ARRIVE showed no unknown option and no invalid value.

`id=B8b` in RESULT.txt is the name on arm row 4. The template says `id=<ID>` and does not define another identifier.

## Decisions

A background loop committed each finished chunk about every 4 minutes and fetched the handoff branch on each of those pushes, so a cut-off chat would lose at most the chunk still being played. fastchess wrote an untracked `config.json` in the repository root because the match was started from that directory. Its resign, draw, maxmoves, and tablebase switches are `enabled: false`. That file is not part of the result and was not added.

times: see stamps.txt

## git status --short and ls -la

The two blocks below were captured after this report, `POOL.txt`, `RESULT.txt`, and the STEP 5 stamps line were written, and before the STEP 5 commit.

```
$ git status --short
 M forge-combo29/grok2/064/stamps.txt
?? config.json
?? forge-combo29/grok2/064/POOL.txt
?? forge-combo29/grok2/064/REPORT.md
?? forge-combo29/grok2/064/RESULT.txt

$ ls -la forge-combo29/grok2/064
total 2928
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2244 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56236 Nov 20 14:24 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51494 Nov 20 14:24 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56033 Nov 20 14:30 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:30 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56488 Nov 20 14:35 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51524 Nov 20 14:35 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56290 Nov 20 14:40 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 14:40 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56154 Nov 20 14:45 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51506 Nov 20 14:45 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56493 Nov 20 14:50 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51448 Nov 20 14:50 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56017 Nov 20 14:55 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51428 Nov 20 14:55 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56482 Nov 20 15:00 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51531 Nov 20 15:00 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56386 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51283 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56336 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51425 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56532 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51223 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  55962 Nov 20 13:54 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51250 Nov 20 13:54 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56190 Nov 20 13:59 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 13:59 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56241 Nov 20 14:04 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51358 Nov 20 14:04 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56251 Nov 20 14:09 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51521 Nov 20 14:09 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56281 Nov 20 14:14 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51283 Nov 20 14:14 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56080 Nov 20 14:19 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 14:19 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47011 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu  42179 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   7816 Nov 20 13:27 harness.py
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5164 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5375 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 13:27 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281937 Nov 20 13:28 o1_B.txt
-rw-r--r-- 1 ubuntu ubuntu    784 Nov 20 13:28 o1_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282248 Nov 20 13:28 o2_off.txt
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:28 o2_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282898 Nov 20 13:28 o3_on.txt
-rw-r--r-- 1 ubuntu ubuntu    817 Nov 20 13:28 o3_on.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6426 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    602 Nov 20 15:04 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3733 Nov 20 13:27 summarize.py
```

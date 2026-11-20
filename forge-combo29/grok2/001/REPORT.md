# grok2 seat 001

Arm 1, B1a. Source seat 030, branch for-fable-and-opus/grok-030, commit 416700fe0ace1656a1285fc536c347718c1a4af7. Model in SEAT.txt: Grok 4.7.

## Patch

sha256 of ~/arm.patch, which is `git show FETCH_HEAD:forge-combo29/grok/030/idea.patch.txt`:

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

That is the table sha256. `git apply --check` then `git apply` in the work tree both succeeded. `git diff --stat` there:

```
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

SWITCH is IdeaB1. IdeaB1_Scale and IdeaB1_Fade were left at the patch defaults and were never sent.

## Builds

Both trees are commit 6b98f2170a3210e71beed04bbd2553972c253ed7. Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. The CPU has AVX-512 and BMI2, so the CMake default stands: FORGE_MARCH x86-64-v4, FORGE_PORTABLE off. The first configure used /usr/bin/c++ (Clang 18) and failed with `cannot find -lstdc++`. The exes that were measured were configured with `-DCMAKE_CXX_COMPILER=g++`.

exe B: /agent/repos/base/forge-combo29/build/forge
exe P: /agent/repos/work/forge-combo29/build/forge

## Honesty

Fresh process per line, no setoption. Perft was `position startpos` then `go perft 5`. Pasted from the raw files:

exe B:

```
info string bench depth 11 nodes 312866 time 310 nps 1009245
info string bench depth 13 nodes 862329 time 712 nps 1211136
info string bench depth 16 nodes 3024920 time 1564 nps 1934092
nodes 4865609
```

exe P:

```
info string bench depth 11 nodes 312866 time 346 nps 904236
info string bench depth 13 nodes 862329 time 896 nps 962420
info string bench depth 16 nodes 3024920 time 2141 nps 1412853
nodes 4865609
```

Those are the required pins: 312866, 862329, 3024920, 4865609.

## Three O runs

S14 in the listed order, then Threads 1, then Hash 16. Run (2) adds IdeaB1 false. Run (3) adds IdeaB1 true. ucinewgame and isready before every position, isready after every setoption, go depth 12. Pasted output of summarize_o.py reading the raw transcripts (o_table.txt):

```
positions 200 sum 9500069 first 41311 24872 28574
/agent/repos/dwqww/forge-combo29/grok2/001/o_P_off.txt positions 200 sum 9500069 first 41311 24872 28574 differ 0
/agent/repos/dwqww/forge-combo29/grok2/001/o_P_on.txt positions 200 sum 10081213 first 12481 31753 31668 differ 200
```

Against the table: (1) sum 9,500,069 and first three 41,311 / 24,872 / 28,574. (2) equal on all 200. (3) sum 10,081,213, first three 12,481 / 31,753 / 31,668, 200 differ. All three match.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both match the brief. Seat 001 takes every 90th line starting at line 1. The last 300 lines of mine.epd were the controls. Chunks used the top of mine.epd and stopped at chunk 22 (5500 openings), short of those 300.

## C-ARRIVE

`grep -c "setoption name IdeaB1 value true"` on ~/arrive.log printed 20. `grep -c -E "unknown option|invalid value|No such option"` printed 0. The 20 surrounding log lines are in arrive_check.txt. fastchess accepted `engine=true`.

## C-HALF

Pasted output of `python3 games_tsv.py pool FULL half.tsv` (half_pool.txt):

```
side FULL: games 400 W-L-D 245-20-135 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 34, 89, 71] Elo +221.14 95% [+194.35, +250.47]
```

FULL's Elo is +221.14, above +20. fastchess printed the same Elo and the same W-L-D.

## Pool

22 chunks, 11000 games. Pasted POOL.txt (`python3 games_tsv.py pool ON chunk_*.tsv`):

```
side ON: games 11000 W-L-D 2954-2910-5136 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [274, 1319, 2269, 1365, 273] Elo +1.39 95% [-2.93, +5.71]
```

## suspicions, not proven

The match Elo is +1.39 and the 95% interval crosses zero. That is not a demonstrated gain. Chunk 22 started at 14:55:58Z, when elapsed minutes were still 94, and fastchess finished it at 15:00:00Z, before minute 103. It is counted because Finished match was in the log and the tsv was written.

## what I did NOT do

I did not write a new search idea, open a pull request, force-push, or write any branch except for-fable-and-opus/grok2-001. I did not send IdeaB1_Scale or IdeaB1_Fade. I did not pass -draw, -resign, -maxmoves, or tablebases. I did not replay an opening. I did not commit an exe, a net, a PGN, the book, or engine source. I did not switch to arm 10. fastchess wrote config.json in the repository directory during C-HALF; I moved that file to /home/ubuntu/fastchess-config.json and did not commit it. Its adjudication switches were disabled.

## what I am NOT sure about

The RESULT.txt `id` field is not defined beyond `<ID>`. I filled `B1a`, the label of this arm in the brief. The model name is Grok 4.7 in SEAT.txt. The first O-run harness blocked on a full pipe before `uciok`. The run that produced the files used a reader thread and `stdbuf -oL`. The node sums still match the table, so that wrapper did not change these searches. I did not prove that two plays of the same opening are byte-identical.

## times: see stamps.txt

The first stamp, 2026-11-20T13:21:06Z, is minute 0. Play refused a new chunk after chunk 22 with `minute 95: no new chunk`.

## git status --short

```
 M forge-combo29/grok2/001/stamps.txt
?? forge-combo29/grok2/001/POOL.txt
?? forge-combo29/grok2/001/REPORT.md
?? forge-combo29/grok2/001/RESULT.txt
?? forge-combo29/grok2/001/chunk_22.out
?? forge-combo29/grok2/001/chunk_22.tsv
```

## ls -la

```
total 3588
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:20 ..
-rw-r--r-- 1 ubuntu ubuntu   2170 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56169 Nov 20 14:12 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51369 Nov 20 14:12 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56101 Nov 20 14:16 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51386 Nov 20 14:16 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56513 Nov 20 14:20 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:20 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 14:24 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51546 Nov 20 14:24 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56333 Nov 20 14:28 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51377 Nov 20 14:28 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56320 Nov 20 14:32 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51486 Nov 20 14:32 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56427 Nov 20 14:36 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51537 Nov 20 14:36 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56129 Nov 20 14:40 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51421 Nov 20 14:40 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56203 Nov 20 14:44 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51354 Nov 20 14:44 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56222 Nov 20 14:48 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51570 Nov 20 14:48 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56414 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51204 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56424 Nov 20 14:52 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51433 Nov 20 14:52 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56361 Nov 20 14:55 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51563 Nov 20 14:55 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56465 Nov 20 15:00 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51673 Nov 20 15:00 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56328 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51339 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56156 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51464 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  55984 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51352 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56097 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51318 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56367 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51455 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56454 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51469 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56140 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51518 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56184 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51360 Nov 20 14:07 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46810 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1062 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42229 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:23 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:23 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:23 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:23 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:23 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:23 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    215 Nov 20 13:23 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:23 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:23 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5154 Nov 20 13:23 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:23 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5154 Nov 20 13:23 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:23 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5157 Nov 20 13:23 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    215 Nov 20 13:23 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5368 Nov 20 13:23 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    942 Nov 20 13:27 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu    856 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 318117 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    890 Nov 20 13:26 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 318348 Nov 20 13:26 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    889 Nov 20 13:26 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 319316 Nov 20 13:26 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   4098 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    280 Nov 20 13:26 o_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5739 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     73 Nov 20 13:20 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    812 Nov 20 15:02 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1180 Nov 20 13:24 summarize_o.py
```

# grok2 seat 045

## Arm and source seat

Seat 045, arm 5, id S10. Source seat 081, commit b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa, branch for-fable-and-opus/grok-081, file forge-combo29/grok/081/idea.patch.txt. SWITCH IdeaS10. Model Grok 4.7.

`git rev-parse FETCH_HEAD` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-081` printed b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa.

## Patch sha256 and git apply

```
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  /home/ubuntu/arm.patch
```

That is the arm table sha256. In /agent/repos/work, `git apply --check ~/arm.patch` and `git apply ~/arm.patch` both exited 0. `git diff --stat` printed:

```
 forge-combo29/include/forge/eval.hpp   |   3 +
 forge-combo29/include/forge/search.hpp |  10 ++
 forge-combo29/src/eval.cpp             |  26 ++++++
 forge-combo29/src/search.cpp           | 163 +++++++++++++++++++++++++++++++--
 forge-combo29/src/uci.cpp              |  13 ++-
 5 files changed, 208 insertions(+), 7 deletions(-)
```

The patch also advertises IdeaS10_Flat, IdeaS10_Look, IdeaS10_Shrink and IdeaS10_Depth. Those stayed at the engine default. Match and O-run commands send only IdeaS10.

Build: CMake Release, /usr/bin/g++ 13.3.0, GCC libstdc++. The machine has AVX-512 and BMI2, so the build uses the CMake default -march=x86-64-v4 and leaves FORGE_PORTABLE off. Exe P is /agent/repos/work/forge-combo29/build-rel/forge. Exe B is /agent/repos/base/forge-combo29/build-rel/forge. Neither binary is in this commit.

## Honesty numbers

Fresh process per line, no setoption. Expected: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Grep of the raw files:

```
forge-combo29/grok2/045/honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 166 nps 1884734
forge-combo29/grok2/045/honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 425 nps 2029009
forge-combo29/grok2/045/honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1405 nps 2152967
forge-combo29/grok2/045/honesty_B_perft5.txt:nodes 4865609
forge-combo29/grok2/045/honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 166 nps 1884734
forge-combo29/grok2/045/honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 420 nps 2053164
forge-combo29/grok2/045/honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1395 nps 2168401
forge-combo29/grok2/045/honesty_P_perft5.txt:nodes 4865609
```

Exe B and exe P both match all four counts. honesty=ok.

## Three O runs

Script o_table.py reading the raw transcripts. Expected from the arm table: exe B sum 9,500,069 and first three 41,311 / 24,872 / 28,574; SWITCH false equal on all 200; SWITCH true sum 9,542,904, same first three, 10 positions differ.

Pasted o_rows_B.txt:

```
file forge-combo29/grok2/045/o_B.raw
sum 9500069
first3 41311 24872 28574
```

Pasted o_rows_P_off.txt:

```
file forge-combo29/grok2/045/o_P_off.raw
sum 9500069
first3 41311 24872 28574
differ_from forge-combo29/grok2/045/o_B.raw 0
equal 200
```

Pasted o_rows_P_on.txt:

```
file forge-combo29/grok2/045/o_P_on.raw
sum 9542904
first3 41311 24872 28574
differ_from forge-combo29/grok2/045/o_B.raw 10
equal 190
```

off_identical=yes. on_sum=9542904. on_ok=yes.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

book=ok. Seat openings are every 90th line of uho.epd starting at line 45. The last 300 of mine.epd are ctl.epd and were not used as chunk openings. mine.epd has 29245 lines. 17 chunks use the first 4250 lines.

## C-ARRIVE and C-HALF

C-ARRIVE: `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` exited 0 and printed Finished match. arrive_check.txt:

```
setoption name IdeaS10 value true count: 20
unknown option|invalid value|No such option count: 0
```

arrive=ok.

C-HALF: ~/half.sh is match.sh with the two engine lines changed to FULL nodes=20000 option.IdeaS10=false and HALF nodes=10000 option.IdeaS10=false, and with nodes=20000 removed from -each. `python3 ~/games_tsv.py pool FULL` on half.tsv printed:

```
side FULL: games 400 W-L-D 243-39-118 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 8, 47, 74, 70] Elo +195.51 95% [+167.72, +225.78]
```

half_elo=+195.51, which is above +20. PASS.

## POOL.txt and chunks

17 chunks, 500 games each, 8500 games. Every chunk tsv has 500 lines and every termination field is normal. `python3 ~/games_tsv.py pool ON` wrote POOL.txt:

```
side ON: games 8500 W-L-D 2245-2321-3934 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [127, 849, 2355, 811, 108] Elo -3.11 95% [-7.19, +0.98]
```

chunks=17 games=8500 wld=2245-2321-3934 ptnml=127,849,2355,811,108 elo=-3.11 lo=-7.19 hi=+0.98.

Chunk 17 finished at 2026-11-20T15:00:08Z. play.sh then stopped because the next chunk would have started after minute 95. No chunk was killed.

## suspicions, not proven

A pool of the first 7 chunks only (3500 games) printed Elo -6.95 95% [-13.07, -0.83]. That interval sits below 0. The full 8500-game interval includes 0. The 3500-game line is a partial sample, not the result.

Chunks 11 and 15 took about 14 minutes; the others took about 4. During chunk 11 the load average was about 2.9 and six forge processes were using the CPU. I did not prove why those two chunks were slower. Their tsv files are still 500 games with termination normal.

fastchess wrote config.json in the repository root while matches ran. In that file resign, draw, maxmoves and tb_adjudication are all enabled false. The match command line has no -draw, -resign, -maxmoves or tablebase flag. I moved that file to /home/ubuntu/fastchess-last-config.json before this report's status snapshot so it would stay out of the commit.

## what I did NOT do

I did not open a pull request. I did not change engine source and I did not commit an executable, a net, a PGN or the book. I did not send IdeaS10_Flat, IdeaS10_Look, IdeaS10_Shrink or IdeaS10_Depth. I did not play arm 10. I did not repeat an opening. I did not adjudicate games. No forge-combo29/soak_all/FABLE_TO_grok2_<N>.md existed on handoff/fable-opus-combo29-all-20261114 at the fetches in this run, so no STOP file was applied.

## what I am NOT sure about

I am not sure the id field should be the table's short name S10 rather than the switch name IdeaS10. The line uses S10.

I am not sure why fastchess showed engine processes only about two minutes old while a chunk had been running longer. The games in the tsv still pair (4250 openings, each in exactly 2 games) and every termination is normal.

The 95% interval of the 8500-game pool includes both a small loss and a small gain. The point Elo is -3.11.

## times: see stamps.txt

Minute 0 is the first line of stamps.txt, 2026-11-20T13:22:26Z. Minute 95 is 2026-11-20T14:57:26Z. Minute 103 is 2026-11-20T15:05:26Z.

## git status --short and ls -la

The next two blocks are the command output taken after this report and RESULT.txt were written, and before the STEP 5 commit.

```
$ git status --short
 M forge-combo29/grok2/045/stamps.txt
?? forge-combo29/grok2/045/POOL.txt
?? forge-combo29/grok2/045/REPORT.md
?? forge-combo29/grok2/045/RESULT.txt
?? forge-combo29/grok2/045/half_tsv_log.txt

$ ls -la forge-combo29/grok2/045
total 2920
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:08 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2216 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56408 Nov 20 14:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51578 Nov 20 14:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56635 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51568 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56535 Nov 20 14:29 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:29 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56040 Nov 20 14:33 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51464 Nov 20 14:33 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56521 Nov 20 14:37 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51419 Nov 20 14:37 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56160 Nov 20 14:52 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:52 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56457 Nov 20 14:56 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:56 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56081 Nov 20 15:00 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51443 Nov 20 15:00 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56063 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51103 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56353 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51318 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56458 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51261 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56127 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51343 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55903 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51345 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56644 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51590 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56404 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51425 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56105 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51532 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55985 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51550 Nov 20 14:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46790 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:32 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1062 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42330 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:32 half_tsv_log.txt
-rw-r--r-- 1 ubuntu ubuntu    260 Nov 20 13:26 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    260 Nov 20 13:26 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    260 Nov 20 13:26 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    262 Nov 20 13:26 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    260 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    260 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    260 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    262 Nov 20 13:26 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    914 Nov 20 13:25 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1046 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    855 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281644 Nov 20 13:26 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    894 Nov 20 13:26 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282013 Nov 20 13:26 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    891 Nov 20 13:26 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282088 Nov 20 13:26 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu     74 Nov 20 13:27 o_rows_B.txt
-rw-r--r-- 1 ubuntu ubuntu    134 Nov 20 13:27 o_rows_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    134 Nov 20 13:27 o_rows_P_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   5312 Nov 20 13:26 o_run.py
-rwxr-xr-x 1 ubuntu ubuntu   1751 Nov 20 13:26 o_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:07 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   7433 Nov 20 15:08 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:08 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    930 Nov 20 15:08 stamps.txt
```

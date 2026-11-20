# grok2 seat 017

Arm 7, id K4a, source seat 093, branch for-fable-and-opus/grok-093, commit ddc850cbf04b8c7a8592624037844077b33c8ab0. SWITCH IdeaK4. Model name passed to take_seat2.sh: Grok 4.7.

## Patch sha256 and git apply

```
e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree printed:

```
APPLY OK
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
```

IdeaK4_Shrink was left at its default. It was never sent.

## Honesty numbers

Fresh process, no setoption. Both exe B (`/agent/repos/base/forge-combo29/build/forge`) and exe P (`/agent/repos/work/forge-combo29/build/forge`), GCC 13.3.0, Release, default march x86-64-v4 (this machine has AVX-512 and BMI2).

```
honesty_B_bench11.txt: info string bench depth 11 nodes 312866 time 177 nps 1767604
honesty_B_bench13.txt: info string bench depth 13 nodes 862329 time 441 nps 1955394
honesty_B_bench16.txt: info string bench depth 16 nodes 3024920 time 1442 nps 2097725
honesty_B_perft5.txt: nodes 4865609
honesty_P_bench11.txt: info string bench depth 11 nodes 312866 time 160 nps 1955412
honesty_P_bench13.txt: info string bench depth 13 nodes 862329 time 449 nps 1920554
honesty_P_bench16.txt: info string bench depth 16 nodes 3024920 time 1481 nps 2042484
honesty_P_perft5.txt: nodes 4865609
```

Wanted 312866, 862329, 3024920, 4865609. Both exes match.

## Three O runs

`python3 forge-combo29/grok2/017/o_table.py` on the raw files:

```
forge-combo29/grok2/017/o_B.raw n=200 sum=9500069 first=41311 24872 28574
forge-combo29/grok2/017/o_Poff.raw n=200 sum=9500069 first=41311 24872 28574
forge-combo29/grok2/017/o_Pon.raw n=200 sum=8921190 first=24693 26341 35070
differ forge-combo29/grok2/017/o_Poff.raw vs forge-combo29/grok2/017/o_B.raw: 0
differ forge-combo29/grok2/017/o_Pon.raw vs forge-combo29/grok2/017/o_B.raw: 200
```

Table wanted: (1) sum 9500069, first 41311 / 24872 / 28574; (2) equal to (1) on all 200; (3) sum 8921190, first 24693 / 26341 / 35070, 200 differ. All three match. id name on both exes: Chess Engine Forge 6.4.24 candidate. S14, Threads 1 and Hash 16 were sent once before the 200 positions; ucinewgame and isready before every position. first200.fens sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both match the brief. Seat 017 took every 90th line from line 17: 29245 lines in mine.epd. The last 300 were the controls and were not used by the chunks.

## C-ARRIVE and C-HALF

arrive_check.txt: `setoption name IdeaK4 value true` count 20, and `unknown option|invalid value|No such option` count 0. The 20 log lines around the first true setoption are in that file. fastchess accepted `engine=true`.

C-HALF, `python3 ~/games_tsv.py pool FULL` on half.tsv (also half_pool.txt):

```
side FULL: games 400 W-L-D 240-31-129 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 4, 38, 99, 58] Elo +201.43 95% [+176.63, +228.24]
```

FULL's Elo is above +20. Pass.

## POOL.txt and chunks

21 chunks, each 500 games, 10500 games. play.sh printed `minute 95: no new chunk` and stopped. No FAILED line in play.log. Pasted POOL.txt:

```
side ON: games 10500 W-L-D 2812-2843-4845 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [260, 1278, 2196, 1265, 251] Elo -1.03 95% [-5.42, +3.37]
```

## suspicions, not proven

At 6000 games the split was 1609-1609-2782, Elo +0.00. I did not investigate that tie. The final pool is the result above. The 95% interval includes 0.

## what I did NOT do

No pull request. No engine source committed. No PGN, exe, or net file committed. No adjudication flags. IdeaK4_Shrink not sent. No second seat, no force-push. No FABLE_TO_grok2 file was on the handoff branch at any fetch, so nothing from the channel changed the run. git user.name was already set, so it was left as it was.

## what I am NOT sure about

S14 was sent once per O-run rather than again before every position. The node counts matched the table. Chunks 13 through 21 were committed by ~/push_chunks.sh (same branch, same 500-line and "done" checks, channel fetch on each push) because a four-minute manual loop was dropping the gap between chunks. I am sure those 500-line files are the ones play.log marked done. I am not sure a handoff file appeared in a commit this fetch's depth-1 tip did not contain; every fetch of that branch returned no FABLE_TO_grok2 name.

## times: see stamps.txt

times: see stamps.txt

## git status --short
```
 M forge-combo29/grok2/017/stamps.txt
?? config.json
?? forge-combo29/grok2/017/POOL.txt
?? forge-combo29/grok2/017/REPORT.md
?? forge-combo29/grok2/017/RESULT.txt
```

## ls -la
```
total 3328
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2237 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56154 Nov 20 14:13 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51341 Nov 20 14:13 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56264 Nov 20 14:17 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 14:17 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55994 Nov 20 14:21 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51419 Nov 20 14:21 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56211 Nov 20 14:26 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51431 Nov 20 14:26 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56395 Nov 20 14:30 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51437 Nov 20 14:30 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56268 Nov 20 14:34 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51454 Nov 20 14:34 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56138 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51517 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56456 Nov 20 14:43 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 14:43 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56329 Nov 20 14:47 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51536 Nov 20 14:47 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  55941 Nov 20 14:51 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51418 Nov 20 14:51 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56384 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51194 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55955 Nov 20 14:55 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51343 Nov 20 14:55 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56345 Nov 20 14:59 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51423 Nov 20 14:59 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56147 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51307 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56650 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51452 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56600 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51392 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56310 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51360 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56365 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51273 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51408 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56612 Nov 20 14:04 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51596 Nov 20 14:04 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55973 Nov 20 14:08 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51407 Nov 20 14:08 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46672 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:30 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42319 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:23 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:23 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:23 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:23 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 13:23 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:23 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:23 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:23 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:23 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1157 Nov 20 13:23 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281882 Nov 20 13:25 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    864 Nov 20 13:25 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 282035 Nov 20 13:25 o_Poff.raw
-rw-r--r-- 1 ubuntu ubuntu    861 Nov 20 13:25 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 280948 Nov 20 13:25 o_Pon.raw
-rw-r--r-- 1 ubuntu ubuntu   3818 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1380 Nov 20 13:25 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5072 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    754 Nov 20 15:05 stamps.txt
```

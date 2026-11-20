# grok3 seat 010

Seat 010, arm 1, 20,000 nodes, chunks of 250 openings (500 games). Model Grok 4.7. Branch for-fable-and-opus/grok3-010. Match is the main match: IdeaB8=true and HindsightDepth=true (ON) against IdeaB8=false and HindsightDepth=false (OFF).

## Patch

sha256 of ~/b8.patch (from 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt, FETCH_HEAD of for-fable-and-opus/grok-028 was 4bf95fd80adf523e97fa250bb8572c946cf0fc75):

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/b8.patch
```

That is the required hash. `git apply --check ~/b8.patch` then `git apply ~/b8.patch` in the worktree ../work at 6b98f2170a3210e71beed04bbd2553972c253ed7. Worktree diff stat after apply:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

The first cmake used /usr/bin/c++ (Clang 18) and stopped with `cannot find -lstdc++`. The brief requires g++ (GCC 13 or newer, GCC's own C++ library). I removed ~/build and configured again with CC=gcc, CXX=g++, and -DCMAKE_CXX_COMPILER=g++. The log line is `The CXX compiler identification is GNU 13.3.0`. /proc/cpuinfo has avx512f and bmi2, so I did not add -DFORGE_PORTABLE=ON or -DFORGE_MARCH. Exe is /home/ubuntu/build/forge. Its sha256, from the O-run meta files, is 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422. id name: Chess Engine Forge 6.4.24 candidate. No engine source and no exe is committed.

## Honesty

Fresh processes, no setoption. Files honesty_bench11.txt, honesty_bench13.txt, honesty_bench16.txt, honesty_perft5.txt:

```
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 435 nps 1982365
info string bench depth 16 nodes 3024920 time 1416 nps 2136242
nodes 4865609
```

Required: 312866, 862329, 3024920, 4865609. All four match.

## Four O runs

Required text, then what o_runs.py printed and what the row files sum to.

(1) both off. Required sum 9,500,069; first three 41,311 / 24,872 / 28,574; sha256 of o_off.rows.txt dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7.

Printed: `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. sha256sum printed that hash. Recount of the file: n 200, sum 9500069, first three 41311, 24872, 28574.

(2) IdeaB8 only. Required sum 9,718,009; first three 17,283 / 17,878 / 31,115.

Printed: `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`. Recount: sum 9718009, first three 17283, 17878, 31115.

(3) HindsightDepth only. Required sum 9,845,650; first three 23,395 / 31,504 / 35,958.

Printed: `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`. Recount: sum 9845650, first three 23395, 31504, 35958.

(4) both on. No required sum. Printed: `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. Recount of o_both.rows.txt: sum 9758416, first three 18538, 34070, 39093 (moves f1e2, f1c4, e5d4). Positions whose node count differs from (1): `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200. Recount of the two files: 200.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Same as the brief's copy. mine.epd has 13390 lines. Controls use the last 300 of those (10 arrive, 200 half). Chunks take the top and stop at line 13090, so they do not use those 300.

## games_tsv.py known answer

~/ka.tsv from for-fable-and-opus/grok2-004 forge-combo29/grok2/004/chunk_1.tsv, sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required print.

## C-ARRIVE and C-HALF

C-ARRIVE: match.sh on ctl_arrive.epd, 10 rounds, trace log. Counts in arrive_check.txt: IdeaB8 value true = 20, HindsightDepth value true = 20, unknown option|invalid value|no such option = 0. The 20 log lines around the first IdeaB8 setoption are in that file. fastchess finished the match (20 games).

C-HALF: half.sh on ctl_half.epd, 200 rounds. half.out and half.tsv. Pool of FULL:

```
side FULL: games 400 W-L-D 270-46-84 pairs 200 (openings not in exactly 2 games: 0)
ptnml [4, 6, 41, 60, 89] Elo +219.87 95% [+187.61, +255.89]
```

PASS: +219.87 is above +20. fastchess's own line was Elo 219.87 +/- 34.14.

## POOL.txt and chunks

10 chunks, each 500 games, 5000 games. Every chunk's fastchess log contains "Finished match". play.log has no FAILED line. Termination column of all 5000 tsv rows is `normal`. Result column: 1460 of 1-0, 1246 of 0-1, 2294 of 1/2-1/2 (those are game results, not ON's score). ON's score is the pool below. Pasted POOL.txt:

```
side ON: games 5000 W-L-D 1472-1234-2294 pairs 2500 (openings not in exactly 2 games: 0)
ptnml [101, 534, 1041, 674, 150] Elo +16.55 95% [+10.17, +22.94]
```

## suspicions, not proven

None. The three known O runs match the published numbers to the node, the off-file hash matches, and both-on is the same exe with both options accepted (C-ARRIVE sent them, zero refusal lines). I have not read another seat's o_both.rows.txt, so I have not checked that their both-on sum equals 9758416.

## what I did NOT do

No pull request. No --force. No push except HEAD to for-fable-and-opus/grok3-010. No engine source committed. No PGN, exe, net, or book committed. No adjudication flags (-draw, -resign, -maxmoves, tablebases) on match.sh or half.sh. No fallback match. No second half-control. No chunk killed. Channel fetch at step 1 and again at 2026-11-20T19:12:27Z: no file named FABLE_TO_grok3_*.md under forge-combo29/soak_all. fastchess wrote an untracked config.json in the repository root during the controls; its resign, draw, maxmoves, and tb_adjudication enabled fields are false. I did not commit it.

## what I am NOT sure about

Whether every other seat's both-on O run prints the same sum and first three. This seat's file says sum 9758416 and first three 18538 / 34070 / 39093, with 200 positions differing from both-off.

## times: see stamps.txt

## git status --short and ls -la

Captured after POOL.txt, REPORT.md, RESULT.txt, and the STEP 5 stamp line were written, before the commit that adds them.
```
 M forge-combo29/grok3/010/stamps.txt
?? config.json
?? forge-combo29/grok3/010/POOL.txt
?? forge-combo29/grok3/010/REPORT.md
?? forge-combo29/grok3/010/RESULT.txt
```

```
total 1276
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:40 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2450 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56790 Nov 20 19:37 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51567 Nov 20 19:37 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 55743 Nov 20 18:59 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51496 Nov 20 18:59 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56197 Nov 20 19:03 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51685 Nov 20 19:03 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56250 Nov 20 19:07 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51540 Nov 20 19:07 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56603 Nov 20 19:11 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51758 Nov 20 19:11 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 55858 Nov 20 19:15 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51558 Nov 20 19:15 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56522 Nov 20 19:20 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51611 Nov 20 19:20 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 55714 Nov 20 19:24 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51544 Nov 20 19:24 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56521 Nov 20 19:28 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51561 Nov 20 19:28 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 55979 Nov 20 19:33 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51373 Nov 20 19:33 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45794 Nov 20 18:54 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42065 Nov 20 18:54 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:54 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:54 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu   154 Nov 20 19:38 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6514 Nov 20 19:40 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   295 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   502 Nov 20 19:40 stamps.txt
```

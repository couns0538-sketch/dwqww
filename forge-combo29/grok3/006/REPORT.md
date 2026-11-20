# Seat 006

Seat 006, arm 3, node count 60000. Chunk size 100 openings (200 games). Match is main: IdeaB8 and HindsightDepth both on, against both off. Model name passed to take_seat3.sh: Grok 4.7.

# Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474
Source commit printed by git rev-parse FETCH_HEAD: 4bf95fd80adf523e97fa250bb8572c946cf0fc75
git apply --check ~/b8.patch then git apply ~/b8.patch in the worktree outside this repository. Apply succeeded. Diff stat: forge-combo29/include/forge/search.hpp, forge-combo29/src/search.cpp, forge-combo29/src/uci.cpp (173 insertions, 4 deletions). Nothing from that worktree was committed.

Decision: the first cmake used /usr/bin/c++ (Clang 18.1.3) and failed to link libstdc++. The brief says to cmake with g++ (GCC 13 or newer, GCC's own C++ library). This machine has g++ 13.3.0 and has AVX-512 and BMI2, so the rebuild was cmake with -DCMAKE_CXX_COMPILER=g++ and -DCMAKE_BUILD_TYPE=Release, and without FORGE_PORTABLE. The honesty numbers and O runs (1) (2) (3) then matched the known figures, so the measured exe is that g++ build: /home/ubuntu/build/forge, sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422, id name Chess Engine Forge 6.4.24 candidate.

# Honesty

Raw lines from the honesty files (fresh process, no setoption):

- honesty_bench11.txt: info string bench depth 11 nodes 312866 time 172 nps 1818988
- honesty_bench13.txt: info string bench depth 13 nodes 862329 time 462 nps 1866512
- honesty_bench16.txt: info string bench depth 16 nodes 3024920 time 1490 nps 2030147
- honesty_perft5.txt ends with: nodes 4865609

These are the known numbers: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

# Four O runs

Against the known text. Each meta file names exe /home/ubuntu/build/forge and the sha256 above.

(1) o_off.rows.txt IdeaB8=false HindsightDepth=false
printed: rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574
file head: 41311, 24872, 28574
sha256sum o_off.rows.txt: dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7
Known: sum 9,500,069; first three 41,311 / 24,872 / 28,574; sha256 dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. Match.

(2) o_b8.rows.txt IdeaB8=true HindsightDepth=false
printed: rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115
file head: 17283, 17878, 31115
Known: sum 9,718,009; first three 17,283 / 17,878 / 31,115. Match.

(3) o_k3.rows.txt IdeaB8=false HindsightDepth=true
printed: rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958
file head: 23395, 31504, 35958
Known: sum 9,845,650; first three 23,395 / 31,504 / 35,958. Match.

(4) o_both.rows.txt IdeaB8=true HindsightDepth=true
printed: rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093
file head: 18538, 34070, 39093
awk sum of column 2: 9758416
positions whose node count differs from (1): paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l = 200
No known answer was given for (4).

# Book

sha256 ~/uho.zip: 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
wc -l ~/uho.epd: 2632036
sha256 ~/uho.epd: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
Known zip and epd hashes match. Seat openings: awk from line 2150000+6 every 36th line, wc -l ~/mine.epd = 13390.

# games_tsv.py known answer

sha256 ~/ka.tsv: 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd
python3 ~/games_tsv.py pool ON ~/ka.tsv printed:
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
That is the known answer.

# C-ARRIVE

arrive_check.txt counts:
grep -c setoption name IdeaB8 value true: 20
grep -c setoption name HindsightDepth value true: 20
grep -c -i -E unknown option|invalid value|no such option: 0
The 20 log lines around the first setoption of IdeaB8 are in arrive_check.txt. The first such engine line is: ON <--- setoption name IdeaB8 value true, followed by setoption name HindsightDepth value true. Required: IdeaB8 count 1 or more, HindsightDepth count 1 or more, refusal count 0. Pass. fastchess also printed Finished match for the 20-game control.

# C-HALF

python3 ~/games_tsv.py pool FULL forge-combo29/grok3/006/half.tsv printed:
side FULL: games 400 W-L-D 287-43-70 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 5, 39, 59, 96] Elo +246.30 95% [+214.41, +282.23]
PASS: FULL Elo +246.30 is above +20.

# POOL.txt

8 chunks, each chunk_N.tsv has 200 lines, 1600 games. Pasted POOL.txt:

side ON: games 1600 W-L-D 418-362-820 pairs 800 (openings not in exactly 2 games: 0)
ptnml [22, 165, 376, 209, 28] Elo +12.17 95% [+2.00, +22.35]

# suspicions, not proven

The both-on node sum 9,758,416 sits near IdeaB8 alone (9,718,009) and below HindsightDepth alone (9,845,650). Node totals are not Elo. This seat's match at 60000 nodes is Elo +12.17 with interval [+2.00, +22.35]. That single arm does not decide whether the two ideas add to about +17 or overlap near +10.

# what I did NOT do

I did not open a pull request. I did not use --force. I did not push any branch except for-fable-and-opus/grok3-006. I did not commit an engine source file, an exe, an object file, a net, a PGN, or the book. I did not add -draw, -resign, -maxmoves, or tablebases. I did not play the fallback match. I did not start a chunk after minute 46. Chunk 8 had already started and finished at 2026-11-20T19:35:08Z; play.sh then printed "minute 46: no new chunk" and exited. I did not kill fastchess. I did not commit config.json, which fastchess wrote in the repository root (the process cwd). Its resign, draw, maxmoves, and tb_adjudication enabled fields are false. All 1600 chunk rows have termination normal.

# what I am NOT sure about

I am not sure why fastchess wrote config.json into the repository root. I did not pass a config file. I left it untracked. I am not sure the channel fetch was complete beyond the name listing: git ls-tree of forge-combo29/soak_all/ on handoff/fable-opus-combo29-all-20261114 showed no file matching FABLE_TO_grok3_ at step 1 and again during step 4. No STOP line was present because no such file existed.

# times: see stamps.txt

2026-11-20T19:37:50Z is the STEP 5 stamp below. First stamp, which minute 46 is counted from: 2026-11-20T18:48:49Z.

2026-11-20T18:48:49Z STEP 1 seat
2026-11-20T18:52:45Z STEP 2 honesty and O runs
2026-11-20T18:56:20Z STEP 3 controls
2026-11-20T19:01:25Z chunk 1 done
2026-11-20T19:06:22Z chunk 2 done
2026-11-20T19:11:19Z chunk 3 done
2026-11-20T19:16:10Z chunk 4 done
2026-11-20T19:20:55Z chunk 5 done
2026-11-20T19:25:42Z chunk 6 done
2026-11-20T19:30:30Z chunk 7 done
2026-11-20T19:35:08Z chunk 8 done
2026-11-20T19:37:50Z STEP 5 pool report

# git status --short and ls -la

The listing is appended immediately after this file and RESULT.txt exist.

```
$ git status --short
 M forge-combo29/grok3/006/stamps.txt
?? config.json
?? forge-combo29/grok3/006/POOL.txt
?? forge-combo29/grok3/006/REPORT.md
?? forge-combo29/grok3/006/RESULT.txt

$ ls -la forge-combo29/grok3/006
total 580
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:37 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2293 Nov 20 18:56 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22598 Nov 20 19:01 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20640 Nov 20 19:01 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22402 Nov 20 19:06 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20540 Nov 20 19:06 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22367 Nov 20 19:11 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20668 Nov 20 19:11 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22814 Nov 20 19:16 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20729 Nov 20 19:16 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22415 Nov 20 19:20 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20801 Nov 20 19:20 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22637 Nov 20 19:25 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20628 Nov 20 19:25 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22548 Nov 20 19:30 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20773 Nov 20 19:30 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22672 Nov 20 19:35 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20688 Nov 20 19:35 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:56 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45540 Nov 20 18:56 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:56 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41884 Nov 20 18:56 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:56 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:56 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:36 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  7132 Nov 20 19:38 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:37 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    87 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   429 Nov 20 19:37 stamps.txt
```

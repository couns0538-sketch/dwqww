# grok3 seat 025 report

Seat 025, arm 1, 20,000 nodes. Chunk size 250 openings (500 games). Match is the main match: IdeaB8=true and HindsightDepth=true (ON) against IdeaB8=false and HindsightDepth=false (OFF). Model name passed to take_seat3.sh: Grok 4.7.

## Patch

Patch file ~/b8.patch from commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75, path forge-combo29/grok/028/idea.patch.txt.
sha256 f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474 (the required hash).
`git apply --check ~/b8.patch && git apply ~/b8.patch` in the worktree printed APPLY OK.
Worktree diff after apply: forge-combo29/include/forge/search.hpp, forge-combo29/src/search.cpp, forge-combo29/src/uci.cpp (3 files, 173 insertions, 4 deletions). Nothing from the build or the patch was committed.

Decision: /usr/bin/c++ is clang 18 and cannot link libstdc++. The brief says CMake with g++ (GCC 13 or newer). Configure used -DCMAKE_CXX_COMPILER=g++. g++ is Ubuntu 13.3.0. /proc/cpuinfo has avx512f and bmi2, so FORGE_PORTABLE and FORGE_MARCH were not set.

## Honesty

Fresh processes, no setoption before the command. Raw files honesty_bench11.txt, honesty_bench13.txt, honesty_bench16.txt, honesty_perft5.txt.

- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609

All four match the known numbers.

## Four O runs

Engine ~/build/forge, id name Chess Engine Forge 6.4.24 candidate. Harness ~/o_runs.py, copy in this folder.

(1) IdeaB8=false HindsightDepth=false: rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574. sha256 of o_off.rows.txt is dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. Matches the known answer.
(2) IdeaB8=true HindsightDepth=false: rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115. Matches the known answer.
(3) IdeaB8=false HindsightDepth=true: rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958. Matches the known answer.
(4) IdeaB8=true HindsightDepth=true: rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093. No known answer was given. Positions whose node count differs from (1): 200 (paste of o_off.rows.txt and o_both.rows.txt, awk '$2 != $5' | wc -l).

## Book

sha256 of ~/uho.zip is 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07.
~/uho.epd is 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a.
Both match the given copy. Seat openings: awk from line 2150000+25, every 36th line, 13390 lines in ~/mine.epd. Controls used the last 300 of those lines. Chunks used the top.

## games_tsv.py known answer

Fetched for-fable-and-opus/grok2-004, file forge-combo29/grok2/004/chunk_1.tsv.
sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.
`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
That is the known answer.

## C-ARRIVE

`bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` finished the match (20 games).
Counts, also in arrive_check.txt:
setoption name IdeaB8 value true: 20
setoption name HindsightDepth value true: 20
unknown option|invalid value|no such option: 0
arrive=ok.

## C-HALF

`bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn` finished 400 games.
`python3 ~/games_tsv.py pool FULL forge-combo29/grok3/025/half.tsv` printed:
side FULL: games 400 W-L-D 284-42-74 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 6, 42, 48, 102] Elo +243.55 95% [+209.80, +281.82]
FULL Elo +243.55 is above +20. half_elo=+243.55. Passed.

## POOL.txt

10 chunks, each 500 games, 5000 games. Openings not in exactly 2 games: 0. Pasted POOL.txt:

side ON: games 5000 W-L-D 1458-1227-2315 pairs 2500 (openings not in exactly 2 games: 0)
ptnml [111, 540, 1005, 695, 149] Elo +16.06 95% [+9.59, +22.55]

## suspicions, not proven

The depth-12 node sum with both ideas on (9,758,416) is near IdeaB8 alone (9,718,009), not near adding the two separate node increases. That is 200 positions at depth 12. It is not an Elo claim. The match Elo above is the measurement at 20,000 nodes.

## what I did NOT do

No pull request. No engine source committed. No --force. No adjudication options on the fastchess command (no -draw, -resign, -maxmoves, no tablebases). No fallback match. No second seat. No FABLE_TO_grok3 file existed on the channel at step 1 or mid step 4, so no extra instruction applied. fastchess wrote /agent/repos/dwqww/config.json (its own config; resign, draw, maxmoves and tb adjudication are enabled false). I did not commit it.

## what I am NOT sure about

I have only this seat's games. I did not recount the Elo formula beyond the known-answer check of games_tsv.py, which matched. I am sure the POOL.txt lines above are the script's print on the ten committed chunk tsv files.

times: see stamps.txt

## git status --short

 M forge-combo29/grok3/025/stamps.txt
?? config.json
?? forge-combo29/grok3/025/POOL.txt
?? forge-combo29/grok3/025/REPORT.md
?? forge-combo29/grok3/025/RESULT.txt

## ls -la forge-combo29/grok3/025

total 1276
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:40 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2269 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56180 Nov 20 19:38 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51508 Nov 20 19:38 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 56557 Nov 20 18:59 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51702 Nov 20 18:59 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56596 Nov 20 19:03 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51704 Nov 20 19:03 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56211 Nov 20 19:08 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51561 Nov 20 19:08 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 55960 Nov 20 19:12 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51484 Nov 20 19:12 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56115 Nov 20 19:16 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51661 Nov 20 19:16 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56404 Nov 20 19:21 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51408 Nov 20 19:21 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56431 Nov 20 19:25 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51765 Nov 20 19:25 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 55971 Nov 20 19:29 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51496 Nov 20 19:29 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56338 Nov 20 19:34 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51620 Nov 20 19:34 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45553 Nov 20 18:55 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41977 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:52 honesty_perft5.txt
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
-rw-r--r-- 1 ubuntu ubuntu   153 Nov 20 19:39 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  7908 Nov 20 19:40 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   294 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   498 Nov 20 19:40 stamps.txt

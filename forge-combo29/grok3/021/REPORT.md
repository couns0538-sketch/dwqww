# grok3 seat 021

Seat 021, arm 3, 60,000 nodes, chunk size 100 openings (200 games). Model Grok 4.7. Branch for-fable-and-opus/grok3-021. Match is the main match: IdeaB8 true and HindsightDepth true (ON) against both false (OFF).

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474. That matches the required hash. The bytes came from git show 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt. git rev-parse FETCH_HEAD after fetching for-fable-and-opus/grok-028 printed 4bf95fd80adf523e97fa250bb8572c946cf0fc75.

git apply --check ~/b8.patch and git apply ~/b8.patch both exited 0 (the command printed APPLY OK). The patch was applied only in the outside worktree ../work at base 6b98f2170a3210e71beed04bbd2553972c253ed7. At report time, git diff --stat in that worktree was:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

No engine source file was committed. The default /usr/bin/c++ is Clang 18.1.3 and its link test failed (cannot find -lstdc++). The brief requires g++ with GCC's C++ library, and /usr/bin/g++ is GCC 13.3.0 and linked a test program, so cmake was run with -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release. The CPU flags include avx512 and bmi2, so FORGE_PORTABLE and FORGE_MARCH were left at the CMake default (x86-64-v4). The exe is /home/ubuntu/build/forge. Its sha256 in o_off.rows.txt.meta is 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422. id name Chess Engine Forge 6.4.24 candidate.

## Honesty

Each line is a fresh process with no setoption. Raw files:

- honesty_bench11.txt: info string bench depth 11 nodes 312866
- honesty_bench13.txt: info string bench depth 13 nodes 862329
- honesty_bench16.txt: info string bench depth 16 nodes 3024920
- honesty_perft5.txt: nodes 4865609

Those are the required counts (312866, 862329, 3024920, 4865609).

## Four O runs

Required text, and what o_runs.py printed (recomputed from the row files at report time: same sums and first three):

1. Both off. Required sum 9,500,069, first three 41,311 / 24,872 / 28,574. Got rows 200 sum 9500069 first three 41311 24872 28574. sha256 of o_off.rows.txt is dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7, the required hash.
2. IdeaB8 only. Required sum 9,718,009, first three 17,283 / 17,878 / 31,115. Got 9718009 and 17283 17878 31115.
3. HindsightDepth only. Required sum 9,845,650, first three 23,395 / 31,504 / 35,958. Got 9845650 and 23395 31504 35958.
4. Both on. No required sum. Got rows 200 sum 9758416 first three 18538 34070 39093. Positions whose node count differs from run 1: 200 (paste | awk '$2 != $5' | wc -l, and a recount of the two files).

## Book

sha256 ~/uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07. ~/uho.epd 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a. Both match the required hashes. Seat openings: awk from line 2150000+21, every 36th line, wrote ~/mine.epd with 13390 lines. Controls are the last 300 of those lines (10 arrive, 200 half) and were not used as match chunks.

## games_tsv.py known answer

Fetched for-fable-and-opus/grok2-004 chunk_1.tsv. sha256 ~/ka.tsv 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd. python3 ~/games_tsv.py pool ON ~/ka.tsv printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required print.

## C-ARRIVE and C-HALF

C-ARRIVE (match.sh on ctl_arrive.epd, 10 rounds, trace log). Counts in arrive_check.txt, which I opened:

- setoption name IdeaB8 value true: 20
- setoption name HindsightDepth value true: 20
- unknown option / invalid value / no such option: 0

The first IdeaB8 setoption is log line 398, sent to engine ON, followed by HindsightDepth true. 20 log lines around it are in arrive_check.txt. fastchess printed Finished match for 20 games.

C-HALF: half.sh, 200 openings, 400 games. python3 games_tsv.py pool FULL half.tsv printed, and I ran it again at report time:

```
side FULL: games 400 W-L-D 276-57-67 pairs 200 (openings not in exactly 2 games: 0)
ptnml [5, 8, 45, 47, 95] Elo +213.60 95% [+179.73, +251.54]
```

FULL Elo +213.60 is above +20. PASS. half.out's final block also says Elo 213.60 and Finished match, Games 400.

## POOL.txt and chunks

8 chunks, each 200 games, 1600 games, 0 unscored results. chunk_1.tsv has 100 games ON vs OFF and 100 OFF vs ON. Pasted POOL.txt:

```
side ON: games 1600 W-L-D 456-382-762 pairs 800 (openings not in exactly 2 games: 0)
ptnml [29, 151, 365, 227, 28] Elo +16.08 95% [+5.65, +26.54]
```

## suspicions, not proven

The 95% interval [+5.65, +26.54] covers both a gain near +10 and a gain near +17, so this seat's 1600 games at 60,000 nodes do not by themselves separate "the two ideas add" from "they overlap". Node counts are a different measurement: both-on sum 9,758,416 sits between IdeaB8-only (9,718,009) and HindsightDepth-only (9,845,650), and all 200 positions changed their node count versus both-off. I do not treat that node pattern as an Elo result.

fastchess wrote config.json in the repository root because the match processes were started with that cwd. I opened it. resign, draw, maxmoves and tb_adjudication are all enabled false. I did not commit it. I have not proved that this file cannot affect some other fastchess invocation; match.sh passed every option on the command line, and C-ARRIVE's trace log shows those options reaching engine ON.

## what I did NOT do

I did not open a pull request. I did not force-push. I did not push any branch except for-fable-and-opus/grok3-021. I did not commit an engine binary, a net, a PGN, or a changed engine source file. I did not turn on adjudication. I did not play the fallback match. I did not start a chunk after minute 46. Chunk 8 had already started (19:31:02Z) and finished at 19:36:02Z, before minute 51 (19:40:15Z), so I did not kill it. I did not commit ~/arrive.log, only arrive_check.txt. No FABLE_TO_grok3 file existed on the handoff branch at STEP 1 or at the middle of STEP 4, so there was no channel instruction to follow. I did not commit config.json.

## what I am NOT sure about

I did not save the cmake and git apply stdout into the seat folder. The honesty numbers and the four O runs matching the known counts are the check that this exe is the patched engine. I am not sure a second machine's g++ would produce the same exe sha256; the node counts matched anyway.

games_tsv.py's Elo is the number I report. I did not reconcile it against fastchess's own Elo line for the eight chunks pooled together. The known-answer test of games_tsv.py matched, and C-HALF's point Elo matched fastchess's final line (213.60).

## times: see stamps.txt

STEP 1 stamp 2026-11-20T18:49:15Z. Minute 46 is 46 minutes after that line. play.out ended with "minute 46: no new chunk" after chunk 8.

## git status --short and ls -la

Captured immediately before this block was appended. REPORT.md in the listing does not include this block.
```
 M forge-combo29/grok3/021/stamps.txt
?? config.json
?? forge-combo29/grok3/021/POOL.txt
?? forge-combo29/grok3/021/REPORT.md
?? forge-combo29/grok3/021/RESULT.txt
```

```
total 580
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:38 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2271 Nov 20 18:53 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22836 Nov 20 18:58 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20791 Nov 20 18:58 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22284 Nov 20 19:04 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20575 Nov 20 19:04 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22469 Nov 20 19:10 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20690 Nov 20 19:10 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22533 Nov 20 19:15 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20644 Nov 20 19:15 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22296 Nov 20 19:20 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20556 Nov 20 19:20 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22459 Nov 20 19:25 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20667 Nov 20 19:25 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22328 Nov 20 19:31 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20572 Nov 20 19:31 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22158 Nov 20 19:36 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20499 Nov 20 19:36 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45806 Nov 20 18:53 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41984 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:50 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:50 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:37 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  7466 Nov 20 19:38 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:38 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   384 Nov 20 19:38 stamps.txt
```

# Seat 014

Seat 014, arm 2, 2000 nodes. Chunk size 500 openings (1000 games). Match main: ON is IdeaB8=true and HindsightDepth=true, OFF is both false. Model name passed to take_seat3.sh: Grok 4.7. Branch for-fable-and-opus/grok3-014, local branch grok3-seat.

# Patch

sha256 of the patch file: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

git rev-parse of for-fable-and-opus/grok-028 was 4bf95fd80adf523e97fa250bb8572c946cf0fc75. The patch was `git show 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`. `git apply --check` and `git apply` both succeeded on the worktree at base 6b98f2170a3210e71beed04bbd2553972c253ed7. The apply stat was forge-combo29/include/forge/search.hpp, forge-combo29/src/search.cpp, and forge-combo29/src/uci.cpp (173 insertions, 4 deletions). The patch was not committed.

The first cmake used /usr/bin/c++ (Clang 18.1.3) and failed to link libstdc++. The build that was measured used `cmake -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release`. g++ is GCC 13.3.0. /proc/cpuinfo contains avx512 and bmi2, so FORGE_PORTABLE was not added. The engine is /home/ubuntu/build/forge. o_both.rows.txt.meta records id name Chess Engine Forge 6.4.24 candidate and exe sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422.

# Honesty

Raw files in this folder:

- honesty_bench11.txt: info string bench depth 11 nodes 312866
- honesty_bench13.txt: info string bench depth 13 nodes 862329
- honesty_bench16.txt: info string bench depth 16 nodes 3024920
- honesty_perft5.txt last line: nodes 4865609

These are the known numbers. honesty=ok.

# Four O runs

Against the known text:

1. IdeaB8=false HindsightDepth=false. Required sum 9,500,069 and first three 41,311 / 24,872 / 28,574. o_off.rows.txt begins 41311, 24872, 28574. awk sum 9500069. sha256 dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. off_ok=yes.
2. IdeaB8=true HindsightDepth=false. Required sum 9,718,009 and first three 17,283 / 17,878 / 31,115. o_b8.rows.txt begins 17283, 17878, 31115. awk sum 9718009. b8_ok=yes.
3. IdeaB8=false HindsightDepth=true. Required sum 9,845,650 and first three 23,395 / 31,504 / 35,958. o_k3.rows.txt begins 23395, 31504, 35958. awk sum 9845650. k3_ok=yes.
4. IdeaB8=true HindsightDepth=true. No required sum in the brief. o_both.rows.txt begins 18538 f1e2, 34070 f1c4, 39093 e5d4. awk sum 9758416. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200. both_sum=9758416, both_first3=18538/34070/39093, both_differ=200.

At 2026-11-20T19:29:29Z, depth-1 fetches of seats 001, 002, 003, 004 and 005 each had o_both.rows.txt summing to 9758416.

# Book

sha256 ~/uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 (the known zip hash).

wc -l ~/uho.epd was 2632036. sha256 ~/uho.epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a (the known epd hash). book=ok.

mine.epd has 13390 lines (seat 014: NR >= 2150014 and (NR - 2150014) % 36 == 0). The last 300 lines were kept for the controls and were not used as chunks.

# Known answer of games_tsv.py

~/ka.tsv from for-fable-and-opus/grok2-004 forge-combo29/grok2/004/chunk_1.tsv. sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the known answer. tsv_ka=ok.

# C-ARRIVE

arrive_check.txt counts:

```
setoption name IdeaB8 value true: 20
setoption name HindsightDepth value true: 20
unknown option|invalid value|no such option: 0
```

The same file has 20 log lines around the first `setoption name IdeaB8 value true`. That line is the ON engine receiving the option, followed by HindsightDepth value true. arrive=ok.

# C-HALF

`python3 ~/games_tsv.py pool FULL` on half.tsv printed:

```
side FULL: games 400 W-L-D 265-61-74 pairs 200 (openings not in exactly 2 games: 0)
ptnml [3, 8, 53, 54, 82] Elo +195.51 95% [+164.83, +229.24]
```

half.out ends with `Elo: 195.51 +/- 32.20` for FULL vs HALF, 400 games, Wins 265, Losses 61, Draws 74, and `Finished match`. FULL's Elo is above +20. half_elo=+195.51.

# POOL.txt

26 chunks. Each chunk_*.tsv has 1000 lines (26000 games). Each chunk_*.out contains one `Finished match`. A search for "adjudicat" in those outs was 0 in every file.

Pasted POOL.txt:

```
side ON: games 26000 W-L-D 9676-8400-7924 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1152, 2532, 4797, 2926, 1593] Elo +17.06 95% [+13.71, +20.42]
```

chunks=26 games=26000 wld=9676-8400-7924 ptnml=1152,2532,4797,2926,1593 elo=+17.06 lo=+13.71 hi=+20.42.

# suspicions, not proven

The both-on node sum (9,758,416) is not the sum of the two separate gains over off (B8 +217,940 nodes, K3 +345,581 nodes, both +258,347 nodes). Seats 001 through 005 show the same both-on sum, so this is the shared engine answer on these 200 positions. The game result above is the measurement the brief asked for. I am not using the node sums as an Elo.

fastchess wrote an untracked config.json in the repository root because play.sh was started with that directory as cwd. I did not commit it. In that file, resign, draw, maxmoves and tb_adjudication are enabled false. match.sh was not given -draw, -resign, or -maxmoves.

# what I did NOT do

No pull request. No force-push. No commit of engine source, an executable, a net, a PGN, or the book. No fallback match. No FABLE_TO_grok3 file existed on handoff/fable-opus-combo29-all-20261114 at STEP 1 or at the STEP 4 fetch (2026-11-20T19:11:07Z, chunk 14 running). No chunk after the reserved 300 openings. play.sh stopped with "openings used up" after chunk 26, before minute 46.

# what I am NOT sure about

I compared the both-on row sum only with seats 001, 002, 003, 004 and 005, not with every seat. I did not re-pool each chunk on its own. POOL.txt is one pool of all 26 tsv files. The binary behind the numbers is the g++ rebuild, after the Clang configure failed.

# times: see stamps.txt

First stamps line: 2026-11-20T18:49:20Z STEP 1. Last chunk line: 2026-11-20T19:26:35Z chunk 26 done. STEP 5 line: 2026-11-20T19:30:42Z STEP 5.

# git status --short

 M forge-combo29/grok3/014/stamps.txt
?? config.json
?? forge-combo29/grok3/014/POOL.txt
?? forge-combo29/grok3/014/REPORT.md
?? forge-combo29/grok3/014/RESULT.txt

# ls -la

This listing was run while REPORT.md still held placeholders and was 6323 bytes. Inserting the listing into REPORT.md grew that file. Every other size is the committed file.

total 5768
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:31 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu   2271 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110337 Nov 20 19:06 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102469 Nov 20 19:06 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 110836 Nov 20 19:07 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102522 Nov 20 19:07 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 110695 Nov 20 19:08 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102658 Nov 20 19:08 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 111230 Nov 20 19:09 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102734 Nov 20 19:09 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 110881 Nov 20 19:11 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102634 Nov 20 19:11 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110857 Nov 20 19:12 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102580 Nov 20 19:12 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110696 Nov 20 19:13 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102658 Nov 20 19:13 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 110639 Nov 20 19:15 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102405 Nov 20 19:15 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 110598 Nov 20 19:16 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102327 Nov 20 19:16 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 110310 Nov 20 19:17 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102387 Nov 20 19:17 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 109797 Nov 20 18:54 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102193 Nov 20 18:54 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 110716 Nov 20 19:18 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102784 Nov 20 19:18 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 111121 Nov 20 19:20 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102721 Nov 20 19:20 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110843 Nov 20 19:21 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102516 Nov 20 19:21 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 110269 Nov 20 19:22 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102336 Nov 20 19:22 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110993 Nov 20 19:24 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102548 Nov 20 19:24 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110661 Nov 20 19:25 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102516 Nov 20 19:25 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110922 Nov 20 19:26 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102434 Nov 20 19:26 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110955 Nov 20 18:55 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102357 Nov 20 18:55 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110705 Nov 20 18:56 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102754 Nov 20 18:56 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110707 Nov 20 18:58 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102366 Nov 20 18:58 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 111106 Nov 20 18:59 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102685 Nov 20 18:59 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110936 Nov 20 19:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102481 Nov 20 19:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 111444 Nov 20 19:01 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102685 Nov 20 19:01 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110968 Nov 20 19:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102569 Nov 20 19:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110283 Nov 20 19:04 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102427 Nov 20 19:04 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45527 Nov 20 18:52 half.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu  41922 Nov 20 18:52 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:50 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:50 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu   1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:28 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6323 Nov 20 19:31 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:30 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 19:30 stamps.txt

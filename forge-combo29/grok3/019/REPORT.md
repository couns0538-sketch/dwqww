# grok3 seat 019

Seat 019, arm 1, 20,000 nodes. Chunk size 250 openings (500 games). Match is main: IdeaB8 and HindsightDepth both on, against both off. Model name passed to take_seat3.sh: Grok 4.7.

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

That is the required hash. The blob came from commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75, path forge-combo29/grok/028/idea.patch.txt. `git apply --check` and `git apply` both succeeded (the command printed APPLY_OK).

The first cmake used /usr/bin/c++ (Clang 18.1.3) and failed to link: `cannot find -lstdc++`. The brief requires g++ (GCC 13 or newer, GCC's own C++ library). I removed ~/build and configured again with CXX=g++. g++ is GCC 13.3.0 and a one-line program linked. /proc/cpuinfo has avx512f and bmi2, so I did not add -DFORGE_PORTABLE=ON or -DFORGE_MARCH. The engine file used for every later command is /home/ubuntu/build/forge. Its sha256, recorded in each .meta file, is 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422. id name: Chess Engine Forge 6.4.24 candidate.

## Honesty

A fresh process for each line, no setoption before the command. Raw output is in this folder.

- bench 11: nodes 312866 (required 312866)
- bench 13: nodes 862329 (required 862329)
- bench 16: nodes 3024920 (required 3024920)
- go perft 5: nodes 4865609 (required 4865609)

## Four O runs

Known text, and what the saved rows say (recomputed from the files):

(1) both off. Required sum 9,500,069, first three 41,311 / 24,872 / 28,574, sha256 dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. Got that sum, those three, and that sha256 of o_off.rows.txt. off_ok=yes.

(2) IdeaB8 on, HindsightDepth off. Required sum 9,718,009, first three 17,283 / 17,878 / 31,115. Got that. b8_ok=yes.

(3) IdeaB8 off, HindsightDepth on. Required sum 9,845,650, first three 23,395 / 31,504 / 35,958. Got that. k3_ok=yes.

(4) both on. No required answer. Sum 9,758,416. First three 18,538 / 34,070 / 39,093. Positions whose node count differs from (1): 200 of 200.

## Book

~/uho.zip sha256 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 (required hash, book=ok).

~/uho.epd: 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a (required).

Seat openings: awk from line 2150000+19, every 36th line, wrote ~/mine.epd with 13390 lines. Controls used the last 300 of those lines (10 arrive, 200 half). Chunks took lines from the top and stopped at chunk 11, which ends at line 2750, short of those 300.

## games_tsv.py known answer

~/ka.tsv sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd (required).

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]

That is the required text. tsv_ka=ok.

## C-ARRIVE

`grep -c` on ~/arrive.log:

- setoption name IdeaB8 value true: 20
- setoption name HindsightDepth value true: 20
- unknown option|invalid value|no such option: 0

arrive=ok. The three counts and 20 log lines around the first IdeaB8 setoption are in arrive_check.txt. The whole log was not committed.

## C-HALF

`python3 ~/games_tsv.py pool FULL` on half.tsv printed:

side FULL: games 400 W-L-D 260-53-87 pairs 200 (openings not in exactly 2 games: 0)
ptnml [4, 9, 44, 62, 81] Elo +199.05 95% [+167.87, +233.44]

The finished-match line in half.out is Elo: 199.05 +/- 32.79, Games: 400, Wins: 260, Losses: 53, Draws: 87. FULL's Elo is above +20. half_elo=+199.05.

## Pool

Chunks: 11. Each chunk is 500 games. Play.sh stopped itself with "minute 46: no new chunk" after chunk 11. Chunk 11 finished at 2026-11-20T19:39:02Z, before minute 51 (19:40:23Z). No chunk was killed. Every chunk_*.tsv termination field is "normal" (5500 of 5500).

Pasted POOL.txt:

side ON: games 5500 W-L-D 1613-1364-2523 pairs 2750 (openings not in exactly 2 games: 0)
ptnml [110, 613, 1127, 718, 182] Elo +15.74 95% [+9.57, +21.92]

## Suspicions, not proven

The point +15.74 is nearer "the two add" (about +17) than "they overlap" (about +10). The 95% interval [+9.57, +21.92] still covers both of those figures. I do not call the question decided.

Run (4)'s node sum 9,758,416 sits between run (2) 9,718,009 and run (3) 9,845,650, and all 200 positions changed their node count versus both off. That is consistent with both options doing something at once. It is not an Elo result.

## What I did NOT do

I did not change engine source, commit an exe, a net, a PGN, or the book. I did not open a pull request. I did not play the fallback match. I did not pass -draw, -resign, -maxmoves, or tablebases. I did not start a chunk after play.sh's minute-46 check. I did not repeat an opening. This seat did not play 2,000 or 60,000 nodes.

No forge-combo29/soak_all/FABLE_TO_grok3_<N>.md existed on handoff/fable-opus-combo29-all-20261114 at step 1 or in the middle of step 4 (git ls-tree | grep FABLE_TO_grok3_ printed none). I did not touch ~/STOP_PLAY.

fastchess wrote config.json in the repository root while the two controls ran with that directory as cwd, and another in the home directory while the chunks ran. Both have resign, draw, maxmoves, and tb_adjudication enabled set to false. I did not git add either file.

## What I am NOT sure about

I am sure of the numbers above because I recomputed them from the committed row files and from POOL.txt. I am not sure the +15.74 interval is narrow enough for the owner's next test. I am not sure fastchess and games_tsv.py round Elo the same way on every sample; on this half match and on the known-answer file they printed the same Elo to two decimals.

The Clang configure failed before any engine binary existed. I am sure the measured binary is the g++ one named in the .meta files, because runs (1) (2) and (3) then matched the known node counts.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok3/019/stamps.txt
?? config.json
?? forge-combo29/grok3/019/POOL.txt
?? forge-combo29/grok3/019/REPORT.md
?? forge-combo29/grok3/019/RESULT.txt
```

## ls -la forge-combo29/grok3/019

```
total 1384
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:41 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2288 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56358 Nov 20 19:34 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51360 Nov 20 19:34 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 55606 Nov 20 19:39 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 51432 Nov 20 19:39 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 56028 Nov 20 18:57 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51585 Nov 20 18:57 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56361 Nov 20 19:01 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51598 Nov 20 19:01 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56552 Nov 20 19:05 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51482 Nov 20 19:05 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56071 Nov 20 19:09 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51444 Nov 20 19:09 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56125 Nov 20 19:14 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51635 Nov 20 19:14 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56338 Nov 20 19:18 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51571 Nov 20 19:18 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56133 Nov 20 19:22 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51596 Nov 20 19:22 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56053 Nov 20 19:26 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51704 Nov 20 19:26 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56218 Nov 20 19:30 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51503 Nov 20 19:30 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:53 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45789 Nov 20 18:53 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:53 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42049 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:50 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:53 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:51 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:53 play.sh
-rw-r--r-- 1 ubuntu ubuntu   153 Nov 20 19:39 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6193 Nov 20 19:41 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   294 Nov 20 19:41 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   542 Nov 20 19:41 stamps.txt
```

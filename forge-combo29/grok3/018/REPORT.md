# grok3 seat 018 report

Seat 018, arm 3, 60,000 nodes, chunk size 100 openings (200 games). Model Grok 4.7. Match is the main match: IdeaB8=true and HindsightDepth=true (ON) against IdeaB8=false and HindsightDepth=false (OFF). Branch for-fable-and-opus/grok3-018. Local branch grok3-seat.

## Patch and build

Patch file ~/b8.patch from 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt.
sha256sum ~/b8.patch printed f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474, the required digest.
git apply --check ~/b8.patch and git apply ~/b8.patch both exited 0 (the shell printed APPLY OK) in the work tree ../work at base 6b98f2170a3210e71beed04bbd2553972c253ed7.
The default /usr/bin/c++ is Clang 18.1.3 and its link failed with "cannot find -lstdc++". The brief requires g++ (GCC 13 or newer, GCC's own C++ library). I configured with -DCMAKE_CXX_COMPILER=g++ (GCC 13.3.0). /proc/cpuinfo has avx512f and bmi2, so I did not add -DFORGE_PORTABLE=ON. The engine is /home/ubuntu/build/forge. Nothing of the build was committed.
The four .meta files name that exe, sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422, id name Chess Engine Forge 6.4.24 candidate.

## Honesty

Fresh processes, no setoption. Files in this folder:

- honesty_bench11.txt: info string bench depth 11 nodes 312866
- honesty_bench13.txt: info string bench depth 13 nodes 862329
- honesty_bench16.txt: info string bench depth 16 nodes 3024920
- honesty_perft5.txt ends with nodes 4865609

Those are the required counts. honesty=ok.

## Four O runs

Compared with the known text. Counts below are recomputed from the committed row files.

(1) o_off.rows.txt IdeaB8=false HindsightDepth=false. Required sum 9,500,069, first three 41,311 / 24,872 / 28,574, sha256 dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. File: 200 rows, sum 9500069, first three 41311 / 24872 / 28574. sha256sum of the file printed that digest. off_ok=yes.

(2) o_b8.rows.txt IdeaB8=true HindsightDepth=false. Required sum 9,718,009, first three 17,283 / 17,878 / 31,115. File: sum 9718009, first three 17283 / 17878 / 31115. b8_ok=yes.

(3) o_k3.rows.txt IdeaB8=false HindsightDepth=true. Required sum 9,845,650, first three 23,395 / 31,504 / 35,958. File: sum 9845650, first three 23395 / 31504 / 35958. k3_ok=yes.

(4) o_both.rows.txt IdeaB8=true HindsightDepth=true. No known answer. File: sum 9758416, first three 18538 / 34070 / 39093. Positions whose node count differs from (1), paste of the two row files with awk '$2 != $5': 200. both_differ=200.

The four processes ran at the same time, one engine each. (1), (2) and (3) matched the known numbers, so I did not rerun them.

## Book

sha256sum ~/uho.zip printed 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07.
wc -l ~/uho.epd printed 2632036. sha256sum ~/uho.epd printed 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a.
Both match the brief. book=ok.
~/mine.epd is 13390 lines (seat 018, lines at or after 2,150,018, every 36th). Chunks 1 to 9 used lines 1 to 900. The control 300 lines are the tail and were not used as chunk openings.

## games_tsv.py known answer

sha256sum ~/ka.tsv printed 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.
python3 ~/games_tsv.py pool ON ~/ka.tsv printed:
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
That is the required text. tsv_ka=ok.

## C-ARRIVE and C-HALF

C-ARRIVE: bash ~/match.sh ~/ctl_arrive.epd 10, fastchess trace log. Counts in arrive_check.txt, which I opened:
grep -c setoption name IdeaB8 value true: 20
grep -c setoption name HindsightDepth value true: 20
grep -c -i -E unknown option|invalid value|no such option: 0
The same file holds arrive.log lines 519-538 around the first IdeaB8 setoption. arrive=ok.

C-HALF: bash ~/half.sh ~/ctl_half.epd 200. half.out (opened) ends with:
Results of FULL vs HALF (2000 nodes - 1000 nodes, 1t, 16MB, ctl_half.epd):
Elo: 246.30 +/- 36.90, nElo: 313.92 +/- 34.05
Games: 400, Wins: 286, Losses: 42, Draws: 72
Ptnml(0-2): [3, 5, 41, 47, 104]
Finished match
python3 ~/games_tsv.py pool FULL on half.tsv printed:
side FULL: games 400 W-L-D 286-42-72 pairs 200 (openings not in exactly 2 games: 0)
ptnml [3, 5, 41, 47, 104] Elo +246.30 95% [+211.79, +285.60]
FULL's Elo is above +20. half_elo=+246.30. Passed on the first run.

## POOL.txt and chunks

9 chunks, each 200 games, 1800 games. play.sh logged "minute 46: no new chunk" and exited. No "FAILED" line in ~/play.log. Each chunk_N.tsv is 200 lines. Pasted POOL.txt:

side ON: games 1800 W-L-D 483-427-890 pairs 900 (openings not in exactly 2 games: 0)
ptnml [23, 207, 396, 239, 35] Elo +10.81 95% [+0.98, +20.66]

## suspicions, not proven

The point estimate +10.81 at 60,000 nodes sits nearer an overlap of about +10 than a sum of about +17. The 95% interval [+0.98, +20.66] still contains both, so this seat does not decide that question.
both_differ=200 means every one of the 200 positions changed its node count with both ideas on. That is the measured count. I have not seen another seat's run (4), so I cannot tell whether 9758416 is the common value.
An untracked config.json (7207 bytes, mtime 19:37Z) appeared in the repository root while chunk 9 was running. It is a fastchess config. Its resign, draw, maxmoves and tb_adjudication enabled fields are false. I did not add it. I do not know a second writer besides fastchess using this directory as its current folder.

## what I did NOT do

I did not open a pull request. I did not use --force. I did not commit an engine source file, an executable, a net, a PGN, or config.json. I did not add adjudication (no -draw, -resign, -maxmoves, no tablebases). I did not play the fallback match. I did not start a chunk after minute 46. I did not kill a chunk: chunk 9 finished at 2026-11-20T19:37:29Z, and minute 51 was 2026-11-20T19:40:06Z. I did not set git user.name; it was already set, and the commits succeeded. The channel branch had no forge-combo29/soak_all/FABLE_TO_grok3_*.md at step 1 or in the middle of step 4, so no extra order applied.

## what I am NOT sure about

I am not sure that other seats printed the same both_sum 9758416. I am not sure the population Elo at 60,000 nodes is +10.81; the interval above is the uncertainty from these 900 pairs. I am sure the known honesty numbers, runs (1) (2) (3), the book hashes, the games_tsv known answer, C-ARRIVE and C-HALF matched the files named here, because I recomputed them from those files before writing this report.

## times: see stamps.txt

2026-11-20T18:49:06Z STEP 1 seat
2026-11-20T18:51:18Z STEP 2 honesty and O runs
2026-11-20T18:53:41Z STEP 3 controls
2026-11-20T18:58:43Z chunk 1 done
2026-11-20T19:03:30Z chunk 2 done
2026-11-20T19:08:26Z chunk 3 done
2026-11-20T19:13:23Z chunk 4 done
2026-11-20T19:18:32Z chunk 5 done
2026-11-20T19:23:07Z chunk 6 done
2026-11-20T19:27:48Z chunk 7 done
2026-11-20T19:32:39Z chunk 8 done
2026-11-20T19:37:29Z chunk 9 done
2026-11-20T19:39:33Z STEP 5 pool report

The status and listing below were taken after RESULT.txt, POOL.txt, this report and the step 5 stamp existed, and before the step 5 commit. The commit adds the seat-folder paths that status shows as new or modified. config.json stays untracked.

## git status --short

 M forge-combo29/grok3/018/stamps.txt
?? config.json
?? forge-combo29/grok3/018/POOL.txt
?? forge-combo29/grok3/018/REPORT.md
?? forge-combo29/grok3/018/RESULT.txt

## ls -la

total 632
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:41 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2313 Nov 20 18:53 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22396 Nov 20 18:58 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20648 Nov 20 18:58 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22405 Nov 20 19:03 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20675 Nov 20 19:03 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22309 Nov 20 19:08 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20650 Nov 20 19:08 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22504 Nov 20 19:13 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20714 Nov 20 19:13 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22534 Nov 20 19:18 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20738 Nov 20 19:18 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22792 Nov 20 19:23 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20773 Nov 20 19:23 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22265 Nov 20 19:27 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20711 Nov 20 19:27 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22420 Nov 20 19:32 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20640 Nov 20 19:32 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 22675 Nov 20 19:37 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 20752 Nov 20 19:37 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45555 Nov 20 18:53 half.out
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42103 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:50 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:50 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:38 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu 10213 Nov 20 19:41 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:41 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   463 Nov 20 19:39 stamps.txt

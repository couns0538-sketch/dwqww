# grok3 seat 022 report

Seat 022, arm 1, 20,000 nodes. Chunk size 250 openings (500 games). Match is the main match: ON (IdeaB8=true, HindsightDepth=true) against OFF (both false). Local branch grok3-seat, remote for-fable-and-opus/grok3-022.

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

That is the required hash. The bytes came from `git show 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt` after `git rev-parse FETCH_HEAD` printed 4bf95fd80adf523e97fa250bb8572c946cf0fc75.

`git apply --check ~/b8.patch && git apply ~/b8.patch` in the work tree ../work (base 6b98f2170a3210e71beed04bbd2553972c253ed7) printed APPLY_OK at 2026-11-20T18:50:08Z. The patch is not committed. No engine source file was committed.

`/usr/bin/c++` on this machine is Clang 18.1.3 and the first cmake failed to link libstdc++. I configured again with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0). CPU flags include AVX-512 and BMI2, so I did not add FORGE_PORTABLE. The built exe is /home/ubuntu/build/forge. CMakeCache CMAKE_CXX_COMPILER is /usr/bin/g++.

## Honesty

Fresh processes, no setoption before the command. Raw files in this folder:

- bench 11: nodes 312866 (honesty_bench11.txt)
- bench 13: nodes 862329 (honesty_bench13.txt)
- bench 16: nodes 3024920 (honesty_bench16.txt)
- go perft 5: nodes 4865609 (honesty_perft5.txt)

These are the required numbers.

## Four O runs

first200.fens sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines.

Required text, and what this build printed:

1. IdeaB8=false HindsightDepth=false: required sum 9,500,069, first three 41,311 / 24,872 / 28,574. Printed rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574. File sums from the rows: 9500069, first nodes 41311, 24872, 28574. sha256 of o_off.rows.txt: dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7 (the required hash).
2. IdeaB8=true HindsightDepth=false: required sum 9,718,009, first three 17,283 / 17,878 / 31,115. Printed that. File sum 9718009, first nodes 17283, 17878, 31115.
3. IdeaB8=false HindsightDepth=true: required sum 9,845,650, first three 23,395 / 31,504 / 35,958. Printed that. File sum 9845650, first nodes 23395, 31504, 35958.
4. IdeaB8=true HindsightDepth=true: no required sum. Printed rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093. File sum 9758416, first nodes 18538, 34070, 39093. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200.

## Book

~/uho.zip sha256 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 (matches the stated copy).

~/uho.epd: 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a (matches). book=ok.

~/mine.epd: 13390 lines. Controls taken from its last 300 lines (ctl_arrive 10, ctl_half 200). Chunks used lines from the top and did not reach those 300.

## games_tsv.py known answer

~/ka.tsv sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]

That is the required print. tsv_ka=ok.

## C-ARRIVE

Counts in arrive_check.txt, from the trace log:

grep -c "setoption name IdeaB8 value true" 20
grep -c "setoption name HindsightDepth value true" 20
grep -c -i -E "unknown option|invalid value|no such option" 0

The same file has the 20 log lines around the first `setoption name IdeaB8 value true` (arrive.log line 398). arrive=ok.

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok3/022/half.tsv` printed:

side FULL: games 400 W-L-D 269-46-85 pairs 200 (openings not in exactly 2 games: 0)
ptnml [5, 4, 40, 65, 86] Elo +218.61 95% [+186.69, +254.18]

FULL Elo +218.61 is above +20. half_elo=+218.61. Passed.

## POOL.txt

10 chunks, each 500 games, 5000 games. Openings not in exactly 2 games: 0. Pasted POOL.txt:

side ON: games 5000 W-L-D 1452-1254-2294 pairs 2500 (openings not in exactly 2 games: 0)
ptnml [83, 589, 1030, 643, 155] Elo +13.77 95% [+7.42, +20.12]

Number of chunks: 10.

Every chunk tsv line has a score. Termination field is "normal" on all 5000 games. fastchess wrote an untracked config.json in the repository root during the last chunk; resign, draw, maxmoves, and tb_adjudication are all "enabled": false. I did not pass -draw, -resign, -maxmoves, or tablebases. The .out files contain 0 lines matching adjudication. I did not commit config.json.

## suspicions, not proven

None. The clang link failure was a toolchain mismatch; after the g++ rebuild the honesty numbers and runs 1 to 3 matched the known values, so that fault is closed.

## what I did NOT do

I did not open a pull request. I did not change engine source. I did not commit the exe, the patch, a PGN, or the book. I did not play the fallback match. I did not start a chunk after minute 46 (first stamp 2026-11-20T18:49:23Z; minute 46 is 19:35:23Z). Chunk 10 had already started (chunk 9 finished 19:32:57Z) and finished 19:37:15Z. play.sh then printed "minute 46: no new chunk" and exited. I did not kill fastchess. I did not repeat an opening. I did not read other seats' run-4 numbers. No FABLE_TO_grok3 file existed on handoff/fable-opus-combo29-all-20261114 at STEP 1 or at 2026-11-20T19:09:01Z.

## what I am NOT sure about

Run 4 has no published known sum. My both_sum is 9758416, both_first3 is 18538/34070/39093, both_differ is 200. I have not compared that to another seat. I am not sure the other seats print the same run 4.

## times: see stamps.txt

2026-11-20T18:49:23Z STEP 1
2026-11-20T18:52:44Z STEP 2
2026-11-20T18:54:38Z STEP 3
2026-11-20T18:58:57Z chunk 1 done
2026-11-20T19:03:09Z chunk 2 done
2026-11-20T19:07:20Z chunk 3 done
2026-11-20T19:11:27Z chunk 4 done
2026-11-20T19:15:47Z chunk 5 done
2026-11-20T19:20:04Z chunk 6 done
2026-11-20T19:24:21Z chunk 7 done
2026-11-20T19:28:40Z chunk 8 done
2026-11-20T19:32:57Z chunk 9 done
2026-11-20T19:37:15Z chunk 10 done
2026-11-20T19:40:07Z STEP 5


## git status --short

```
 M forge-combo29/grok3/022/stamps.txt
?? config.json
?? forge-combo29/grok3/022/POOL.txt
?? forge-combo29/grok3/022/REPORT.md
?? forge-combo29/grok3/022/RESULT.txt
```

## ls -la forge-combo29/grok3/022

```
total 1276
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:40 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2307 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56363 Nov 20 19:37 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51588 Nov 20 19:37 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 55917 Nov 20 18:58 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51500 Nov 20 18:58 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56197 Nov 20 19:03 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51567 Nov 20 19:03 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 55981 Nov 20 19:07 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51496 Nov 20 19:07 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56611 Nov 20 19:11 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51774 Nov 20 19:11 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56349 Nov 20 19:15 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51619 Nov 20 19:15 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56170 Nov 20 19:20 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51584 Nov 20 19:20 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56115 Nov 20 19:24 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51543 Nov 20 19:24 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56089 Nov 20 19:28 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51478 Nov 20 19:28 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56292 Nov 20 19:32 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51548 Nov 20 19:32 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45783 Nov 20 18:54 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42044 Nov 20 18:54 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
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
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu   152 Nov 20 19:38 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6337 Nov 20 19:40 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   293 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    90 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   453 Nov 20 19:40 stamps.txt
```

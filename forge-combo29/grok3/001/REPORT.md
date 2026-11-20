# grok3 seat 001

Seat 001, arm 1, 20,000 nodes, chunk 250 openings (500 games). Match main: both ideas on (IdeaB8 and HindsightDepth) against both off. take_seat3.sh model argument: Grok 4.7.

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

The patch bytes came from 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt. git rev-parse FETCH_HEAD after fetching for-fable-and-opus/grok-028 printed that same hash. git apply --check and git apply on the worktree at 6b98f2170a3210e71beed04bbd2553972c253ed7 both succeeded.

CMake used g++ (GCC 13.3.0). /usr/bin/c++ on this machine is clang++ 18, and cmake's first try failed at link with "cannot find -lstdc++". The build line therefore added -DCMAKE_CXX_COMPILER=g++ and -DCMAKE_C_COMPILER=gcc. The CPU reports avx512f and bmi2, so FORGE_PORTABLE was left off. The engine file is /home/ubuntu/build/forge. No engine source, object, or executable was committed.

## Honesty

Each line is a fresh process of /home/ubuntu/build/forge with no setoption before the command.

- honesty_bench11.txt: info string bench depth 11 nodes 312866 (expected 312866)
- honesty_bench13.txt: info string bench depth 13 nodes 862329 (expected 862329)
- honesty_bench16.txt: info string bench depth 16 nodes 3024920 (expected 3024920)
- honesty_perft5.txt: nodes 4865609 (expected 4865609)

honesty ok.

## Four O runs

Same exe, sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422, id name Chess Engine Forge 6.4.24 candidate. Sums below were recomputed from the row files.

(1) IdeaB8=false HindsightDepth=false. rows 200, sum 9500069, first three 41311 / 24872 / 28574. Expected sum 9500069 and first three 41311 / 24872 / 28574. sha256 of o_off.rows.txt: dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7, which is the expected hash. off_ok yes.

(2) IdeaB8=true HindsightDepth=false. rows 200, sum 9718009, first three 17283 / 17878 / 31115. Expected sum 9718009 and first three 17283 / 17878 / 31115. b8_ok yes.

(3) IdeaB8=false HindsightDepth=true. rows 200, sum 9845650, first three 23395 / 31504 / 35958. Expected sum 9845650 and first three 23395 / 31504 / 35958. k3_ok yes.

(4) IdeaB8=true HindsightDepth=true. rows 200, sum 9758416, first three 18538 / 34070 / 39093. No expected sum was given. Positions whose node count differs from (1), from `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l`: 200. o_both.rows.txt.meta sends IdeaB8 true and HindsightDepth true.

## Book

~/uho.zip sha256 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07. That matches the given hash.

~/uho.epd: 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a. That matches the given line count and hash. book ok.

~/mine.epd: 13390 lines. The last 300 lines were kept for the controls (ctl.epd 300, ctl_arrive.epd 10, ctl_half.epd 200). Chunks used lines from the top and stopped at chunk 10 (2,500 openings), short of those 300 lines.

## games_tsv.py known answer

~/ka.tsv from for-fable-and-opus/grok2-004:forge-combo29/grok2/004/chunk_1.tsv, sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.

python3 ~/games_tsv.py pool ON ~/ka.tsv printed:

    side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
    ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]

That is the known answer. tsv_ka ok.

## C-ARRIVE

Command: bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true

arrive_check.txt counts:

    setoption name IdeaB8 value true: 20
    setoption name HindsightDepth value true: 20
    unknown option|invalid value|no such option: 0

The same file holds the 20 log lines around the first IdeaB8 setoption (arrive.log lines 520-539). Those lines include `ON <--- setoption name IdeaB8 value true` and `ON <--- setoption name HindsightDepth value true`. arrive ok.

## C-HALF

Command: bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn, then games_tsv.py tsv and pool FULL on half.tsv.

python3 ~/games_tsv.py pool FULL forge-combo29/grok3/001/half.tsv printed:

    side FULL: games 400 W-L-D 280-50-70 pairs 200 (openings not in exactly 2 games: 0)
    ptnml [3, 6, 45, 50, 96] Elo +227.56 95% [+194.53, +264.65]

FULL's Elo is above +20. half_elo +227.56. Passed on the first run. fastchess's own summary in half.out also says Elo: 227.56 for FULL vs HALF.

## Pool

10 chunks. POOL.txt, from `python3 ~/games_tsv.py pool ON forge-combo29/grok3/001/chunk_*.tsv`:

    side ON: games 5000 W-L-D 1480-1222-2298 pairs 2500 (openings not in exactly 2 games: 0)
    ptnml [99, 554, 995, 694, 158] Elo +17.94 95% [+11.47, +24.43]

Each chunk_*.tsv has 500 lines (5000 games). Each chunk's fastchess log contains "Finished match". play.sh committed and pushed each chunk. After chunk 10, play.sh printed "minute 46: no new chunk" and exited.

## suspicions, not proven

The both-on node sum (9758416) sits next to IdeaB8 alone (9718009) and under HindsightDepth alone (9845650). That is a count of nodes at depth 12. The Elo measurement is the POOL.txt line, +17.94 with 95% interval [+11.47, +24.43].

fastchess wrote config.json in the repository root during chunk 10, because play.sh was started with that directory as the working directory. In that file the resign, draw, maxmoves, and tb_adjudication objects each have "enabled": false. The file was not committed. It is not an instruction.

## what I did NOT do

No pull request. No --force. No commit of an executable, a net, a PGN, or any engine source. The patch lives only in the outside worktree. No adjudication flags were passed to fastchess. The fallback match was not played. C-HALF was not rerun. No chunk was killed: chunk 10's stamp is 2026-11-20T19:37:38Z, and minute 51 after the first stamp 2026-11-20T18:48:39Z is 2026-11-20T19:39:39Z. config.json was not committed. The channel fetch at step 1 and again at 2026-11-20T19:11:42Z listed no forge-combo29/soak_all/FABLE_TO_grok3_*.md file.

## what I am NOT sure about

I have not compared run (4) with another seat. This seat's both sum is 9758416, and 200 of 200 positions differ in node count from run (1). Whether every other seat printed that same pair is outside this run.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok3/001/stamps.txt
?? config.json
?? forge-combo29/grok3/001/POOL.txt
?? forge-combo29/grok3/001/REPORT.md
?? forge-combo29/grok3/001/RESULT.txt
```

## ls -la forge-combo29/grok3/001

```
total 1276
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:40 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2262 Nov 20 18:53 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 55896 Nov 20 19:37 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51595 Nov 20 19:37 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 56382 Nov 20 18:58 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51781 Nov 20 18:58 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56448 Nov 20 19:02 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51595 Nov 20 19:02 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 55895 Nov 20 19:07 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51470 Nov 20 19:07 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56383 Nov 20 19:11 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51749 Nov 20 19:11 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56885 Nov 20 19:16 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51686 Nov 20 19:16 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56000 Nov 20 19:20 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51497 Nov 20 19:20 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56187 Nov 20 19:24 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51716 Nov 20 19:24 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 55915 Nov 20 19:29 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51768 Nov 20 19:29 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56252 Nov 20 19:33 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51587 Nov 20 19:33 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45856 Nov 20 18:53 half.out
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41893 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:54 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu   152 Nov 20 19:39 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6564 Nov 20 19:40 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   293 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    88 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   516 Nov 20 19:40 stamps.txt
```

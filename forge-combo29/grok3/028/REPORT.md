# grok3 seat 028

Seat 028, arm 1, 20000 nodes. Chunk size 250 openings (500 games). Match is main: both ideas ON (IdeaB8=true, HindsightDepth=true) against both OFF.

Patch sha256 f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474, equal to the required hash. `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both succeeded on the work tree at 6b98f2170a3210e71beed04bbd2553972c253ed7. The patch bytes came from 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt.

Honesty, each a fresh process with no setoption, from the saved files:
- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609
All four match the known numbers.

Four O runs, against the known text. (1) must be sum 9,500,069, first three 41,311 / 24,872 / 28,574, and sha256 of o_off.rows.txt dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. Printed and saved in o_prints.txt: rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574, and that sha256. (2) must be sum 9,718,009, first three 17,283 / 17,878 / 31,115. Printed: rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115. (3) must be sum 9,845,650, first three 23,395 / 31,504 / 35,958. Printed: rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958. (4) has no known answer. Printed: rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093. Positions whose node count differs from (1): 200 (paste of the two row files, awk '$2 != $5' | wc -l).

Book sha256 of ~/uho.zip: 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07. ~/uho.epd: 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a. Both match the known copy. mine.epd has 13390 lines.

Known answer of games_tsv.py: ka.tsv sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd. Printed:
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
That matches.

C-ARRIVE: grep counts in arrive.log, saved in arrive_check.txt: setoption name IdeaB8 value true = 20, setoption name HindsightDepth value true = 20, unknown option|invalid value|no such option = 0. Pass.
C-HALF: pool of half.tsv, saved in half_pool.txt:
side FULL: games 400 W-L-D 267-47-86 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 9, 43, 63, 84] Elo +214.85 95% [+184.47, +248.46]
FULL Elo is above +20. Pass.

POOL.txt pasted here. Chunks: 9.
side ON: games 4500 W-L-D 1342-1097-2061 pairs 2250 (openings not in exactly 2 games: 0)
ptnml [91, 491, 893, 632, 143] Elo +18.93 95% [+12.10, +25.79]

suspicions, not proven
None.

what I did NOT do
I did not open a pull request. I did not change any engine source. I did not play the fallback match. I did not pass -draw, -resign, -maxmoves, or tablebases. I did not force-push, and I did not push any branch except for-fable-and-opus/grok3-028. I did not commit the engine binary, a net, a PGN, or config.json. I did not start a new chunk after minute 46. No file named FABLE_TO_grok3_<N>.md was on the handoff branch at step 1 or in the middle of step 4, so there was no channel note to apply. I did not sleep 60 after setup_bg, because ~/setup_bg.log had already printed fastchess OK, python-chess OK, book OK, and setup_bg done.

what I am NOT sure about
The first cmake used /usr/bin/c++ (clang 18) and failed to link libstdc++. I configured again with -DCMAKE_CXX_COMPILER=g++ (g++ 13.3.0). The machine has AVX-512 and BMI2, so I did not add FORGE_PORTABLE. After that build, the honesty numbers and O runs (1) (2) (3) matched, so I treat this binary as the required engine. I did not compare its sha256 with another seat. fastchess wrote config.json in the repository root and in $HOME; resign, draw, maxmoves, and tablebase adjudication are enabled false in that file. A grep of the nine chunk .out files for adjudication, resign, maxmoves, and tablebase returned 0 lines. Every TSV termination field is the word normal. Chunk 1's .out endings are mates, threefold, fifty-move, insufficient material, and stalemate.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok3/028/stamps.txt
?? config.json
?? forge-combo29/grok3/028/POOL.txt
?? forge-combo29/grok3/028/REPORT.md
?? forge-combo29/grok3/028/RESULT.txt
```

```
$ ls -la forge-combo29/grok3/028
total 1176
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:38 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2196 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56446 Nov 20 19:00 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51673 Nov 20 19:00 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56391 Nov 20 19:04 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51738 Nov 20 19:04 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56075 Nov 20 19:09 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51565 Nov 20 19:09 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56104 Nov 20 19:14 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51580 Nov 20 19:14 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56297 Nov 20 19:18 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51838 Nov 20 19:18 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56334 Nov 20 19:23 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51664 Nov 20 19:23 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56330 Nov 20 19:27 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51524 Nov 20 19:27 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56352 Nov 20 19:32 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51561 Nov 20 19:32 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 55700 Nov 20 19:36 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51588 Nov 20 19:36 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45828 Nov 20 18:55 half.out
-rw-r--r-- 1 ubuntu ubuntu   144 Nov 20 18:55 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42079 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:54 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   606 Nov 20 18:53 o_prints.txt
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:51 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu   152 Nov 20 19:37 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  7142 Nov 20 19:38 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   292 Nov 20 19:38 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   463 Nov 20 19:38 stamps.txt
```

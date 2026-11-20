# grok3 seat 026

Seat 026, arm 2, 2,000 nodes. Match is the main match: both ideas on (IdeaB8=true, HindsightDepth=true) against both off. Chunk size 500 openings (1,000 games). Model name passed to take_seat3.sh: Grok 4.7. SEAT.txt records the seat line.

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

Source commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75, file forge-combo29/grok/028/idea.patch.txt. `git apply --check` then `git apply` on the work tree at 6b98f2170a3210e71beed04bbd2553972c253ed7. Both succeeded (APPLY OK).

Build: CMake Release with g++ 13.3.0 (`-DCMAKE_CXX_COMPILER=g++`). The machine has AVX-512 and BMI2, so no FORGE_PORTABLE / FORGE_MARCH flags. The first configure used /usr/bin/c++ (clang 18) and failed to link libstdc++; I wiped the build directory and configured again with g++. Honesty and the three known O runs then matched, so that binary is the one measured. Exe: /home/ubuntu/build/forge. Meta sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422. id name Chess Engine Forge 6.4.24 candidate.

## Honesty

Raw files in this folder, one fresh process each, no setoption before the command:

- honesty_bench11.txt: info string bench depth 11 nodes 312866 time 163 nps 1919423
- honesty_bench13.txt: info string bench depth 13 nodes 862329 time 429 nps 2010090
- honesty_bench16.txt: info string bench depth 16 nodes 3024920 time 1417 nps 2134735
- honesty_perft5.txt last line: nodes 4865609

These are the known numbers (312866, 862329, 3024920, 4865609).

## Four O runs

Against the brief's known text. Each meta file records the option lines.

1. o_off.rows.txt IdeaB8=false HindsightDepth=false. Printed: rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574. sha256 dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7. Matches the known sum, first three, and sha256.
2. o_b8.rows.txt IdeaB8=true HindsightDepth=false. Printed: rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115. Matches.
3. o_k3.rows.txt IdeaB8=false HindsightDepth=true. Printed: rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958. Matches.
4. o_both.rows.txt IdeaB8=true HindsightDepth=true. No known answer. Printed: rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093. File head: `1 18538 f1e2`, `2 34070 f1c4`, `3 39093 e5d4`. Positions whose node count differs from run 1: 200 (`paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l`).

## Book

~/uho.zip sha256 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 (matches). ~/uho.epd 2632036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a (matches). Seat openings: 13390 lines in mine.epd. Controls taken from the last 300 lines.

## games_tsv.py known answer

~/ka.tsv sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd.

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

Matches the known answer.

## C-ARRIVE

arrive_check.txt counts: IdeaB8 value true 20, HindsightDepth value true 20, refusal pattern 0. The 20 log lines around the first IdeaB8 setoption are in that file. The trace shows fastchess sending `setoption name IdeaB8 value true` and `setoption name HindsightDepth value true` to engine ON.

## C-HALF

400 games, FULL 2000 nodes vs HALF 1000 nodes, both ideas off. games_tsv.py pool FULL on half.tsv:

```
side FULL: games 400 W-L-D 274-47-79 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 42, 68, 83] Elo +223.69 95% [+194.40, +256.09]
```

PASS: Elo above +20. half.out agrees (Elo 223.69).

## Pool

26 chunks, each 1000 games, 26000 games. play.sh stopped with "openings used up" after chunk 26. No FAILED line in play.log. No chunk was killed. POOL.txt:

```
side ON: games 26000 W-L-D 9544-8511-7945 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1213, 2542, 4768, 2953, 1524] Elo +13.81 95% [+10.46, +17.17]
```

## suspicions, not proven

None about the build or the games. Runs 1 to 3 matched the known node counts and best-move file hash, C-ARRIVE showed the options, and C-HALF showed the node limit and the side order. The both-on node sum (9,758,416) is not a sum of the two separate node increases. That is a node-count observation, not an Elo claim and not evidence of a wrong binary.

## what I did NOT do

No pull request. No engine source edit and no commit of an exe, object file, net, or PGN. No adjudication (-draw, -resign, -maxmoves, tablebases). No fallback match. No force-push and no push except for-fable-and-opus/grok3-026. No second play of an opening. Channel had no forge-combo29/soak_all/FABLE_TO_grok3_*.md at STEP 1 or mid STEP 4, so no STOP.

## what I am NOT sure about

I have not seen the other seats' run-4 sums, so I cannot confirm that 9,758,416 is the common both-on answer. The Elo interval is the one games_tsv.py prints from the pair-score variance.

## times: see stamps.txt

The listing below was captured after POOL.txt, RESULT.txt and this REPORT.md existed, and before this paste was appended. The append is the only later edit of REPORT.md.

```
$ git status --short
 M forge-combo29/grok3/026/stamps.txt
?? config.json
?? forge-combo29/grok3/026/POOL.txt
?? forge-combo29/grok3/026/REPORT.md
?? forge-combo29/grok3/026/RESULT.txt

$ ls -la forge-combo29/grok3/026
total 5760
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:30 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu   2251 Nov 20 18:53 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110916 Nov 20 19:07 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102548 Nov 20 19:07 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 110738 Nov 20 19:08 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102663 Nov 20 19:08 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 110569 Nov 20 19:10 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102543 Nov 20 19:10 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 110692 Nov 20 19:11 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102523 Nov 20 19:11 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 111110 Nov 20 19:12 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102540 Nov 20 19:12 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 111327 Nov 20 19:13 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102472 Nov 20 19:13 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110846 Nov 20 19:14 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102252 Nov 20 19:14 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 110562 Nov 20 19:16 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102435 Nov 20 19:16 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 110182 Nov 20 19:17 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102238 Nov 20 19:17 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 110755 Nov 20 19:18 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102390 Nov 20 19:18 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110115 Nov 20 18:55 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102422 Nov 20 18:55 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 111479 Nov 20 19:19 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102565 Nov 20 19:19 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 111263 Nov 20 19:20 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102607 Nov 20 19:20 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110639 Nov 20 19:22 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102738 Nov 20 19:22 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 110274 Nov 20 19:23 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102421 Nov 20 19:23 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110686 Nov 20 19:24 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102416 Nov 20 19:24 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110755 Nov 20 19:25 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102442 Nov 20 19:25 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110932 Nov 20 19:27 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102625 Nov 20 19:27 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110788 Nov 20 18:57 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102469 Nov 20 18:57 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110358 Nov 20 18:58 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102358 Nov 20 18:58 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 111165 Nov 20 18:59 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102624 Nov 20 18:59 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 110303 Nov 20 19:01 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102468 Nov 20 19:01 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110857 Nov 20 19:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102597 Nov 20 19:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 111227 Nov 20 19:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102775 Nov 20 19:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110299 Nov 20 19:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102265 Nov 20 19:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110846 Nov 20 19:06 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102717 Nov 20 19:06 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45720 Nov 20 18:53 half.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42030 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:52 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1022 Nov 20 18:54 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:53 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu   1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:29 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5415 Nov 20 19:30 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:30 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     87 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 19:30 stamps.txt
```

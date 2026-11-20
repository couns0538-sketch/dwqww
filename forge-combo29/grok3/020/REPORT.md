# grok3 seat 020

Seat 020, arm 2, 2,000 nodes, chunks of 500 openings (1,000 games). Match is the main match: IdeaB8 and HindsightDepth both on, against both off. SEAT.txt names model Grok 4.7.

## Patch

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`. That is the required hash. The patch was taken from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt` after `git rev-parse FETCH_HEAD` printed that commit. In the work tree, `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both exited 0.

The first cmake used `/usr/bin/c++`, which is clang, and stopped with `cannot find -lstdc++`. The brief requires g++. The machine has AVX-512 and BMI2 (GCC 13.3.0), so the rebuild did not pass `FORGE_PORTABLE`. The measured binary is `~/build/forge` from `cmake -S ../work/forge-combo29 -B ~/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++` and `cmake --build`, which printed `BUILD_OK`.

## Honesty

Each line is a fresh process of that binary, with no setoption before the command. The saved files say:

- bench 11: nodes 312866
- bench 13: nodes 862329
- bench 16: nodes 3024920
- go perft 5: nodes 4865609

Those are the required counts.

## Four O runs

`~/first200.fens` sha256 is `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (200 lines).

| run | options | sum | first three | against the known text |
| --- | --- | --- | --- | --- |
| o_off | IdeaB8=false HindsightDepth=false | 9,500,069 | 41,311 / 24,872 / 28,574 | matches |
| o_b8 | IdeaB8=true HindsightDepth=false | 9,718,009 | 17,283 / 17,878 / 31,115 | matches |
| o_k3 | IdeaB8=false HindsightDepth=true | 9,845,650 | 23,395 / 31,504 / 35,958 | matches |
| o_both | IdeaB8=true HindsightDepth=true | 9,758,416 | 18,538 / 34,070 / 39,093 | no known answer |

`sha256sum` of `o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. Positions whose node count differs between o_off and o_both: 200 of 200. Each run wrote 200 rows.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `wc -l ~/uho.epd` printed 2632036 and `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both match the copies named in the brief. `~/mine.epd` has 13390 lines.

## games_tsv.py known answer

`~/ka.tsv` sha256 is `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text.

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`: IdeaB8 value true appears 20 times, HindsightDepth value true appears 20 times, and the refusal pattern appears 0 times. The same file has the 20 log lines around the first IdeaB8 setoption.

C-HALF: `python3 ~/games_tsv.py pool FULL` on `half.tsv` printed games 400, W-L-D 276-44-80, pairs 200 (openings not in exactly 2 games: 0), ptnml [1, 5, 45, 59, 90], Elo +230.16 95% [+199.40, +264.46]. The last Elo line in `half.out` is `Elo: 230.16 +/- 32.53`. FULL is above +20, so the control passed.

## POOL.txt and chunks

26 chunks, each 1,000 games, 26,000 games. Every termination field is `normal`. No game has result `*`. `play.out` ends with `openings used up`: chunk 27 would have started past the 300 lines kept for the controls (`27 * 500 > 13390 - 300`). The 90 openings between line 13000 and that reserve were not played. Play had already stopped before minute 46.

```
side ON: games 26000 W-L-D 9523-8454-8023 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1148, 2585, 4813, 2958, 1496] Elo +14.29 95% [+10.97, +17.62]
```

## suspicions, not proven

Run 4 has no published node sum. On this seat the both-on sum (9,758,416) is above IdeaB8 alone and below HindsightDepth alone, and all 200 positions differ from both-off. I do not have a proven account of why the combined search is smaller than HindsightDepth alone. Runs 1 to 3 match the known node counts and the off-row hash, so this is not the plain engine wearing the option names.

## what I did NOT do

I did not open a pull request. I did not change engine source, and I did not commit the binary, the net, a PGN, or the applied work tree. I did not play the fallback (HindsightDepth alone). I did not pass adjudication flags. I did not repeat an opening, and I did not start a short chunk for the 90 leftover openings. I did not kill a match at minute 51, because play had already exited. The handoff tree had no `FABLE_TO_grok3_<N>.md` at step 1 or in the middle of step 4.

## what I am NOT sure about

I have not compared this seat's run-4 sum with any other seat. If another seat's both-on rows differ, this seat is not pooled. The Elo interval is the one `games_tsv.py` prints.

## times: see stamps.txt

The first line of `stamps.txt` is `2026-11-20T18:49:14Z STEP 1 seat`. Later lines are the step stamps and one line per finished chunk.

## git status --short and ls -la

These two outputs were pasted from the commands run after this report, `POOL.txt`, and `RESULT.txt` were written and before the step 5 commit.

```
$ git status --short
 M forge-combo29/grok3/020/stamps.txt
?? config.json
?? forge-combo29/grok3/020/POOL.txt
?? forge-combo29/grok3/020/REPORT.md
?? forge-combo29/grok3/020/RESULT.txt
```

```
$ ls -la forge-combo29/grok3/020
total 5772
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:32 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu   2350 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110455 Nov 20 19:07 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102518 Nov 20 19:07 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 110561 Nov 20 19:08 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102352 Nov 20 19:08 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 111230 Nov 20 19:10 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102621 Nov 20 19:10 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 111326 Nov 20 19:11 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102782 Nov 20 19:11 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 110774 Nov 20 19:12 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102605 Nov 20 19:12 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110497 Nov 20 19:13 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102431 Nov 20 19:13 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110751 Nov 20 19:15 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102678 Nov 20 19:15 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 110118 Nov 20 19:16 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102626 Nov 20 19:16 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 110807 Nov 20 19:17 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102596 Nov 20 19:17 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 111023 Nov 20 19:18 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102439 Nov 20 19:18 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110399 Nov 20 18:55 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102474 Nov 20 18:55 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 111500 Nov 20 19:20 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102749 Nov 20 19:20 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 110506 Nov 20 19:21 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102367 Nov 20 19:21 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110458 Nov 20 19:22 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102606 Nov 20 19:22 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 111408 Nov 20 19:23 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102645 Nov 20 19:23 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110818 Nov 20 19:25 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102626 Nov 20 19:25 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110927 Nov 20 19:26 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102500 Nov 20 19:26 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110767 Nov 20 19:27 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102593 Nov 20 19:27 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110915 Nov 20 18:56 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102606 Nov 20 18:56 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110758 Nov 20 18:58 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102473 Nov 20 18:58 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110704 Nov 20 18:59 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102491 Nov 20 18:59 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 111024 Nov 20 19:00 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102725 Nov 20 19:00 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110532 Nov 20 19:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102689 Nov 20 19:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 110730 Nov 20 19:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102740 Nov 20 19:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110686 Nov 20 19:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102471 Nov 20 19:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110906 Nov 20 19:06 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102577 Nov 20 19:06 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:53 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45713 Nov 20 18:53 half.out
-rwxr-xr-x 1 ubuntu ubuntu    986 Nov 20 18:53 half.sh
-rw-r--r-- 1 ubuntu ubuntu  41949 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:51 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1022 Nov 20 18:53 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:52 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu   1755 Nov 20 18:53 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:31 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5534 Nov 20 19:32 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:32 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     88 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1058 Nov 20 19:32 stamps.txt
```

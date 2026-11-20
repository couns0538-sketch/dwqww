# grok3 seat 004

Seat 004, arm 1, 20,000 nodes, chunks of 250 openings (500 games). Model Grok 4.7. Branch for-fable-and-opus/grok3-004. SEAT.txt: `seat 004, arm 1, nodes 20000, model Grok 4.7, 2026-11-20T18:48:31Z, token 30237968912127`.

## Patch

sha256 of ~/b8.patch: `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474` (the required hash). Source commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75` (`git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-028`). `git apply --check ~/b8.patch` then `git apply ~/b8.patch` in the work tree printed `APPLY OK`.

Decision: the first cmake used `/usr/bin/c++`, which is clang++ 18.1.3, and failed (`cannot find -lstdc++`). The brief asks for g++. I deleted ~/build and configured again with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0). `/proc/cpuinfo` has avx512f and bmi2, so I did not add `-DFORGE_PORTABLE=ON` or `-DFORGE_MARCH=x86-64-v3`. The log ended `BUILD_OK`. The binary is `/home/ubuntu/build/forge`. Its sha256, from o_both.rows.txt.meta, is `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`. id name: `Chess Engine Forge 6.4.24 candidate`.

## Honesty

Fresh processes, no setoption. From the saved files:

- bench 11: `info string bench depth 11 nodes 312866 time 162 nps 1931271`
- bench 13: `info string bench depth 13 nodes 862329 time 443 nps 1946566`
- bench 16: `info string bench depth 16 nodes 3024920 time 1422 nps 2127229`
- go perft 5: `nodes 4865609`

Those are the required node counts.

## Four O runs

Against the known text. o_runs.py on `/home/ubuntu/build/forge` and ~/first200.fens (sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines).

1. IdeaB8=false HindsightDepth=false. Printed `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. File head: `41311`, `24872`, `28574`. sha256 of o_off.rows.txt: `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. Matches.
2. IdeaB8=true HindsightDepth=false. Printed `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`. File head: `17283`, `17878`, `31115`. Matches.
3. IdeaB8=false HindsightDepth=true. Printed `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`. File head: `23395`, `31504`, `35958`. Matches.
4. IdeaB8=true HindsightDepth=true. Printed `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. File head: `18538`, `34070`, `39093`. Positions whose node count differs from run 1: `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed `200`.

## Book

~/uho.zip sha256 `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. ~/uho.epd `2632036` lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both match. ~/mine.epd is 13390 lines. The controls used the last 300 of those lines.

## games_tsv.py known answer

~/ka.tsv from for-fable-and-opus/grok2-004, sha256 `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

Matches.

## C-ARRIVE and C-HALF

C-ARRIVE counts from ~/arrive.log, saved in arrive_check.txt: IdeaB8 value true = 20, HindsightDepth value true = 20, unknown option|invalid value|no such option = 0. The match printed `Finished match`.

C-HALF, `python3 ~/games_tsv.py pool FULL` on half.tsv:

```
side FULL: games 400 W-L-D 296-45-59 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 5, 44, 46, 105] Elo +256.16 95% [+223.07, +293.75]
```

FULL's Elo is above +20. Pass. Main match (both ideas on against both off), not the fallback.

## POOL.txt

10 chunks, each 500 games, 5000 games. Pasted POOL.txt:

```
side ON: games 5000 W-L-D 1431-1225-2344 pairs 2500 (openings not in exactly 2 games: 0)
ptnml [90, 577, 1013, 677, 143] Elo +14.32 95% [+7.97, +20.68]
```

## suspicions, not proven

fastchess wrote an untracked `config.json` in the repository root (play.sh's working directory was the repository). I did not commit it. The resign, draw, maxmoves, and tablebase keys in that file have `"enabled": false`. A search of ~/chunk_*.out for adjudicat, resign, and syzygy found no lines. I am not sure whether fastchess loaded that file; the match command did not pass adjudication options, and the finished-game lines I saw were mates and threefold repetitions.

## what I did NOT do

No pull request. No `--force`. No engine source committed. No PGN, no exe, no net, no whole arrive.log. No fallback match. No portable march flags. No second 60-second wait on setup_bg: the log already said `fastchess OK`, `python-chess OK`, `book OK`, `setup_bg done`. No FABLE_TO_grok3 file existed at the step 1 read or the step 4 read, so I did not stop early. I did not kill chunk 10: it finished at 2026-11-20T19:37:19Z, before minute 51, and play.sh then printed `minute 46: no new chunk`.

## what I am NOT sure about

Whether the two ideas add or overlap. This seat, both on against both off at 20,000 nodes, is Elo +14.32 with 95% [+7.97, +20.68]. That interval covers both about +17 and about +10. Run 4 has no published known answer; the sum and the 200 differing positions are what this binary printed.

times: see stamps.txt

## git status --short and ls -la

```
 M forge-combo29/grok3/004/stamps.txt
?? config.json
?? forge-combo29/grok3/004/POOL.txt
?? forge-combo29/grok3/004/REPORT.md
?? forge-combo29/grok3/004/RESULT.txt
```

```
total 1276
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:39 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2281 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56282 Nov 20 19:37 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51697 Nov 20 19:37 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 56183 Nov 20 18:59 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51576 Nov 20 18:59 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56436 Nov 20 19:03 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51788 Nov 20 19:03 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56031 Nov 20 19:07 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51627 Nov 20 19:07 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56313 Nov 20 19:11 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51488 Nov 20 19:11 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 56314 Nov 20 19:16 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51524 Nov 20 19:16 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56427 Nov 20 19:20 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51698 Nov 20 19:20 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56567 Nov 20 19:24 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51521 Nov 20 19:24 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 56192 Nov 20 19:28 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51768 Nov 20 19:28 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56071 Nov 20 19:33 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51715 Nov 20 19:33 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45259 Nov 20 18:54 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41924 Nov 20 18:54 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:51 honesty_perft5.txt
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
-rw-r--r-- 1 ubuntu ubuntu  8300 Nov 20 19:39 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   293 Nov 20 19:39 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   514 Nov 20 19:39 stamps.txt
```

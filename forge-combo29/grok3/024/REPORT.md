# grok3 seat 024

Seat 024, arm 3, 60,000 nodes. Chunk size 100 openings (200 games). Match is the main match: both ideas ON against both OFF. Model Grok 4.7.

## Patch

sha256 of ~/b8.patch: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

That is the required hash. Source commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75, path forge-combo29/grok/028/idea.patch.txt. `git apply --check` then `git apply` in the work tree outside the repository. Apply succeeded. Diff stat: forge-combo29/include/forge/search.hpp, forge-combo29/src/search.cpp, forge-combo29/src/uci.cpp; 3 files, 173 insertions, 4 deletions. Nothing from the build or the patched tree was committed.

CMake used g++ 13.3.0 (GCC's libstdc++). `/usr/bin/c++` on this machine is Clang 18.1.3 and cannot link `-lstdc++`, so the first configure failed. I reconfigured with `-DCMAKE_CXX_COMPILER=g++`. The CPU reports AVX-512 and BMI2, so FORGE_PORTABLE stayed off and -march stayed the CMake default x86-64-v4. The honesty numbers below matched, which is why that choice stands.

## Honesty

Fresh process each time, no setoption before the command. Raw files in this folder.

- bench 11: nodes 312866 (honesty_bench11.txt)
- bench 13: nodes 862329 (honesty_bench13.txt)
- bench 16: nodes 3024920 (honesty_bench16.txt)
- go perft 5: nodes 4865609 (honesty_perft5.txt)

All four match the known numbers.

## Four O runs

Engine `/home/ubuntu/build/forge`, sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422, id name Chess Engine Forge 6.4.24 candidate. Threads 1, Hash 16, S14, then the two options. 200 positions each.

| run | options | sum | first three | against the known text |
| --- | --- | --- | --- | --- |
| o_off | IdeaB8=false HindsightDepth=false | 9,500,069 | 41,311 / 24,872 / 28,574 | matches |
| o_b8 | IdeaB8=true HindsightDepth=false | 9,718,009 | 17,283 / 17,878 / 31,115 | matches |
| o_k3 | IdeaB8=false HindsightDepth=true | 9,845,650 | 23,395 / 31,504 / 35,958 | matches |
| o_both | IdeaB8=true HindsightDepth=true | 9,758,416 | 18,538 / 34,070 / 39,093 | no known answer |

sha256 of o_off.rows.txt: dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7 (matches).

Positions whose node count differs between o_off and o_both: 200. Counted with `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l`.

## Book

~/uho.zip sha256 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 (matches).

~/uho.epd 2,632,036 lines, sha256 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a (matches).

Own openings: lines at or after 2,150,024, every 36th. ~/mine.epd has 13,390 lines. The last 300 lines were kept for the controls and were not used as match openings.

## games_tsv.py known answer

Fetched for-fable-and-opus/grok2-004 chunk_1.tsv. sha256 6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd (matches).

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the known answer.

## C-ARRIVE

`bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`

Finished match, 20 games, exit 0. Counts from arrive_check.txt, which also holds the 20 log lines around the first `setoption name IdeaB8 value true`:

- setoption name IdeaB8 value true: 20
- setoption name HindsightDepth value true: 20
- unknown option / invalid value / no such option: 0

Pass. Main match, so IdeaB8 true is required and was present.

## C-HALF

`bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn` then games_tsv.py tsv and pool FULL.

```
side FULL: games 400 W-L-D 270-52-78 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 54, 53, 86] Elo +212.37 95% [+182.51, +245.31]
```

FULL's Elo is +212.37, above +20. Pass. fastchess printed the same Elo and the same W-L-D.

## POOL.txt

9 chunks, each 200 games, 1,800 games. Pasted POOL.txt:

```
side ON: games 1800 W-L-D 471-429-900 pairs 900 (openings not in exactly 2 games: 0)
ptnml [25, 205, 403, 237, 30] Elo +8.11 95% [-1.61, +17.84]
```

Chunk finish times are in stamps.txt (chunk 1 at 2026-11-20T19:00:34Z through chunk 9 at 2026-11-20T19:38:54Z). play.sh then printed `minute 46: no new chunk` and exited. No chunk was killed. No line `commit or push FAILED` is in ~/play.log.

## suspicions, not proven

The point estimate +8.11 Elo at 60,000 nodes sits nearer a partial overlap than a full +17 add, and the 95% interval [-1.61, +17.84] includes both zero and about +17. This seat does not decide whether the two ideas add. That is one sample of 1,800 games, not a pooled result.

I have not seen another seat's o_both sum. Mine is 9,758,416 with first three 18,538 / 34,070 / 39,093 and 200 positions differing from o_off. If another seat's run 4 differs, this one is the one I measured on the exe whose sha256 is above.

## what I did NOT do

I did not open a pull request. I did not change engine source in the repository and I did not commit an exe, a net, a PGN, or a binary. I did not pass adjudication flags. I did not play the fallback (HindsightDepth alone). I did not start a chunk after minute 46. I did not repeat an opening. I did not push any branch except for-fable-and-opus/grok3-024, and I did not use --force.

## what I am NOT sure about

I am not sure the other seats' run 4 matches this one, because I only ran this build. I am not sure the +8.11 Elo is a real gain at 60,000 nodes, because the interval includes zero. I am sure of the counts in the files named above, because I re-read them before writing this report.

## times: see stamps.txt

The first line of stamps.txt is 2026-11-20T18:49:35Z STEP 1 seat. Minute 46 from that line is 19:35:35Z. Minute 51 is 19:40:35Z. Chunk 9 finished at 19:38:54Z.

## git status --short and ls -la

```
 M forge-combo29/grok3/024/stamps.txt
?? config.json
?? forge-combo29/grok3/024/POOL.txt
?? forge-combo29/grok3/024/REPORT.md
?? forge-combo29/grok3/024/RESULT.txt
```

```
total 628
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:40 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:49 ..
-rw-r--r-- 1 ubuntu ubuntu  2276 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22442 Nov 20 19:00 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20616 Nov 20 19:00 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22417 Nov 20 19:05 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20621 Nov 20 19:05 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22618 Nov 20 19:10 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20654 Nov 20 19:10 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22438 Nov 20 19:15 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20672 Nov 20 19:15 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22326 Nov 20 19:19 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20641 Nov 20 19:19 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22568 Nov 20 19:24 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20554 Nov 20 19:24 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22688 Nov 20 19:29 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20694 Nov 20 19:29 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22641 Nov 20 19:34 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20747 Nov 20 19:34 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 22357 Nov 20 19:38 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 20597 Nov 20 19:38 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu  2779 Nov 20 18:55 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45650 Nov 20 18:55 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:55 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42083 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:52 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:55 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:53 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:55 play.sh
-rw-r--r-- 1 ubuntu ubuntu   145 Nov 20 19:39 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6013 Nov 20 19:40 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   286 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    90 Nov 20 18:49 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   470 Nov 20 19:40 stamps.txt
```

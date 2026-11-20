# grok3 seat 005

Seat 005, arm 2, 2000 nodes. Chunk size 500 openings (1000 games). Model Grok 4.7. Branch `for-fable-and-opus/grok3-005`. Match is the main match: IdeaB8 and HindsightDepth both on, against both off.

## Patch

`sha256sum ~/b8.patch` printed

`f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`

That is the required hash. The patch came from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt` (`git rev-parse FETCH_HEAD` printed that commit). In the work tree outside this repository, `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both exited 0.

The machine has AVX-512 and BMI2, so cmake was Release with g++ and without `FORGE_PORTABLE`. `/usr/bin/c++` is Clang 18 and cannot link `libstdc++` here; the build used `CC=gcc` and `CXX=g++` (g++ 13.3.0). Nothing from the build was committed.

## Honesty

Fresh processes, no `setoption` before the command. Saved files:

- `honesty_bench11.txt`: `info string bench depth 11 nodes 312866 time 162 nps 1931271`
- `honesty_bench13.txt`: `info string bench depth 13 nodes 862329 time 426 nps 2024246`
- `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920 time 1440 nps 2100638`
- `honesty_perft5.txt`: `nodes 4865609`

Those node counts are the required ones: 312866, 862329, 3024920, 4865609.

## Four O runs

`~/first200.fens` sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines. Exe `/home/ubuntu/build/forge`, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, `id name Chess Engine Forge 6.4.24 candidate`. Each run sent Threads 1, Hash 16, the 14 S14 settings, then the two idea options. From the row files:

| run | required | got sum | got first three |
| --- | --- | --- | --- |
| (1) both off | sum 9500069; first 41311 / 24872 / 28574 | 9500069 | 41311 / 24872 / 28574 |
| (2) IdeaB8 only | sum 9718009; first 17283 / 17878 / 31115 | 9718009 | 17283 / 17878 / 31115 |
| (3) HindsightDepth only | sum 9845650; first 23395 / 31504 / 35958 | 9845650 | 23395 / 31504 / 35958 |
| (4) both on | no known answer | 9758416 | 18538 / 34070 / 39093 |

`sha256sum` of `o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`.

Positions whose node count differs between (1) and (4), `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l`: **200**.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`.

`wc -l ~/uho.epd` printed 2632036. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`.

Both match the given copy. Seat openings: 13390 lines in `~/mine.epd`. The last 300 were kept for the controls and were not used as chunks.

## games_tsv.py known answer

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`.

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text.

## C-ARRIVE

`arrive_check.txt` counts, from the trace log of `match.sh` on 10 openings (20 games):

- `setoption name IdeaB8 value true`: 20
- `setoption name HindsightDepth value true`: 20
- `unknown option|invalid value|no such option`: 0

The same file has 20 log lines around the first `setoption name IdeaB8 value true`, including `ON <--- setoption name IdeaB8 value true` and `ON <--- setoption name HindsightDepth value true`.

## C-HALF

`python3 ~/games_tsv.py pool FULL forge-combo29/grok3/005/half.tsv` printed

```
side FULL: games 400 W-L-D 273-50-77 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 10, 45, 53, 91] Elo +218.61 95% [+186.86, +253.97]
```

FULL's Elo is +218.61, above +20. Passed.

## Pool

26 chunks. Each `chunk_N.tsv` has 1000 games. Every game's termination field is `normal`. `play.log` has 26 lines `chunk N done` and no `FAILED`. `play.out` ends with `openings used up` (13000 openings used; the next chunk of 500 would have passed the 13090 lines left after the 300-line reserve). Each counted chunk's `.out` ends with `Finished match`. The chunk 26 summary line is `Results of ON vs OFF (2000 nodes, 1t, 16MB, chunk_26.epd)`.

`POOL.txt`:

```
side ON: games 26000 W-L-D 9760-8245-7995 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1149, 2441, 4789, 2988, 1633] Elo +20.27 95% [+16.91, +23.63]
```

## suspicions, not proven

An untracked `config.json` appeared in the repository root while fastchess was running. Its keys are fastchess's own config keys, including `resign`, `draw`, and `maxmoves`. `match.sh` does not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. All 26000 game rows say `normal`. I did not commit `config.json`. I have not proved which process wrote it.

Run (4)'s node sum, 9758416, sits between the IdeaB8-only sum and the HindsightDepth-only sum. That is a node-count observation, not an Elo claim about overlap.

## what I did NOT do

I did not open a pull request. I did not change engine source, and I did not commit an executable, a net, a PGN, or the patch. I did not use `--force`. I did not play the fallback match. I did not start another chunk after the openings reserved for the controls. I did not adjudicate games. There was no `FABLE_TO_grok3_<N>.md` on the handoff branch at step 1 or in the middle of step 4.

## what I am NOT sure about

I am not sure that every other seat's run (4) prints the same sum 9758416. This machine printed that sum once.

I am not sure the repository-root `config.json` is harmless beyond being untracked. It was not an input to the match command.

## times: see stamps.txt

The first stamp is `2026-11-20T18:48:46Z STEP 1 seat`. Chunk 26 is `2026-11-20T19:26:43Z chunk 26 done`. Play then printed `openings used up`, before minute 46.

## git status --short

Taken at 2026-11-20T19:29:37Z, after POOL.txt, REPORT.md, RESULT.txt, and the step 5 stamp existed, and before the step 5 commit. Filling this section changed only the later byte size of REPORT.md. `config.json` is not in this seat's folder and is not committed.

```
 M forge-combo29/grok3/005/stamps.txt
?? config.json
?? forge-combo29/grok3/005/POOL.txt
?? forge-combo29/grok3/005/REPORT.md
?? forge-combo29/grok3/005/RESULT.txt
```

## ls -la

`ls -la forge-combo29/grok3/005` at 2026-11-20T19:29:37Z:

```
total 5768
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:29 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu   2191 Nov 20 18:53 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 111108 Nov 20 19:06 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102476 Nov 20 19:06 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 111451 Nov 20 19:07 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102645 Nov 20 19:07 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 111000 Nov 20 19:09 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102286 Nov 20 19:09 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 110555 Nov 20 19:10 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102503 Nov 20 19:10 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 111236 Nov 20 19:11 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102588 Nov 20 19:11 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110927 Nov 20 19:12 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102594 Nov 20 19:12 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 111004 Nov 20 19:13 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102297 Nov 20 19:13 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 111251 Nov 20 19:15 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102635 Nov 20 19:15 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 111069 Nov 20 19:16 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102528 Nov 20 19:16 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 110326 Nov 20 19:17 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102362 Nov 20 19:17 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110595 Nov 20 18:55 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102549 Nov 20 18:55 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 111235 Nov 20 19:19 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102444 Nov 20 19:19 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 110699 Nov 20 19:20 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102563 Nov 20 19:20 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110355 Nov 20 19:21 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102347 Nov 20 19:21 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 110319 Nov 20 19:22 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102620 Nov 20 19:22 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110994 Nov 20 19:24 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102533 Nov 20 19:24 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110461 Nov 20 19:25 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102687 Nov 20 19:25 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110572 Nov 20 19:26 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102553 Nov 20 19:26 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110683 Nov 20 18:56 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102569 Nov 20 18:56 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110721 Nov 20 18:58 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102622 Nov 20 18:58 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110658 Nov 20 18:59 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102742 Nov 20 18:59 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 110319 Nov 20 19:00 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102544 Nov 20 19:00 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 111282 Nov 20 19:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102777 Nov 20 19:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 111163 Nov 20 19:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102502 Nov 20 19:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110719 Nov 20 19:04 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102513 Nov 20 19:04 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110609 Nov 20 19:05 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102584 Nov 20 19:05 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45606 Nov 20 18:53 half.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu  41912 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:51 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:51 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:51 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:51 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:51 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu   1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:28 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5965 Nov 20 19:29 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:29 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     86 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1067 Nov 20 19:29 stamps.txt
```

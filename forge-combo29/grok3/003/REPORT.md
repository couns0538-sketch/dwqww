# grok3 seat 003

Seat 003, arm 3, 60,000 nodes, chunks of 100 openings (200 games). Model Grok 4.7. Match is the main match: IdeaB8 and HindsightDepth both on, against both off. Branch `for-fable-and-opus/grok3-003`.

## Patch sha256 and git apply

`git rev-parse FETCH_HEAD` after `git fetch -q --depth 1 origin for-fable-and-opus/grok-028` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`.

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`.

`git apply --check ~/b8.patch` and `git apply ~/b8.patch` in the work tree both succeeded (`APPLY OK`).

The first cmake used `/usr/bin/c++`, which is clang 18, and stopped with `cannot find -lstdc++`. I removed `~/build` and configured again with `CC=gcc` and `CXX=g++` (g++ 13.3.0, GCC's libstdc++). The CPU has AVX-512 and BMI2, so I did not add `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. The binary is `/home/ubuntu/build/forge`. Its sha256, from every O-run `.meta`, is `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`. `id name Chess Engine Forge 6.4.24 candidate`.

## Honesty numbers

Fresh processes, no `setoption` before the command. Files `honesty_bench11.txt`, `honesty_bench13.txt`, `honesty_bench16.txt`, `honesty_perft5.txt`.

- bench 11: `info string bench depth 11 nodes 312866 time 166 nps 1884734` (nodes 312866)
- bench 13: `info string bench depth 13 nodes 862329 time 426 nps 2024246` (nodes 862329)
- bench 16: `info string bench depth 16 nodes 3024920 time 1431 nps 2113850` (nodes 3024920)
- go perft 5: last line `nodes 4865609`

## Four O runs

Known text, then what this build printed.

1. Both off. Known: sum 9,500,069; first three 41,311 / 24,872 / 28,574; sha256 of `o_off.rows.txt` `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. Printed: `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. `sha256sum` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`.
2. IdeaB8 only. Known: sum 9,718,009; first three 17,283 / 17,878 / 31,115. Printed: `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`.
3. HindsightDepth only. Known: sum 9,845,650; first three 23,395 / 31,504 / 35,958. Printed: `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`.
4. Both on. No known answer. Printed: `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. File rows: `18538`, `34070`, `39093`. Sum of the node column is 9758416. Positions whose node count differs from run 1: `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200.

## Book sha256

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`.

`wc -l ~/uho.epd` printed `2632036`. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`.

`~/mine.epd` is 13390 lines. The controls use the last 300 of those lines.

## Known answer of games_tsv.py

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`.

`python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): `setoption name IdeaB8 value true` count 20, `setoption name HindsightDepth value true` count 20, refusal count 0. The 20 log lines around the first IdeaB8 setoption are in that file.

C-HALF, `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/003/half.tsv` printed:

```
side FULL: games 400 W-L-D 278-43-79 pairs 200 (openings not in exactly 2 games: 0)
ptnml [4, 6, 38, 55, 97] Elo +234.12 95% [+200.32, +272.30]
```

FULL's Elo is +234.12, above +20. Passed on the first run. `half.out` also ends with `Elo: 234.12 +/- 35.99` and `Finished match`.

## POOL.txt and chunks

8 chunks, each 200 games, 1600 games. `python3 ~/games_tsv.py pool ON forge-combo29/grok3/003/chunk_*.tsv` wrote `POOL.txt`:

```
side ON: games 1600 W-L-D 435-363-802 pairs 800 (openings not in exactly 2 games: 0)
ptnml [19, 176, 352, 220, 33] Elo +15.65 95% [+5.23, +26.09]
```

## suspicions, not proven

None. The 95% interval [+5.23, +26.09] still covers both a sum near +17 and an overlap near +10. That is the width of this seat's sample, not a second measurement.

## what I did NOT do

I did not open a pull request. I did not change engine source and I did not commit an executable, a net, a PGN, or the book. I did not play the fallback match. I did not start a chunk after minute 46. Chunk 8 had already started and finished at 19:35:23Z; `play.sh` then printed `minute 46: no new chunk` and exited. I did not kill fastchess. I did not commit `config.json` in the repository root (fastchess wrote it because the match's working directory was the repo). Its adjudication switches are `enabled: false`. No FABLE_TO_grok3 file was on the channel at step 1 or in the middle of step 4.

## what I am NOT sure about

I have not read another seat's `o_both.rows.txt`, so I cannot say from this machine that their both-on sum is also 9758416. The bench time and nps fields are this machine's speed; the node counts are the check I matched.

## times: see stamps.txt

times: see stamps.txt

## git status --short and ls -la

`git status --short`:

```
?? config.json
?? forge-combo29/grok3/003/POOL.txt
?? forge-combo29/grok3/003/REPORT.md
?? forge-combo29/grok3/003/RESULT.txt
```

`ls -la` of `forge-combo29/grok3/003`:

```
total 580
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:38 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2267 Nov 20 18:55 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22464 Nov 20 19:00 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20611 Nov 20 19:00 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22652 Nov 20 19:05 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20767 Nov 20 19:05 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22613 Nov 20 19:10 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20681 Nov 20 19:10 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22561 Nov 20 19:15 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20597 Nov 20 19:15 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22471 Nov 20 19:20 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20701 Nov 20 19:20 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22506 Nov 20 19:25 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20697 Nov 20 19:25 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22705 Nov 20 19:30 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20699 Nov 20 19:30 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22278 Nov 20 19:35 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20607 Nov 20 19:35 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45565 Nov 20 18:56 half.out
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42002 Nov 20 18:55 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:52 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:54 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:53 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:53 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:53 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:53 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:53 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:53 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:53 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:53 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:54 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:37 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  5296 Nov 20 19:38 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:38 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    88 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   356 Nov 20 19:35 stamps.txt
```

That listing was captured before this block was pasted into REPORT.md, so the REPORT.md size above is the size before the paste. Every other name is unchanged. `config.json` is untracked in the repo root and is not in this folder.

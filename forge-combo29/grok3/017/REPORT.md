# grok3 seat 017

Seat 017, arm 2, 2,000 nodes. Chunk size 500 openings (1,000 games). Match is the main match: IdeaB8 on and HindsightDepth on, against both off. Branch `for-fable-and-opus/grok3-017`. Model name passed to take_seat3.sh: Grok 4.7.

## Patch

`~/b8.patch` from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`.

sha256 `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474` (matches the brief).

`git apply --check ~/b8.patch` then `git apply ~/b8.patch` in the work tree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`. Both succeeded (`APPLY OK`).

Build decision: `/usr/bin/c++` is Clang 18.1.3 and the first cmake failed at link (`cannot find -lstdc++`). The brief requires g++ with GCC's C++ library. I removed `~/build` and configured again with `CXX=g++` and `-DCMAKE_CXX_COMPILER=g++`. The compiler line was `GNU 13.3.0`. `/proc/cpuinfo` has `avx512f` and `bmi2`, so I did not pass `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. Binary: `/home/ubuntu/build/forge`.

## Honesty

Fresh process, no setoption, raw files in this folder.

- `honesty_bench11.txt`: `nodes 312866`
- `honesty_bench13.txt`: `nodes 862329`
- `honesty_bench16.txt`: `nodes 3024920`
- `honesty_perft5.txt`: `nodes 4865609`

All four match the brief.

## Four O runs

`o_runs.py` on `/home/ubuntu/build/forge` and `~/first200.fens` (sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines).

Known text: off sum 9,500,069 first three 41,311 / 24,872 / 28,574 and sha256 of `o_off.rows.txt` `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`; B8 sum 9,718,009 first three 17,283 / 17,878 / 31,115; HindsightDepth sum 9,845,650 first three 23,395 / 31,504 / 35,958.

Measured, recomputed from the row files:

| run | sum | first three | vs known |
| --- | --- | --- | --- |
| o_off.rows.txt IdeaB8=false HindsightDepth=false | 9500069 | 41311 / 24872 / 28574 | match, sha256 dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7 |
| o_b8.rows.txt IdeaB8=true HindsightDepth=false | 9718009 | 17283 / 17878 / 31115 | match |
| o_k3.rows.txt IdeaB8=false HindsightDepth=true | 9845650 | 23395 / 31504 / 35958 | match |
| o_both.rows.txt IdeaB8=true HindsightDepth=true | 9758416 | 18538 / 34070 / 39093 | no known answer in the brief |

Positions whose node count differs between `o_off.rows.txt` and `o_both.rows.txt`: 200 (paste/awk `$2 != $5`).

## Book

`~/uho.zip` sha256 `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07` (matches).

`~/uho.epd` 2632036 lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (matches).

`~/mine.epd` 13390 lines. Control slice: 300 lines, arrive 10, half 200.

## games_tsv.py known answer

`~/ka.tsv` from `for-fable-and-opus/grok2-004` `forge-combo29/grok2/004/chunk_1.tsv`, sha256 `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`.

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

Matches the brief.

## C-ARRIVE

`bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true` exited 0 and printed `Finished match`.

From `arrive_check.txt` (counts, then 20 log lines around the first `setoption name IdeaB8 value true`):

- `setoption name IdeaB8 value true`: 20
- `setoption name HindsightDepth value true`: 20
- `unknown option|invalid value|no such option`: 0

The log line is `ON <--- setoption name IdeaB8 value true` followed by `setoption name HindsightDepth value true`.

## C-HALF

`bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn` exited 0, `Finished match`, 400 games.

`python3 ~/games_tsv.py pool FULL forge-combo29/grok3/017/half.tsv` printed:

```
side FULL: games 400 W-L-D 280-39-81 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 8, 44, 47, 101] Elo +242.18 95% [+209.35, +279.25]
```

FULL Elo +242.18 is above +20. Pass.

## Pool

`python3 ~/games_tsv.py pool ON forge-combo29/grok3/017/chunk_*.tsv` wrote `POOL.txt`. Chunks: 26. Each `chunk_N.tsv` is 1000 lines (wc total 26000). `~/play.out` ends with `openings used up`. No `FAILED` line in `~/play.log`.

Pasted `POOL.txt`:

```
side ON: games 26000 W-L-D 9532-8476-7992 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1174, 2561, 4816, 2933, 1516] Elo +14.12 95% [+10.78, +17.46]
```

Why 26 chunks and then stop: `~/mine.epd` has 13390 lines, so play.sh's LAST is 13090. Chunk 26 uses lines 12501-13000. Chunk 27 would need line 13500, which is past LAST, so play.sh printed `openings used up` and exited. That was at 2026-11-20T19:26:12Z, before minute 46 (19:35:08Z, 46 minutes after the first stamps line 2026-11-20T18:49:08Z). I did not start another chunk.

## Channel

Fetched `handoff/fable-opus-combo29-all-20261114` at STEP 1 and again during STEP 4. `git ls-tree` of `forge-combo29/soak_all/` has no `FABLE_TO_grok3_*.md`.

## suspicions, not proven

The both-on depth-12 node sum (9,758,416) is near IdeaB8 alone (9,718,009) and below HindsightDepth alone (9,845,650). Node sums are not Elo. I do not treat that as evidence that the two ideas overlap.

At 2,000 nodes the pair Elo is +14.12 with 95% interval [+10.78, +17.46]. That interval reaches both rough figures named in the brief (about +10 and about +17). This seat is only the 2,000-node arm, so it does not by itself decide add versus overlap at 20,000 or 60,000 nodes.

## what I did NOT do

- No pull request.
- No engine source committed. The patch was applied only in the outside work tree.
- No `--force`, no push to any branch other than `for-fable-and-opus/grok3-017`.
- No adjudication (`-draw`, `-resign`, `-maxmoves`, tablebases). fastchess wrote an untracked `config.json` in the repository root while playing; its resign, draw, maxmoves and tablebase `enabled` fields are false. I did not commit it. It is outside the seat folder.
- No fallback match. (1), (2) and (3) matched, so the match stayed main.
- No second use of an opening.
- No `FABLE_TO_grok3` instruction, because none was in the channel.

## what I am NOT sure about

- I have not compared `o_both.rows.txt` with any other seat. The brief says seats whose run (4) differs are not pooled. Mine is recorded here; sameness with the others is for the recount.
- I am sure the played binary is the g++ build that reproduced the honesty numbers and runs (1), (2) and (3). I did not produce a Clang binary.

## times: see stamps.txt

## git status --short and ls -la

Taken immediately before the STEP 5 commit, then appended below.

```
$ git status --short
 M forge-combo29/grok3/017/stamps.txt
?? config.json
?? forge-combo29/grok3/017/POOL.txt
?? forge-combo29/grok3/017/REPORT.md
?? forge-combo29/grok3/017/RESULT.txt
```

```
$ ls -la forge-combo29/grok3/017
total 5772
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:31 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu   2257 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 110444 Nov 20 19:06 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102595 Nov 20 19:06 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 110122 Nov 20 19:07 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102533 Nov 20 19:07 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 111061 Nov 20 19:08 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102740 Nov 20 19:08 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 111217 Nov 20 19:09 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102563 Nov 20 19:09 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 111077 Nov 20 19:11 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102503 Nov 20 19:11 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 110974 Nov 20 19:12 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102576 Nov 20 19:12 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 110868 Nov 20 19:13 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102572 Nov 20 19:13 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 110621 Nov 20 19:15 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102429 Nov 20 19:15 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 110751 Nov 20 19:16 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102377 Nov 20 19:16 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 110714 Nov 20 19:17 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102560 Nov 20 19:17 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110641 Nov 20 18:54 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102306 Nov 20 18:54 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 110649 Nov 20 19:18 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102388 Nov 20 19:18 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 111124 Nov 20 19:20 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102634 Nov 20 19:20 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 111167 Nov 20 19:21 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102515 Nov 20 19:21 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 110743 Nov 20 19:22 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102633 Nov 20 19:22 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110239 Nov 20 19:23 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102635 Nov 20 19:23 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110655 Nov 20 19:25 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102463 Nov 20 19:25 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110572 Nov 20 19:26 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102451 Nov 20 19:26 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110752 Nov 20 18:56 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102634 Nov 20 18:56 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110829 Nov 20 18:57 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102626 Nov 20 18:57 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110633 Nov 20 18:58 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102762 Nov 20 18:58 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 110961 Nov 20 18:59 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102529 Nov 20 18:59 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110743 Nov 20 19:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102752 Nov 20 19:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 110172 Nov 20 19:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102682 Nov 20 19:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 111146 Nov 20 19:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102786 Nov 20 19:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 110158 Nov 20 19:04 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102349 Nov 20 19:04 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45657 Nov 20 18:52 half.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu  41957 Nov 20 18:52 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:50 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:51 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:51 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:51 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:51 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:51 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:51 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:51 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu   1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:30 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6600 Nov 20 19:31 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:31 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     86 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 19:32 stamps.txt
```

# REPORT seat 061

## Arm and source seat

Seat 061, arm 1, id B1a. Source seat 030, commit `416700fe0ace1656a1285fc536c347718c1a4af7`, branch `for-fable-and-opus/grok-030`, file `forge-combo29/grok/030/idea.patch.txt`. SWITCH `IdeaB1`.

`git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-030` printed `416700fe0ace1656a1285fc536c347718c1a4af7`.

## Patch sha256 and git apply

```
sha256sum ~/arm.patch
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. `git diff --stat` there:

```
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

`/usr/bin/c++` is Clang 18 and cannot link `libstdc++`. Both exes were built with CMake and g++ 13.3 (`-DCMAKE_CXX_COMPILER=g++`, `CMAKE_BUILD_TYPE=Release`). This machine has AVX-512 and BMI2, so `FORGE_PORTABLE` stayed off and `-march` stayed `x86-64-v4`. IdeaB1_Scale and IdeaB1_Fade were left at their defaults and were never sent.

## Honesty numbers

`summarize_honesty.py` reading the raw transcripts:

```
B_bench11.txt: info string bench depth 11 nodes 312866 time 173 nps 1808473
B_bench13.txt: info string bench depth 13 nodes 862329 time 458 nps 1882814
B_bench16.txt: info string bench depth 16 nodes 3024920 time 1487 nps 2034243
P_bench11.txt: info string bench depth 11 nodes 312866 time 167 nps 1873449
P_bench13.txt: info string bench depth 13 nodes 862329 time 470 nps 1834742
P_bench16.txt: info string bench depth 16 nodes 3024920 time 1479 nps 2045246
B_perft5.txt: nodes 4865609
P_perft5.txt: nodes 4865609
```

Expected: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Both exes match. honesty=ok.

## Three O runs

`summarize_o.py o_B.txt o_off.txt o_on.txt` (saved as `o_summary.txt`):

```
B positions 200 sum 9500069 first 41311 24872 28574
OFF positions 200 sum 9500069 first 41311 24872 28574 differ=0
ON positions 200 sum 10081213 first 12481 31753 31668 differ=200
OFF_mismatches 0 []
```

Against the arm table:

- (1) exe B: expected sum 9500069 and first three 41311 / 24872 / 28574. Got that.
- (2) exe P, IdeaB1 false: expected equal to (1) on all 200. differ=0.
- (3) exe P, IdeaB1 true: expected sum 10081213, first three 12481 / 31753 / 31668, 200 differ. Got that.

off_identical=yes. on_sum=10081213. on_ok=yes.

Each run sent Threads 1, Hash 16, then S14 in the brief's order, then IdeaB1 for the patched exe (`false` or `true`). Each setoption was followed by isready, and every line up to readyok was read. Each position was ucinewgame, isready, position, isready, go depth 12. The exe path, sha256, id name and option lines are in `o_B.meta`, `o_off.meta` and `o_on.meta`. id name is `Chess Engine Forge 6.4.24 candidate`.

## Book

`book_check.txt`:

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
wc -l openings
  29245 /home/ubuntu/mine.epd
    300 /home/ubuntu/ctl.epd
     10 /home/ubuntu/ctl_arrive.epd
    200 /home/ubuntu/ctl_half.epd
  29755 total
```

Both sha256 values match the brief. book=ok. Seat 061 keeps every 90th line starting at line 61. Chunks 1-20 are lines 1-5000 of `mine.epd`. The control slice is the last 300 lines (from line 28946). The chunks do not reach it.

## C-ARRIVE and C-HALF

`arrive_check.txt` counts:

```
grep -c "setoption name IdeaB1 value true" ~/arrive.log
20
grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

The true count is at least 1 and the refusal count is 0. arrive=ok. The same file has the 20 log lines around the first `setoption name IdeaB1 value true` (arrive.log line 398, window 388-407).

C-HALF, `games_tsv.py pool FULL half.tsv` (`half_pool.txt`):

```
side FULL: games 400 W-L-D 212-37-151 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 13, 48, 90, 49] Elo +162.99 95% [+138.31, +189.31]
```

FULL's Elo is +162.99, above +20. half_elo=+162.99. `half.out` contains one `Finished match`.

## POOL and chunks

20 chunks, 10000 games. `games_tsv.py pool ON chunk_*.tsv` (`POOL.txt`):

```
side ON: games 10000 W-L-D 2701-2661-4638 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [258, 1190, 2063, 1232, 257] Elo +1.39 95% [-3.17, +5.95]
```

Each `chunk_N.tsv` has 500 rows and 250 distinct FENs, and every FEN is one of the 250 lines in `~/chunk_N.epd`. The first row is not always the first EPD line, because fastchess plays 3 games at once. A scan of `chunk_*.out` for `unknown option`, `invalid value` and `No such option` summed to 0. `play.log` has 0 `FAILED` lines. `play.out` ends with `minute 95: no new chunk`. Chunk 20 started at 14:57:31Z, when whole minutes since the first stamp were still 94, and it finished at 15:02:04Z with `Finished match`. It counts. No chunk was killed.

## suspicions, not proven

fastchess wrote an untracked `config.json` in the repository root during C-HALF, because that command's cwd was the repo. In that file resign, draw, maxmoves and tablebase adjudication are `enabled: false`. match.sh passes no `-draw`, `-resign`, `-maxmoves` or tablebase flag. I did not prove later chunks ignored the file. I did prove each chunk's game FENs are exactly the FENs in that chunk's EPD.

Chunk wall time moved between about 4 and 5 minutes. That is not proven to have changed a game: every chunk ended with `Finished match` and 500 scored rows.

## what I did NOT do

- No pull request.
- No engine source file committed. The patch is only in the work tree.
- Did not send IdeaB1_Scale or IdeaB1_Fade.
- Did not play the last 300 lines of mine.epd.
- No adjudication.
- Did not re-run this morning's seat 030 PGN through games_tsv.py.
- Did not commit a PGN, an executable, the net, the book, or config.json.
- A `.pyc` was committed with the STEP 2 files and removed in the following commit.

## what I am NOT sure about

I am not sure fastchess waits for `readyok` after every setoption in the matches the way the depth-12 harness does. The C-ARRIVE trace shows `setoption name IdeaB1 value true` 20 times and the refusal count is 0. I did not read every line of all 20 match logs.

The Elo and the interval are the two lines `games_tsv.py` printed. I did not compute a second interval.

## times

times: see stamps.txt

## git status --short and ls -la

The block below is the command output from just before the STEP 5 commit. `REPORT.md` and `RESULT.txt` are in that listing.

```
$ git status --short
 M forge-combo29/grok2/061/stamps.txt
?? config.json
?? forge-combo29/grok2/061/POOL.txt
?? forge-combo29/grok2/061/REPORT.md
?? forge-combo29/grok2/061/RESULT.txt
?? forge-combo29/grok2/061/chunk_20.out
?? forge-combo29/grok2/061/chunk_20.tsv
?? forge-combo29/grok2/061/honesty_summary.txt
?? forge-combo29/grok2/061/summarize_honesty.py

$ ls -la forge-combo29/grok2/061
total 3296
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2244 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:25 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    417 Nov 20 13:30 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:25 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56119 Nov 20 14:16 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51446 Nov 20 14:16 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55770 Nov 20 14:21 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51321 Nov 20 14:21 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55857 Nov 20 14:25 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 14:25 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56219 Nov 20 14:30 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51448 Nov 20 14:30 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56265 Nov 20 14:34 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 14:34 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56170 Nov 20 14:39 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 14:39 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56573 Nov 20 14:44 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51567 Nov 20 14:44 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56242 Nov 20 14:48 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51455 Nov 20 14:48 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  57015 Nov 20 14:53 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51656 Nov 20 14:53 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56007 Nov 20 14:57 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51370 Nov 20 14:57 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56759 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51279 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56415 Nov 20 15:02 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51431 Nov 20 15:02 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56324 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56291 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51360 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56305 Nov 20 13:48 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51400 Nov 20 13:48 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56146 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56497 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56301 Nov 20 14:02 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51169 Nov 20 14:02 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56146 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  57282 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51502 Nov 20 14:11 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2473 Nov 20 13:25 engine_io.py
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47041 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1057 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42260 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   2762 Nov 20 13:25 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    516 Nov 20 15:04 honesty_summary.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    878 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281920 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    916 Nov 20 13:25 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282055 Nov 20 13:25 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    914 Nov 20 13:25 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 283023 Nov 20 13:25 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   3885 Nov 20 13:25 orun.py
-rw-r--r-- 1 ubuntu ubuntu    200 Nov 20 13:25 o_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5155 Nov 20 13:25 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5155 Nov 20 13:25 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5157 Nov 20 13:25 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5368 Nov 20 13:25 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   6849 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 15:04 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    502 Nov 20 15:03 summarize_honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1847 Nov 20 13:25 summarize_o.py
```

# grok2 seat 039

Arm 9, id S13, source seat 016, branch `for-fable-and-opus/grok-016`, commit `cdde64371237fe7778c713655c0c4b5c957a5fe2`. Switch `IdeaS13`. Model Grok 4.7.

## Patch

`sha256sum ~/arm.patch` printed `f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4`, the arm table's hash. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both exited 0. The applied diff is three files: `forge-combo29/include/forge/search.hpp`, `forge-combo29/src/search.cpp`, `forge-combo29/src/uci.cpp` (64 insertions, 1 deletion). The patch is not committed. `IdeaS13_Lookback` and `IdeaS13_ReduceDivisor` were left at the patch defaults and were never sent.

## Builds

Release CMake build with g++ 13.3.0, default `FORGE_MARCH=x86-64-v4` (this machine has AVX-512 and BMI2, so `FORGE_PORTABLE` was left off). exe B: `/agent/repos/base/forge-combo29/build/forge`. exe P: `/agent/repos/work/forge-combo29/build/forge`. id name on both: `Chess Engine Forge 6.4.24 candidate`.

## Honesty

`summarize_honesty.py` reading the raw transcripts:

```
B bench11 nodes 312866 expected 312866 OK
B bench13 nodes 862329 expected 862329 OK
B bench16 nodes 3024920 expected 3024920 OK
B perft5 nodes 4865609 expected 4865609 OK
P bench11 nodes 312866 expected 312866 OK
P bench13 nodes 862329 expected 862329 OK
P bench16 nodes 3024920 expected 3024920 OK
P perft5 nodes 4865609 expected 4865609 OK
```

Each command was a fresh process, with `uci` and `isready` and no `setoption`.

## O runs

Table for arm 9: exe B sum 9500069, first three 41311 / 24872 / 28574. Switch false equals B on all 200. Switch true sum 9722445, first three 19900 / 22525 / 42778, 200 differ.

`summarize_o.py` reading `o_B.txt`, `o_Poff.txt`, `o_Pon.txt`:

```
B positions 200 sum 9500069 first 41311 / 24872 / 28574
Poff positions 200 sum 9500069 first 41311 / 24872 / 28574
Pon positions 200 sum 9722445 first 19900 / 22525 / 42778
Poff differ_from_B 0
Pon differ_from_B 200
```

S14 was sent in the stated order, then Threads 1 and Hash 16 before it, then `IdeaS13` false or true on exe P only. `ucinewgame` and `isready` before every position. `go depth 12`. FEN file sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines.

## Book

```
uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
uho.epd lines 2632036 sha 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
```

Both match the brief. Seat 039 openings are every 90th line of `uho.epd` starting at line 39 (`29245` lines in `mine.epd`).

## C-ARRIVE

`grep -c "setoption name IdeaS13 value true" ~/arrive.log` = 20. `grep -c -E "unknown option|invalid value|No such option"` = 0. The 20 log lines around the first switch `setoption` are in `arrive_check.txt`. fastchess accepted `engine=true`.

## C-HALF

`games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 237-41-122 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 11, 44, 79, 65] Elo +186.25 95% [+158.78, +216.02]
```

FULL's Elo is above +20. Pass.

## POOL

17 chunks, 8500 games. Each `chunk_N.tsv` has 500 lines. `games_tsv.py pool ON` wrote `POOL.txt`:

```
side ON: games 8500 W-L-D 2174-2362-3964 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [233, 1091, 1744, 995, 187] Elo -7.69 95% [-12.60, -2.77]
```

ON (IdeaS13 true) against OFF (IdeaS13 false), 20000 nodes, Threads 1, Hash 16, S14, no adjudication. Every termination field in the 8500 rows is `normal`.

## suspicions, not proven

None. The node counts matched the arm table. The negative Elo is the measured match result: the 95% interval is entirely below zero. C-HALF shows the node limit reaches the engine and the named side is the side the pool script scores.

## what I did NOT do

No pull request. No engine source committed. No second patch and no arm 10 (run 3 matched). No `IdeaS13_Lookback` or `IdeaS13_ReduceDivisor` setoption. No `FORGE_PORTABLE`. No `-draw`, `-resign`, `-maxmoves`, or tablebases. No repeated openings. No PGN, exe, or net file committed. No chunk was still running at minute 103, so fastchess was not killed. The seat-030 games_tsv known answer was not replayed; that PGN is not in this checkout. `config.json` written by fastchess (resign/draw/maxmoves enabled false) was not committed.

## what I am NOT sure about

Fastchess sends `IdeaS13` before Hash and the S14 options (seen in `arrive.log`). The O-run harness sends Threads, Hash, S14, then the switch. I am not sure the two orders are identical in every engine, but both set the same final values before `go`, and the O runs matched. Chunks 10 through 17 were committed by a local watcher (`~/commit_chunks.sh`) within a minute of each `Finished match`; I checked its log and `git ls-remote` afterwards rather than watching each commit in the foreground.

## times: see stamps.txt

First stamp `2026-11-20T13:22:27Z`. Last chunk stamp `2026-11-20T14:57:36Z`. `play.sh` printed `minute 95: no new chunk`.

## git status --short and ls -la

These two outputs were pasted after this file and `RESULT.txt` and `POOL.txt` were already on disk, and before the STEP 5 commit.

```
$ git status --short
 M forge-combo29/grok2/039/stamps.txt
?? config.json
?? forge-combo29/grok2/039/POOL.txt
?? forge-combo29/grok2/039/REPORT.md
?? forge-combo29/grok2/039/RESULT.txt

$ ls -la forge-combo29/grok2/039
total 2952
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2249 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    208 Nov 20 13:31 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56426 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56456 Nov 20 14:27 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 14:27 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56242 Nov 20 14:32 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51253 Nov 20 14:32 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56524 Nov 20 14:37 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51510 Nov 20 14:37 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56056 Nov 20 14:42 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 14:42 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56446 Nov 20 14:47 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:47 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56111 Nov 20 14:52 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51230 Nov 20 14:52 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56428 Nov 20 14:57 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51564 Nov 20 14:57 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56477 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51290 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56245 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56510 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51377 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56301 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51305 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56153 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56180 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51501 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56282 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56108 Nov 20 14:12 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:12 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56538 Nov 20 14:17 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51388 Nov 20 14:17 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46488 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1090 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42167 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5215 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5184 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5184 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5186 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5397 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3940 Nov 20 13:25 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    342 Nov 20 13:27 honesty_summary.txt
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281686 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    828 Nov 20 13:26 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 281893 Nov 20 13:26 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    827 Nov 20 13:26 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 282082 Nov 20 13:26 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   4487 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 13:27 o_summary.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5369 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    685 Nov 20 15:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1191 Nov 20 13:27 summarize_honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1614 Nov 20 13:25 summarize_o.py
```
